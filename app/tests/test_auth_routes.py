"""
Tests for authentication routes.
"""
from unittest import mock

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from starlette.datastructures import URL, State
from starlette.middleware.sessions import SessionMiddleware

from app.auth.config import AuthSettings
from app.auth.msal_client import MSALClient
from app.routers.auth import auth_router


class TestAuthRoutes:
    """Test suite for authentication routes."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock authentication settings."""
        return AuthSettings(
            CLIENT_ID="test-client-id",
            CLIENT_SECRET="test-client-secret",
            TENANT_ID="test-tenant-id",
            REDIRECT_PATH="/auth/callback",
            SCOPE=["User.Read", "profile", "email"]
        )
    
    @pytest.fixture
    def mock_auth_client(self, mock_settings):
        """Create a mock MSAL client."""
        client = mock.MagicMock(spec=MSALClient)
        client.get_auth_url.return_value = "https://login.example.com/auth"
        client.get_token_from_code.return_value = {
            "access_token": "test-access-token",
            "id_token": "test-id-token",
            "refresh_token": "test-refresh-token"
        }
        client.get_token_claims.return_value = {
            "oid": "test-user-id",
            "name": "Test User",
            "preferred_username": "test.user@example.com"
        }
        # Add settings attribute
        client.settings = mock_settings
        return client
    
    @pytest.fixture
    def app(self, mock_auth_client):
        """Create a test FastAPI app with auth router."""
        app = FastAPI()
        # Add session middleware for tests
        app.add_middleware(
            SessionMiddleware,
            secret_key="test-secret-key",
            session_cookie="session",
            max_age=86400,
            same_site="lax",
            https_only=False
        )
        app.include_router(auth_router)
        app.state.auth_client = mock_auth_client
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app, base_url="http://testserver")
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_login_redirect(self, client, mock_auth_client):
        """Test login endpoint redirects to Microsoft login."""
        response = client.get("/auth/login")
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert mock_auth_client.get_auth_url.called
        
        # Check Location header contains the auth URL
        assert "location" in response.headers
        assert response.headers["location"] == "https://login.example.com/auth"
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_login_with_next(self, client, mock_auth_client):
        """Test login endpoint with next parameter."""
        response = client.get("/auth/login?next=/protected")
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        mock_auth_client.get_auth_url.assert_called_once()
        
        # Check that the state includes the next URL
        call_args = mock_auth_client.get_auth_url.call_args[1]
        assert "state" in call_args
        assert "/protected" in call_args["state"]
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_callback_success(self, client, mock_auth_client):
        """Test callback endpoint with successful authorization."""
        response = client.get(
            "/auth/callback?code=test-auth-code&state={}"
        )
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        mock_auth_client.get_token_from_code.assert_called_once()
        
        # Should redirect to home by default
        assert response.headers["location"] == "/"
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_callback_with_next(self, client, mock_auth_client):
        """Test callback endpoint with next parameter in state."""
        # Create state with next URL
        import json
        import base64
        state = base64.b64encode(
            json.dumps({"next": "/protected"}).encode()
        ).decode()
        
        response = client.get(
            f"/auth/callback?code=test-auth-code&state={state}"
        )
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/protected"
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_callback_error(self, client):
        """Test callback endpoint with error."""
        response = client.get(
            "/auth/callback?error=access_denied&error_description=User+canceled"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "access_denied" in response.text
        assert "User canceled" in response.text
    
    @pytest.mark.skip("Route tests need more complex setup in Docker environment")
    def test_logout(self, client):
        """Test logout endpoint clears session."""
        # Set a cookie with session data
        client.cookies.set("session", "session-data")
        
        response = client.get("/auth/logout")
        
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/"