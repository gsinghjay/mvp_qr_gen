"""
Test cases for the QR code service layer using real database sessions.
"""

from datetime import UTC, datetime
from io import BytesIO
import uuid
import asyncio

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..models import QRCode
from ..schemas import QRCodeCreate, QRCodeUpdate, QRType
from ..services.qr_service import QRCodeService


class TestQRCodeServiceWithRealDB:
    """Test cases for QRCodeService using real database sessions."""

    def test_get_qr_by_id_success(self, test_db):
        """Test retrieving a QR code by ID successfully."""
        # Arrange - Create a test QR code in the database
        test_qr = QRCode(
            id=str(uuid.uuid4()),
            content="test-content",
            qr_type="static",
            created_at=datetime.now(UTC),
        )
        test_db.add(test_qr)
        test_db.commit()
        test_db.refresh(test_qr)

        # Act
        service = QRCodeService(test_db)
        result = service.get_qr_by_id(test_qr.id)

        # Assert
        assert result is not None
        assert result.id == test_qr.id
        assert result.content == "test-content"
        assert result.qr_type == "static"

    def test_get_qr_by_id_not_found(self, test_db):
        """Test retrieving a non-existent QR code by ID."""
        # Act & Assert
        service = QRCodeService(test_db)
        with pytest.raises(HTTPException) as excinfo:
            service.get_qr_by_id("nonexistent")

        # Verify exception details
        assert excinfo.value.status_code == 404
        assert "QR code not found" in str(excinfo.value.detail)

    def test_create_static_qr(self, test_db):
        """Test creating a static QR code."""
        # Arrange
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.STATIC,
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act
        service = QRCodeService(test_db)
        result = service.create_static_qr(qr_data)

        # Assert
        assert result is not None
        assert result.qr_type == "static"
        assert result.content == "test-content"
        assert result.fill_color == "#000000"
        assert result.back_color == "#FFFFFF"
        
        # Verify the QR code was actually saved to the database
        db_qr = test_db.execute(
            select(QRCode).where(QRCode.id == result.id)
        ).scalar_one()
        
        assert db_qr is not None
        assert db_qr.qr_type == "static"
        assert db_qr.content == "test-content"

    def test_create_dynamic_qr(self, test_db):
        """Test creating a dynamic QR code."""
        # Arrange
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act
        service = QRCodeService(test_db)
        result = service.create_dynamic_qr(qr_data)

        # Assert
        assert result is not None
        assert result.qr_type == "dynamic"
        assert result.redirect_url == "https://example.com/"  # Should add trailing slash
        
        # Verify the QR code was actually saved to the database
        db_qr = test_db.execute(
            select(QRCode).where(QRCode.id == result.id)
        ).scalar_one()
        
        assert db_qr is not None
        assert db_qr.qr_type == "dynamic"
        assert db_qr.redirect_url == "https://example.com/"
        assert db_qr.content.startswith("/r/")  # Should create a redirect path

    def test_update_dynamic_qr(self, test_db):
        """Test updating a dynamic QR code."""
        # Arrange - Create a test dynamic QR code
        test_qr = QRCode(
            id=str(uuid.uuid4()),
            content="/r/abcd1234",
            qr_type="dynamic",
            redirect_url="https://example.com/old",
            created_at=datetime.now(UTC),
        )
        test_db.add(test_qr)
        test_db.commit()
        test_db.refresh(test_qr)

        update_data = QRCodeUpdate(redirect_url="https://example.com/new")

        # Act
        service = QRCodeService(test_db)
        result = service.update_dynamic_qr(test_qr.id, update_data)

        # Assert
        assert result is not None
        assert result.redirect_url == "https://example.com/new"
        
        # Verify the QR code was actually updated in the database
        db_qr = test_db.execute(
            select(QRCode).where(QRCode.id == test_qr.id)
        ).scalar_one()
        
        assert db_qr is not None
        assert db_qr.redirect_url == "https://example.com/new"

    def test_update_scan_count(self, test_db):
        """Test updating scan count for a QR code."""
        # Arrange - Create a test QR code
        test_qr = QRCode(
            id=str(uuid.uuid4()),
            content="test-content",
            qr_type="static",
            created_at=datetime.now(UTC),
            scan_count=0,
            last_scan_at=None,
        )
        test_db.add(test_qr)
        test_db.commit()
        test_db.refresh(test_qr)
        
        test_timestamp = datetime.now(UTC)

        # Act
        service = QRCodeService(test_db)
        service.update_scan_count(test_qr.id, test_timestamp)

        # Assert - Verify the scan count was updated in the database
        db_qr = test_db.execute(
            select(QRCode).where(QRCode.id == test_qr.id)
        ).scalar_one()
        
        assert db_qr.scan_count == 1
        assert db_qr.last_scan_at is not None
        assert db_qr.last_scan_at.replace(microsecond=0) == test_timestamp.replace(microsecond=0)

    def test_generate_qr_image(self, test_db):
        """Test generating a QR code image."""
        # Act
        service = QRCodeService(test_db)
        result = service.generate_qr_image(
            content="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Assert
        assert isinstance(result, BytesIO)
        # Verify the BytesIO object contains image data
        result.seek(0)
        image_data = result.read()
        assert len(image_data) > 0

    def test_generate_qr(self, test_db):
        """Test generating a QR code for response."""
        # Act
        service = QRCodeService(test_db)
        result = service.generate_qr(
            data="https://example.com",
            image_format="png",
        )

        # Assert
        assert isinstance(result, StreamingResponse)
        assert result.media_type == "image/png"
        
        # Verify the response contains image data
        # Convert async generator to bytes
        response_iter = result.body_iterator
        # Use asyncio to run the async generator and collect the chunks
        response_data = b""
        async def collect_response():
            nonlocal response_data
            async for chunk in response_iter:
                response_data += chunk
        
        # Run the async function to collect the response data
        asyncio.run(collect_response())
        
        # Verify we got some data
        assert len(response_data) > 0

    def test_validate_qr_code_valid(self, test_db):
        """Test validating a valid QR code."""
        # Arrange
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert - should not raise an exception
        service = QRCodeService(test_db)
        service.validate_qr_code(qr_data)

    def test_validate_qr_code_invalid_dynamic_without_redirect(self, test_db):
        """Test validating an invalid dynamic QR code without redirect URL."""
        # Arrange
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url=None,
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert
        service = QRCodeService(test_db)
        with pytest.raises(ValueError) as excinfo:
            service.validate_qr_code(qr_data)

        assert "Dynamic QR codes require a redirect URL" in str(excinfo.value)

    def test_validate_qr_code_invalid_static_with_redirect(self, test_db):
        """Test validating an invalid static QR code with redirect URL."""
        # Arrange
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.STATIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert
        service = QRCodeService(test_db)
        with pytest.raises(ValueError) as excinfo:
            service.validate_qr_code(qr_data)

        assert "Static QR codes cannot have a redirect URL" in str(excinfo.value) 