"""
Tests for the group membership authentication functionality.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from fastapi import HTTPException

from app.auth.sso import User, get_user_groups, is_user_in_group, requires_group


class AsyncMockResponse:
    """Mock response for httpx."""
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.data = data or {}
    
    def json(self):
        return self.data


class AsyncClientContextManagerMock:
    """Async context manager mock for httpx.AsyncClient."""
    
    def __init__(self, mock_response=None):
        self.mock_response = mock_response or AsyncMockResponse(
            status_code=200,
            data={
                "value": [
                    {
                        "@odata.type": "#microsoft.graph.group",
                        "id": "group1",
                        "displayName": "Test Group 1"
                    },
                    {
                        "@odata.type": "#microsoft.graph.group",
                        "id": "admin-group",
                        "displayName": "Administrators"
                    },
                    {
                        # This is not a group and should be filtered out
                        "@odata.type": "#microsoft.graph.directoryRole",
                        "id": "role1",
                        "displayName": "Directory Role"
                    }
                ]
            }
        )
        self.get = AsyncMock(return_value=self.mock_response)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_get_user_groups_success():
    """Test getting user groups from Microsoft Graph API successfully."""
    mock_client = AsyncClientContextManagerMock()
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        groups = await get_user_groups("test-access-token")
        
        # Verify the correct groups were returned
        assert len(groups) == 2
        assert "group1" in groups
        assert "admin-group" in groups
        assert "role1" not in groups  # Should filter out non-group types
        
        # Verify the API call was made correctly
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert args[0] == "https://graph.microsoft.com/v1.0/me/memberOf"
        assert kwargs["headers"]["Authorization"] == "Bearer test-access-token"


@pytest.mark.asyncio
async def test_get_user_groups_api_error():
    """Test handling API errors when getting user groups."""
    # Configure mock to return an error
    mock_client = AsyncClientContextManagerMock(
        mock_response=AsyncMockResponse(status_code=401, data={})
    )
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        # This should return an empty list instead of raising an exception
        groups = await get_user_groups("invalid-token")
        
        # Should return empty list on error
        assert groups == []


@pytest.mark.asyncio
async def test_get_user_groups_exception():
    """Test handling exceptions when getting user groups."""
    # Configure the client to raise an exception
    with patch("httpx.AsyncClient", side_effect=Exception("Test error")):
        # This should return an empty list instead of raising an exception
        groups = await get_user_groups("test-token")
        
        # Should return empty list on exception
        assert groups == []


def test_requires_group_factory():
    """Test the requires_group dependency factory."""
    # Create a dependency
    dependency = requires_group("admin-group")
    
    # Create users
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
    
    # Test the dependency with admin user
    # This should not raise an exception
    async def test_admin():
        result = await dependency(admin_user)
        assert result == admin_user
    
    import asyncio
    asyncio.run(test_admin())
    
    # Test the dependency with regular user
    # This should raise a 403 exception
    async def test_regular():
        with pytest.raises(HTTPException) as excinfo:
            await dependency(regular_user)
        assert excinfo.value.status_code == 403
    
    asyncio.run(test_regular())


def test_group_membership_in_token():
    """Test that group membership is correctly included in the JWT token."""
    from app.auth.sso import create_access_token
    from jose import jwt
    from app.core.config import settings
    
    # Create test data
    user_id = "test-user-id"
    email = "test@example.com"
    name = "Test User"
    groups = ["group1", "admin-group"]
    
    # Create a token
    token = create_access_token({
        "sub": user_id,
        "email": email,
        "name": name,
        "groups": groups
    })
    
    # Decode the token without verifying the signature
    # This is acceptable for testing because we're only checking that the data is included
    payload = jwt.decode(
        token,
        settings.SESSION_SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_signature": False}
    )
    
    # Verify the token contains the correct data
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["name"] == name
    assert payload["groups"] == groups 