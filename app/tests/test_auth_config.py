"""
Tests for authentication configuration.
"""
import os
from unittest.mock import patch

import pytest
from jose import jwt

from app.core.config import settings
from app.auth.sso import create_access_token


def test_settings_has_sso_config():
    """Test that settings has SSO configuration."""
    assert hasattr(settings, "AZURE_CLIENT_ID")
    assert hasattr(settings, "AZURE_CLIENT_SECRET")
    assert hasattr(settings, "AZURE_TENANT_ID")
    assert hasattr(settings, "SESSION_SECRET_KEY")
    assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")


def test_create_access_token():
    """Test that access tokens can be created and decoded."""
    # Create test data
    test_data = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Create token
    token = create_access_token(test_data)
    
    # Decode token
    payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=["HS256"])
    
    # Check that payload contains expected data
    assert payload["sub"] == "test-user-id"
    assert payload["email"] == "test@example.com"
    assert payload["name"] == "Test User"
    assert "exp" in payload  # Expiration time should be set


def test_env_variables_loaded():
    """Test that environment variables are loaded correctly."""
    # Use patch to mock environment variables for testing
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