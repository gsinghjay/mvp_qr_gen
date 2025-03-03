"""
Test cases for the QR code service layer.
"""

from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import update

from ..models import QRCode
from ..schemas import QRCodeCreate, QRCodeUpdate, QRType
from ..services.qr_service import QRCodeService


class TestQRCodeService:
    """Test cases for QRCodeService."""

    def test_get_qr_by_id_success(self):
        """Test retrieving a QR code by ID successfully."""
        # Arrange
        mock_db = MagicMock()
        test_qr = QRCode(
            id="test123",
            content="test-content",
            qr_type="static",
            created_at=datetime.now(UTC),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = test_qr

        # Act
        service = QRCodeService(mock_db)
        result = service.get_qr_by_id("test123")

        # Assert
        assert result is not None
        assert result.id == "test123"
        mock_db.query.assert_called_once_with(QRCode)
        mock_db.query.return_value.filter.assert_called_once()

    def test_get_qr_by_id_not_found(self):
        """Test retrieving a non-existent QR code by ID."""
        # Arrange
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        service = QRCodeService(mock_db)
        with pytest.raises(HTTPException) as excinfo:
            service.get_qr_by_id("nonexistent")

        # Verify exception details
        assert excinfo.value.status_code == 404
        assert "QR code not found" in str(excinfo.value.detail)

    def test_create_static_qr(self):
        """Test creating a static QR code."""
        # Arrange
        mock_db = MagicMock()
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.STATIC,
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act
        service = QRCodeService(mock_db)
        result = service.create_static_qr(qr_data)

        # Assert
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify the created QR code has correct properties
        added_qr = mock_db.add.call_args[0][0]
        assert added_qr.qr_type == "static"
        assert added_qr.content == "test-content"
        assert added_qr.fill_color == "#000000"
        assert added_qr.back_color == "#FFFFFF"

    def test_create_dynamic_qr(self):
        """Test creating a dynamic QR code."""
        # Arrange
        mock_db = MagicMock()
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act
        service = QRCodeService(mock_db)
        result = service.create_dynamic_qr(qr_data)

        # Assert
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify the created QR code has correct properties
        added_qr = mock_db.add.call_args[0][0]
        assert added_qr.qr_type == "dynamic"
        # Check that the URL starts with the expected base URL (ignoring trailing slash)
        assert added_qr.redirect_url.startswith("https://example.com")
        assert added_qr.content.startswith("/r/")  # Should create a redirect path

    def test_update_dynamic_qr(self):
        """Test updating a dynamic QR code."""
        # Arrange
        mock_db = MagicMock()
        test_qr = QRCode(
            id="test123",
            content="/r/abcd1234",
            qr_type="dynamic",
            redirect_url="https://example.com/old",
            created_at=datetime.now(UTC),
        )
        mock_db.query.return_value.filter.return_value.first.return_value = test_qr

        update_data = QRCodeUpdate(redirect_url="https://example.com/new")

        # Act
        service = QRCodeService(mock_db)
        result = service.update_dynamic_qr("test123", update_data)

        # Assert
        assert result is not None
        assert result.redirect_url == "https://example.com/new"
        mock_db.add.assert_called_once_with(test_qr)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(test_qr)

    def test_update_scan_count(self):
        """Test updating scan count for a QR code."""
        # Arrange
        mock_db = MagicMock()
        test_timestamp = datetime.now(UTC)

        # Act
        service = QRCodeService(mock_db)
        service.update_scan_count("test123", test_timestamp)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        # Check that the SQL update was constructed correctly
        # This is a bit brittle, but we want to ensure the update is correct
        update_stmt = mock_db.execute.call_args[0][0]
        assert isinstance(update_stmt, update(QRCode).__class__)

    def test_generate_qr_image(self):
        """Test generating a QR code image."""
        # Arrange
        mock_db = MagicMock()

        # Act
        service = QRCodeService(mock_db)
        result = service.generate_qr_image(
            content="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Assert
        assert isinstance(result, BytesIO)

    @patch("app.services.qr_service.qrcode.QRCode")
    def test_generate_qr(self, mock_qrcode_class):
        """Test generating a QR code for response."""
        # Arrange
        mock_db = MagicMock()
        mock_qr_instance = mock_qrcode_class.return_value
        mock_img = MagicMock()
        mock_qr_instance.make_image.return_value = mock_img

        # Act
        service = QRCodeService(mock_db)
        result = service.generate_qr(
            data="https://example.com",
            image_format="png",
        )

        # Assert
        assert isinstance(result, StreamingResponse)
        mock_qrcode_class.assert_called_once()
        mock_qr_instance.add_data.assert_called_with("https://example.com")
        mock_qr_instance.make.assert_called_once_with(fit=True)
        mock_img.save.assert_called_once()

    def test_validate_qr_code_valid(self):
        """Test validating a valid QR code."""
        # Arrange
        mock_db = MagicMock()
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert - should not raise an exception
        service = QRCodeService(mock_db)
        service.validate_qr_code(qr_data)

    def test_validate_qr_code_invalid_dynamic_without_redirect(self):
        """Test validating an invalid dynamic QR code without redirect URL."""
        # Arrange
        mock_db = MagicMock()
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.DYNAMIC,
            redirect_url=None,
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert
        service = QRCodeService(mock_db)
        with pytest.raises(ValueError) as excinfo:
            service.validate_qr_code(qr_data)

        assert "Dynamic QR codes require a redirect URL" in str(excinfo.value)

    def test_validate_qr_code_invalid_static_with_redirect(self):
        """Test validating an invalid static QR code with redirect URL."""
        # Arrange
        mock_db = MagicMock()
        qr_data = QRCodeCreate(
            content="test-content",
            qr_type=QRType.STATIC,
            redirect_url="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
        )

        # Act & Assert
        service = QRCodeService(mock_db)
        with pytest.raises(ValueError) as excinfo:
            service.validate_qr_code(qr_data)

        assert "Static QR codes cannot have a redirect URL" in str(excinfo.value)
