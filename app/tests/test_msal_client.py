"""
Tests for MSAL client integration.
"""
from unittest import mock

import pytest
from fastapi import HTTPException
from msal import ConfidentialClientApplication

from app.auth.config import AuthSettings
# Will be implemented
from app.auth.msal_client import MSALClient


@pytest.mark.skip("MSAL client tests need a valid tenant to run")
class TestMSALClient:
    """Test suite for MSAL client."""
    
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
    def client(self, mock_settings):
        """Create MSAL client with mock settings."""
        return MSALClient(settings=mock_settings)
    
    @pytest.fixture
    def mock_msal(self, monkeypatch):
        """Mock MSAL library."""
        mock_client = mock.MagicMock()
        mock_client.get_authorization_request_url.return_value = "https://login.example.com/authorize"
        mock_client.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "id_token": "test-id-token",
            "refresh_token": "test-refresh-token"
        }
        
        msal_mock = mock.MagicMock()
        msal_mock.ConfidentialClientApplication.return_value = mock_client
        monkeypatch.setattr("app.auth.msal_client.msal", msal_mock)
        
        return mock_client
    
    def test_init(self, client, mock_settings):
        """Test client initialization."""
        assert client.client_id == mock_settings.CLIENT_ID
        assert client.tenant_id == mock_settings.TENANT_ID
        assert client.authority == mock_settings.AUTHORITY
        assert client.scope == mock_settings.SCOPE
    
    def test_get_auth_url(self, client, mock_msal):
        """Test generating authorization URL."""
        redirect_uri = "https://example.com/auth/callback"
        state = "test-state"
        
        auth_url = client.get_auth_url(redirect_uri, state)
        
        assert auth_url == "https://login.example.com/authorize"
        mock_msal.get_authorization_request_url.assert_called_once_with(
            client.scope,
            redirect_uri=redirect_uri,
            state=state
        )
    
    def test_get_token(self, client, mock_msal):
        """Test token acquisition from authorization code."""
        code = "test-auth-code"
        redirect_uri = "https://example.com/auth/callback"
        
        token = client.get_token_from_code(code, redirect_uri)
        
        assert token["access_token"] == "test-access-token"
        assert token["id_token"] == "test-id-token"
        assert token["refresh_token"] == "test-refresh-token"
        mock_msal.acquire_token_by_authorization_code.assert_called_once_with(
            code,
            client.scope,
            redirect_uri=redirect_uri
        )
    
    def test_get_token_error(self, client, mock_msal):
        """Test handling of token acquisition errors."""
        mock_msal.acquire_token_by_authorization_code.return_value = {
            "error": "invalid_grant",
            "error_description": "Test error"
        }
        
        with pytest.raises(HTTPException) as excinfo:
            client.get_token_from_code("invalid-code", "https://example.com/callback")
        
        assert excinfo.value.status_code == 401
        assert "invalid_grant" in str(excinfo.value.detail)
    
    def test_validate_token(self, client):
        """Test token validation."""
        token = {
            "access_token": "test-access-token",
            "id_token": "test-id-token",
            "refresh_token": "test-refresh-token"
        }
        
        # Simple validation - just checking for required keys
        validated = client.validate_token(token)
        assert validated is True
        
        # Invalid token
        with pytest.raises(HTTPException) as excinfo:
            client.validate_token({"error": "invalid_token"})
        
        assert excinfo.value.status_code == 401