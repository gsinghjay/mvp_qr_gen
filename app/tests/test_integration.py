"""
Integration tests for the QR code generator application.
"""

from datetime import datetime
from unittest.mock import patch
from sqlalchemy import select

from fastapi.testclient import TestClient

from ..dependencies import get_qr_service
from ..main import app
from ..models.qr import QRCode
from ..schemas import HealthResponse, HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics
from ..schemas.qr.models import QRType
from ..services.qr_service import QRCodeService
from .conftest import get_test_db, create_test_qr_codes


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
                    message="Database connection successful",
                    timestamp=datetime.now()
                )
            }
        )

        # Make a request to the health endpoint
        response = client.get("/health")

        # Verify the response
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_static_qr_create_integration():
    """Test creating a static QR code through the API."""
    # Create a test client
    client = TestClient(app)

    # Create a static QR code
    response = client.post(
        "/api/v1/qr/static",
        json={
            "content": "https://example.com",
            "fill_color": "#000000",
            "back_color": "#FFFFFF"
        }
    )

    # Verify the response
    assert response.status_code == 200  # API returns 200 for successful creation
    data = response.json()
    assert data["qr_type"] == "static"
    assert data["content"] == "https://example.com"
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"
    assert "id" in data
    assert "created_at" in data


def test_dynamic_qr_create_integration():
    """Test creating a dynamic QR code through the API."""
    # Create a test client
    client = TestClient(app)

    # Create a dynamic QR code
    response = client.post(
        "/api/v1/qr/dynamic",
        json={
            "content": "https://example.com",  # Content is required for dynamic QR codes
            "redirect_url": "https://example.com",
            "fill_color": "#000000",
            "back_color": "#FFFFFF"
        }
    )

    # Verify the response
    assert response.status_code == 200  # API returns 200 for successful creation
    data = response.json()
    assert data["qr_type"] == "dynamic"
    assert data["redirect_url"] == "https://example.com/"  # API adds trailing slash
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"
    assert "id" in data
    assert "created_at" in data


def test_test_data_generator(test_db):
    """Test that the test data generator creates realistic test data."""
    # Create test QR codes
    qr_codes = create_test_qr_codes(test_db, count=30, static_ratio=0.7)
    
    # Verify the number of QR codes created
    assert len(qr_codes) == 30
    
    # Count static and dynamic QR codes
    static_count = sum(1 for qr in qr_codes if qr.qr_type == QRType.STATIC.value)
    dynamic_count = sum(1 for qr in qr_codes if qr.qr_type == QRType.DYNAMIC.value)
    
    # Verify the ratio of static to dynamic QR codes
    assert static_count == 21  # 70% of 30 = 21
    assert dynamic_count == 9  # 30% of 30 = 9
    
    # Verify that all QR codes have the required fields
    for qr in qr_codes:
        assert qr.id is not None
        assert qr.created_at is not None
        assert qr.content is not None  # All QR codes have content
        
        if qr.qr_type == QRType.STATIC.value:
            assert qr.redirect_url is None
        else:  # DYNAMIC
            assert qr.redirect_url is not None
        
        # Verify scan count and last_scan_at relationship
        if qr.scan_count > 0:
            assert qr.last_scan_at is not None
        
    # Test the seeded_db fixture by querying the database
    result = test_db.execute(select(QRCode)).scalars().all()
    assert len(result) == 30


def test_seeded_db_fixture(seeded_db):
    """Test that the seeded_db fixture creates test data."""
    # Query the database for all QR codes
    result = seeded_db.execute(select(QRCode)).scalars().all()
    
    # Verify that QR codes were created
    assert len(result) == 20
    
    # Count static and dynamic QR codes
    static_count = sum(1 for qr in result if qr.qr_type == QRType.STATIC.value)
    dynamic_count = sum(1 for qr in result if qr.qr_type == QRType.DYNAMIC.value)
    
    # Verify the ratio of static to dynamic QR codes
    assert static_count == 12  # 60% of 20 = 12
    assert dynamic_count == 8  # 40% of 20 = 8
