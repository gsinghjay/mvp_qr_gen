"""
Unit tests for the QRCodeService class.

This module tests the QRCodeService class with a focus on the feature flag integration
with NewQRGenerationService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC
from io import BytesIO

from app.services.qr_service import QRCodeService
from app.services.new_qr_generation_service import NewQRGenerationService
from app.repositories import QRCodeRepository, ScanLogRepository
from app.schemas.common import QRType, ErrorCorrectionLevel
from app.schemas.qr.parameters import StaticQRCreateParameters, DynamicQRCreateParameters, QRImageParameters
from app.core.exceptions import QRCodeValidationError, RedirectURLError


class TestQRCodeService:
    """Tests for the QRCodeService class."""

    @pytest.fixture
    def mock_qr_code_repo(self):
        """Fixture for a mock QRCodeRepository."""
        mock_repo = Mock(spec=QRCodeRepository)
        # Configure common mock behaviors here
        return mock_repo

    @pytest.fixture
    def mock_scan_log_repo(self):
        """Fixture for a mock ScanLogRepository."""
        mock_repo = Mock(spec=ScanLogRepository)
        # Configure common mock behaviors here
        return mock_repo

    @pytest.fixture
    def mock_new_qr_generation_service(self):
        """Fixture for a mock NewQRGenerationService."""
        mock_service = Mock(spec=NewQRGenerationService)
        # Configure the create_and_format_qr_sync method to return a mock image
        mock_service.create_and_format_qr_sync.return_value = b"mock_image_bytes"
        return mock_service

    @pytest.fixture
    def qr_service(self, mock_qr_code_repo, mock_scan_log_repo):
        """Fixture for a QRCodeService instance without NewQRGenerationService."""
        return QRCodeService(
            qr_code_repo=mock_qr_code_repo,
            scan_log_repo=mock_scan_log_repo
        )

    @pytest.fixture
    def qr_service_with_new_service(self, mock_qr_code_repo, mock_scan_log_repo, mock_new_qr_generation_service):
        """Fixture for a QRCodeService instance with NewQRGenerationService."""
        return QRCodeService(
            qr_code_repo=mock_qr_code_repo,
            scan_log_repo=mock_scan_log_repo,
            new_qr_generation_service=mock_new_qr_generation_service
        )

    @pytest.fixture
    def static_qr_params(self):
        """Fixture for StaticQRCreateParameters."""
        return StaticQRCreateParameters(
            content="https://example.com",
            title="Test QR",
            fill_color="#000000",
            back_color="#FFFFFF",
            size=10,
            border=4,
            error_level=ErrorCorrectionLevel.M
        )

    @pytest.fixture
    def dynamic_qr_params(self):
        """Fixture for DynamicQRCreateParameters."""
        return DynamicQRCreateParameters(
            redirect_url="https://example.com/redirect",
            title="Test Dynamic QR",
            fill_color="#000000",
            back_color="#FFFFFF",
            size=10,
            border=4,
            error_level=ErrorCorrectionLevel.M
        )

    def test_create_static_qr_old_path(self, qr_service, static_qr_params, mock_qr_code_repo):
        """Test creating a static QR code using the old path."""
        # Configure mock to return a QR code
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.content = static_qr_params.content
        mock_qr_code_repo.create.return_value = mock_qr

        # Call the service method
        result = qr_service.create_static_qr(static_qr_params)

        # Verify the result
        assert result == mock_qr
        mock_qr_code_repo.create.assert_called_once()

    @patch('app.services.qr_service.should_use_new_service')
    @patch('app.services.qr_service.settings')
    def test_create_static_qr_new_path(self, mock_settings, mock_should_use_new_service, 
                                      qr_service_with_new_service, static_qr_params, 
                                      mock_qr_code_repo, mock_new_qr_generation_service):
        """Test creating a static QR code with feature flag enabled."""
        # Configure mocks
        mock_settings.USE_NEW_QR_GENERATION_SERVICE = True
        mock_should_use_new_service.return_value = True
        
        # Configure mock to return a QR code
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.content = static_qr_params.content
        mock_qr_code_repo.create.return_value = mock_qr

        # Call the service method
        result = qr_service_with_new_service.create_static_qr(static_qr_params)

        # Verify the result
        assert result == mock_qr
        mock_qr_code_repo.create.assert_called_once()
        
        # Verify new service was called
        mock_new_qr_generation_service.create_and_format_qr_sync.assert_called_once()

    def test_create_dynamic_qr_old_path(self, qr_service, dynamic_qr_params, mock_qr_code_repo):
        """Test creating a dynamic QR code using the old path."""
        # Configure mock to return a QR code
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.redirect_url = str(dynamic_qr_params.redirect_url)
        mock_qr_code_repo.create.return_value = mock_qr
        
        # Patch the _is_safe_redirect_url method to return True
        with patch.object(QRCodeService, '_is_safe_redirect_url', return_value=True):
            # Call the service method
            result = qr_service.create_dynamic_qr(dynamic_qr_params)

            # Verify the result
            assert result == mock_qr
            mock_qr_code_repo.create.assert_called_once()

    @patch('app.services.qr_service.should_use_new_service')
    @patch('app.services.qr_service.settings')
    def test_create_dynamic_qr_new_path(self, mock_settings, mock_should_use_new_service, 
                                       qr_service_with_new_service, dynamic_qr_params, 
                                       mock_qr_code_repo, mock_new_qr_generation_service):
        """Test creating a dynamic QR code with feature flag enabled."""
        # Configure mocks
        mock_settings.USE_NEW_QR_GENERATION_SERVICE = True
        mock_should_use_new_service.return_value = True
        mock_settings.BASE_URL = "https://test.example.com"
        
        # Configure mock to return a QR code
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.redirect_url = str(dynamic_qr_params.redirect_url)
        mock_qr_code_repo.create.return_value = mock_qr
        
        # Patch the _is_safe_redirect_url method to return True
        with patch.object(QRCodeService, '_is_safe_redirect_url', return_value=True):
            # Call the service method
            result = qr_service_with_new_service.create_dynamic_qr(dynamic_qr_params)

            # Verify the result
            assert result == mock_qr
            mock_qr_code_repo.create.assert_called_once()
            
            # Verify new service was called
            mock_new_qr_generation_service.create_and_format_qr_sync.assert_called_once()

    def test_generate_qr_image_old_path(self, qr_service):
        """Test generating a QR code image using the old path."""
        # Patch the qr_imaging_util function
        with patch('app.services.qr_service.qr_imaging_util', return_value=b"mock_image_bytes"):
            # Call the service method
            result = qr_service.generate_qr_image(
                content="https://example.com",
                fill_color="#000000",
                back_color="#FFFFFF",
                box_size=10,
                border=4,
                image_format="PNG"
            )
            
            # Verify the result is a BytesIO object
            assert isinstance(result, BytesIO)
            # Verify the BytesIO object contains the expected bytes
            result.seek(0)
            assert result.read() == b"mock_image_bytes"

    @patch('app.services.qr_service.should_use_new_service')
    @patch('app.services.qr_service.settings')
    def test_generate_qr_image_new_path(self, mock_settings, mock_should_use_new_service, 
                                       qr_service_with_new_service, mock_new_qr_generation_service):
        """Test generating a QR code image with feature flag enabled."""
        # Configure mocks
        mock_settings.USE_NEW_QR_GENERATION_SERVICE = True
        mock_should_use_new_service.return_value = True
        
        # Call the service method
        result = qr_service_with_new_service.generate_qr_image(
            content="https://example.com",
            fill_color="#000000",
            back_color="#FFFFFF",
            box_size=10,
            border=4,
            image_format="PNG"
        )
        
        # Verify the result is a BytesIO object
        assert isinstance(result, BytesIO)
        # Verify the BytesIO object contains the expected bytes
        result.seek(0)
        assert result.read() == b"mock_image_bytes"
        
        # Verify new service was called
        mock_new_qr_generation_service.create_and_format_qr_sync.assert_called_once()

    def test_generate_qr_old_path(self, qr_service):
        """Test generating a QR code response using the old path."""
        # Patch the generate_qr_response function
        mock_response = MagicMock()
        with patch('app.services.qr_service.generate_qr_response', return_value=mock_response):
            # Call the service method
            result = qr_service.generate_qr(
                data="https://example.com",
                size=10,
                border=4,
                fill_color="#000000",
                back_color="#FFFFFF",
                image_format="png"
            )
            
            # Verify the result
            assert result == mock_response

    @patch('app.services.qr_service.should_use_new_service')
    @patch('app.services.qr_service.settings')
    def test_generate_qr_new_path(self, mock_settings, mock_should_use_new_service, 
                                 qr_service_with_new_service, mock_new_qr_generation_service):
        """Test generating a QR code response with feature flag enabled."""
        # Configure mocks
        mock_settings.USE_NEW_QR_GENERATION_SERVICE = True
        mock_should_use_new_service.return_value = True
        
        # Mock StreamingResponse
        with patch('app.services.qr_service.StreamingResponse') as mock_streaming_response:
            mock_response = MagicMock()
            mock_streaming_response.return_value = mock_response
            
            # Call the service method
            result = qr_service_with_new_service.generate_qr(
                data="https://example.com",
                size=10,
                border=4,
                fill_color="#000000",
                back_color="#FFFFFF",
                image_format="png"
            )
            
            # Verify the result
            assert result == mock_response
            
            # Verify new service was called
            mock_new_qr_generation_service.create_and_format_qr_sync.assert_called_once()

    def test_new_service_fallback_on_error(self, qr_service_with_new_service, mock_new_qr_generation_service):
        """Test fallback to old path when new service fails."""
        # Configure new service to raise an exception
        mock_new_qr_generation_service.create_and_format_qr_sync.side_effect = Exception("Test error")
        
        # Configure settings and should_use_new_service
        with patch('app.services.qr_service.settings') as mock_settings, \
             patch('app.services.qr_service.should_use_new_service') as mock_should_use_new_service, \
             patch('app.services.qr_service.qr_imaging_util', return_value=b"mock_image_bytes"):
            
            mock_settings.USE_NEW_QR_GENERATION_SERVICE = True
            mock_should_use_new_service.return_value = True
            
            # Call the service method
            result = qr_service_with_new_service.generate_qr_image(
                content="https://example.com",
                fill_color="#000000",
                back_color="#FFFFFF",
                box_size=10,
                border=4,
                image_format="PNG"
            )
            
            # Verify the result is a BytesIO object with the old path result
            assert isinstance(result, BytesIO)
            result.seek(0)
            assert result.read() == b"mock_image_bytes"
            
            # Verify both services were called
            mock_new_qr_generation_service.create_and_format_qr_sync.assert_called_once() 