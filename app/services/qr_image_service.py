"""
Service for generating QR code images.
"""
import logging
import time
from io import BytesIO
from typing import Optional, Union

import aiobreaker
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse


from ..core.config import settings, Settings, should_use_new_service
from ..core.exceptions import QRCodeGenerationError
from ..schemas.common import ErrorCorrectionLevel
from ..schemas.qr.parameters import QRImageParameters
from ..services.new_qr_generation_service import NewQRGenerationService # Assuming this will be the new home or imported
from ..utils.qr_imaging import generate_qr_image as qr_imaging_util_legacy, generate_qr_response as generate_qr_response_legacy
from ..core.metrics_logger import MetricsLogger


logger = logging.getLogger(__name__)

# Define supported image formats and their media types
IMAGE_FORMATS = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

class QRImageService:
    """Service class for QR code image generation."""

    def __init__(
        self,
        new_qr_generation_service: Optional[NewQRGenerationService],
        new_qr_generation_breaker: Optional[aiobreaker.CircuitBreaker],
        app_settings: Settings = settings # Allow settings injection for testability
    ):
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker
        self.settings = app_settings

    async def generate_qr_for_streaming(
        self,
        data: str,
        image_params: QRImageParameters,
        error_level_str: Optional[str] = "M", # Renamed from error_level to avoid conflict
        image_format: str = "png",
        image_quality: Optional[int] = 90, # Kept for legacy compatibility
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters for streaming response.

        Args:
            data: Content to encode in the QR code
            image_params: Object containing all image styling parameters
            error_level_str: Error correction level string (l, m, q, h)
            image_format: Output image format (png, jpeg, svg, webp)
            image_quality: Quality for lossy formats (1-100) - for legacy path

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        pixel_size = image_params.size * 25  # Default/legacy calculation, new service might handle it differently

        if image_params.physical_size is not None and image_params.physical_unit is not None and image_params.dpi is not None:
            if image_params.physical_unit == "in":
                pixel_size = int(image_params.physical_size * image_params.dpi)
            elif image_params.physical_unit == "cm":
                pixel_size = int(image_params.physical_size * image_params.dpi / 2.54)
            elif image_params.physical_unit == "mm":
                pixel_size = int(image_params.physical_size * image_params.dpi / 25.4)

        error_correction = ErrorCorrectionLevel.M  # Default
        if error_level_str:
            error_level_map = {
                'l': ErrorCorrectionLevel.L,
                'm': ErrorCorrectionLevel.M,
                'q': ErrorCorrectionLevel.Q,
                'h': ErrorCorrectionLevel.H
            }
            error_correction = error_level_map.get(error_level_str.lower(), ErrorCorrectionLevel.M)

        try:
            if (self.new_qr_generation_service is not None and
                self.new_qr_generation_breaker is not None and
                self.settings.USE_NEW_QR_GENERATION_SERVICE and
                should_use_new_service(self.settings, user_identifier=data)):

                new_path_start_time = time.perf_counter()
                try:
                    @self.new_qr_generation_breaker
                    async def protected_generate_qr():
                        return await self.new_qr_generation_service.create_and_format_qr(
                            content=data,
                            image_params=image_params, # Pass the whole params object
                            output_format=image_format,
                            error_correction=error_correction
                        )

                    image_bytes = await protected_generate_qr()

                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_for_streaming", True, new_path_duration)
                    logger.info(f"Generated QR code with new service (format: {image_format})")
                    MetricsLogger.log_image_generated(image_format, True)

                    media_type = IMAGE_FORMATS.get(image_format.lower(), "application/octet-stream")
                    return StreamingResponse(
                        BytesIO(image_bytes),
                        media_type=media_type,
                        headers={"Content-Disposition": f"inline; filename=qr_code.{image_format.lower()}"}
                    )
                except aiobreaker.CircuitBreakerError as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_for_streaming", False, new_path_duration)
                    logger.warning(f"Circuit breaker open for NewQRGenerationService: {e}, falling back to legacy.")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "generate_qr_for_streaming", "circuit_open")
                except Exception as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_for_streaming", False, new_path_duration)
                    logger.error(f"Error with NewQRGenerationService: {e}, falling back to legacy.")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "generate_qr_for_streaming", "exception")

            # Legacy implementation (fallback or when new service is disabled)
            old_path_start_time = time.perf_counter()
            try:
                # Convert QRImageParameters to legacy generate_qr_response_legacy arguments
                response = generate_qr_response_legacy(
                    content=data,
                    image_format=image_format,
                    size=pixel_size, # Legacy uses calculated pixel_size
                    fill_color=image_params.fill_color,
                    back_color=image_params.back_color,
                    border=image_params.border,
                    image_quality=image_quality, # Legacy specific
                    logo_path=True if image_params.include_logo else None,
                    error_level=error_level_str, # Legacy uses string
                    svg_title=image_params.svg_title,
                    svg_description=image_params.svg_description,
                    physical_size=image_params.physical_size,
                    physical_unit=image_params.physical_unit,
                    dpi=image_params.dpi
                )
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "generate_qr_for_streaming", True, old_path_duration)
                logger.info(f"Generated QR code with legacy service (format: {image_format})")
                MetricsLogger.log_image_generated(image_format, True)
                return response
            except Exception as e:
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "generate_qr_for_streaming", False, old_path_duration)
                MetricsLogger.log_image_generated(image_format, False)
                logger.error(f"Legacy QR generation failed: {e}")
                raise QRCodeGenerationError(f"Failed to generate QR code using legacy path: {e}")

        except Exception as e:
            MetricsLogger.log_image_generated(image_format, False)
            logger.exception(f"Unhandled error during QR image generation (format: {image_format}): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate QR code image: {str(e)}"
            )

    def generate_qr_image_bytes(
        self,
        content: str,
        image_params: QRImageParameters, # Using the new params object
        image_format: str = "PNG",
        error_level_str: Optional[str] = "M", # Legacy compatible error level
    ) -> BytesIO:
        """
        Generate a QR code image and return as BytesIO.
        This method primarily uses the legacy imaging utility directly.
        The new service path is more geared towards `create_and_format_qr` which returns bytes directly.

        Args:
            content: The content to encode in the QR code
            image_params: Parameters for QR image generation.
            image_format: The format of the image (PNG, JPEG, etc.)
            error_level_str: Error correction level string (l, m, q, h) for legacy path

        Returns:
            A BytesIO object containing the image data

        Raises:
            QRCodeGenerationError: If there are issues with QR generation.
        """
        try:
            # For byte generation, the legacy path is more direct with qr_imaging_util_legacy
            # If new service path is desired here, it would be similar to generate_qr_for_streaming
            # but without the StreamingResponse wrapping.

            # Calculate the approximate size based on box_size for legacy util
            # The QRImageParameters has 'size' which is a scale factor.
            legacy_box_size = image_params.size # This 'size' is more like 'scale' or 'box_size' for legacy

            # So, if `image_params.size` is the "scale factor", then:
            pixel_size_for_legacy_util = image_params.size * 25 # Replicating old logic if size is scale

            # Generate the QR code using the legacy utility function
            img_bytes = qr_imaging_util_legacy(
                content=content,
                image_format=image_format.lower(),
                # qr_imaging_util_legacy expects 'size' to be pixel size, not scale factor
                # This is a slight mismatch. The original generate_qr_image_service used box_size.
                # If image_params.size is a scale factor (e.g. 10), then pixel size might be size * 25.
                # For now, we'll pass image_params.size as box_size as per original method's box_size param.
                # This might need adjustment based on how 'size' in QRImageParameters is intended.
                # The original method had `size = box_size * 25` then called `qr_imaging_util` with that `size`.
                # Let's assume image_params.size is the intended final pixel size for this legacy path for now.
                # Correction: The old method `generate_qr_image_service` took `box_size` and calculated `size`.
                # The `qr_imaging_util_legacy` takes `size` which is the overall image size.
                size=pixel_size_for_legacy_util, # This should be overall pixel size
                fill_color=image_params.fill_color,
                back_color=image_params.back_color,
                border=image_params.border,
                logo_path=True if image_params.include_logo else None,
                error_level=error_level_str # Legacy util takes string
            )

            img_buffer = BytesIO(img_bytes)
            img_buffer.seek(0)

            MetricsLogger.log_image_generated(image_format.lower(), True)
            return img_buffer
        except ValueError as e:
            MetricsLogger.log_image_generated(image_format.lower(), False)
            logger.error(f"Parameter validation error generating QR image bytes (legacy): {e}")
            raise QRCodeGenerationError(f"Invalid parameters for QR image bytes generation: {str(e)}")
        except IOError as e:
            MetricsLogger.log_image_generated(image_format.lower(), False)
            logger.error(f"IO error generating QR image bytes (legacy): {e}")
            raise QRCodeGenerationError(f"Error processing QR image bytes: {str(e)}")
        except Exception as e:
            MetricsLogger.log_image_generated(image_format.lower(), False)
            logger.error(f"General error generating QR image bytes (legacy): {e}")
            raise QRCodeGenerationError(f"General error in QR image bytes generation: {str(e)}")

    async def create_and_format_qr_from_service(
        self,
        content: str,
        image_params: QRImageParameters,
        output_format: str,
        error_correction: ErrorCorrectionLevel
    ) -> bytes:
        """
        Uses the NewQRGenerationService to create QR image bytes.
        This method is intended to be called by other services (e.g., QRManagementService)
        when the new generation path is active.
        """
        if not (self.new_qr_generation_service and self.new_qr_generation_breaker and
                self.settings.USE_NEW_QR_GENERATION_SERVICE and
                should_use_new_service(self.settings, user_identifier=content)):
            # This situation should ideally be handled by the caller by checking flags,
            # or this method could fall back to calling generate_qr_image_bytes (legacy).
            # For now, let's raise an error if called inappropriately.
            logger.warning("create_and_format_qr_from_service called when new service path is not active/configured.")
            # Fallback to legacy byte generation
            img_buffer = self.generate_qr_image_bytes(
                content=content,
                image_params=image_params,
                image_format=output_format,
                error_level_str=error_correction.value # Convert enum to string for legacy
            )
            return img_buffer.getvalue()


        new_path_start_time = time.perf_counter()
        try:
            @self.new_qr_generation_breaker
            async def protected_action():
                return await self.new_qr_generation_service.create_and_format_qr(
                    content=content,
                    image_params=image_params,
                    output_format=output_format,
                    error_correction=error_correction
                )

            image_bytes = await protected_action()

            new_path_duration = time.perf_counter() - new_path_start_time
            MetricsLogger.log_qr_generation_path("new", "create_and_format_qr_from_service", True, new_path_duration)
            MetricsLogger.log_image_generated(output_format, True)
            return image_bytes

        except aiobreaker.CircuitBreakerError as e:
            new_path_duration = time.perf_counter() - new_path_start_time
            MetricsLogger.log_qr_generation_path("new", "create_and_format_qr_from_service", False, new_path_duration)
            logger.warning(f"Circuit breaker open for NewQRGenerationService in create_and_format_qr_from_service: {e}. Falling back.")
            MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_and_format_qr_from_service", "circuit_open")
            # Fallback to legacy byte generation
            # Ensure log_image_generated is called correctly in the fallback path if generate_qr_image_bytes raises an error
            try:
                img_buffer = self.generate_qr_image_bytes(
                    content=content,
                    image_params=image_params,
                    image_format=output_format,
                    error_level_str=error_correction.value # Convert enum to string for legacy
                )
                return img_buffer.getvalue()
            except Exception:
                MetricsLogger.log_image_generated(output_format, False) # Log failure if fallback fails
                raise # Re-raise the original error or a new one
        except Exception as e:
            new_path_duration = time.perf_counter() - new_path_start_time
            MetricsLogger.log_qr_generation_path("new", "create_and_format_qr_from_service", False, new_path_duration)
            logger.error(f"Error with NewQRGenerationService in create_and_format_qr_from_service: {e}. Falling back.")
            MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_and_format_qr_from_service", "exception")
            # Fallback to legacy byte generation
            try:
                img_buffer = self.generate_qr_image_bytes(
                    content=content,
                    image_params=image_params,
                    image_format=output_format,
                    error_level_str=error_correction.value # Convert enum to string for legacy
                )
                return img_buffer.getvalue()
            except Exception:
                MetricsLogger.log_image_generated(output_format, False) # Log failure if fallback fails
                raise # Re-raise the original error or a new one
