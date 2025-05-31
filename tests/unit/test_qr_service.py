"""
Unit tests for the QRCodeService facade.
"""
import unittest
from unittest.mock import MagicMock, AsyncMock

from app.services.qr_service import QRCodeService
from app.services.qr_management_service import QRManagementService
from app.services.qr_image_service import QRImageService
from app.services.qr_analytics_service import QRAnalyticsService
from app.services.qr_validation_service import QRValidationService
from app.core.config import Settings # For app_settings injection
from app.schemas.qr.parameters import StaticQRCreateParameters, DynamicQRCreateParameters, QRUpdateParameters, QRImageParameters
from app.schemas.common import QRType, ErrorCorrectionLevel
from app.models.qr import QRCode # For type hinting return values
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import datetime

class TestQRCodeServiceFacade(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_qr_management_service = MagicMock(spec=QRManagementService)
        self.mock_qr_image_service = MagicMock(spec=QRImageService)
        self.mock_qr_analytics_service = MagicMock(spec=QRAnalyticsService) # Changed to MagicMock for consistency if only sync methods are called
        self.mock_qr_validation_service = MagicMock(spec=QRValidationService)

        # Configure async methods on the mocks
        self.mock_qr_management_service.create_static_qr = AsyncMock()
        self.mock_qr_management_service.create_dynamic_qr = AsyncMock()
        self.mock_qr_management_service.update_qr = AsyncMock()
        self.mock_qr_management_service.update_dynamic_qr = AsyncMock() # Added for completeness

        self.mock_qr_image_service.generate_qr_for_streaming = AsyncMock()
        # generate_qr_image_bytes is synchronous, so no AsyncMock needed for it on QRImageService mock

        # QRAnalyticsService methods called by facade are synchronous
        # QRValidationService methods called by facade are synchronous

        self.mock_settings = Settings() # Default settings

        self.facade_service = QRCodeService(
            qr_management_service=self.mock_qr_management_service,
            qr_image_service=self.mock_qr_image_service,
            qr_analytics_service=self.mock_qr_analytics_service,
            qr_validation_service=self.mock_qr_validation_service,
            app_settings=self.mock_settings
        )

    # Test Validation Service Delegation
    def test_is_safe_redirect_url_delegation(self):
        url = "http://example.com"
        self.mock_qr_validation_service.is_safe_redirect_url.return_value = True
        result = self.facade_service._is_safe_redirect_url(url) # Test protected if used internally
        self.assertTrue(result)
        self.mock_qr_validation_service.is_safe_redirect_url.assert_called_once_with(url)

    def test_validate_qr_code_delegation(self):
        mock_qr_data = MagicMock()
        self.facade_service.validate_qr_code(mock_qr_data)
        self.mock_qr_validation_service.validate_qr_creation_data.assert_called_once_with(mock_qr_data)

    # Test QR Management Service Delegation
    def test_get_qr_by_id_delegation(self):
        qr_id = "test_id"
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.get_qr_by_id.return_value = expected_qr
        result = self.facade_service.get_qr_by_id(qr_id)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.get_qr_by_id.assert_called_once_with(qr_id)

    def test_get_qr_by_short_id_delegation(self):
        short_id = "shorty"
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.get_qr_by_short_id.return_value = expected_qr
        result = self.facade_service.get_qr_by_short_id(short_id)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.get_qr_by_short_id.assert_called_once_with(short_id)

    def test_list_qr_codes_delegation(self):
        self.mock_qr_management_service.list_qr_codes.return_value = ([], 0)
        self.facade_service.list_qr_codes(skip=1, limit=5)
        self.mock_qr_management_service.list_qr_codes.assert_called_once_with(
            skip=1, limit=5, qr_type=None, search=None, sort_by=None, sort_desc=False
        )

    async def test_create_static_qr_delegation(self):
        params = MagicMock(spec=StaticQRCreateParameters)
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.create_static_qr.return_value = expected_qr

        result = await self.facade_service.create_static_qr(params)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.create_static_qr.assert_called_once_with(params)

    async def test_create_dynamic_qr_delegation(self):
        params = MagicMock(spec=DynamicQRCreateParameters)
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.create_dynamic_qr.return_value = expected_qr

        result = await self.facade_service.create_dynamic_qr(params)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.create_dynamic_qr.assert_called_once_with(params)

    async def test_update_qr_delegation(self):
        qr_id = "update_id"
        params = MagicMock(spec=QRUpdateParameters)
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.update_qr.return_value = expected_qr

        result = await self.facade_service.update_qr(qr_id, params)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.update_qr.assert_called_once_with(qr_id, params)

    async def test_update_dynamic_qr_delegation(self):
        qr_id = "update_dyn_id"
        params = MagicMock(spec=QRUpdateParameters)
        expected_qr = MagicMock(spec=QRCode)
        self.mock_qr_management_service.update_dynamic_qr.return_value = expected_qr # Ensure this method exists on mock

        result = await self.facade_service.update_dynamic_qr(qr_id, params)
        self.assertEqual(result, expected_qr)
        self.mock_qr_management_service.update_dynamic_qr.assert_called_once_with(qr_id, params)


    def test_delete_qr_delegation(self):
        qr_id = "delete_id"
        self.facade_service.delete_qr(qr_id)
        self.mock_qr_management_service.delete_qr.assert_called_once_with(qr_id)

    # Test QR Image Service Delegation
    async def test_generate_qr_delegation(self):
        expected_response = MagicMock(spec=StreamingResponse)
        self.mock_qr_image_service.generate_qr_for_streaming.return_value = expected_response

        response = await self.facade_service.generate_qr(
            data="test_content", size=12, border=3, fill_color="#0000FF", back_color="#FFFF00", # Changed to hex
            error_level="H", image_format="svg", image_quality=80, include_logo=True,
            svg_title="title", svg_description="desc", physical_size=5.0, physical_unit="cm", dpi=300
        )
        self.assertEqual(response, expected_response)
        self.mock_qr_image_service.generate_qr_for_streaming.assert_called_once()
        call_args = self.mock_qr_image_service.generate_qr_for_streaming.call_args[1] # Get kwargs
        self.assertEqual(call_args['data'], "test_content")
        self.assertEqual(call_args['image_format'], "svg")
        self.assertEqual(call_args['error_level_str'], "H")
        # Check image_params object
        image_params_arg = call_args['image_params']
        self.assertIsInstance(image_params_arg, QRImageParameters)
        self.assertEqual(image_params_arg.size, 12)
        self.assertEqual(image_params_arg.border, 3)
        self.assertEqual(image_params_arg.fill_color, "#0000FF")
        self.assertEqual(image_params_arg.back_color, "#FFFF00")
        self.assertTrue(image_params_arg.include_logo)
        self.assertEqual(image_params_arg.svg_title, "title")
        self.assertEqual(image_params_arg.svg_description, "desc")
        self.assertEqual(image_params_arg.physical_size, 5.0)
        self.assertEqual(image_params_arg.physical_unit, "cm")
        self.assertEqual(image_params_arg.dpi, 300)


    def test_generate_qr_image_service_delegation(self): # Old name
        expected_response = MagicMock(spec=BytesIO)
        self.mock_qr_image_service.generate_qr_image_bytes.return_value = expected_response

        response = self.facade_service.generate_qr_image_service(
            content="test_content", box_size=15, border=5, fill_color="#FF0000", back_color="#00FF00", # Changed to hex
            image_format="jpeg", logo_path=True
        )
        self.assertEqual(response, expected_response)
        self.mock_qr_image_service.generate_qr_image_bytes.assert_called_once()
        call_args = self.mock_qr_image_service.generate_qr_image_bytes.call_args[1]
        self.assertEqual(call_args['content'], "test_content")
        self.assertEqual(call_args['image_format'], "jpeg")
        image_params_arg = call_args['image_params']
        self.assertIsInstance(image_params_arg, QRImageParameters)
        self.assertEqual(image_params_arg.size, 15) # box_size maps to size
        self.assertEqual(image_params_arg.border, 5)
        self.assertEqual(image_params_arg.fill_color, "#FF0000")
        self.assertEqual(image_params_arg.back_color, "#00FF00")
        self.assertTrue(image_params_arg.include_logo)


    # Test Analytics Service Delegation
    def test_update_scan_count_delegation(self):
        qr_id = "scan_id"
        ts = datetime.utcnow()
        self.facade_service.update_scan_count(qr_id, ts)
        self.mock_qr_analytics_service.update_qr_scan_count_stats.assert_called_once_with(qr_id, ts, is_genuine_scan_signal=False)

    def test_update_scan_statistics_delegation(self):
        qr_id = "stats_id"
        ts = datetime.utcnow()
        ip = "1.1.1.1"
        ua = "agent"
        is_genuine = True
        self.facade_service.update_scan_statistics(qr_id, ts, ip, ua, is_genuine)
        self.mock_qr_analytics_service.record_scan_event.assert_called_once_with(
            qr_id=qr_id, timestamp=ts, client_ip=ip, user_agent=ua, is_genuine_scan_signal=is_genuine
        )

    def test_get_dashboard_data_delegation(self):
        expected_data = {"total": 10}
        self.mock_qr_analytics_service.get_dashboard_summary.return_value = expected_data
        result = self.facade_service.get_dashboard_data()
        self.assertEqual(result, expected_data)
        self.mock_qr_analytics_service.get_dashboard_summary.assert_called_once()

    def test_get_scan_analytics_data_delegation(self):
        qr_id = "analytics_id"
        expected_data = {"scans": 50}
        self.mock_qr_analytics_service.get_detailed_scan_analytics.return_value = expected_data
        result = self.facade_service.get_scan_analytics_data(qr_id)
        self.assertEqual(result, expected_data)
        self.mock_qr_analytics_service.get_detailed_scan_analytics.assert_called_once_with(qr_id)

if __name__ == '__main__':
    unittest.main()
