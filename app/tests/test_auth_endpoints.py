"""
Tests for authentication endpoints.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from fastapi_sso.sso.microsoft import MicrosoftSSO
from fastapi.responses import RedirectResponse

from app.auth.sso import User
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
    
    # Make request to logout endpoint
    response = client.get("/auth/logout", follow_redirects=False)
    
    # Check that response is a redirect to home
    assert response.status_code == 307
    assert response.headers["location"] == "/"
    
    # Check that auth_token cookie was cleared
    # In TestClient, the cookie is not actually in response.cookies but in the Set-Cookie header
    assert "Set-Cookie" in response.headers
    assert "auth_token=" in response.headers["Set-Cookie"]
    assert "Max-Age=0" in response.headers["Set-Cookie"] or "expires=Thu, 01 Jan 1970" in response.headers["Set-Cookie"]


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