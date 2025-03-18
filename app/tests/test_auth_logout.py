"""
Tests for the enhanced logout functionality.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.auth.sso import create_access_token, User
from app.main import app
from app.core.config import settings


@pytest.fixture
def test_client_with_auth_cookie():
    """Create a test client with an authentication cookie."""
    # Create a test client
    client = TestClient(app)
    
    # Create a token for testing
    test_token = create_access_token(
        data={"sub": "test-user", "email": "test@example.com", "name": "Test User"},
        expires_delta=timedelta(minutes=15)
    )
    
    # Set the token as a cookie
    client.cookies.set("auth_token", test_token)
    
    return client


def test_logout_clears_auth_cookie(test_client_with_auth_cookie):
    """Test that logout endpoint properly clears the auth cookie."""
    client = test_client_with_auth_cookie
    
    # Verify auth cookie is set before logout
    assert "auth_token" in client.cookies, "Auth cookie should be set before logout"
    
    # Create client with no redirects
    no_redirect_client = TestClient(app, follow_redirects=False)
    no_redirect_client.cookies.set("auth_token", client.cookies["auth_token"])
    
    # Perform logout with mocked settings to prevent Azure AD logout
    # We need to patch both AZURE_CLIENT_ID and AZURE_TENANT_ID to None to force local logout
    with patch.multiple(settings, 
                     ENVIRONMENT="development",
                     AZURE_CLIENT_ID=None,
                     AZURE_TENANT_ID=None):
        response = no_redirect_client.get("/auth/logout")
    
    # Check status code - should be a redirect
    assert response.status_code == 307, "Logout should return a redirect"
    
    # Check that response is redirecting to the correct page
    assert response.headers["location"] == "/portal-login", "Should redirect to portal-login"
    
    # Check for Set-Cookie header that clears the cookie
    assert "Set-Cookie" in response.headers, "Response should include Set-Cookie header"
    
    # Check cookie properties in the Set-Cookie header
    cookie_header = response.headers["Set-Cookie"]
    assert "auth_token=" in cookie_header, "Cookie header should contain auth_token"
    assert "Max-Age=0" in cookie_header, "Cookie should have Max-Age=0"
    assert "Path=/" in cookie_header, "Cookie should have Path=/"
    assert "HttpOnly" in cookie_header, "Cookie should be HttpOnly"
    
    # Check for cache control headers
    assert "Cache-Control" in response.headers, "Response should include Cache-Control header"
    assert "no-cache" in response.headers["Cache-Control"], "Cache-Control should include no-cache"
    assert "Pragma" in response.headers, "Response should include Pragma header"
    assert "no-cache" in response.headers["Pragma"], "Pragma should be no-cache"
    assert "Expires" in response.headers, "Response should include Expires header"
    assert "0" in response.headers["Expires"], "Expires should be 0"
    
    # Note: We can't check the client.cookies state here because TestClient doesn't 
    # update its cookies from response headers in the same way a browser would.
    # In a real browser, the cookie would be cleared.


def test_logout_redirects_to_azure_in_production():
    """Test that logout endpoint redirects to Azure AD logout in production."""
    # Create a client with no redirects
    no_redirect_client = TestClient(app, follow_redirects=False)
    
    # Create a token for testing
    test_token = create_access_token(
        data={"sub": "test-user-id", "email": "test@example.com", "name": "Test User"},
        expires_delta=timedelta(minutes=15)
    )
    
    # Set the token in cookies
    no_redirect_client.cookies.set("auth_token", test_token)
    
    # Mock production environment and Azure AD settings
    with patch.multiple(settings, 
                      ENVIRONMENT="production", 
                      AZURE_CLIENT_ID="test-client-id",
                      AZURE_TENANT_ID="test-tenant-id"):
        
        # Mock the base_url property to return a predictable value
        mock_request = MagicMock()
        mock_request.base_url = "https://example.com/"
        
        with patch("app.routers.auth.Request", return_value=mock_request):
            response = no_redirect_client.get("/auth/logout")
        
        # Check status code - should be a redirect
        assert response.status_code == 307, "Logout should return a redirect"
        
        # Check that response is redirecting to Azure AD logout
        expected_base_url = "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/logout"
        assert expected_base_url in response.headers["location"], f"Should redirect to Azure AD logout, got {response.headers['location']}"
        
        # Check that the client_id parameter is included
        assert "client_id=test-client-id" in response.headers["location"], "Client ID should be in the redirect URL"
        
        # Check that the post_logout_redirect_uri parameter is included
        assert "post_logout_redirect_uri=" in response.headers["location"], "Post-logout redirect URI should be in the redirect URL"


def test_authenticated_routes_after_logout():
    """Test that authenticated routes are no longer accessible after logout."""
    # Create a client with a mock user dependency for authenticated state
    client = TestClient(app)
    
    # Create a user for authentication
    mock_user = User(id="test-user-id", email="test@example.com", display_name="Test User")
    
    # First check that we can access an authenticated endpoint when properly authenticated
    with patch("app.auth.sso.get_current_user", return_value=mock_user):
        # Set the token in cookies
        token = create_access_token({"sub": mock_user.id, "email": mock_user.email, "name": mock_user.display_name})
        client.cookies.set("auth_token", token)
        
        pre_response = client.get("/auth/me")
        assert pre_response.status_code == 200, "Should be able to access /auth/me when authenticated"
        assert pre_response.json()["id"] == "test-user-id"
    
    # Now simulate logging out by clearing the cookie and patching the dependency to raise 401
    client.cookies.clear()
    
    # This reflects what happens after logout - no valid token, so get_current_user raises an exception
    post_response = client.get("/auth/me")
    assert post_response.status_code == 401, "Should not be able to access /auth/me after logout"
    assert "detail" in post_response.json(), "Response should include an error detail"
    assert "Could not validate credentials" in post_response.json()["detail"], "Error should mention credentials" 