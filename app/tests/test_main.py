"""
Unit tests for the QR code generator API endpoints.
"""

import asyncio
import re
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from faker import Faker
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from unittest.mock import patch

from ..database import Base, engine, get_db
from ..dependencies import get_qr_service
from ..main import app
from ..models import QRCode
from ..schemas import QRType, HealthResponse, HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics
from ..services.qr_service import QRCodeService

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
    }
    json_payload = jsonable_encoder(payload)
    endpoint = f"/api/v1/qr/{qr_type.value}"
    response = client.post(endpoint, json=json_payload)
    assert response.status_code == 200, f"Failed to create QR code: {response.text}"
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
    # No need to override dependencies, already handled by client fixture
    
    payload = {
        "content": "https://example.com",
        "qr_type": QRType.STATIC,
        "redirect_url": None,
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
    }
    json_payload = jsonable_encoder(payload)

    response = client.post("/api/v1/qr/static", json=json_payload)
    assert response.status_code == 200, f"Failed to create static QR code: {response.text}"
    data = response.json()

    # Verify response data
    assert data["content"] == "https://example.com"
    assert data["qr_type"] == QRType.STATIC
    assert data["redirect_url"] is None
    assert "id" in data
    assert "created_at" in data
    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    assert created_at.tzinfo is not None, "created_at should be timezone-aware"
    assert data["scan_count"] == 0
    assert data["last_scan_at"] is None
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"

    # Verify database state
    db_qr = test_db.query(QRCode).filter(QRCode.id == data["id"]).first()
    assert db_qr is not None
    assert db_qr.content == "https://example.com"
    assert db_qr.created_at.tzinfo is not None, "Database created_at should be timezone-aware"


def test_create_dynamic_qr(client: TestClient, test_db: Session):
    """Test creating a dynamic QR code."""
    # No need to override dependencies, already handled by client fixture
    
    payload = {
        "content": "My GitHub",
        "qr_type": QRType.DYNAMIC,
        "redirect_url": "https://github.com/example",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
    }
    json_payload = jsonable_encoder(payload)

    response = client.post("/api/v1/qr/dynamic", json=json_payload)
    assert response.status_code == 200, f"Failed to create dynamic QR code: {response.text}"
    data = response.json()

    # Verify response data
    assert data["qr_type"] == QRType.DYNAMIC
    assert data["redirect_url"] == "https://github.com/example"
    assert data["content"].startswith("/r/")
    assert "id" in data
    assert "created_at" in data
    assert data["scan_count"] == 0
    assert data["last_scan_at"] is None
    assert data["fill_color"] == "#000000"
    assert data["back_color"] == "#FFFFFF"

    # Verify database state
    db_qr = test_db.query(QRCode).filter(QRCode.id == data["id"]).first()
    assert db_qr is not None
    assert db_qr.redirect_url == "https://github.com/example"
    assert db_qr.content.startswith("/r/")


def test_list_qr_codes(client: TestClient, test_db: Session):
    """Test listing QR codes with pagination."""
    # Clean any existing data to ensure predictable test state
    test_db.query(QRCode).delete()
    test_db.commit()
    
    # Create test QR codes
    static_qr = create_test_qr_code(client, QRType.STATIC)
    dynamic_qr = create_test_qr_code(client, QRType.DYNAMIC)
    
    # Store the IDs of the created QR codes
    created_ids = {static_qr["id"], dynamic_qr["id"]}
    
    # Test listing with pagination
    response = client.get("/api/v1/qr?skip=0&limit=10")
    assert response.status_code == 200, f"Failed to list QR codes: {response.text}"
    data = response.json()
    
    # Verify response structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    
    # Ensure our created QR codes are in the results
    result_ids = {item["id"] for item in data["items"]}
    assert created_ids.issubset(result_ids), f"Created QR codes {created_ids} not found in results {result_ids}"
    
    # Expect at least our 2 created items
    assert data["total"] >= 2
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_get_qr_code(client: TestClient, test_db: Session):
    """Test getting a specific QR code by ID."""
    # Create a test QR code
    created_qr = create_test_qr_code(client, QRType.STATIC)
    test_db.commit()

    # Get the QR code
    response = client.get(f"/api/v1/qr/{created_qr['id']}")
    assert response.status_code == 200
    data = response.json()

    # Verify response data
    assert data["id"] == created_qr["id"]
    assert data["content"] == created_qr["content"]
    assert data["qr_type"] == created_qr["qr_type"]
    assert data["fill_color"] == created_qr["fill_color"]
    assert data["back_color"] == created_qr["back_color"]


def test_get_qr_image(client: TestClient, test_db: Session):
    """Test getting a QR code image."""
    # Create a test QR code
    created_qr = create_test_qr_code(client, QRType.STATIC)
    test_db.commit()

    # Test different image formats
    format_content_types = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "webp": "image/webp",
    }

    for fmt, content_type in format_content_types.items():
        response = client.get(f"/api/v1/qr/{created_qr['id']}/image?image_format={fmt}")
        assert response.status_code == 200
        assert response.headers["content-type"] == content_type


@pytest.mark.asyncio
async def test_dynamic_qr_redirect(client: TestClient, test_db: Session):
    """Test dynamic QR code redirection and concurrent access."""
    # No need to override dependencies, already handled by client fixture
    
    # Create a dynamic QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    short_id = created_qr["content"].replace("/r/", "")
    
    # Ensure the QR code was created and properly saved in the database
    db_qr = test_db.query(QRCode).filter(QRCode.id == created_qr["id"]).first()
    assert db_qr is not None, "QR code was not found in the database"
    assert db_qr.redirect_url == created_qr["redirect_url"]
    
    # Get initial scan count
    initial_scan_count = db_qr.scan_count
    
    # Test redirection
    response = client.get(f"/r/{short_id}", follow_redirects=False)
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}"
    assert response.headers["location"] == created_qr["redirect_url"]
    
    # Verify scan count was updated (in background task)
    # Need to give the background task time to complete
    await asyncio.sleep(0.1)
    
    # Refresh the database object
    test_db.refresh(db_qr)
    assert db_qr.scan_count == initial_scan_count + 1, "Scan count should have been incremented"
    assert db_qr.last_scan_at is not None, "Last scan timestamp should be set"


def test_update_dynamic_qr(client: TestClient, test_db: Session):
    """Test updating a dynamic QR code's redirect URL."""
    # No need to override dependencies, already handled by client fixture
    
    # Create a dynamic QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    
    # Update redirect URL
    new_url = "https://github.com/new-example"
    response = client.put(f"/api/v1/qr/{created_qr['id']}", json={"redirect_url": new_url})
    assert response.status_code == 200, f"Failed to update QR code: {response.text}"
    data = response.json()
    
    # Verify response data
    assert data["id"] == created_qr["id"]
    assert data["qr_type"] == QRType.DYNAMIC
    assert data["redirect_url"] == new_url
    assert data["content"] == created_qr["content"]
    assert data["fill_color"] == created_qr["fill_color"]
    assert data["back_color"] == created_qr["back_color"]
    
    # Verify database state
    db_qr = test_db.query(QRCode).filter(QRCode.id == created_qr["id"]).first()
    assert db_qr is not None
    assert db_qr.redirect_url == new_url


@pytest.mark.parametrize(
    "qr_type,expected_status,include_redirect",
    [
        (QRType.STATIC, 200, False),
        (QRType.DYNAMIC, 200, True),
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
    """Test QR code color validation with various formats."""
    # Override the QR service dependency to use the test database
    def get_test_qr_service():
        yield QRCodeService(test_db)
    
    app.dependency_overrides[get_qr_service] = get_test_qr_service
    
    payload = {
        "content": fake.url(),
        "qr_type": QRType.STATIC,
        "fill_color": color,
        "back_color": ("#000000" if color == "#FFFFFF" else "#FFFFFF"),  # Ensure different colors
        "size": 10,
        "border": 4,
    }

    json_payload = jsonable_encoder(payload)
    response = client.post("/api/v1/qr/static", json=json_payload)

    # Clean up dependency override
    app.dependency_overrides.pop(get_qr_service, None)
    
    # Valid hex colors should succeed, others should fail validation
    is_valid_hex = bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))
    expected_status = 200 if is_valid_hex else 422
    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status} for color {color}, got {response.status_code}"

    if expected_status == 200:
        data = response.json()
        assert data["fill_color"] == color.upper()
        assert data["back_color"] == payload["back_color"].upper()
        assert data["qr_type"] == QRType.STATIC


@pytest.mark.asyncio
async def test_concurrent_qr_code_access(client: TestClient, test_db: Session):
    """Test concurrent access to QR codes."""
    # No need to override dependencies, already handled by client fixture
    
    # Create a test QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    short_id = created_qr["content"].replace("/r/", "")
    
    # Ensure the QR code was created and properly saved in the database
    db_qr = test_db.query(QRCode).filter(QRCode.id == created_qr["id"]).first()
    assert db_qr is not None, "QR code was not found in the database"
    
    # Initial scan count
    initial_scan_count = db_qr.scan_count
    
    # Number of concurrent requests
    num_requests = 5
    
    # Define a function to access the QR code
    async def access_qr():
        # Use the client to make requests
        response = client.get(f"/r/{short_id}", follow_redirects=False)
        assert response.status_code == 302
        return response.status_code
    
    # Create tasks for concurrent access
    tasks = [access_qr() for _ in range(num_requests)]
    
    # Run concurrent requests
    results = await asyncio.gather(*tasks)
    
    # Verify all requests were successful
    assert all(status_code == 302 for status_code in results)
    
    # Give background tasks time to complete
    await asyncio.sleep(0.2)
    
    # Check that scan count was updated correctly (should be initial + num_requests)
    test_db.refresh(db_qr)
    assert db_qr.scan_count == initial_scan_count + num_requests, f"Expected scan count {initial_scan_count + num_requests}, got {db_qr.scan_count}"


def test_health_check_endpoint(client: TestClient):
    """Test the health check endpoint."""
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
    with patch('app.services.health.HealthService.get_health_status') as mock_health:
        # Configure the mock to return a degraded response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.DEGRADED,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(
                cpu_usage=92.0,  # High CPU usage
                memory_usage=20.0,
                disk_usage=30.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.WARN,
                    latency_ms=500.0,  # High latency
                    message="Database connection slow",
                    last_checked=datetime.now()
                )
            }
        )
        
        # Make a request to the health check endpoint
        response = client.get("/health")
        
        # Degraded still returns 200 OK but with degraded status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


def test_health_check_unhealthy(client: TestClient):
    """Test the health check endpoint when service is unhealthy."""
    with patch('app.services.health.HealthService.get_health_status') as mock_health:
        # Configure the mock to return an unhealthy response
        mock_health.return_value = HealthResponse(
            status=HealthStatus.UNHEALTHY,
            version="1.0.0",
            uptime_seconds=100.0,
            system_metrics=SystemMetrics(
                cpu_usage=10.0,
                memory_usage=20.0,
                disk_usage=30.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.FAIL,
                    latency_ms=0.0,
                    message="Database connection failed",
                    last_checked=datetime.now()
                )
            }
        )
        
        # Make a request to the health check endpoint
        response = client.get("/health")
        
        # Unhealthy returns 503 Service Unavailable
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "Service is currently unhealthy" in data["detail"]
