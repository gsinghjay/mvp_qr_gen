"""
Unit tests for QRImageService.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import aiobreaker
from io import BytesIO

from app.services.qr_image_service import QRImageService, IMAGE_FORMATS
from app.services.new_qr_generation_service import NewQRGenerationService
from app.schemas.qr.parameters import QRImageParameters
from app.schemas.common import ErrorCorrectionLevel
from app.core.config import Settings
from app.core.exceptions import QRCodeGenerationError
from fastapi.responses import StreamingResponse

class TestQRImageService(unittest.IsolatedAsyncioTestCase): # Use IsolatedAsyncioTestCase for async methods

    def setUp(self):
        self.mock_new_qr_generation_service = AsyncMock(spec=NewQRGenerationService)
        # Ensure its async methods are also AsyncMocks
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock()

        # Use MagicMock for the breaker to allow direct assignment of dunder methods
        self.mock_new_qr_generation_breaker = MagicMock(name="CircuitBreakerMock")
        self.mock_new_qr_generation_breaker.state = "closed" # Default state

        # Mock __aenter__ and __aexit__ for async context manager usage
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(return_value=None)
        self.mock_new_qr_generation_breaker.__aexit__ = AsyncMock(return_value=None)

        # Configure the mock for when it's used as a decorator.
        # When called (as a decorator), it should return a wrapper that calls the original function.
        # The wrapper itself needs to be an async function.
        async def decorator_wrapper(func_to_decorate):
            async def wrapped_func(*args, **kwargs):
                # Simulate circuit open behavior for decorator based on state
                if self.mock_new_qr_generation_breaker.state == "open":
                     # Check if a specific test wants this decorator path to raise CircuitBreakerError
                    if getattr(self.mock_new_qr_generation_breaker, 'raise_on_decorator_call_if_open', False):
                        raise aiobreaker.CircuitBreakerError()

                # Allow specific tests to make the decorated function raise an error
                if getattr(self.mock_new_qr_generation_breaker, 'force_exception_in_decorated_func', False):
                    raise Exception("Forced error in decorated function by breaker mock")

                return await func_to_decorate(*args, **kwargs)
            return wrapped_func

        # This makes the mock_new_qr_generation_breaker instance itself callable as a decorator
        # When the breaker mock is called (as a decorator on an async function),
        # its side_effect should return an async function (wrapper).
        def decorator_emulator(original_async_func):
            async def new_async_func(*args, **kwargs):
                # Ensure flags are checked safely, defaulting to False if not present for a test
                breaker_open_and_raises = getattr(self.mock_new_qr_generation_breaker, '_mock_breaker_is_open_and_raises_in_decorator', False)
                force_exception_in_func = getattr(self.mock_new_qr_generation_breaker, '_mock_force_exception_in_decorated_func', False)

                if self.mock_new_qr_generation_breaker.state == "open" and breaker_open_and_raises:
                    raise aiobreaker.CircuitBreakerError(message="Breaker is open and configured to raise in decorator mock", reopen_time=10) # Correct instantiation

                if force_exception_in_func:
                    raise Exception("Forced error in decorated function by breaker mock")

                return await original_async_func(*args, **kwargs)
            return new_async_func

        self.mock_new_qr_generation_breaker.side_effect = decorator_emulator

        # Ensure these flags are reset for each test run by default in tearDown or per-test setup
        # For now, we rely on tests that need these flags to set them, and others to not set them.
        # A more robust solution would be a tearDown method or per-test explicit setting.
        # Let's add explicit reset here for these flags for good measure before each test method implicitly uses this setUp.
        self._reset_breaker_mock_flags()


        self.mock_settings = Settings(USE_NEW_QR_GENERATION_SERVICE=True, FEATURE_FLAG_NEW_QR_SERVICE_USERS='all')

        self.service = QRImageService(
            new_qr_generation_service=self.mock_new_qr_generation_service,
            new_qr_generation_breaker=self.mock_new_qr_generation_breaker,
            app_settings=self.mock_settings
        )
        self.image_params = QRImageParameters(
            size=10, border=4, fill_color="#000000", back_color="#FFFFFF", include_logo=False
        )
        self.test_qr_data = "test_qr_content"
        self.test_image_bytes = b"fake_qr_image_bytes"

    async def test_generate_qr_for_streaming_new_service_success(self):
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(return_value=self.test_image_bytes)

        response = await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        self.assertIsInstance(response, StreamingResponse)
        self.mock_new_qr_generation_service.create_and_format_qr.assert_called_once()
        # Add more assertions about response content if possible

    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_if_new_service_disabled(self, mock_legacy_gen):
        self.mock_settings.USE_NEW_QR_GENERATION_SERVICE = False
        # Re-initialize service with updated settings
        service_new_settings = QRImageService(
            new_qr_generation_service=self.mock_new_qr_generation_service,
            new_qr_generation_breaker=self.mock_new_qr_generation_breaker,
            app_settings=self.mock_settings
        )
        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await service_new_settings.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()

    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_on_breaker_open(self, mock_legacy_gen):
        self.mock_new_qr_generation_breaker.state = "open" # Simulate circuit breaker open
        # Make the context manager raise CircuitBreakerError
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(side_effect=aiobreaker.CircuitBreakerError(message="Breaker open for streaming test", reopen_time=10))

        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()
        # Reset breaker mock for other tests
        self.mock_new_qr_generation_breaker.state = "closed"
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(return_value=None)


    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_on_new_service_exception(self, mock_legacy_gen):
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(side_effect=Exception("New service failed"))
        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_called_once()

    @patch('app.services.qr_image_service.qr_imaging_util_legacy')
    def test_generate_qr_image_bytes_uses_legacy_path(self, mock_legacy_util):
        mock_legacy_util.return_value = self.test_image_bytes

        result_bytes_io = self.service.generate_qr_image_bytes(
            content=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        self.assertIsInstance(result_bytes_io, BytesIO)
        self.assertEqual(result_bytes_io.getvalue(), self.test_image_bytes)
        mock_legacy_util.assert_called_once()

    @patch('app.services.qr_image_service.qr_imaging_util_legacy', side_effect=ValueError("Bad params"))
    def test_generate_qr_image_bytes_legacy_value_error(self, mock_legacy_util):
        with self.assertRaisesRegex(QRCodeGenerationError, "Invalid parameters"):
            self.service.generate_qr_image_bytes(
                content=self.test_qr_data,
                image_params=self.image_params,
                image_format="png"
            )

    @patch('app.services.qr_image_service.qr_imaging_util_legacy', side_effect=IOError("File issue"))
    def test_generate_qr_image_bytes_legacy_io_error(self, mock_legacy_util):
        with self.assertRaisesRegex(QRCodeGenerationError, "Error processing"):
            self.service.generate_qr_image_bytes(
                content=self.test_qr_data,
                image_params=self.image_params,
                image_format="png"
            )

    async def test_create_and_format_qr_from_service_new_path(self):
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(return_value=self.test_image_bytes)
        # Ensure no forced exception for this test
        if hasattr(self.mock_new_qr_generation_breaker, '_mock_force_exception_in_decorated_func'):
            delattr(self.mock_new_qr_generation_breaker, '_mock_force_exception_in_decorated_func')
        if hasattr(self.mock_new_qr_generation_breaker, '_mock_breaker_is_open_and_raises_in_decorator'):
            delattr(self.mock_new_qr_generation_breaker, '_mock_breaker_is_open_and_raises_in_decorator')
        self.mock_new_qr_generation_breaker.state = "closed"


        result = await self.service.create_and_format_qr_from_service(
            content=self.test_qr_data,
            image_params=self.image_params,
            output_format="png",
            error_correction=ErrorCorrectionLevel.M
        )
        self.assertEqual(result, self.test_image_bytes)
        self.mock_new_qr_generation_service.create_and_format_qr.assert_called_once()

    def _reset_breaker_mock_flags(self):
        if hasattr(self.mock_new_qr_generation_breaker, '_mock_breaker_is_open_and_raises_in_decorator'):
            delattr(self.mock_new_qr_generation_breaker, '_mock_breaker_is_open_and_raises_in_decorator')
        if hasattr(self.mock_new_qr_generation_breaker, '_mock_force_exception_in_decorated_func'):
            delattr(self.mock_new_qr_generation_breaker, '_mock_force_exception_in_decorated_func')

    async def test_generate_qr_for_streaming_new_service_success(self):
        self._reset_breaker_mock_flags()
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(return_value=self.test_image_bytes)

        response = await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        self.assertIsInstance(response, StreamingResponse)
        self.mock_new_qr_generation_service.create_and_format_qr.assert_called_once()
        # Add more assertions about response content if possible

    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_if_new_service_disabled(self, mock_legacy_gen):
        self._reset_breaker_mock_flags()
        self.mock_settings.USE_NEW_QR_GENERATION_SERVICE = False
        # Re-initialize service with updated settings
        service_new_settings = QRImageService(
            new_qr_generation_service=self.mock_new_qr_generation_service,
            new_qr_generation_breaker=self.mock_new_qr_generation_breaker,
            app_settings=self.mock_settings
        )
        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await service_new_settings.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()

    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_on_breaker_open(self, mock_legacy_gen):
        self._reset_breaker_mock_flags()
        self.mock_new_qr_generation_breaker.state = "open" # Simulate circuit breaker open
        self.mock_new_qr_generation_breaker._mock_breaker_is_open_and_raises_in_decorator = True
        # Make the context manager raise CircuitBreakerError
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(side_effect=aiobreaker.CircuitBreakerError(message="Breaker open on __aenter__ for streaming test (test)", reopen_time=10))

        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()
        # Reset breaker mock for other tests
        self.mock_new_qr_generation_breaker.state = "closed"
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(return_value=None)
        self.mock_new_qr_generation_breaker._mock_breaker_is_open_and_raises_in_decorator = False


    @patch('app.services.qr_image_service.generate_qr_response_legacy')
    async def test_generate_qr_for_streaming_fallback_to_legacy_on_new_service_exception(self, mock_legacy_gen):
        self._reset_breaker_mock_flags()
        # This test expects the new service path to be tried, and then to fallback
        self.mock_new_qr_generation_breaker._mock_force_exception_in_decorated_func = True # Force exception inside the decorated function call

        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(side_effect=Exception("New service failed"))
        mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

        await self.service.generate_qr_for_streaming(
            data=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        mock_legacy_gen.assert_called_once()
        # The new service path is attempted, but the decorator mock forces an exception *before*
        # self.mock_new_qr_generation_service.create_and_format_qr is called.
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()

    @patch('app.services.qr_image_service.qr_imaging_util_legacy')
    def test_generate_qr_image_bytes_uses_legacy_path(self, mock_legacy_util):
        self._reset_breaker_mock_flags()
        mock_legacy_util.return_value = self.test_image_bytes

        result_bytes_io = self.service.generate_qr_image_bytes(
            content=self.test_qr_data,
            image_params=self.image_params,
            image_format="png"
        )
        self.assertIsInstance(result_bytes_io, BytesIO)
        self.assertEqual(result_bytes_io.getvalue(), self.test_image_bytes)
        mock_legacy_util.assert_called_once()

    @patch('app.services.qr_image_service.qr_imaging_util_legacy', side_effect=ValueError("Bad params"))
    def test_generate_qr_image_bytes_legacy_value_error(self, mock_legacy_util):
        self._reset_breaker_mock_flags()
        with self.assertRaisesRegex(QRCodeGenerationError, "Invalid parameters"):
            self.service.generate_qr_image_bytes(
                content=self.test_qr_data,
                image_params=self.image_params,
                image_format="png"
            )

    @patch('app.services.qr_image_service.qr_imaging_util_legacy', side_effect=IOError("File issue"))
    def test_generate_qr_image_bytes_legacy_io_error(self, mock_legacy_util):
        self._reset_breaker_mock_flags()
        with self.assertRaisesRegex(QRCodeGenerationError, "Error processing"):
            self.service.generate_qr_image_bytes(
                content=self.test_qr_data,
                image_params=self.image_params,
                image_format="png"
            )

    async def test_create_and_format_qr_from_service_new_path(self):
        self._reset_breaker_mock_flags()
        self.mock_new_qr_generation_service.create_and_format_qr = AsyncMock(return_value=self.test_image_bytes)

        result = await self.service.create_and_format_qr_from_service(
            content=self.test_qr_data,
            image_params=self.image_params,
            output_format="png",
            error_correction=ErrorCorrectionLevel.M
        )
        self.assertEqual(result, self.test_image_bytes)
        self.mock_new_qr_generation_service.create_and_format_qr.assert_called_once()

    @patch('app.services.qr_image_service.QRImageService.generate_qr_image_bytes', return_value=BytesIO(b"legacy_bytes"))
    async def test_create_and_format_qr_from_service_fallback_on_breaker_open(self, mock_legacy_bytes_method):
        self._reset_breaker_mock_flags()
        self.mock_new_qr_generation_breaker.state = "open"
        self.mock_new_qr_generation_breaker._mock_breaker_is_open_and_raises_in_decorator = True
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(side_effect=aiobreaker.CircuitBreakerError(message="Breaker open on __aenter__ (test)", reopen_time=10))


        result = await self.service.create_and_format_qr_from_service(
            content=self.test_qr_data,
            image_params=self.image_params,
            output_format="png",
            error_correction=ErrorCorrectionLevel.M
        )
        self.assertEqual(result, b"legacy_bytes")
        mock_legacy_bytes_method.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()
        # Reset breaker mock
        self.mock_new_qr_generation_breaker.state = "closed"
        self.mock_new_qr_generation_breaker.__aenter__ = AsyncMock(return_value=None)

    @patch('app.services.qr_image_service.QRImageService.generate_qr_image_bytes', return_value=BytesIO(b"legacy_bytes"))
    async def test_create_and_format_qr_from_service_fallback_if_new_service_disabled(self, mock_legacy_bytes_method):
        self.mock_settings.USE_NEW_QR_GENERATION_SERVICE = False
        service_new_settings = QRImageService( # Re-init with new settings
            new_qr_generation_service=self.mock_new_qr_generation_service,
            new_qr_generation_breaker=self.mock_new_qr_generation_breaker,
            app_settings=self.mock_settings
        )
        result = await service_new_settings.create_and_format_qr_from_service(
            content=self.test_qr_data,
            image_params=self.image_params,
            output_format="png",
            error_correction=ErrorCorrectionLevel.M
        )
        self.assertEqual(result, b"legacy_bytes")
        mock_legacy_bytes_method.assert_called_once()
        self.mock_new_qr_generation_service.create_and_format_qr.assert_not_called()


    async def test_generate_qr_for_streaming_physical_size_calculation(self):
        # This test focuses on the pixel_size calculation, assuming legacy path for simplicity
        # as new service path delegates this. We need to mock the legacy generator.
        self.mock_settings.USE_NEW_QR_GENERATION_SERVICE = False # Force legacy
        service_new_settings = QRImageService(
            self.mock_new_qr_generation_service, self.mock_new_qr_generation_breaker, self.mock_settings
        )

        with patch('app.services.qr_image_service.generate_qr_response_legacy') as mock_legacy_gen:
            mock_legacy_gen.return_value = StreamingResponse(BytesIO(self.test_image_bytes))

            # Test with inches
            physical_params_in = self.image_params.model_copy(update={
                "physical_size": 2.0, "physical_unit": "in", "dpi": 300
            })
            await service_new_settings.generate_qr_for_streaming(self.test_qr_data, physical_params_in, "png")
            self.assertEqual(mock_legacy_gen.call_args.kwargs['size'], 600) # 2.0 * 300

            # Test with cm
            physical_params_cm = self.image_params.model_copy(update={
                "physical_size": 5.08, "physical_unit": "cm", "dpi": 100 # 5.08cm = 2 inches
            })
            await service_new_settings.generate_qr_for_streaming(self.test_qr_data, physical_params_cm, "png")
            self.assertEqual(mock_legacy_gen.call_args.kwargs['size'], int(5.08 * 100 / 2.54)) # Should be 200

            # Test with mm
            physical_params_mm = self.image_params.model_copy(update={
                "physical_size": 25.4, "physical_unit": "mm", "dpi": 72 # 25.4mm = 1 inch
            })
            await service_new_settings.generate_qr_for_streaming(self.test_qr_data, physical_params_mm, "png")
            self.assertEqual(mock_legacy_gen.call_args.kwargs['size'], int(25.4 * 72 / 25.4)) # Should be 72

            # Test with default if physical unit unknown
            physical_params_unknown = self.image_params.model_copy(update={
                "physical_size": 1.0, "physical_unit": "xx", "dpi": 100
            })
            await service_new_settings.generate_qr_for_streaming(self.test_qr_data, physical_params_unknown, "png")
            self.assertEqual(mock_legacy_gen.call_args.kwargs['size'], self.image_params.size * 25) # Default: 10 * 25 = 250

if __name__ == '__main__':
    unittest.main()
