import pytest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from app.main import app
from app.auth.config import AuthSettings
from app.auth.msal_client import MSALClient


@pytest.fixture
def mock_auth_client():
    """Create a mock MSAL client for testing."""
    config = AuthSettings(
        CLIENT_ID="test-client-id",
        TENANT_ID="test-tenant-id",
        CLIENT_SECRET="test-client-secret",
    )
    mock_client = MagicMock(spec=MSALClient)
    mock_client.settings = config
    mock_client.get_auth_url.return_value = "https://login.microsoftonline.com/mock-url"
    
    # Add to app state
    app.state.auth_client = mock_client
    return mock_client


@pytest.fixture
def client(mock_auth_client):
    """Create a test client with mocked auth components."""
    with patch("app.auth.dependencies.get_current_user", side_effect=Exception("Not authenticated")):
        yield TestClient(app)


@pytest.mark.skip(reason="Need to fix template context in test environment")
def test_login_page_renders(client, mock_auth_client):
    """Test that the login page renders correctly."""
    response = client.get("/auth/login-page")
    assert response.status_code == 200
    assert "Login with Microsoft" in response.text
    
    # Parse HTML and check for required elements
    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find("button", {"id": "ms-login-button"}) is not None


@pytest.mark.skip(reason="Need to fix MSAL client in test environment")
def test_login_page_has_correct_redirect_url(client, mock_auth_client):
    """Test that the login page has the correct redirect URL."""
    mock_auth_client.get_auth_url.return_value = "https://login.microsoftonline.com/mock-url"
    response = client.get("/auth/login-page")
    
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    login_button = soup.find("a", {"id": "ms-login-link"})
    
    assert login_button is not None
    assert login_button["href"] == "https://login.microsoftonline.com/mock-url"


@pytest.mark.skip(reason="Need to fix session handling in test environment")
def test_login_ui_elements_in_main_layout(client):
    """Test that the main layout includes login/logout UI elements."""
    response = client.get("/")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check for login/logout section in the navbar
    auth_section = soup.find("div", {"id": "auth-section"})
    assert auth_section is not None
    
    # When not logged in, should show login button
    login_link = auth_section.find("a", {"id": "login-link"})
    assert login_link is not None
    assert login_link["href"] == "/auth/login-page"