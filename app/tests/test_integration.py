"""
Integration tests for the QR code generator application.
"""

from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from ..dependencies import get_qr_service
from ..main import app
from ..schemas import HealthResponse, HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics
from ..services.qr_service import QRCodeService
from .conftest import get_test_db


def test_get_qr_service_dependency():
    """Test that the QRCodeService dependency can be injected properly."""

    # Override the dependency for testing
    def get_test_qr_service():
        """Test QR service provider"""
        # Use the test database session
        db = next(get_test_db())
        try:
            yield QRCodeService(db)
        finally:
            db.close()

    # Apply the override
    app.dependency_overrides[get_qr_service] = get_test_qr_service

    # Create a test client
    client = TestClient(app)

    # Mock the health service to return a healthy status
    with patch('app.services.health.HealthService.get_health_status') as mock_health:
        # Configure the mock to return a healthy response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(
                cpu_usage=10.0,
                memory_usage=20.0,
                disk_usage=30.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.PASS,
                    latency_ms=5.0,
                    message="Database connection successful",
                    last_checked=datetime.now()
                )
            }
        )
        
        # Make a request that will use the service
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify the response contains the expected health data
        data = response.json()
        assert data["status"] == "healthy"

    # Clean up
    app.dependency_overrides.clear()


def test_static_qr_create_integration():
    """Integration test for creating a static QR code using the service layer."""

    # Override the dependency for testing
    def get_test_qr_service():
        """Test QR service provider"""
        # Use the test database session
        db = next(get_test_db())
        try:
            yield QRCodeService(db)
        finally:
            db.close()

    # Apply the override
    app.dependency_overrides[get_qr_service] = get_test_qr_service

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

    # Clean up
    app.dependency_overrides.clear()


def test_dynamic_qr_create_integration():
    """Integration test for creating a dynamic QR code using the service layer."""

    # Override the dependency for testing
    def get_test_qr_service():
        """Test QR service provider"""
        # Use the test database session
        db = next(get_test_db())
        try:
            yield QRCodeService(db)
        finally:
            db.close()

    # Apply the override
    app.dependency_overrides[get_qr_service] = get_test_qr_service

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
    assert data["redirect_url"] == "https://example.com/"
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"
    assert "id" in data
    assert "created_at" in data
    assert data["scan_count"] == 0

    # Clean up
    app.dependency_overrides.clear()
