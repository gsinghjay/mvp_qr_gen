"""
Tests for authentication dependencies.
"""
from unittest import mock

import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import State

from app.auth.msal_client import MSALClient
# Will be implemented
from app.auth.dependencies import get_current_user, get_auth_client


class TestAuthDependencies:
    """Test suite for authentication dependencies."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request with session."""
        mock_req = mock.MagicMock(spec=Request)
        mock_req.session = {}
        mock_req.app = mock.MagicMock()
        mock_req.app.state = State()
        mock_req.app.state.auth_client = mock.MagicMock(spec=MSALClient)
        
        return mock_req
    
    @pytest.fixture
    def mock_user_data(self):
        """Mock user data from token claims."""
        return {
            "oid": "test-user-id",
            "name": "Test User",
            "preferred_username": "test.user@example.com",
            "roles": ["User"]
        }
    
    def test_get_auth_client(self, mock_request):
        """Test retrieving the auth client from app state."""
        client = get_auth_client(mock_request)
        assert client is mock_request.app.state.auth_client
    
    def test_get_current_user_authenticated(self, mock_request, mock_user_data):
        """Test current user is returned when authenticated."""
        # Set user in session
        mock_request.session["user"] = mock_user_data
        
        user = get_current_user(mock_request)
        assert user == mock_user_data
        assert user["name"] == "Test User"
        assert user["oid"] == "test-user-id"
    
    def test_get_current_user_unauthenticated(self, mock_request):
        """Test exception is raised when user is not authenticated."""
        # Empty session
        mock_request.session = {}
        
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(mock_request)
        
        assert excinfo.value.status_code == 401
        assert "Not authenticated" in str(excinfo.value.detail)
    
    def test_get_current_user_partial_session(self, mock_request):
        """Test exception is raised when session is incomplete."""
        # Incomplete session data
        mock_request.session["partial"] = "data"
        
        with pytest.raises(HTTPException) as excinfo:
            get_current_user(mock_request)
        
        assert excinfo.value.status_code == 401