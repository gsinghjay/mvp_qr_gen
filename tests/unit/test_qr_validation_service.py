"""
Unit tests for QRValidationService.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.services.qr_validation_service import QRValidationService
from app.schemas.qr.models import QRCodeCreate
from app.schemas.common import QRType, ErrorCorrectionLevel
from app.core.config import Settings
from app.core.exceptions import QRCodeValidationError, RedirectURLError
from pydantic import ValidationError as PydanticValidationError # Import Pydantic's error

class TestQRValidationService(unittest.TestCase):

    def setUp(self):
        self.service = QRValidationService()
        # Mock settings that might be used by the service
        self.mock_settings = Settings(
            ALLOWED_REDIRECT_DOMAINS=["example.com", "sub.example.org"],
            MAX_QR_SIZE=100, # Example value
            MAX_QR_BORDER=20   # Example value
        )

    @patch('app.services.qr_validation_service.settings', new_callable=Settings)
    def test_is_safe_redirect_url_allowed(self, mock_settings: Settings):
        mock_settings.ALLOWED_REDIRECT_DOMAINS = ["example.com", "sub.example.org"]
        self.assertTrue(self.service.is_safe_redirect_url("https://example.com/path"))
        self.assertTrue(self.service.is_safe_redirect_url("http://example.com"))
        self.assertTrue(self.service.is_safe_redirect_url("https://www.example.com/another?query=1"))
        self.assertTrue(self.service.is_safe_redirect_url("https://sub.example.org/path"))
        self.assertTrue(self.service.is_safe_redirect_url("https://deep.sub.example.org/path"))


    @patch('app.services.qr_validation_service.settings', new_callable=Settings)
    def test_is_safe_redirect_url_denied(self, mock_settings: Settings):
        mock_settings.ALLOWED_REDIRECT_DOMAINS = ["example.com"]
        self.assertFalse(self.service.is_safe_redirect_url("https://evil.com/path"))
        self.assertFalse(self.service.is_safe_redirect_url("ftp://example.com/path"))
        self.assertFalse(self.service.is_safe_redirect_url("https://another-example.com"))
        self.assertFalse(self.service.is_safe_redirect_url("http://example.org")) # Not in example.com

    @patch('app.services.qr_validation_service.settings', new_callable=Settings)
    def test_is_safe_redirect_url_no_domains_configured(self, mock_settings: Settings):
        mock_settings.ALLOWED_REDIRECT_DOMAINS = [] # No domains configured
        self.assertFalse(self.service.is_safe_redirect_url("https://example.com/path"))

    @patch('app.services.qr_validation_service.settings', new_callable=Settings)
    def test_is_safe_redirect_url_malformed(self, mock_settings: Settings):
        mock_settings.ALLOWED_REDIRECT_DOMAINS = ["example.com"]
        self.assertFalse(self.service.is_safe_redirect_url("http://[::1]:80")) # Invalid URL
        self.assertFalse(self.service.is_safe_redirect_url("randomstring"))


    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_static_valid(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 100
        mock_app_settings.MAX_QR_BORDER = 10
        qr_data = QRCodeCreate(
            content="Test static content",
            qr_type=QRType.STATIC,
            title="Test Title",
            fill_color="#000000",
            back_color="#FFFFFF",
            size=10, # scale factor
            border=4,
            error_level=ErrorCorrectionLevel.M.value
        )
        try:
            self.service.validate_qr_creation_data(qr_data)
        except QRCodeValidationError:
            self.fail("validate_qr_creation_data raised QRCodeValidationError unexpectedly for valid static QR.")

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_dynamic_valid(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 100
        mock_app_settings.MAX_QR_BORDER = 10
        qr_data = QRCodeCreate(
            content="https://example.com/r/test", # content will be the full redirect path for dynamic
            qr_type=QRType.DYNAMIC,
            redirect_url="https://safe.example.com/target", # original target URL
            title="Test Dynamic",
            fill_color="#123456",
            back_color="#FEDCBA",
            size=20,
            border=2,
            error_level=ErrorCorrectionLevel.H.value,
            short_id="test"
        )
        # Note: is_safe_redirect_url is typically called *before* creating QRCodeCreate for dynamic QRs
        # This validation focuses on other aspects like content presence for type.
        try:
            self.service.validate_qr_creation_data(qr_data)
        except (QRCodeValidationError, RedirectURLError):
            self.fail("validate_qr_creation_data raised error unexpectedly for valid dynamic QR.")

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_static_no_content(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 100
        mock_app_settings.MAX_QR_BORDER = 10
        qr_data = QRCodeCreate(
            content="", # Empty content
            qr_type=QRType.STATIC,
            size=10, border=1, error_level='M'
        )
        with self.assertRaisesRegex(QRCodeValidationError, "Static QR codes must have content"):
            self.service.validate_qr_creation_data(qr_data)

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_dynamic_no_redirect_url(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 100
        mock_app_settings.MAX_QR_BORDER = 10
        # Pydantic's HttpUrl will fail on empty string before our service validation is hit.
        # So, we expect a QRCodeValidationError (from Pydantic) rather than our service's RedirectURLError.
        # To test the service's RedirectURLError specifically, redirect_url would need to be None,
        # but HttpUrl doesn't allow None by default unless Optional[HttpUrl] is used.
        # For this test, we acknowledge Pydantic catches it first.
        with self.assertRaises(PydanticValidationError): # Expect Pydantic's ValidationError
            qr_data = QRCodeCreate(
                content="https://example.com/r/test",
                qr_type=QRType.DYNAMIC,
                redirect_url="", # Empty redirect_url, Pydantic will raise error
                size=10, border=1, error_level='M', short_id="test"
            )
        # The following service call won't be reached if Pydantic validation for redirect_url fails.
        # If we wanted to test the specific raise in the service, we'd have to bypass Pydantic's HttpUrl validation
        # or ensure redirect_url is truly None and the field is Optional.
        # For now, this test confirms that an invalid empty redirect_url is caught.
        # To test the service's specific check for a missing redirect_url (if it were None and Optional):
        # qr_data_for_service_check = MagicMock(spec=QRCodeCreate)
        # qr_data_for_service_check.qr_type = QRType.DYNAMIC
        # qr_data_for_service_check.redirect_url = None
        # with self.assertRaisesRegex(RedirectURLError, "Dynamic QR codes must have a redirect URL"):
        #     self.service.validate_qr_creation_data(qr_data_for_service_check)


    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_invalid_size_too_large(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 50
        mock_app_settings.MAX_QR_BORDER = 10
        qr_data = QRCodeCreate(content="test", qr_type=QRType.STATIC, size=51, border=1, error_level='M')
        with self.assertRaisesRegex(QRCodeValidationError, "QR code size must be between 1 and 50"):
            self.service.validate_qr_creation_data(qr_data)

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_invalid_size_too_large(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 50
        mock_app_settings.MAX_QR_BORDER = 10
        qr_data = QRCodeCreate(content="test", qr_type=QRType.STATIC, size=51, border=1, error_level='M')
        with self.assertRaisesRegex(QRCodeValidationError, "QR code size must be between 1 and 50"):
            self.service.validate_qr_creation_data(qr_data)

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_invalid_size_too_small(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 50
        mock_app_settings.MAX_QR_BORDER = 10
        # Pydantic model QRCodeCreate has size >= 1. This will be caught by Pydantic.
        with self.assertRaises(PydanticValidationError): # Expect Pydantic's ValidationError
            qr_data = QRCodeCreate(content="test", qr_type=QRType.STATIC, size=0, border=1, error_level='M')
        # To test the service's specific check if Pydantic allowed size=0:
        # qr_data_for_service_check = MagicMock(spec=QRCodeCreate)
        # ... setup qr_data_for_service_check with size=0 ...
        # with self.assertRaisesRegex(QRCodeValidationError, "QR code size must be between 1 and 50"):
        #     self.service.validate_qr_creation_data(qr_data_for_service_check)

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_invalid_border_too_large(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 50
        mock_app_settings.MAX_QR_BORDER = 5
        qr_data = QRCodeCreate(content="test", qr_type=QRType.STATIC, size=10, border=6, error_level='M')
        with self.assertRaisesRegex(QRCodeValidationError, "QR code border must be between 0 and 5"):
            self.service.validate_qr_creation_data(qr_data)

    @patch('app.services.qr_validation_service.settings')
    def test_validate_qr_creation_data_invalid_border_negative(self, mock_app_settings):
        mock_app_settings.MAX_QR_SIZE = 50
        mock_app_settings.MAX_QR_BORDER = 5
        # Pydantic model QRCodeCreate has border >= 0. This will be caught by Pydantic.
        with self.assertRaises(PydanticValidationError): # Expect Pydantic's ValidationError
            qr_data = QRCodeCreate(content="test", qr_type=QRType.STATIC, size=10, border=-1, error_level='M')
        # To test the service's specific check if Pydantic allowed border=-1:
        # qr_data_for_service_check = MagicMock(spec=QRCodeCreate)
        # ... setup qr_data_for_service_check with border=-1 ...
        # with self.assertRaisesRegex(QRCodeValidationError, "QR code border must be between 0 and 5"):
        #     self.service.validate_qr_creation_data(qr_data_for_service_check)
            self.service.validate_qr_creation_data(qr_data)

if __name__ == '__main__':
    unittest.main()
