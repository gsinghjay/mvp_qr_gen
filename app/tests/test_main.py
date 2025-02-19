"""
Unit tests for the QR code generator API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks, HTTPException
from fastapi.encoders import jsonable_encoder
from ..main import app
from ..database import Base, engine
from ..schemas import QRType, QRCodeCreate, QRCodeResponse
from ..models import QRCode
import json
from datetime import datetime, timezone
import time
import asyncio
import httpx
import uuid
from sqlalchemy.orm import Session
import os
from faker import Faker
import re

# Initialize Faker for generating test data
fake = Faker()

@pytest.fixture(autouse=True)
def setup_database():
    """Setup a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def create_test_qr_code(client: TestClient, qr_type: QRType = QRType.STATIC) -> dict:
    """Helper function to create a test QR code."""
    # Ensure different colors for fill and background
    fill_color = "#000000"
    back_color = "#FFFFFF"
    
    payload = {
        "content": fake.url() if qr_type == QRType.STATIC else fake.company(),
        "qr_type": qr_type,
        "redirect_url": fake.url() if qr_type == QRType.DYNAMIC else None,
        "fill_color": fill_color,
        "back_color": back_color,
        "size": 10,
        "border": 4
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
    if created_at_str.endswith('Z'):
        created_at_str = created_at_str[:-1] + '+00:00'
    
    try:
        created_at = datetime.fromisoformat(created_at_str)
        assert created_at.tzinfo is not None, "created_at should be timezone-aware"
        assert created_at.tzinfo == timezone.utc, "created_at should be in UTC"
    except ValueError as e:
        pytest.fail(f"Invalid created_at format: {created_at_str}. Error: {str(e)}")
    
    if data.get("last_scan_at"):
        last_scan_at_str = data["last_scan_at"]
        if last_scan_at_str.endswith('Z'):
            last_scan_at_str = last_scan_at_str[:-1] + '+00:00'
        
        try:
            last_scan_at = datetime.fromisoformat(last_scan_at_str)
            assert last_scan_at.tzinfo is not None, "last_scan_at should be timezone-aware"
            assert last_scan_at.tzinfo == timezone.utc, "last_scan_at should be in UTC"
        except ValueError as e:
            pytest.fail(f"Invalid last_scan_at format: {last_scan_at_str}. Error: {str(e)}")
    
    return data

def test_create_static_qr(client: TestClient, test_db: Session):
    """Test creating a static QR code."""
    payload = {
        "content": "https://example.com",
        "qr_type": QRType.STATIC,
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4
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
    payload = {
        "content": "My GitHub",
        "qr_type": QRType.DYNAMIC,
        "redirect_url": "https://github.com/example",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4
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

def test_list_qr_codes(client: TestClient, test_db: Session):
    """Test listing QR codes with pagination."""
    # Create test QR codes
    static_qr = create_test_qr_code(client, QRType.STATIC)
    dynamic_qr = create_test_qr_code(client, QRType.DYNAMIC)
    
    # Test listing with pagination
    response = client.get("/api/v1/qr?skip=0&limit=10")
    assert response.status_code == 200, f"Failed to list QR codes: {response.text}"
    data = response.json()
    
    # Verify response structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 10

    # Verify QR codes are in the response
    qr_ids = {item["id"] for item in data["items"]}
    assert static_qr["id"] in qr_ids
    assert dynamic_qr["id"] in qr_ids

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
        "webp": "image/webp"
    }
    
    for fmt, content_type in format_content_types.items():
        response = client.get(f"/api/v1/qr/{created_qr['id']}/image?image_format={fmt}")
        assert response.status_code == 200
        assert response.headers["content-type"] == content_type

@pytest.mark.asyncio
async def test_dynamic_qr_redirect(client: TestClient, test_db: Session):
    """Test dynamic QR code redirection and concurrent access."""
    # Create a dynamic QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    short_id = created_qr["content"].replace("/r/", "")
    
    # Test redirection
    response = client.get(f"/r/{short_id}", follow_redirects=False)
    assert response.status_code == 302, f"Failed to redirect: {response.text}"
    
    # Compare URLs ignoring scheme (http vs https)
    redirect_url = response.headers["location"]
    expected_url = created_qr["redirect_url"]
    assert redirect_url.replace("https://", "").replace("http://", "") == \
           expected_url.replace("https://", "").replace("http://", ""), \
           f"Redirect URL mismatch: got {redirect_url}, expected {expected_url}"

    # Verify scan count and timestamp are updated
    db_qr = test_db.query(QRCode).filter(QRCode.id == created_qr["id"]).first()
    assert db_qr.scan_count == 1
    assert db_qr.last_scan_at is not None
    assert db_qr.last_scan_at.tzinfo is not None  # Verify timezone awareness

def test_update_dynamic_qr(client: TestClient, test_db: Session):
    """Test updating a dynamic QR code's redirect URL."""
    # Create a dynamic QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    
    # Update redirect URL
    new_url = "https://github.com/new-example"
    response = client.put(
        f"/api/v1/qr/{created_qr['id']}",
        json={"redirect_url": new_url}
    )
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
    
    # Test error cases
    
    # Test updating non-existent QR code
    response = client.put(
        f"/api/v1/qr/{uuid.uuid4()}",
        json={"redirect_url": new_url}
    )
    assert response.status_code == 404
    
    # Test updating static QR code
    static_qr = create_test_qr_code(client, QRType.STATIC)
    response = client.put(
        f"/api/v1/qr/{static_qr['id']}",
        json={"redirect_url": new_url}
    )
    assert response.status_code == 400
    
    # Test invalid redirect URL
    response = client.put(
        f"/api/v1/qr/{created_qr['id']}",
        json={"redirect_url": "not-a-url"}
    )
    assert response.status_code == 422

@pytest.mark.parametrize("qr_type,expected_status,include_redirect", [
    (QRType.STATIC, 200, False),
    (QRType.DYNAMIC, 200, True),
    ("invalid", 422, False),
    (QRType.DYNAMIC, 422, False),  # Dynamic without redirect_url should fail
    (QRType.STATIC, 422, True)     # Static with redirect_url should fail
])
def test_qr_code_types(client: TestClient, test_db: Session, qr_type, expected_status, include_redirect):
    """Test different QR code types with expected outcomes."""
    payload = {
        "content": fake.url() if qr_type == QRType.STATIC else fake.company(),
        "qr_type": qr_type,
        "fill_color": fake.hex_color().upper(),  # Ensure uppercase hex color
        "back_color": fake.hex_color().upper(),  # Ensure uppercase hex color
        "size": fake.random_int(min=5, max=50),
        "border": fake.random_int(min=1, max=10)
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
    
    assert response.status_code == expected_status, f"Expected status {expected_status} for QR type {qr_type}, got {response.status_code}. Response: {response.text}"
    
    if expected_status == 200:
        data = response.json()
        assert data["qr_type"] == qr_type
        assert data["fill_color"].upper() == payload["fill_color"].upper()  # Case-insensitive comparison
        assert data["back_color"].upper() == payload["back_color"].upper()  # Case-insensitive comparison
        if include_redirect:
            assert data["redirect_url"] == payload["redirect_url"]

@pytest.mark.parametrize("color", [
    "#000000",      # Valid black
    "#FFFFFF",      # Valid white
    "#FF0000",      # Valid red
    "invalid",      # Invalid format
    "#FFG000",      # Invalid hex
    "rgb(0,0,0)",   # Invalid format
    "",             # Empty string
])
def test_qr_code_color_validation(client: TestClient, test_db: Session, color):
    """Test QR code color validation with various formats."""
    payload = {
        "content": fake.url(),
        "qr_type": QRType.STATIC,
        "fill_color": color,
        "back_color": "#000000" if color == "#FFFFFF" else "#FFFFFF",  # Ensure different colors
        "size": 10,
        "border": 4
    }

    json_payload = jsonable_encoder(payload)
    response = client.post("/api/v1/qr/static", json=json_payload)

    # Valid hex colors should succeed, others should fail validation
    is_valid_hex = bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))
    expected_status = 200 if is_valid_hex else 422
    assert response.status_code == expected_status, f"Expected status {expected_status} for color {color}, got {response.status_code}"

    if expected_status == 200:
        data = response.json()
        assert data["fill_color"] == color.upper()
        assert data["back_color"] == payload["back_color"].upper()
        assert data["qr_type"] == QRType.STATIC

@pytest.mark.asyncio
async def test_concurrent_qr_code_access(client: TestClient, test_db: Session):
    """Test concurrent access to QR codes."""
    # Create a test QR code
    created_qr = create_test_qr_code(client, QRType.DYNAMIC)
    short_id = created_qr["content"].replace("/r/", "")

    # Simulate concurrent access
    async def access_qr():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
            response = await async_client.get(f"/r/{short_id}", follow_redirects=False)
            return response.status_code

    # Run multiple concurrent requests
    num_requests = 5
    tasks = [access_qr() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)

    # Verify all requests were successful
    assert all(status == 302 for status in results), f"Not all redirects were successful: {results}"

    # Verify the scan count was updated correctly
    db_qr = test_db.query(QRCode).filter(QRCode.id == created_qr["id"]).first()
    assert db_qr.scan_count == num_requests
    test_db.commit() 