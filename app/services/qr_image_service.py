import logging
import time
from io import BytesIO
from typing import Optional

import aiobreaker
from fastapi.responses import StreamingResponse

from app.core.config import Settings, should_use_new_service
from app.services.new_qr_generation_service import NewQRGenerationService
from app.schemas.common import ErrorCorrectionLevel
from app.schemas.qr.parameters import QRImageParameters
from app.utils.qr_imaging import generate_qr_response # For the legacy path
from app.core.metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)

# Define supported image formats and their media types (copied from qr_service.py)
IMAGE_FORMATS = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

class QRImageService:
    def __init__(
        self,
        settings: Settings,
        new_qr_generation_service: Optional[NewQRGenerationService],
        new_qr_generation_breaker: Optional[aiobreaker.CircuitBreaker],
    ):
        self.settings = settings
        self.settings = settings
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker

    @MetricsLogger.time_service_call("QRImageService", "generate_qr_image_response") # Updated Metric Tag
    async def generate_qr_image_response(
        self,
        data: str, # Content to encode
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_level: Optional[str] = None,
        image_format: str = "png",
        image_quality: Optional[int] = None,
        include_logo: bool = False,
        svg_title: Optional[str] = None,
        svg_description: Optional[str] = None,
        physical_size: Optional[float] = None,
        physical_unit: Optional[str] = None,
        dpi: Optional[int] = None,
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters and return as a StreamingResponse.
        (Method moved from QRCodeService.generate_qr and renamed)
        """
        # If physical dimensions are specified, use them directly
        if physical_size is not None and physical_unit is not None and dpi is not None:
            if physical_unit == "in":
                pixel_size = int(physical_size * dpi)
            elif physical_unit == "cm":
                pixel_size = int(physical_size * dpi / 2.54)
            elif physical_unit == "mm":
                pixel_size = int(physical_size * dpi / 25.4)
            else:
                pixel_size = size * 25
        else:
            pixel_size = size * 25

        try:
            # Use self.settings for configuration access
            if (self.new_qr_generation_service is not None and
                self.new_qr_generation_breaker is not None and
                self.settings.USE_NEW_QR_GENERATION_SERVICE and
                should_use_new_service(self.settings, user_identifier=data)):

                new_path_start_time = time.perf_counter()
                try:
                    error_correction_enum = ErrorCorrectionLevel.M # Default
                    if error_level:
                        error_level_map = {
                            'l': ErrorCorrectionLevel.L, 'm': ErrorCorrectionLevel.M,
                            'q': ErrorCorrectionLevel.Q, 'h': ErrorCorrectionLevel.H
                        }
                        error_correction_enum = error_level_map.get(error_level.lower(), ErrorCorrectionLevel.M)

                    image_params = QRImageParameters(
                        fill_color=fill_color, back_color=back_color, size=size,
                        border=border, include_logo=include_logo, svg_title=svg_title,
                        svg_description=svg_description, physical_size=physical_size,
                        physical_unit=physical_unit, dpi=dpi
                    )

                    @self.new_qr_generation_breaker
                    async def protected_generate_qr():
                        return await self.new_qr_generation_service.create_and_format_qr(
                            content=data, image_params=image_params,
                            output_format=image_format, error_correction=error_correction_enum
                        )

                    image_bytes = await protected_generate_qr()

                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_image_response", True, new_path_duration)
                    logger.info(f"Generated QR code with new service (format: {image_format})")
                    MetricsLogger.log_image_generated(image_format, True)

                    media_type = IMAGE_FORMATS.get(image_format.lower(), "application/octet-stream")
                    return StreamingResponse(
                        BytesIO(image_bytes), media_type=media_type,
                        headers={"Content-Disposition": f"inline; filename=qr_code.{image_format.lower()}"}
                    )

                except aiobreaker.CircuitBreakerError as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_image_response", False, new_path_duration)
                    logger.warning(f"Circuit breaker open for NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "generate_qr_image_response", "circuit_open")

                except Exception as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_qr_image_response", False, new_path_duration)
                    logger.error(f"Error with NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "generate_qr_image_response", "exception")

            # Legacy implementation
            old_path_start_time = time.perf_counter()
            try:
                # generate_qr_response is imported from app.utils.qr_imaging
                response = generate_qr_response(
                    content=data, image_format=image_format, size=pixel_size,
                    fill_color=fill_color, back_color=back_color, border=border,
                    image_quality=image_quality, logo_path=True if include_logo else None,
                    error_level=error_level, svg_title=svg_title, svg_description=svg_description,
                    physical_size=physical_size, physical_unit=physical_unit, dpi=dpi
                )

                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "generate_qr_image_response", True, old_path_duration)
                logger.info(f"Generated QR code with legacy service (format: {image_format})")
                MetricsLogger.log_image_generated(image_format, True)
                return response
            except Exception as e:
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "generate_qr_image_response", False, old_path_duration)
                MetricsLogger.log_image_generated(image_format, False)
                raise
        except Exception as e:
            MetricsLogger.log_image_generated(image_format, False)
            # Re-raise the original exception if it's not handled above
            # Or, if specific HTTPExceptions are expected:
            # from fastapi import HTTPException
            # if isinstance(e, HTTPException): raise
            # else: raise HTTPException(status_code=500, detail=str(e))
            raise
