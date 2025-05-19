"""
Unit tests for the QR code generator API endpoints.
"""

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from faker import Faker
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..dependencies import get_qr_service
from ..main import app
from ..models import QRCode
from ..models.qr import QRCode
from ..schemas import (
    HealthResponse,
    HealthStatus,
    QRType,
    ServiceCheck,
    ServiceStatus,
    SystemMetrics,
)
from ..schemas.qr.models import QRType
from ..services.qr_service import QRCodeService
from .utils import validate_color_code, validate_qr_code_data

# Initialize Faker for generating test data
fake = Faker()

# The setup_database fixture is imported from conftest.py


def create_test_qr_code(client: TestClient, qr_type: QRType = QRType.STATIC) -> dict:
    """Helper function to create a test QR code."""
    # No need to override dependencies, already handled by client fixture

    # Ensure different colors for fill and background
    fill_color = "#000000"
    back_color = "#FFFFFF"

    # Generate a random short_id for dynamic QR codes
    short_id = str(uuid.uuid4())[:8]

    # For dynamic QR codes, we should set the content to include the "/r/" prefix
    # that would be used in redirection
    content = fake.url() if qr_type == QRType.STATIC else f"/r/{short_id}"

    payload = {
        "content": content,
        "qr_type": qr_type,
        "redirect_url": fake.url() if qr_type == QRType.DYNAMIC else None,
        "fill_color": fill_color,
        "back_color": back_color,
        "size": 10,
        "border": 4,
        "title": f"Test {qr_type.value.title()} QR",
        "description": f"A test {qr_type.value} QR code generated for testing",
    }
    json_payload = jsonable_encoder(payload)
    endpoint = f"/api/v1/qr/{qr_type.value}"
    response = client.post(endpoint, json=json_payload)
    assert response.status_code == 201, f"Failed to create QR code: {response.text}"
    data = response.json()

    # Verify timezone-aware datetime fields
    assert "created_at" in data, "Response missing created_at field"
    created_at_str = data["created_at"]

    # Handle 'Z' suffix by replacing with '+00:00'
    if created_at_str.endswith("Z"):
        created_at_str = created_at_str[:-1] + "+00:00"

    try:
        created_at = datetime.fromisoformat(created_at_str)
        assert created_at.tzinfo is not None, "created_at should be timezone-aware"
        assert created_at.tzinfo == UTC, "created_at should be in UTC"
    except ValueError as e:
        pytest.fail(f"Invalid created_at format: {created_at_str}. Error: {str(e)}")

    if data.get("last_scan_at"):
        last_scan_at_str = data["last_scan_at"]
        if last_scan_at_str.endswith("Z"):
            last_scan_at_str = last_scan_at_str[:-1] + "+00:00"

        try:
            last_scan_at = datetime.fromisoformat(last_scan_at_str)
            assert last_scan_at.tzinfo is not None, "last_scan_at should be timezone-aware"
            assert last_scan_at.tzinfo == UTC, "last_scan_at should be in UTC"
        except ValueError as e:
            pytest.fail(f"Invalid last_scan_at format: {last_scan_at_str}. Error: {str(e)}")

    return data


def test_create_static_qr(client: TestClient, test_db: Session):
    """Test creating a static QR code."""
    payload = {
        "content": "https://example.com",
        "qr_type": QRType.STATIC,
        "redirect_url": None,
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
        "title": "Test Static QR",
        "description": "A test static QR code",
    }
    json_payload = jsonable_encoder(payload)

    response = client.post("/api/v1/qr/static", json=json_payload)
    assert response.status_code == 201, f"Failed to create static QR code: {response.text}"
    data = response.json()

    # Use our utility function to validate the response data
    assert validate_qr_code_data(
        data,
        {
            "content": "https://example.com",
            "qr_type": "static",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "redirect_url": None,
            "title": "Test Static QR",
        },
    )

    # Verify the QR code was created in the database
    qr_id = data["id"]
    qr = test_db.query(QRCode).filter(QRCode.id == qr_id).first()
    assert qr is not None
    assert validate_qr_code_data(
        {
            "id": str(qr.id),
            "content": qr.content,
            "qr_type": qr.qr_type,
            "fill_color": qr.fill_color,
            "back_color": qr.back_color,
            "redirect_url": qr.redirect_url,
            "created_at": qr.created_at.isoformat(),
        }
    )


def test_create_dynamic_qr(client: TestClient, test_db: Session):
    """Test creating a dynamic QR code."""
    payload = {
        "content": None,  # Content is optional for dynamic QR codes
        "redirect_url": "https://example.com/redirect",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
        "title": "Test Dynamic QR",
        "description": "A test dynamic QR code",
    }
    json_payload = jsonable_encoder(payload)

    response = client.post("/api/v1/qr/dynamic", json=json_payload)
    assert response.status_code == 201, f"Failed to create dynamic QR code: {response.text}"
    data = response.json()

    # Use our utility function to validate the response data
    assert validate_qr_code_data(
        data,
        {
            "qr_type": "dynamic",
            "redirect_url": "https://example.com/redirect",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "title": "Test Dynamic QR",
        },
    )

    # Verify the content starts with "/r/" for redirection
    assert "/r/" in data["content"], f"Content should contain '/r/': {data['content']}"

    # Verify the QR code was created in the database
    qr_id = data["id"]
    qr = test_db.query(QRCode).filter(QRCode.id == qr_id).first()
    assert qr is not None
    assert validate_qr_code_data(
        {
            "id": str(qr.id),
            "content": qr.content,
            "qr_type": qr.qr_type,
            "redirect_url": qr.redirect_url,
            "fill_color": qr.fill_color,
            "back_color": qr.back_color,
            "created_at": qr.created_at.isoformat(),
        }
    )


def test_list_qr_codes(client: TestClient, test_db: Session):
    """Test listing QR codes with pagination."""
    # Create some test QR codes
    qr_codes = []
    for i in range(5):
        qr = create_test_qr_code(client, QRType.STATIC if i % 2 == 0 else QRType.DYNAMIC)
        qr_codes.append(qr)

    # Test listing all QR codes
    response = client.get("/api/v1/qr")
    assert response.status_code == 200
    data = response.json()

    # Verify pagination fields
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= len(qr_codes)

    # Test pagination
    response = client.get("/api/v1/qr?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2

    # Test filtering by type
    response = client.get("/api/v1/qr?qr_type=static")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["qr_type"] == "static"


def test_get_qr_code(client: TestClient, test_db: Session):
    """Test retrieving a QR code by ID."""
    # Create a test QR code
    qr = create_test_qr_code(client, QRType.STATIC)
    qr_id = qr["id"]

    # Test retrieving the QR code
    response = client.get(f"/api/v1/qr/{qr_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify the response data
    assert data["id"] == qr_id
    assert data["qr_type"] == "static"
    assert data["content"] == qr["content"]
    assert data["fill_color"] == qr["fill_color"]
    assert data["back_color"] == qr["back_color"]

    # Test retrieving a non-existent QR code
    response = client.get("/api/v1/qr/non-existent-id")
    assert response.status_code == 404


def test_get_qr_image(client: TestClient, test_db: Session):
    """Test retrieving a QR code image."""
    # Create a test QR code
    qr = create_test_qr_code(client, QRType.STATIC)
    qr_id = qr["id"]

    # Test retrieving the QR code image in different formats
    for image_format in ["png", "jpeg", "svg", "webp"]:
        response = client.get(f"/api/v1/qr/{qr_id}/image?image_format={image_format}")
        assert response.status_code == 200

        # Verify the content type
        if image_format == "svg":
            assert response.headers["content-type"] == "image/svg+xml"
        else:
            assert response.headers["content-type"] == f"image/{image_format}"

        # Verify the image content
        assert len(response.content) > 0

    # Test retrieving a non-existent QR code image
    response = client.get("/api/v1/qr/non-existent-id/image")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dynamic_qr_redirect(client: TestClient, test_db: Session):
    """Test dynamic QR code redirection."""
    # Create a dynamic QR code
    redirect_url = "https://example.com/redirect"
    qr = create_test_qr_code(client, QRType.DYNAMIC)

    # Extract the path from the content (should be like "/r/abc123")
    redirect_path = qr["content"]
    assert "/r/" in redirect_path, f"Redirect path should contain '/r/': {redirect_path}"

    # Test the redirection
    response = client.get(redirect_path, follow_redirects=False)
    assert response.status_code == 302  # HTTP 302 Found
    assert response.headers["location"] == qr["redirect_url"]

    # Verify the scan count was incremented
    response = client.get(f"/api/v1/qr/{qr['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["scan_count"] == 1
    assert data["last_scan_at"] is not None

    # Test redirection for a non-existent path
    response = client.get("/r/non-existent", follow_redirects=False)
    assert response.status_code == 404


def test_update_dynamic_qr(client: TestClient, test_db: Session):
    """Test updating a dynamic QR code."""
    # Create a dynamic QR code
    qr = create_test_qr_code(client, QRType.DYNAMIC)
    qr_id = qr["id"]

    # Update the redirect URL
    new_redirect_url = "https://example.com/updated"
    response = client.put(f"/api/v1/qr/{qr_id}", json={"redirect_url": new_redirect_url})
    assert response.status_code == 200
    data = response.json()

    # Verify the response data
    assert data["id"] == qr_id
    assert data["redirect_url"] == new_redirect_url

    # Verify the QR code was updated in the database
    updated_qr = test_db.query(QRCode).filter(QRCode.id == qr_id).first()
    assert updated_qr is not None
    assert updated_qr.redirect_url == new_redirect_url

    # Test updating a non-existent QR code
    response = client.put("/api/v1/qr/non-existent-id", json={"redirect_url": new_redirect_url})
    assert response.status_code == 404

    # Test updating a static QR code (should fail)
    static_qr = create_test_qr_code(client, QRType.STATIC)
    response = client.put(f"/api/v1/qr/{static_qr['id']}", json={"redirect_url": new_redirect_url})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "qr_type,expected_status,include_redirect",
    [
        (QRType.STATIC, 201, False),
        (QRType.DYNAMIC, 201, True),
        ("invalid", 422, False),
        (QRType.DYNAMIC, 422, False),  # Dynamic without redirect_url should fail
        (QRType.STATIC, 422, True),  # Static with redirect_url should fail
    ],
)
def test_qr_code_types(
    client: TestClient, test_db: Session, qr_type, expected_status, include_redirect
):
    """Test different QR code types with expected outcomes."""

    # Override the QR service dependency to use the test database
    def get_test_qr_service():
        yield QRCodeService(test_db)

    app.dependency_overrides[get_qr_service] = get_test_qr_service

    payload = {
        "content": fake.url() if qr_type == QRType.STATIC else fake.company(),
        "qr_type": qr_type,
        "fill_color": fake.hex_color().upper(),  # Ensure uppercase hex color
        "back_color": fake.hex_color().upper(),  # Ensure uppercase hex color
        "size": fake.random_int(min=5, max=50),
        "border": fake.random_int(min=1, max=10),
    }

    if include_redirect:
        payload["redirect_url"] = fake.url()

    json_payload = jsonable_encoder(payload)

    # Choose the correct endpoint based on the QR type
    if qr_type == QRType.STATIC:
        endpoint = "/api/v1/qr/static"
    elif qr_type == QRType.DYNAMIC:
        endpoint = "/api/v1/qr/dynamic"
    else:
        # For invalid type, use dynamic endpoint to test validation
        endpoint = "/api/v1/qr/dynamic"

    response = client.post(endpoint, json=json_payload)

    # Clean up dependency override
    app.dependency_overrides.pop(get_qr_service, None)

    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status} for QR type {qr_type}, got {response.status_code}. Response: {response.text}"

    if expected_status == 200:
        data = response.json()
        assert data["qr_type"] == qr_type
        assert (
            data["fill_color"].upper() == payload["fill_color"].upper()
        )  # Case-insensitive comparison
        assert (
            data["back_color"].upper() == payload["back_color"].upper()
        )  # Case-insensitive comparison
        if include_redirect:
            assert data["redirect_url"] == payload["redirect_url"]


@pytest.mark.parametrize(
    "color",
    [
        "#000000",  # Valid black
        "#FFFFFF",  # Valid white
        "#FF0000",  # Valid red
        "invalid",  # Invalid format
        "#FFG000",  # Invalid hex
        "rgb(0,0,0)",  # Invalid format
        "",  # Empty string
    ],
)
def test_qr_code_color_validation(client: TestClient, test_db: Session, color):
    """Test QR code color validation."""
    # Create a QR code with the test color
    payload = {
        "content": "https://example.com",
        "fill_color": color,
        "back_color": "#FFFFFF" if color != "#FFFFFF" else "#000000",  # Ensure different colors
    }

    # Attempt to create the QR code
    response = client.post("/api/v1/qr/static", json=payload)

    # Check if the color is valid using our utility function
    try:
        validate_color_code(color)
        expected_status = 201
    except AssertionError:
        expected_status = 422

    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status} for color {color}, got {response.status_code}"


@pytest.mark.asyncio
async def test_concurrent_qr_code_access(client: TestClient, test_db: Session):
    """Test concurrent access to QR codes."""
    # Create a dynamic QR code
    qr = create_test_qr_code(client, QRType.DYNAMIC)
    qr_id = qr["id"]
    redirect_path = qr["content"]

    # Define a function to simulate concurrent access
    async def access_qr():
        # Use the client to make requests
        response = client.get(redirect_path, follow_redirects=False)
        assert response.status_code == 302  # HTTP 302 Found
        return response

    # Simulate concurrent access
    tasks = [access_qr() for _ in range(5)]
    await asyncio.gather(*tasks)

    # Verify the scan count was incremented correctly
    response = client.get(f"/api/v1/qr/{qr_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["scan_count"] == 5
    assert data["last_scan_at"] is not None


def test_health_check_endpoint(client: TestClient):
    """Test the health check endpoint."""
    with patch("app.services.health.HealthService.get_health_status") as mock_health:
        # Configure the mock to return a healthy response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(cpu_usage=10.0, memory_usage=20.0, disk_usage=30.0),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.PASS,
                    latency_ms=5.0,
                    message="Database connection successful",
                    last_checked=datetime.now(),
                )
            },
        )

        # Make a request to the health check endpoint
        response = client.get("/health")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "system_metrics" in data
        assert "checks" in data
        assert "database" in data["checks"]


def test_health_check_degraded(client: TestClient):
    """Test the health check endpoint when service is degraded."""
    with patch("app.services.health.HealthService.get_health_status") as mock_health:
        # Configure the mock to return a degraded response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.DEGRADED,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(
                cpu_usage=92.0, memory_usage=20.0, disk_usage=30.0  # High CPU usage
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.WARN,
                    latency_ms=500.0,  # High latency
                    message="Database connection slow",
                    last_checked=datetime.now(),
                )
            },
        )

        # Make a request to the health check endpoint
        response = client.get("/health")

        # Degraded still returns 200 OK but with degraded status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


def test_health_check_unhealthy(client: TestClient):
    """Test the health check endpoint when service is unhealthy."""
    with patch("app.services.health.HealthService.get_health_status") as mock_health:
        # Configure the mock to return an unhealthy response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.UNHEALTHY,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(cpu_usage=10.0, memory_usage=20.0, disk_usage=30.0),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.FAIL,
                    latency_ms=0.0,
                    message="Database connection failed",
                    last_checked=datetime.now(),
                )
            },
        )

        # Make a request to the health check endpoint
        response = client.get("/health")

        # Unhealthy returns 503 Service Unavailable
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Service is currently unhealthy" in data["detail"]
