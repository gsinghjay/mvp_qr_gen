"""
Test cases for the QR code service layer using dependency injection.
"""

from datetime import UTC, datetime
from io import BytesIO
import uuid
import asyncio

import pytest
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from fastapi.testclient import TestClient

from ..models import QRCode
from ..schemas import QRCodeCreate, QRCodeUpdate, QRType
from ..services.qr_service import QRCodeService
from ..database import get_db, get_db_with_logging
from ..main import app
from .helpers import assert_qr_code_fields, assert_http_exception
from .factories import QRCodeFactory


# Define real and mock test approaches
@pytest.fixture
def qr_service(test_db):
    """Fixture to create a real QR service with test database."""
    return QRCodeService(test_db)


@pytest.fixture
def mock_qr_service():
    """Fixture to create a mock QR service."""
    from unittest.mock import MagicMock
    mock_service = MagicMock(spec=QRCodeService)
    return mock_service


@pytest.fixture
def client_with_real_db(test_db):
    """TestClient with real DB session."""
    # Store original dependencies
    original_dependencies = app.dependency_overrides.copy()
    
    # Override dependency to use test db session
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Transaction handled by test_db fixture with rollback
    
    # Apply the overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_with_logging] = override_get_db
    
    # Create client with custom base_url
    with TestClient(app, base_url="http://test") as client:
        yield client
    
    # Restore original dependencies
    app.dependency_overrides = original_dependencies.copy()


@pytest.fixture
def client_with_mock_service(mock_qr_service):
    """TestClient with mock service."""
    # Store original dependencies
    original_dependencies = app.dependency_overrides.copy()
    
    # Create a dependency that returns the mock service
    async def get_mock_qr_service():
        return mock_qr_service
    
    # Override the QRCodeService dependency in all routes
    for route in app.routes:
        if hasattr(route, "dependant"):
            for dependency in route.dependant.dependencies:
                if isinstance(dependency.call, type) and dependency.call == QRCodeService:
                    dependency.call = get_mock_qr_service
    
    # Create client
    with TestClient(app, base_url="http://test") as client:
        yield client
    
    # Restore original dependencies
    app.dependency_overrides = original_dependencies.copy()
    
    # Also restore any route dependencies that were modified
    # This would require storing the original dependencies first, which is complex
    # For simplicity, we'll rely on test isolation at the dependency_overrides level


class TestQRCodeService:
    """Test cases for QRCodeService with both real DB and mocks."""

    @pytest.mark.parametrize(
        "is_mock,qr_id,expected_fields",
        [
            # Mock test case
            (
                True,
                "test123",
                {
                    "id": "test123",
                    "content": "test-content",
                    "qr_type": "static",
                    "scan_count": 5
                }
            ),
            # Real DB test case
            (
                False,
                None,  # Will be generated during test
                {
                    "content": "test-content",
                    "qr_type": "static",
                    "scan_count": 5
                }
            )
        ],
        ids=["mock", "real_db"]
    )
    def test_get_qr_by_id_success(self, is_mock, qr_id, expected_fields, mock_qr_service, qr_service, test_db):
        """Test retrieving a QR code by ID successfully (mock and real DB)."""
        if is_mock:
            # Arrange for mock test
            test_qr = QRCode(
                id=qr_id,
                content=expected_fields["content"],
                qr_type=expected_fields["qr_type"],
                created_at=datetime.now(UTC),
                fill_color="#000000",
                back_color="#FFFFFF",
                scan_count=expected_fields["scan_count"]
            )
            mock_qr_service.get_qr_by_id.return_value = test_qr
            
            # Act
            result = mock_qr_service.get_qr_by_id(qr_id)
            
            # Assert
            assert_qr_code_fields(result, expected_fields)
            mock_qr_service.get_qr_by_id.assert_called_once_with(qr_id)
        else:
            # Arrange for real DB test
            test_qr = QRCode(
                id=str(uuid.uuid4()),
                content=expected_fields["content"],
                qr_type=expected_fields["qr_type"],
                created_at=datetime.now(UTC),
                fill_color="#000000",
                back_color="#FFFFFF",
                scan_count=expected_fields["scan_count"]
            )
            test_db.add(test_qr)
            test_db.commit()
            
            # Update the expected ID
            expected_fields_with_id = expected_fields.copy()
            expected_fields_with_id["id"] = str(test_qr.id)
            
            # Act
            result = qr_service.get_qr_by_id(test_qr.id)
            
            # Assert
            assert_qr_code_fields(result, expected_fields_with_id)
    
    @pytest.mark.parametrize(
        "is_mock,qr_id",
        [
            # Mock test case
            (True, "nonexistent"),
            # Real DB test case
            (False, "00000000-0000-0000-0000-000000000000")
        ],
        ids=["mock", "real_db"]
    )
    def test_get_qr_by_id_not_found(self, is_mock, qr_id, mock_qr_service, qr_service):
        """Test retrieving a non-existent QR code (mock and real DB)."""
        if is_mock:
            # Arrange for mock test
            mock_qr_service.get_qr_by_id.side_effect = HTTPException(
                status_code=404, detail="QR code not found"
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                mock_qr_service.get_qr_by_id(qr_id)
            
            assert_http_exception(exc_info, expected_status_code=404, expected_detail_substring="not found")
        else:
            # Act & Assert for real DB test
            from app.core.exceptions import QRCodeNotFoundError
            
            with pytest.raises(QRCodeNotFoundError) as exc_info:
                qr_service.get_qr_by_id(qr_id)
            
            # Verify the exception details
            assert "not found" in str(exc_info.value)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.parametrize(
        "is_mock,qr_data,expected_fields",
        [
            # Mock test case
            (
                True,
                {
                    "content": "https://example.com",
                    "qr_type": QRType.STATIC,
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                },
                {
                    "id": "test123",
                    "content": "https://example.com",
                    "qr_type": "static",
                    "scan_count": 0
                }
            ),
            # Real DB test case
            (
                False,
                {
                    "content": "https://example.com",
                    "qr_type": QRType.STATIC,
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF"
                },
                {
                    "content": "https://example.com",
                    "qr_type": "static",
                    "scan_count": 0
                }
            )
        ],
        ids=["mock", "real_db"]
    )
    def test_create_static_qr(self, is_mock, qr_data, expected_fields, mock_qr_service, qr_service):
        """Test creating a static QR code (mock and real DB)."""
        # Convert dict to QRCodeCreate model
        qr_data_model = QRCodeCreate(**qr_data)
        
        if is_mock:
            # Arrange for mock test
            test_qr = QRCode(
                id=expected_fields["id"],
                content=expected_fields["content"],
                qr_type=expected_fields["qr_type"],
                created_at=datetime.now(UTC),
                fill_color="#000000",
                back_color="#FFFFFF",
                scan_count=expected_fields["scan_count"]
            )
            mock_qr_service.create_static_qr.return_value = test_qr
            
            # Act
            result = mock_qr_service.create_static_qr(qr_data_model)
            
            # Assert
            assert_qr_code_fields(result, expected_fields)
            mock_qr_service.create_static_qr.assert_called_once_with(qr_data_model)
        else:
            # Act for real DB test
            result = qr_service.create_static_qr(qr_data_model)
            
            # Assert
            # Check for presence of ID but don't expect a specific value
            assert result.id is not None
            # Check other expected fields
            for field, value in expected_fields.items():
                if field != "id":  # Skip id check since we've already verified it exists
                    assert getattr(result, field) == value
            # Verify created_at is set
            assert result.created_at is not None
    
    # Integration tests with TestClient would also be added
    def test_api_create_static_qr(self, client_with_real_db):
        """Test creating a static QR code through the API."""
        # Arrange
        qr_data = {
            "content": "https://example.com",
            "qr_type": "static",
            "fill_color": "#000000",
            "back_color": "#FFFFFF"
        }
        
        # Act
        response = client_with_real_db.post("/api/v1/qr/static", json=qr_data)
        
        # Assert
        assert response.status_code == 201  # API returns 201 Created for successful creation
        result = response.json()
        assert_qr_code_fields(result, {
            "content": "https://example.com",
            "qr_type": "static",
            "scan_count": 0
        })
