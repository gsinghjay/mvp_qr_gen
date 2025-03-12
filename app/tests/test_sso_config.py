"""
Tests for SSO configuration and integration.
"""
import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.auth.sso import get_microsoft_sso, create_access_token


@pytest.fixture
def app_with_sso():
    """Create a test app with SSO configuration."""
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app_with_sso):
    """Create a test client with SSO configuration."""
    return TestClient(app_with_sso)


def test_sso_config_loads_from_env():
    """Test that SSO configuration loads from environment variables."""
    with patch.dict(os.environ, {
        "AZURE_CLIENT_ID": "test-client-id",
        "AZURE_CLIENT_SECRET": "test-client-secret",
        "AZURE_TENANT_ID": "test-tenant-id",
        "SESSION_SECRET_KEY": "test-secret-key"
    }):
        # Reload settings to pick up new environment variables
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Check that settings were loaded correctly
        assert config.settings.AZURE_CLIENT_ID == "test-client-id"
        assert config.settings.AZURE_CLIENT_SECRET == "test-client-secret"
        assert config.settings.AZURE_TENANT_ID == "test-tenant-id"
        assert config.settings.SESSION_SECRET_KEY == "test-secret-key"


def test_microsoft_sso_initialization():
    """Test that Microsoft SSO client initializes correctly."""
    with patch.dict(os.environ, {
        "AZURE_CLIENT_ID": "test-client-id",
        "AZURE_CLIENT_SECRET": "test-client-secret",
        "AZURE_TENANT_ID": "test-tenant-id",
        "SESSION_SECRET_KEY": "test-secret-key"
    }):
        # Reload settings to pick up new environment variables
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Also reload the auth.sso module to pick up the new settings
        from app.auth import sso
        reload(sso)
        
        # Get Microsoft SSO client
        microsoft_sso = sso.get_microsoft_sso()
        
        # Check that client was initialized correctly
        assert microsoft_sso.client_id == "test-client-id"
        assert microsoft_sso.client_secret == "test-client-secret"
        assert microsoft_sso.tenant == "test-tenant-id"
        assert microsoft_sso.allow_insecure_http == (config.settings.ENVIRONMENT != "production")


def test_jwt_token_creation():
    """Test that JWT tokens are created correctly."""
    with patch.dict(os.environ, {
        "SESSION_SECRET_KEY": "test-secret-key"
    }):
        # Reload settings to pick up new environment variables
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Also reload the auth.sso module to pick up the new settings
        from app.auth import sso
        reload(sso)
        
        # Create a token
        token_data = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "name": "Test User"
        }
        token = sso.create_access_token(token_data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0 