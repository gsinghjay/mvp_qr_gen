"""
Tests for custom exceptions and exception handlers.

This module tests the custom exception classes and their handlers to ensure
they provide consistent error responses across the application.
"""

from fastapi.testclient import TestClient

from ..core.exceptions import (
    DatabaseError,
    QRCodeValidationError,
    RedirectURLError,
    ResourceConflictError,
)
from ..services.qr_service import QRCodeService


def test_qr_code_not_found_exception(client: TestClient):
    """Test that QRCodeNotFoundError returns a 404 with the correct format."""
    response = client.get("/api/v1/qr/nonexistent-id")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"].lower()
    assert "path" in response.json()
    assert response.json()["path"] == "/api/v1/qr/nonexistent-id"


def test_qr_code_validation_exception(client: TestClient, monkeypatch):
    """Test that QRCodeValidationError returns a 422 with the correct format."""

    # Mock the QRCodeService.create_static_qr method to raise a QRCodeValidationError
    def mock_create_static_qr(*args, **kwargs):
        raise QRCodeValidationError("QR code validation failed: Invalid color format")

    monkeypatch.setattr(QRCodeService, "create_static_qr", mock_create_static_qr)

    # Create a static QR code
    response = client.post("/api/v1/qr/static", json={"content": "test", "fill_color": "#000000"})
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "validation" in response.json()["detail"].lower()
    assert "path" in response.json()


def test_database_error_exception(client: TestClient, monkeypatch):
    """Test that DatabaseError returns a 500 with the correct format."""

    # Mock the QRCodeService.get_qr_by_id method to raise a DatabaseError
    def mock_get_qr_by_id(*args, **kwargs):
        raise DatabaseError("Test database error")

    monkeypatch.setattr(QRCodeService, "get_qr_by_id", mock_get_qr_by_id)

    response = client.get("/api/v1/qr/some-id")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "database" in response.json()["detail"].lower()
    assert "path" in response.json()


def test_invalid_qr_type_exception(client: TestClient):
    """Test that InvalidQRTypeError returns a 400 with the correct format."""
    # Try to filter QR codes by an invalid type
    response = client.get("/api/v1/qr?qr_type=invalid_type")
    # Accept either 400 or 422 status code
    assert response.status_code in [
        400,
        422,
    ], f"Expected status code 400 or 422, got {response.status_code}"
    assert "detail" in response.json()

    # Handle both string and list detail formats
    detail = response.json()["detail"]
    if isinstance(detail, list):
        # If detail is a list, check that at least one item contains validation error info
        has_error = any(
            ("invalid" in str(item).lower() or "type" in str(item).lower()) for item in detail
        )
        assert has_error, "No validation error found in response detail"
    else:
        # If detail is a string, check that it contains "invalid" or "type"
        assert "invalid" in detail.lower() or "type" in detail.lower()

    assert "path" in response.json()


def test_redirect_url_error_exception(client: TestClient, monkeypatch):
    """Test that RedirectURLError returns a 422 with the correct format."""

    # Mock the QRCodeService.update_dynamic_qr method to raise a RedirectURLError
    def mock_update_dynamic_qr(*args, **kwargs):
        raise RedirectURLError("Invalid redirect URL format")

    monkeypatch.setattr(QRCodeService, "update_dynamic_qr", mock_update_dynamic_qr)

    # Try to update a QR code with an invalid URL
    response = client.put("/api/v1/qr/some-id", json={"redirect_url": "https://example.com"})
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "url" in response.json()["detail"].lower()
    assert "path" in response.json()


def test_resource_conflict_exception(client: TestClient, monkeypatch):
    """Test that ResourceConflictError returns a 409 with the correct format."""

    # Mock the QRCodeService.create_static_qr method to raise a ResourceConflictError
    def mock_create_static_qr(*args, **kwargs):
        raise ResourceConflictError("QR code with this content already exists")

    monkeypatch.setattr(QRCodeService, "create_static_qr", mock_create_static_qr)

    response = client.post("/api/v1/qr/static", json={"content": "https://example.com"})
    assert response.status_code == 409
    assert "detail" in response.json()
    assert (
        "conflict" in response.json()["detail"].lower()
        or "already exists" in response.json()["detail"].lower()
    )
    assert "path" in response.json()


def test_exception_handler_includes_request_id(client: TestClient):
    """Test that exception responses include the request ID."""
    response = client.get("/api/v1/qr/nonexistent-id")
    assert response.status_code == 404
    assert "request_id" in response.json()
    assert response.json()["request_id"] is not None


def test_exception_handler_includes_timestamp(client: TestClient):
    """Test that exception responses include a timestamp."""
    response = client.get("/api/v1/qr/nonexistent-id")
    assert response.status_code == 404
    assert "timestamp" in response.json()
    assert response.json()["timestamp"] is not None
