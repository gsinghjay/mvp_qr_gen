"""
Tests demonstrating standardized dependency injection patterns.

This module shows how to use the DependencyOverrideManager to consistently
manage dependency overrides in tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, get_db_with_logging
from app.services.qr_service import QRCodeService
from app.dependencies import get_qr_service
from app.tests.helpers import DependencyOverrideManager, assert_qr_code_fields

#
# Basic Context Manager Pattern
#

def test_with_context_manager(test_db):
    """Demonstrate using DependencyOverrideManager as a context manager."""
    
    # Define a test override function
    def test_qr_service():
        # Create a service with custom behavior for testing
        service = QRCodeService(test_db)
        yield service
    
    # Create a manager and register the override
    manager = DependencyOverrideManager(app)
    manager.override(get_qr_service, test_qr_service)
    
    with manager:
        # Inside this context, the override is applied
        client = TestClient(app)
        response = client.post(
            "/api/v1/qr/static",
            json={
                "content": "https://example.com",
                "fill_color": "#000000",
                "back_color": "#FFFFFF"
            },
        )
        assert response.status_code == 200
        # Verify response data
        data = response.json()
        assert_qr_code_fields(data, {
            "qr_type": "static",
            "content": "https://example.com"
        })
    
    # Outside the context, original dependencies are restored
    # No need to manually clean up


#
# Class-based Test Pattern with Fixture
#

@pytest.fixture
def dependency_manager(test_db):
    """Fixture providing a preconfigured dependency manager."""
    # Create with the convenience method
    return DependencyOverrideManager.create_db_override(app, test_db)


class TestDependencyOverrides:
    """Tests using the dependency manager with class-based tests."""
    
    def test_static_qr_creation(self, dependency_manager, test_db):
        """Test creating a static QR code with managed dependencies."""
        with dependency_manager:
            client = TestClient(app)
            response = client.post(
                "/api/v1/qr/static",
                json={
                    "content": "https://example.com/class-test",
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "https://example.com/class-test"
            
            # Verify it's in the database
            from app.models.qr import QRCode
            from sqlalchemy import select
            
            qr_id = data["id"]
            stmt = select(QRCode).where(QRCode.id == qr_id)
            result = test_db.execute(stmt).scalar_one_or_none()
            assert result is not None
            assert result.content == "https://example.com/class-test"
    
    def test_dynamic_qr_creation(self, dependency_manager):
        """Test creating a dynamic QR code with managed dependencies."""
        with dependency_manager:
            client = TestClient(app)
            response = client.post(
                "/api/v1/qr/dynamic",
                json={
                    "content": "https://example.com/content",
                    "redirect_url": "https://example.com/redirect",
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["redirect_url"] == "https://example.com/redirect"
            assert data["qr_type"] == "dynamic"


#
# Custom Override Pattern
#

def test_with_custom_behavior(test_db):
    """Test with a custom override behavior."""
    # Define a mock service with specific test behavior
    class MockQRService(QRCodeService):
        def create_static_qr(self, data):
            # Override to always use test values
            # We need to modify the data object, not kwargs
            data.content = "https://TEST-OVERRIDE.example.com"
            return super().create_static_qr(data)

    # Create the mock service provider
    def get_mock_qr_service():
        yield MockQRService(test_db)
    
    # Setup dependency override
    manager = DependencyOverrideManager(app)
    manager.override(get_qr_service, get_mock_qr_service)
    
    with manager:
        client = TestClient(app)
        response = client.post(
            "/api/v1/qr/static",
            json={
                "content": "https://this-will-be-ignored.com",
                "fill_color": "#000000",
                "back_color": "#FFFFFF"
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Verify our mock service modified the content
        assert data["content"] == "https://TEST-OVERRIDE.example.com" 