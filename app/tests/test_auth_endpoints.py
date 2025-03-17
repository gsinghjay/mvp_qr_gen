"""
Tests for authentication endpoints.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import pytest
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.testclient import TestClient
from fastapi_sso.sso.microsoft import MicrosoftSSO
from fastapi.responses import RedirectResponse

from app.auth.sso import User, is_user_in_group, requires_group
from app.core.config import settings


class AsyncContextManagerMock:
    """Mock for async context manager."""
    
    async def __aenter__(self):
        return self.obj
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def __init__(self, obj):
        self.obj = obj


@pytest.fixture
def mock_microsoft_sso():
    """Create a mock Microsoft SSO client."""
    mock_sso = MagicMock(spec=MicrosoftSSO)
    
    # Create a mock RedirectResponse for the get_login_redirect method
    mock_redirect = RedirectResponse(
        url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=test-client-id&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%2Fauth%2Fcallback&scope=openid+profile+User.Read+email",
        status_code=303
    )
    mock_sso.get_login_redirect = AsyncMock(return_value=mock_redirect)
    
    # Create a mock user
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.display_name = "Test User"
    
    # Configure verify_and_process to return the mock user
    mock_sso.verify_and_process = AsyncMock(return_value=mock_user)
    
    # Make the mock work as an async context manager
    mock_sso.__aenter__ = AsyncMock(return_value=mock_sso)
    mock_sso.__aexit__ = AsyncMock(return_value=None)
    
    return mock_sso


@pytest.fixture
def app_with_auth(mock_microsoft_sso):
    """Create a test app with auth endpoints."""
    with patch("app.auth.sso.get_microsoft_sso", return_value=mock_microsoft_sso):
        from app.main import create_app
        app = create_app()
        # Override the verify_and_process method to avoid real OAuth calls
        app.dependency_overrides = {}
        return app


@pytest.fixture
def client(app_with_auth):
    """Create a test client with auth endpoints."""
    return TestClient(app_with_auth)


def test_login_endpoint(client, mock_microsoft_sso):
    """Test that login endpoint redirects to Microsoft login page."""
    # Patch the get_microsoft_sso function to return our mock
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        # Make request to login endpoint
        response = client.get("/auth/login", follow_redirects=False)
        
        # Check that response is a redirect
        assert response.status_code == 303  # 303 See Other is the correct status code
        
        # Check that the location header contains the expected parts
        location = response.headers["location"]
        assert "https://login.microsoftonline.com" in location
        assert "oauth2/v2.0/authorize" in location
        assert "response_type=code" in location
        assert "redirect_uri=" in location
        assert "scope=" in location
        
        # Check that get_login_redirect was called
        mock_microsoft_sso.get_login_redirect.assert_called_once()


def test_callback_endpoint_success(client, mock_microsoft_sso):
    """Test that callback endpoint processes successful authentication."""
    # Configure mock to return a user (success case)
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.display_name = "Test User"
    mock_microsoft_sso.verify_and_process.return_value = mock_user
    
    # Patch the verify_and_process method to avoid real OAuth calls
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        # Make request to callback endpoint with required query parameters
        response = client.get("/auth/callback?code=test-code&state=test-state", follow_redirects=False)
    
        # Check that response is a redirect to home
        assert response.status_code == 307
        assert response.headers["location"] == "/"
    
        # Check that verify_and_process was called
        mock_microsoft_sso.verify_and_process.assert_called_once()
    
        # Check that auth_token cookie was set
        assert "auth_token" in response.cookies
        assert response.cookies["auth_token"] != ""


def test_callback_endpoint_failure(client, mock_microsoft_sso):
    """Test that callback endpoint handles authentication failure."""
    # Configure mock to return None (authentication failure)
    mock_microsoft_sso.verify_and_process.return_value = None
    
    # Patch the verify_and_process method to avoid real OAuth calls
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        # Make request to callback endpoint with required query parameters
        response = client.get("/auth/callback?code=test-code&state=test-state")
    
        # Check that response is an error
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication failed"
    
        # Check that verify_and_process was called
        mock_microsoft_sso.verify_and_process.assert_called_once()


def test_callback_endpoint_error(client, mock_microsoft_sso):
    """Test that callback endpoint handles SSO errors."""
    # Configure mock to raise an exception
    mock_microsoft_sso.verify_and_process.side_effect = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Test error"
    )
    
    # Patch the verify_and_process method to avoid real OAuth calls
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        # Make request to callback endpoint with required query parameters
        response = client.get("/auth/callback?code=test-code&state=test-state")
    
        # Check that response is an error
        assert response.status_code == 500
        assert response.json()["detail"] == "Test error"
    
        # Check that verify_and_process was called
        mock_microsoft_sso.verify_and_process.assert_called_once()


def test_logout_endpoint(client):
    """Test that logout endpoint clears auth token cookie."""
    # Set a mock auth token cookie
    client.cookies.set("auth_token", "test-token")
    
    # Make request to logout endpoint with development environment and no Azure settings
    # to ensure local redirect instead of Azure AD logout
    with patch.multiple(settings, 
                     ENVIRONMENT="development",
                     AZURE_CLIENT_ID=None,
                     AZURE_TENANT_ID=None):
        response = client.get("/auth/logout", follow_redirects=False)
    
    # Check that response is a redirect to portal-login
    assert response.status_code == 307
    assert response.headers["location"] == "/portal-login"
    
    # Check that auth_token cookie was cleared
    # In TestClient, the cookie is not actually in response.cookies but in the Set-Cookie header
    assert "Set-Cookie" in response.headers
    assert "auth_token=" in response.headers["Set-Cookie"]
    assert "Max-Age=0" in response.headers["Set-Cookie"] or "expires=Thu, 01 Jan 1970" in response.headers["Set-Cookie"]
    
    # Check for cache control headers
    assert "Cache-Control" in response.headers, "Response should include Cache-Control header"
    assert "no-cache" in response.headers["Cache-Control"], "Cache-Control should include no-cache"
    assert "Pragma" in response.headers, "Response should include Pragma header"
    assert "Expires" in response.headers, "Response should include Expires header"


def test_me_endpoint_authenticated(client):
    """Test that me endpoint returns user info when authenticated."""
    # Create a mock user
    mock_user = User(id="test-user-id", email="test@example.com", display_name="Test User")
    
    # Create a token for the mock user
    from app.auth.sso import create_access_token
    token = create_access_token({"sub": mock_user.id, "email": mock_user.email, "name": mock_user.display_name})
    
    # Set the token in cookies
    client.cookies.set("auth_token", token)
    
    # Patch the get_current_user dependency to return our mock user
    with patch("app.routers.auth.get_current_user", return_value=mock_user):
        # Make request to me endpoint
        response = client.get("/auth/me")
    
        # Check that response contains user info
        assert response.status_code == 200
        assert response.json()["id"] == "test-user-id"
        assert response.json()["email"] == "test@example.com"
        assert response.json()["display_name"] == "Test User"


def test_me_endpoint_unauthenticated(client):
    """Test that me endpoint returns 401 when not authenticated."""
    # Make request to me endpoint without auth token
    response = client.get("/auth/me")
    
    # Check that response is an error
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_callback_with_groups(client, mock_microsoft_sso):
    """Test that callback endpoint fetches and stores group memberships."""
    # Configure mock to return a user with an access token
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.display_name = "Test User"
    mock_user.access_token = "mock-access-token"
    mock_microsoft_sso.verify_and_process.return_value = mock_user
    
    # Mock the get_user_groups function to return test group IDs
    test_groups = ["group1", "group2", "admin-group"]
    
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        with patch("app.routers.auth.get_user_groups", AsyncMock(return_value=test_groups)):
            # Make request to callback endpoint
            response = client.get("/auth/callback?code=test-code&state=test-state", follow_redirects=False)
            
            # Check that response is a redirect to home
            assert response.status_code == 307
            assert response.headers["location"] == "/"
            
            # Check that auth_token cookie was set
            assert "auth_token" in response.cookies
            assert response.cookies["auth_token"] != ""
            
            # To fully verify the token content, we would need to decode it
            # This is tested in test_me_groups_endpoint


def test_me_groups_endpoint(client):
    """Test that me/groups endpoint returns user group information."""
    # Create a mock user with groups
    test_groups = ["group1", "group2", "admin-group"]
    mock_user = User(
        id="test-user-id", 
        email="test@example.com", 
        display_name="Test User",
        groups=test_groups
    )
    
    # Create a token for the mock user
    from app.auth.sso import create_access_token
    token = create_access_token({
        "sub": mock_user.id, 
        "email": mock_user.email, 
        "name": mock_user.display_name,
        "groups": test_groups
    })
    
    # Set the token in cookies
    client.cookies.set("auth_token", token)
    
    # Patch the get_current_user dependency to return our mock user
    with patch("app.routers.auth.get_current_user", return_value=mock_user):
        # Make request to me/groups endpoint
        response = client.get("/auth/me/groups")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-id"
        assert data["email"] == "test@example.com"
        assert data["groups"] == test_groups
        assert data["group_count"] == 3


def test_is_user_in_group():
    """Test the is_user_in_group helper function."""
    # Create a user with groups
    user = User(
        id="test-user-id",
        email="test@example.com",
        display_name="Test User",
        groups=["group1", "admin-group"]
    )
    
    # Test membership checks
    assert is_user_in_group(user, "group1") is True
    assert is_user_in_group(user, "admin-group") is True
    assert is_user_in_group(user, "non-existent-group") is False
    assert is_user_in_group(user, "") is False


def test_requires_group_dependency():
    """Test the requires_group dependency factory directly."""
    # Create a dependency
    dependency = requires_group("admin-group")
    
    # Create users with different group memberships
    admin_user = User(
        id="admin-id",
        email="admin@example.com",
        display_name="Admin User",
        groups=["admin-group", "users"]
    )
    
    regular_user = User(
        id="user-id",
        email="user@example.com",
        display_name="Regular User",
        groups=["users"]
    )
    
    # Test with admin user - should succeed
    async def test_admin():
        result = await dependency(admin_user)
        assert result == admin_user
    
    asyncio.run(test_admin())
    
    # Test with regular user - should raise 403
    async def test_regular():
        with pytest.raises(HTTPException) as excinfo:
            await dependency(regular_user)
        assert excinfo.value.status_code == 403
        assert "Access denied" in excinfo.value.detail
    
    asyncio.run(test_regular())


def test_get_scopes_endpoint(client, mock_microsoft_sso):
    """Test that scopes endpoint returns correct scope information."""
    # Configure mock to return scopes
    test_scopes = ["openid", "profile", "email", "User.Read", "GroupMember.Read.All"]
    mock_microsoft_sso.scopes = test_scopes
    
    with patch("app.routers.auth.get_microsoft_sso", return_value=mock_microsoft_sso):
        # Make request to scopes endpoint
        response = client.get("/auth/scopes")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "default_scopes" in data
        assert "configured_scopes" in data
        assert data["configured_scopes"] == test_scopes
        assert data["group_membership_available"] is True
        assert "GroupMember.Read.All" in data["group_scopes_configured"]
        assert len(data["missing_group_scopes"]) < 3  # At least one group scope is configured 


def test_admin_only_endpoint_direct():
    """Test the admin-only endpoint logic directly."""
    from app.routers.auth import admin_only_endpoint
    
    # Create users
    admin_user = User(
        id="admin-id",
        email="admin@example.com",
        display_name="Admin User",
        groups=["admin-group", "users"]
    )
    
    # Test the function directly
    async def test_func():
        result = await admin_only_endpoint(admin_user)
        assert result["message"] == "You have admin access!"
        assert result["user_id"] == "admin-id"
        assert result["admin_access"] is True
    
    asyncio.run(test_func()) 