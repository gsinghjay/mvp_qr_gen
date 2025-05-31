"""
Unit tests for QRManagementService.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from app.services.qr_management_service import QRManagementService
from app.services.qr_validation_service import QRValidationService
from app.services.qr_image_service import QRImageService
from app.repositories.qr_code_repository import QRCodeRepository
from app.models.qr import QRCode
from app.schemas.qr.models import QRCodeCreate
from app.schemas.qr.parameters import StaticQRCreateParameters, DynamicQRCreateParameters, QRUpdateParameters, QRImageParameters
from app.schemas.common import QRType, ErrorCorrectionLevel
from app.core.exceptions import (
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError,
    ResourceConflictError,
    QRCodeGenerationError,
    InvalidQRTypeError # Added import
)
from app.core.config import Settings

class TestQRManagementService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_qr_code_repo = MagicMock(spec=QRCodeRepository)
        self.mock_qr_validation_service = MagicMock(spec=QRValidationService)
        self.mock_qr_image_service = MagicMock(spec=QRImageService)
        # Make async methods on mock_qr_image_service awaitable
        self.mock_qr_image_service.create_and_format_qr_from_service = AsyncMock()


        self.service = QRManagementService(
            qr_code_repo=self.mock_qr_code_repo,
            qr_validation_service=self.mock_qr_validation_service,
            qr_image_service=self.mock_qr_image_service
        )
        # Mock settings for BASE_URL
        self.mock_settings_patcher = patch('app.services.qr_management_service.settings', Settings(BASE_URL="http://test.com"))
        self.mock_settings = self.mock_settings_patcher.start()


    def tearDown(self):
        self.mock_settings_patcher.stop()

    def test_get_qr_by_id_found(self):
        qr_id = "test_id"
        mock_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.get_by_id.return_value = mock_qr

        result = self.service.get_qr_by_id(qr_id)
        self.assertEqual(result, mock_qr)
        self.mock_qr_code_repo.get_by_id.assert_called_once_with(qr_id)

    def test_get_qr_by_id_not_found(self):
        qr_id = "not_found_id"
        self.mock_qr_code_repo.get_by_id.return_value = None
        with self.assertRaises(QRCodeNotFoundError):
            self.service.get_qr_by_id(qr_id)

    def test_get_qr_by_short_id_found_dynamic(self):
        short_id = "shorty"
        mock_qr = MagicMock(spec=QRCode)
        mock_qr.qr_type = QRType.DYNAMIC.value
        self.mock_qr_code_repo.get_by_short_id.return_value = mock_qr

        result = self.service.get_qr_by_short_id(short_id)
        self.assertEqual(result, mock_qr)

    def test_get_qr_by_short_id_not_dynamic_type(self):
        short_id = "shorty_static"
        mock_qr = MagicMock(spec=QRCode)
        mock_qr.qr_type = QRType.STATIC.value # Not dynamic
        self.mock_qr_code_repo.get_by_short_id.return_value = mock_qr
        with self.assertRaises(InvalidQRTypeError): # Corrected expected exception
            try:
                self.service.get_qr_by_short_id(short_id)
            except InvalidQRTypeError: # Catch the correct exception type for the assert
                 raise
            except Exception as e:
                 self.fail(f"Expected InvalidQRTypeError but got {type(e)}")


    def test_list_qr_codes(self):
        mock_qrs = [MagicMock(spec=QRCode)]
        self.mock_qr_code_repo.list_qr_codes.return_value = (mock_qrs, 1)

        qrs, total = self.service.list_qr_codes(skip=0, limit=10)
        self.assertEqual(qrs, mock_qrs)
        self.assertEqual(total, 1)
        self.mock_qr_code_repo.list_qr_codes.assert_called_once()

    async def test_create_static_qr_success(self):
        params = StaticQRCreateParameters(
            content="Test", title="T", error_level=ErrorCorrectionLevel.M,
            size=10, border=1, fill_color="#000000", back_color="#FFFFFF"
        )
        mock_created_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.create.return_value = mock_created_qr
        # Assume validation and image pre-gen pass
        self.mock_qr_validation_service.validate_qr_creation_data.return_value = None
        self.mock_qr_image_service.create_and_format_qr_from_service.return_value = b"imagedata"

        result = await self.service.create_static_qr(params)

        self.assertEqual(result, mock_created_qr)
        self.mock_qr_validation_service.validate_qr_creation_data.assert_called_once()
        self.mock_qr_image_service.create_and_format_qr_from_service.assert_called_once()
        self.mock_qr_code_repo.create.assert_called_once()
        # Add assertion for QRCodeCreate data passed to repo

    async def test_create_static_qr_validation_fails(self):
        params = StaticQRCreateParameters(content="", title="T", error_level=ErrorCorrectionLevel.M, size=10, border=1)
        self.mock_qr_validation_service.validate_qr_creation_data.side_effect = QRCodeValidationError("No content")

        with self.assertRaises(QRCodeValidationError):
            await self.service.create_static_qr(params)
        self.mock_qr_code_repo.create.assert_not_called()

    async def test_create_static_qr_image_pre_gen_fails(self):
        params = StaticQRCreateParameters(content="Test", title="T", error_level=ErrorCorrectionLevel.M, size=10, border=1)
        self.mock_qr_validation_service.validate_qr_creation_data.return_value = None
        self.mock_qr_image_service.create_and_format_qr_from_service.side_effect = QRCodeGenerationError("Image gen failed")

        with self.assertRaises(QRCodeGenerationError):
            await self.service.create_static_qr(params)
        self.mock_qr_code_repo.create.assert_not_called()


    @patch('uuid.uuid4')
    async def test_create_dynamic_qr_success(self, mock_uuid):
        mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
        short_id = '12345678'

        params = DynamicQRCreateParameters(
            redirect_url="https://safe.example.com", title="Dynamic", error_level=ErrorCorrectionLevel.L,
            size=10, border=1, fill_color="#121212", back_color="#FEFEFE" # Using different valid hex
        )
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = True
        self.mock_qr_validation_service.validate_qr_creation_data.return_value = None
        self.mock_qr_image_service.create_and_format_qr_from_service.return_value = b"imagedata"
        mock_created_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.create.return_value = mock_created_qr

        result = await self.service.create_dynamic_qr(params)

        self.assertEqual(result, mock_created_qr)
        self.mock_qr_validation_service.is_safe_redirect_url.assert_called_once_with(str(params.redirect_url))
        self.mock_qr_validation_service.validate_qr_creation_data.assert_called_once()
        # Check that short_id was generated and included in content for image gen and DB
        call_kwargs_img = self.mock_qr_image_service.create_and_format_qr_from_service.call_args.kwargs
        self.assertIn(short_id, call_kwargs_img['content'])

        call_args_db = self.mock_qr_code_repo.create.call_args[0][0] # First positional arg of the first call
        self.assertIn(short_id, call_args_db['content'])
        self.assertEqual(call_args_db['short_id'], short_id)


    async def test_create_dynamic_qr_unsafe_redirect(self):
        params = DynamicQRCreateParameters(redirect_url="http://unsafe.com", title="D", error_level=ErrorCorrectionLevel.L, size=10, border=1)
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = False

        with self.assertRaises(RedirectURLError):
            await self.service.create_dynamic_qr(params)
        self.mock_qr_code_repo.create.assert_not_called()

    async def test_create_dynamic_qr_short_id_collision_handled_by_db(self):
        # This test assumes the DB would raise an error for unique constraint
        # The service currently tries to catch a generic exception and convert it to ResourceConflictError
        params = DynamicQRCreateParameters(redirect_url="https://safe.example.com", title="D", error_level=ErrorCorrectionLevel.L, size=10, border=1)
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = True
        self.mock_qr_validation_service.validate_qr_creation_data.return_value = None
        self.mock_qr_image_service.create_and_format_qr_from_service.return_value = b"imagedata"
        # Simulate DB error for unique constraint
        self.mock_qr_code_repo.create.side_effect = Exception("unique constraint failed for short_id")

        with self.assertRaises(ResourceConflictError):
             await self.service.create_dynamic_qr(params)


    async def test_update_qr_success(self):
        qr_id = "update_id"
        mock_current_qr = MagicMock(spec=QRCode)
        mock_current_qr.qr_type = QRType.STATIC.value
        self.mock_qr_code_repo.get_by_id.return_value = mock_current_qr

        update_params = QRUpdateParameters(title="New Title", description="New Desc")
        mock_updated_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.update_qr.return_value = mock_updated_qr

        result = await self.service.update_qr(qr_id, update_params)

        self.assertEqual(result, mock_updated_qr)
        self.mock_qr_code_repo.update_qr.assert_called_once()
        update_data_arg = self.mock_qr_code_repo.update_qr.call_args[0][1]
        self.assertEqual(update_data_arg['title'], "New Title")
        self.assertIn('updated_at', update_data_arg)

    async def test_update_qr_dynamic_redirect_success(self):
        qr_id = "dyn_update_id"
        mock_current_qr = MagicMock(spec=QRCode)
        mock_current_qr.qr_type = QRType.DYNAMIC.value # Dynamic QR
        self.mock_qr_code_repo.get_by_id.return_value = mock_current_qr
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = True

        new_redirect_url = "https://newsafe.example.com"
        update_params = QRUpdateParameters(redirect_url=new_redirect_url)
        mock_updated_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.update_qr.return_value = mock_updated_qr

        result = await self.service.update_qr(qr_id, update_params)
        self.assertEqual(result, mock_updated_qr)
        self.mock_qr_validation_service.is_safe_redirect_url.assert_called_once_with(str(update_params.redirect_url)) # Use str(HttpUrl)
        update_data_arg = self.mock_qr_code_repo.update_qr.call_args[0][1]
        self.assertEqual(update_data_arg['redirect_url'], str(update_params.redirect_url)) # Compare with str(HttpUrl)


    async def test_update_qr_dynamic_redirect_unsafe(self):
        qr_id = "dyn_update_unsafe"
        mock_current_qr = MagicMock(spec=QRCode)
        mock_current_qr.qr_type = QRType.DYNAMIC.value
        self.mock_qr_code_repo.get_by_id.return_value = mock_current_qr
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = False # Unsafe

        update_params = QRUpdateParameters(redirect_url="http://bad.com")
        with self.assertRaises(RedirectURLError):
            await self.service.update_qr(qr_id, update_params)
        self.mock_qr_code_repo.update_qr.assert_not_called()

    async def test_update_qr_static_attempt_redirect_update(self):
        qr_id = "static_update_redirect_fail"
        mock_current_qr = MagicMock(spec=QRCode)
        mock_current_qr.qr_type = QRType.STATIC.value # Static QR
        self.mock_qr_code_repo.get_by_id.return_value = mock_current_qr

        update_params = QRUpdateParameters(redirect_url="http://try.com")
        with self.assertRaises(QRCodeValidationError): # Or a more specific error
            await self.service.update_qr(qr_id, update_params)
        self.mock_qr_code_repo.update_qr.assert_not_called()

    async def test_update_qr_no_changes(self):
        qr_id = "no_change_id"
        mock_current_qr = MagicMock(spec=QRCode)
        self.mock_qr_code_repo.get_by_id.return_value = mock_current_qr

        update_params = QRUpdateParameters() # No actual update values
        result = await self.service.update_qr(qr_id, update_params)

        self.assertEqual(result, mock_current_qr) # Should return the current QR
        self.mock_qr_code_repo.update_qr.assert_not_called()


    def test_delete_qr_success(self):
        qr_id = "delete_id"
        self.mock_qr_code_repo.delete.return_value = True # Simulate successful delete

        self.service.delete_qr(qr_id)
        self.mock_qr_code_repo.delete.assert_called_once_with(qr_id)

    def test_delete_qr_not_found(self):
        qr_id = "delete_not_found_id"
        self.mock_qr_code_repo.delete.return_value = False # Simulate QR not found by repo

        with self.assertRaises(QRCodeNotFoundError):
            self.service.delete_qr(qr_id)

if __name__ == '__main__':
    unittest.main()
