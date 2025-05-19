"""
Tests for HTTP method decorators.

This module tests the usage of specific HTTP method decorators (@router.get, @router.post, etc.)
and verifies the correct status codes are returned for different operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from .factories import QRCodeFactory
from .helpers import DependencyOverrideManager


@pytest.fixture
def client(test_db: Session) -> TestClient:
    """
    Create a test client with dependency overrides.

    Args:
        test_db: SQLAlchemy session for testing

    Returns:
        TestClient: FastAPI test client
    """
    with DependencyOverrideManager.create_db_override(app, test_db):
        client = TestClient(app)
        yield client


@pytest.fixture
def qr_factory(test_db: Session) -> QRCodeFactory:
    """
    Create a QRCodeFactory with the test database session.

    Args:
        test_db: SQLAlchemy session for testing

    Returns:
        QRCodeFactory: Factory for creating QR codes
    """
    return QRCodeFactory(test_db)


class TestHTTPMethodDecorators:
    """Test cases for HTTP method decorators and status codes."""

    def test_get_returns_200_ok(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that GET endpoint returns 200 OK status code."""
        # Create a QR code to retrieve
        qr = qr_factory.create_dynamic()

        # Test GET endpoint
        response = client.get(f"/api/v1/qr/{qr.id}")
        assert response.status_code == 200

    def test_list_returns_200_ok(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that list endpoint returns 200 OK status code."""
        # Create some QR codes
        qr_factory.create_batch(5)

        # Test list endpoint
        response = client.get("/api/v1/qr")
        assert response.status_code == 200

    def test_put_returns_200_ok(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that PUT endpoint returns 200 OK status code."""
        # Create a dynamic QR code to update
        qr = qr_factory.create_dynamic()

        # Test API v1 update endpoint
        update_data = {"redirect_url": "https://updated-example.com"}
        response = client.put(f"/api/v1/qr/{qr.id}", json=update_data)
        assert response.status_code == 200

    def test_delete_returns_204_no_content(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that DELETE endpoint returns 204 No Content status code."""
        # Create a QR code to delete
        qr = qr_factory.create_dynamic()

        # Test delete endpoint
        response = client.delete(f"/api/v1/qr/{qr.id}")
        assert response.status_code == 204
        assert response.content == b""  # No content in the response body

    def test_method_not_allowed_returns_405(self, client: TestClient):
        """Test that using an unsupported method returns 405 Method Not Allowed."""
        # This endpoint exists but should not support DELETE on collection
        response = client.delete("/api/v1/qr")
        assert response.status_code == 405
