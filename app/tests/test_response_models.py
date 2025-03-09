"""
Tests for response model validation.

This module tests the validation of response models for all endpoints.
It ensures that all API responses conform to their defined Pydantic models.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from ..models.qr import QRCode
from ..schemas import QRCodeResponse, QRCodeList, HTTPError, ImageFormat, QRType
from .factories import QRCodeFactory
from .helpers import (
    validate_response_model,
    validate_list_response,
    assert_error_response,
    DependencyOverrideManager,
)


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


class TestQRCodeResponseModel:
    """Tests for QR code response models."""
    
    def test_get_qr_response_model(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that GET /api/v1/qr/{qr_id} returns a valid QRCodeResponse."""
        # Create a QR code
        qr = qr_factory.create_static()
        
        # Get the QR code
        response = client.get(f"/api/v1/qr/{qr.id}")
        
        # Check status code
        assert response.status_code == 200
        
        # Validate response model
        assert validate_response_model(response.json(), QRCodeResponse)
    
    def test_list_qr_response_model(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that GET /api/v1/qr returns a valid QRCodeList."""
        # Create some QR codes
        for _ in range(5):
            qr_factory.create_static()
        
        # Get the QR codes
        response = client.get("/api/v1/qr")
        
        # Check status code
        assert response.status_code == 200
        
        # Validate response model
        assert validate_list_response(
            response.json(), 
            QRCodeResponse, 
            QRCodeList
        )
    
    def test_create_dynamic_qr_response_model(self, client: TestClient):
        """Test that POST /api/v1/qr/dynamic returns a valid QRCodeResponse."""
        # Create a dynamic QR code
        response = client.post(
            "/api/v1/qr/dynamic",
            json={
                "content": "https://example.com",
                "redirect_url": "https://example.com",
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
            },
        )
        
        # Check status code
        assert response.status_code == 200
        
        # Validate response model
        assert validate_response_model(response.json(), QRCodeResponse)
    
    def test_update_qr_response_model(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that PUT /api/v1/qr/{qr_id} returns a valid QRCodeResponse."""
        # Create a dynamic QR code
        qr = qr_factory.create_dynamic()
        
        # Update the QR code
        response = client.put(
            f"/api/v1/qr/{qr.id}",
            json={"redirect_url": "https://updated-example.com"},
        )
        
        # Check status code
        assert response.status_code == 200
        
        # Validate response model
        assert validate_response_model(response.json(), QRCodeResponse)


class TestErrorResponseModel:
    """Tests for error response models."""
    
    def test_not_found_error_model(self, client: TestClient):
        """Test that 404 errors return a valid HTTPError."""
        # Request a non-existent QR code
        response = client.get("/api/v1/qr/non-existent-id")
        
        # Check status code
        assert response.status_code == 404
        
        # Validate error response
        assert assert_error_response(response.json())
    
    def test_validation_error_model(self, client: TestClient):
        """Test that validation errors return a valid HTTPError."""
        # Create a QR code with invalid data (missing required redirect_url)
        response = client.post(
            "/api/v1/qr/dynamic",
            json={
                "content": "https://example.com",
                "fill_color": "invalid-color",  # Invalid color format
            },
        )
        
        # Check status code
        assert response.status_code == 422
        
        # Validate error response structure (FastAPI validation errors have a different format)
        assert "detail" in response.json()


class TestEnumValidation:
    """Tests for enum validation in request parameters."""
    
    def test_image_format_validation(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that image_format parameter is validated against ImageFormat enum."""
        # Create a QR code
        qr = qr_factory.create_static()
        
        # Test PNG format which is guaranteed to work
        response = client.get(f"/api/v1/qr/{qr.id}/image?image_format=png")
        assert response.status_code == 200
        
        # Test invalid image format
        response = client.get(f"/api/v1/qr/{qr.id}/image?image_format=invalid-format")
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_qr_type_validation(self, client: TestClient, qr_factory: QRCodeFactory):
        """Test that qr_type parameter is validated against QRType enum."""
        # Create some QR codes
        for _ in range(2):
            qr_factory.create_static()
            qr_factory.create_dynamic()
        
        # Test valid QR types
        for type_value in [t.value for t in QRType]:
            response = client.get(f"/api/v1/qr?qr_type={type_value}")
            assert response.status_code == 200
            
            # Validate that filtered results have the correct type
            data = response.json()
            for item in data["items"]:
                assert item["qr_type"] == type_value
        
        # Test invalid QR type
        response = client.get("/api/v1/qr?qr_type=invalid-type")
        assert response.status_code == 422
        assert "detail" in response.json() 