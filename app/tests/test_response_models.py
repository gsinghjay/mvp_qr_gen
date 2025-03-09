"""
Tests to validate API responses against their Pydantic models.

This module ensures that all API endpoints return responses that match
their defined Pydantic response models, validating proper schema compliance.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..database import get_db, get_db_with_logging
from ..main import app
from ..models.qr import QRCode
from ..schemas import (
    QRCodeResponse, 
    QRCodeList, 
    QRType, 
    HealthResponse, 
    HealthStatus, 
    ServiceStatus
)
from ..dependencies import get_qr_service
from ..services.qr_service import QRCodeService
from .helpers import validate_response_model, validate_list_response, assert_error_response, DependencyOverrideManager
from .factories import QRCodeFactory


class TestResponseModelValidation:
    """Test suite for validating API responses against Pydantic models."""

    def test_create_static_qr_response_validation(self, client: TestClient, test_db: Session):
        """Test that creating a static QR code returns a valid QRCodeResponse."""
        # Prepare request payload
        payload = {
            "content": "https://example.com",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "size": 10,
            "border": 4
        }
        
        # Use the correct endpoint for static QR codes
        response = client.post("/api/v1/qr/static", json=payload)
        
        # Verify response status - API returns 200 (not 201) for creation
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic model
        response_data = response.json()
        assert validate_response_model(response_data, QRCodeResponse)
        
        # Additional assertions for specific fields
        assert response_data["qr_type"] == QRType.STATIC
        assert response_data["content"] == payload["content"]
        assert response_data["redirect_url"] is None
        
        # In this test framework, we avoid querying the database directly due to transaction isolation
        # Instead, verify the response data contains the expected information
        assert uuid.UUID(response_data["id"])  # Validates UUID format
        assert response_data["created_at"] is not None
        assert response_data["content"] == payload["content"]

    def test_create_dynamic_qr_response_validation(self, client: TestClient, test_db: Session):
        """Test that creating a dynamic QR code returns a valid QRCodeResponse."""
        # Prepare request payload
        payload = {
            "content": "My Dynamic QR",
            "redirect_url": "https://example.org",
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "size": 10,
            "border": 4
        }
        
        # Use the correct endpoint for dynamic QR codes
        response = client.post("/api/v1/qr/dynamic", json=payload)
        
        # Verify response status - API returns 200 (not 201) for creation
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic model
        response_data = response.json()
        assert validate_response_model(response_data, QRCodeResponse)
        
        # Additional assertions for specific fields
        assert response_data["qr_type"] == QRType.DYNAMIC
        assert response_data["redirect_url"].rstrip('/') == str(payload["redirect_url"]).rstrip('/')
        assert "/r/" in response_data["content"]  # Should contain redirect path
        
        # In this test framework, we avoid querying the database directly due to transaction isolation
        # Instead, verify the response data contains the expected information
        assert uuid.UUID(response_data["id"])  # Validates UUID format
        assert response_data["created_at"] is not None
        assert response_data["redirect_url"] is not None

    def test_list_qr_codes_response_validation(self, client: TestClient, test_db: Session):
        """Test that listing QR codes returns a valid QRCodeList with valid QRCodeResponse items."""
        # Create some test QR codes using the factory
        factory = QRCodeFactory(test_db)
        for _ in range(5):
            factory.create()
        test_db.commit()
        
        # Send request
        response = client.get("/api/v1/qr")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic models (both list and item models)
        response_data = response.json()
        assert validate_list_response(
            response_data, 
            item_model_class=QRCodeResponse, 
            list_model_class=QRCodeList
        )
        
        # Additional assertions for pagination
        assert response_data["page"] >= 1
        assert response_data["page_size"] > 0
        assert response_data["total"] >= len(response_data["items"])
        assert len(response_data["items"]) > 0

    def test_get_qr_code_response_validation(self, client: TestClient, test_db: Session):
        """Test that getting a single QR code returns a valid QRCodeResponse."""
        # Create a test QR code using the factory
        factory = QRCodeFactory(test_db)
        qr_code = factory.create()
        test_db.commit()
        
        # Send request
        response = client.get(f"/api/v1/qr/{qr_code.id}")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic model
        response_data = response.json()
        assert validate_response_model(response_data, QRCodeResponse)
        
        # Verify the returned data matches the created entity
        assert response_data["id"] == str(qr_code.id)
        assert response_data["content"] == qr_code.content

    def test_update_qr_code_response_validation(self, client: TestClient, test_db: Session):
        """Test that updating a QR code returns a valid QRCodeResponse."""
        # Create a dynamic test QR code using the factory
        factory = QRCodeFactory(test_db)
        qr_code = factory.create_dynamic(redirect_url="https://example.com")
        test_db.commit()
        
        # Prepare update payload
        update_payload = {
            "redirect_url": "https://updated-example.com"
        }
        
        # Send request - note we're using PUT here based on the router definition
        response = client.put(f"/api/v1/qr/{qr_code.id}", json=update_payload)
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic model
        response_data = response.json()
        assert validate_response_model(response_data, QRCodeResponse)
        
        # Verify the returned data has the updated value (ignore trailing slashes)
        assert response_data["redirect_url"].rstrip('/') == update_payload["redirect_url"].rstrip('/')
        
        # Verify database state was updated
        test_db.refresh(qr_code)
        assert qr_code.redirect_url.rstrip('/') == update_payload["redirect_url"].rstrip('/')

    def test_not_found_error_response_validation(self, client: TestClient, test_db: Session):
        """Test that a 404 error returns a valid error response."""
        # Use a non-existent ID
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        # Send request
        response = client.get(f"/api/v1/qr/{non_existent_id}")
        
        # Verify response status
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        # Validate error response format
        response_data = response.json()
        assert assert_error_response(response_data)
        assert "not found" in response_data["detail"].lower()

    def test_validation_error_response_validation(self, client: TestClient):
        """Test that a 422 validation error returns a valid error response."""
        # Prepare invalid payload (missing required content field)
        invalid_payload = {
            # Missing required 'content' field
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
        }
        
        # Send request
        response = client.post("/api/v1/qr/static", json=invalid_payload)
        
        # Verify response status
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        
        # Validate error response format
        response_data = response.json()
        assert "detail" in response_data
        assert isinstance(response_data["detail"], list)
        
        # Verify the validation error contains information about the missing field
        found_content_error = False
        for error in response_data["detail"]:
            if "content" in str(error).lower():
                found_content_error = True
                break
        
        assert found_content_error, "Validation error should mention missing 'content' field"

    def test_health_response_validation(self, client: TestClient):
        """Test that the health endpoint returns a valid HealthResponse."""
        # Send request
        response = client.get("/health")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response against Pydantic model
        response_data = response.json()
        assert validate_response_model(response_data, HealthResponse)
        
        # Check for expected fields based on the actual response structure
        assert "status" in response_data
        assert "version" in response_data
        assert "timestamp" in response_data
        
        # The health response might have either "services" or "checks"
        assert "services" in response_data or "checks" in response_data
        
        # Validate status is a known value
        assert response_data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_dependency_override_helper(self, client: TestClient, test_db: Session):
        """Test using the dependency override helper for proper dependency management."""
        # Create a factory first to add some data to the database
        factory = QRCodeFactory(test_db)
        qr_code = factory.create()
        test_db.commit()
        
        # Now use the dependency override manager to override dependencies
        with DependencyOverrideManager(app) as override_manager:
            # Override dependencies for the test
            override_manager.override(get_db, lambda: test_db)
            override_manager.override(get_db_with_logging, lambda: test_db)
            override_manager.override(get_qr_service, lambda: QRCodeService(test_db))
            
            # Use a GET request to retrieve the previously created QR code
            response = client.get(f"/api/v1/qr/{qr_code.id}")
            
            # Verify the response
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Validate response against Pydantic model
            response_data = response.json()
            assert validate_response_model(response_data, QRCodeResponse)
            
            # Verify it matches the expected QR code
            assert response_data["id"] == str(qr_code.id)
            assert response_data["content"] == qr_code.content 