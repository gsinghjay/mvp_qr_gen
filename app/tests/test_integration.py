"""
Integration tests for the QR code generator application.
"""

from fastapi.testclient import TestClient

from ..dependencies import get_qr_service
from ..main import app
from ..services.qr_service import QRCodeService


def test_get_qr_service_dependency():
    """Test that the QRCodeService dependency can be injected properly."""

    # Override the dependency for testing
    def get_test_qr_service():
        """Test QR service provider"""
        from ..database import get_db

        # Get a test database session
        with get_db() as db:
            yield QRCodeService(db)

    # Apply the override
    app.dependency_overrides[get_qr_service] = get_test_qr_service

    # Create a test client
    client = TestClient(app)

    # Make a request that will use the service
    response = client.get("/health")
    assert response.status_code == 200

    # Clean up
    app.dependency_overrides.clear()


def test_static_qr_create_integration():
    """Integration test for creating a static QR code using the service layer."""

    # Create a test client
    client = TestClient(app)

    # Create a static QR code
    response = client.post(
        "/api/v1/qr/static",
        json={
            "content": "test-content",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        },
    )

    # Assert response is successful
    assert response.status_code == 200

    # Validate response data
    data = response.json()
    assert data["content"] == "test-content"
    assert data["qr_type"] == "static"
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"
    assert "id" in data
    assert "created_at" in data
    assert data["scan_count"] == 0


def test_dynamic_qr_create_integration():
    """Integration test for creating a dynamic QR code using the service layer."""

    # Create a test client
    client = TestClient(app)

    # Create a dynamic QR code
    response = client.post(
        "/api/v1/qr/dynamic",
        json={
            "content": "test-content",
            "redirect_url": "https://example.com",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        },
    )

    # Assert response is successful
    assert response.status_code == 200

    # Validate response data
    data = response.json()
    assert data["qr_type"] == "dynamic"
    assert data["redirect_url"] == "https://example.com"
    assert data["content"].startswith("/r/")
    assert "id" in data
    assert "created_at" in data
    assert data["scan_count"] == 0

    # Test updating the QR code
    qr_id = data["id"]
    update_response = client.put(
        f"/api/v1/qr/dynamic/{qr_id}",
        json={
            "redirect_url": "https://example.com/updated",
        },
    )

    # Assert update is successful
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["redirect_url"] == "https://example.com/updated"
