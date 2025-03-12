"""
Integration tests for the QR code generator application.
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from ..dependencies import get_qr_service
from ..main import app
from ..models.qr import QRCode
from ..schemas.qr.models import QRType
from ..services.qr_service import QRCodeService
from .conftest import create_test_qr_code
from .utils import validate_qr_code_data


def test_get_qr_service_dependency(test_db):
    """Test that the QRCodeService dependency can be injected properly."""

    # Override the dependency for testing
    def get_test_qr_service():
        """Test QR service provider"""
        # Use the test database session directly
        yield QRCodeService(test_db)

    # Store original dependency
    original_dependency = app.dependency_overrides.get(get_qr_service)

    # Override with test version
    app.dependency_overrides[get_qr_service] = get_test_qr_service

    # Create a client
    client = TestClient(app)

    # Test creating a QR code to verify the dependency works
    response = client.post(
        "/api/v1/qr/static",
        json={
            "content": "https://example.com",
            "qr_type": "static",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        },
    )

    # Verify response
    assert response.status_code == 201  # API returns 201 Created for successful creation

    # Restore original dependency
    if original_dependency:
        app.dependency_overrides[get_qr_service] = original_dependency
    else:
        del app.dependency_overrides[get_qr_service]


def test_static_qr_create_integration():
    """Test creating a static QR code through the API."""
    # Create a test client
    client = TestClient(app)

    # Create a static QR code
    response = client.post(
        "/api/v1/qr/static",
        json={"content": "https://example.com", "fill_color": "#000000", "back_color": "#FFFFFF"},
    )

    # Verify the response
    assert response.status_code == 201  # API returns 201 Created for successful creation
    data = response.json()
    assert validate_qr_code_data(
        data,
        {
            "qr_type": "static",
            "content": "https://example.com",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        },
    )


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
            "back_color": "#FFFFFF",
        },
    )

    # Verify the response
    assert response.status_code == 201  # API returns 201 Created for successful creation
    data = response.json()
    assert validate_qr_code_data(
        data,
        {
            "qr_type": "dynamic",
            "redirect_url": "https://example.com/",  # API adds trailing slash
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        },
    )


def test_test_data_generator(test_db):
    """Test that the test data generator creates valid QR codes."""
    # Create a test QR code
    test_qr = create_test_qr_code(
        db=test_db,
        qr_type=QRType.STATIC,
        content="https://example.com",
        fill_color="#000000",
        back_color="#FFFFFF",
        scan_count=5,
        created_days_ago=3,
        last_scan_days_ago=1,
    )

    # Verify the QR code was created with the right properties
    assert test_qr.id is not None
    assert test_qr.content == "https://example.com"
    assert test_qr.qr_type == "static"
    assert test_qr.redirect_url is None
    assert test_qr.fill_color == "#000000"
    assert test_qr.back_color == "#FFFFFF"
    assert test_qr.scan_count == 5

    # Verify the dates were set correctly
    now = datetime.now(UTC)
    assert (now - test_qr.created_at).days >= 3
    assert test_qr.last_scan_at is not None
    assert (now - test_qr.last_scan_at).days >= 1

    # Verify we can find it in the database
    result = test_db.scalar(select(QRCode).where(QRCode.id == test_qr.id))
    assert result is not None
    assert result.id == test_qr.id


def test_seeded_db_fixture(seeded_db):
    """Test that the seeded_db fixture provides a database with test data."""
    # Query for all QR codes
    result = seeded_db.execute(select(QRCode)).scalars().all()

    # Verify that there are QR codes in the database
    assert len(result) > 0

    # Verify that both static and dynamic QR codes are present
    static_count = sum(1 for qr in result if qr.qr_type == "static")
    dynamic_count = sum(1 for qr in result if qr.qr_type == "dynamic")

    assert static_count > 0, "No static QR codes found"
    assert dynamic_count > 0, "No dynamic QR codes found"

    # Verify that we can find QR codes by ID
    qr = result[0]
    found_qr = seeded_db.scalar(select(QRCode).where(QRCode.id == qr.id))
    assert found_qr is not None
    assert found_qr.id == qr.id
