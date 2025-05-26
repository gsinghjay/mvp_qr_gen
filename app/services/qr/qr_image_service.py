"""
Service for generating QR code images in various formats with customization options.
"""

import logging
import time
from io import BytesIO
from typing import Optional, Union

import pybreaker
from fastapi.responses import StreamingResponse

from ...core.config import settings, should_use_new_service
from ...core.exceptions import QRCodeValidationError
from ...core.metrics_logger import MetricsLogger
from ...models.qr import QRCode
from ...schemas.common import ErrorCorrectionLevel
from ...schemas.qr.parameters import QRImageParameters
from ...utils.qr_imaging import generate_qr_image as qr_imaging_util, generate_qr_response
from ..new_qr_generation_service import NewQRGenerationService
from .qr_core_service import QRCoreService

# Configure logger
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
    """Service class for QR image generation operations."""

    def __init__(
        self,
        core_service: QRCoreService,
        new_qr_generation_service: Optional[NewQRGenerationService] = None,
        new_qr_generation_breaker: Optional[pybreaker.CircuitBreaker] = None
    ):
        """
        Initialize the QR image service with dependencies.

        Args:
            core_service: QRCoreService for retrieving QR data
            new_qr_generation_service: New QR generation service (optional, for feature flag)
            new_qr_generation_breaker: Circuit breaker for new QR generation service (optional)
        """
        self.core_service = core_service
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker

    @MetricsLogger.time_service_call("QRImageService", "generate_qr_image_service")
    def generate_qr_image(
        self,
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        image_format: str = "PNG",
        logo_path: Optional[Union[str, bool]] = None,
    ) -> BytesIO:
        """
        Generate a QR code image.

        Args:
            content: The content to encode in the QR code
            fill_color: The color of the QR code (foreground)
            back_color: The background color of the QR code
            box_size: The size of each box/module in the QR code
            border: The size of the border around the QR code
            image_format: The format of the image (PNG, JPEG, etc.)
            logo_path: Optional path to a logo image to embed in the QR code
                - If None, no logo is added
                - If True, the default logo is used
                - If a string, it's used as the path to the logo

        Returns:
            A BytesIO object containing the image data

        Raises:
            QRCodeValidationError: If there is an validation error with the QR parameters
            ValueError: If there are issues with the QR generation parameters
            IOError: If there are problems with file operations
        """
        try:
            # Check if we should use the new QR generation service
            if (self.new_qr_generation_service is not None and 
                self.new_qr_generation_breaker is not None and
                settings.USE_NEW_QR_GENERATION_SERVICE and 
                should_use_new_service(settings)):
                
                try:
                    # Create QRImageParameters for the new service
                    image_params = QRImageParameters(
                        size=box_size,
                        border=border,
                        fill_color=fill_color,
                        back_color=back_color,
                        image_format=image_format.lower(),
                        include_logo=bool(logo_path)
                    )
                    
                    # Use circuit breaker to wrap the new service call
                    @self.new_qr_generation_breaker
                    def _attempt_new_service_image_generation():
                        return self.new_qr_generation_service.create_and_format_qr_sync(
                            content=content,
                            image_params=image_params,
                            output_format=image_format.lower()
                        )
                    
                    # Attempt to use the new service with circuit breaker protection
                    image_bytes = _attempt_new_service_image_generation()
                    
                    # Log metrics for the new path
                    MetricsLogger.log_service_call(
                        service_name="NewQRGenerationService", 
                        operation="create_and_format_qr", 
                        duration=0.0  # Duration already logged by the service
                    )
                    
                    # Create a BytesIO object from the bytes
                    img_buffer = BytesIO(image_bytes)
                    img_buffer.seek(0)
                    
                    return img_buffer
                except Exception as e:
                    # Log the error and fall back to the old implementation
                    logger.error(f"Error using new QR generation service: {e}")
                    MetricsLogger.log_service_call(
                        service_name="NewQRGenerationService", 
                        operation="create_and_format_qr", 
                        duration=0.0
                    )
                    # Fall through to old implementation
            
            # Original implementation (fallback or when feature flag is off)
            # Calculate the approximate size based on box_size
            size = box_size * 25  # Rough estimate based on typical QR code size
            
            # Generate the QR code using the utility function
            img_bytes = qr_imaging_util(
                content=content,
                image_format=image_format.lower(),
                size=size,
                fill_color=fill_color,
                back_color=back_color,
                border=border,
                logo_path=logo_path
            )
            
            # Log metrics for the old path
            logger.info("Using OLD QR generation service path")
            MetricsLogger.log_service_call(
                service_name="QRImagingUtil", 
                operation="generate_qr_response", 
                duration=0.0  # Duration already logged by the utility
            )
            
            # Create a BytesIO object from the bytes
            img_buffer = BytesIO(img_bytes)
            img_buffer.seek(0)
            
            return img_buffer
        except ValueError as e:
            # Handle parameter validation errors
            logger.error(f"Parameter validation error generating QR code image: {e}")
            raise QRCodeValidationError(f"Invalid parameters for QR generation: {str(e)}")
        except IOError as e:
            # Handle file/IO errors (e.g., logo file not found)
            logger.error(f"IO error generating QR code image: {e}")
            raise QRCodeValidationError(f"Error processing QR code image: {str(e)}")

    @MetricsLogger.time_service_call("QRImageService", "generate_qr_streaming")
    def generate_qr(
        self,
        data: str,
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_level: str | None = None,
        image_format: str = "png",
        image_quality: int | None = None,
        include_logo: bool = False,
        svg_title: str | None = None,
        svg_description: str | None = None,
        physical_size: float | None = None,
        physical_unit: str | None = None,
        dpi: int | None = None,
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters.

        Args:
            data: Content to encode in the QR code
            size: Size of the QR code image in pixels (approximate)
            border: Border size around the QR code
            fill_color: Color of the QR code pattern
            back_color: Background color
            error_level: Error correction level (l, m, q, h)
            image_format: Output image format (png, jpeg, svg, webp)
            image_quality: Quality for lossy formats (1-100)
            include_logo: Whether to include the default logo
            svg_title: Optional title for SVG format (improves accessibility)
            svg_description: Optional description for SVG format (improves accessibility)
            physical_size: Physical size of the QR code in the specified unit
            physical_unit: Physical unit for size (in, cm, mm)
            dpi: DPI (dots per inch) for physical output

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        try:
            # Check if we should use the new QR generation service
            if (self.new_qr_generation_service is not None and 
                self.new_qr_generation_breaker is not None and
                settings.USE_NEW_QR_GENERATION_SERVICE and 
                should_use_new_service(settings)):
                
                # NEW PATH: Use NewQRGenerationService
                start_time = time.perf_counter()
                try:
                    logger.info("Using NEW QR generation service path")
                    logger.info(f"Requested image format: {image_format}")
                    
                    # Parse error level to ErrorCorrectionLevel enum
                    error_correction = None
                    if error_level:
                        try:
                            error_correction = ErrorCorrectionLevel(error_level)
                        except ValueError:
                            error_correction = ErrorCorrectionLevel.M
                    else:
                        error_correction = ErrorCorrectionLevel.M
                    
                    # Create QRImageParameters for the new service
                    image_params = QRImageParameters(
                        size=size,
                        border=border,
                        fill_color=fill_color,
                        back_color=back_color,
                        image_format=image_format.lower(),
                        image_quality=image_quality,
                        include_logo=include_logo,
                        error_level=error_correction,
                        svg_title=svg_title,
                        svg_description=svg_description,
                        physical_size=physical_size,
                        physical_unit=physical_unit,
                        dpi=dpi
                    )
                    
                    logger.info(f"Using format: {image_format.lower()} for both QRImageParameters and output_format")
                    logger.info(f"QRImageParameters.image_format = {image_params.image_format.value}")
                    
                    # Use circuit breaker to wrap the new service call
                    @self.new_qr_generation_breaker
                    def _attempt_new_service_image_generation():
                        return self.new_qr_generation_service.create_and_format_qr_sync(
                            content=data,
                            image_params=image_params,
                            output_format=image_format.lower()
                        )
                    
                    # Attempt to use the new service with circuit breaker protection
                    image_bytes = _attempt_new_service_image_generation()
                    
                    # Log metrics for successful new path
                    duration = time.perf_counter() - start_time
                    MetricsLogger.log_qr_generation_path("new", "generate_image", duration, True)
                    
                    # Log metrics for successful image generation
                    MetricsLogger.log_image_generated(image_format, True)
                    
                    # Create and return the streaming response
                    return StreamingResponse(
                        BytesIO(image_bytes),
                        media_type=IMAGE_FORMATS.get(image_format.lower(), "application/octet-stream")
                    )
                    
                except pybreaker.CircuitBreakerError as e:
                    # Circuit breaker is open - fallback to old implementation
                    duration = time.perf_counter() - start_time
                    logger.warning(f"Circuit breaker for NewQRGenerationService is OPEN. Falling back. Error: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "generate_qr")
                    MetricsLogger.log_qr_generation_path("new", "generate_image", duration, False)
                    # Fall through to old implementation
                    
                except Exception as e:
                    # Unexpected error in new service - log and fallback
                    duration = time.perf_counter() - start_time
                    logger.error(f"Unexpected error in NewQRGenerationService path, not due to circuit breaker: {e}. Falling back.")
                    MetricsLogger.log_qr_generation_path("new", "generate_image", duration, False)
                    # Fall through to old implementation
            
            # OLD PATH: Use legacy QR generation
            start_time = time.perf_counter()
            try:
                # If physical dimensions are specified, use them directly
                if physical_size is not None and physical_unit is not None and dpi is not None:
                    # Calculate pixel size from physical dimensions and DPI to set final output size
                    if physical_unit == "in":
                        pixel_size = int(physical_size * dpi)
                    elif physical_unit == "cm":
                        pixel_size = int(physical_size * dpi / 2.54)  # 1 inch = 2.54 cm
                    elif physical_unit == "mm":
                        pixel_size = int(physical_size * dpi / 25.4)  # 1 inch = 25.4 mm
                    else:
                        # Default to size parameter if physical unit is not recognized
                        pixel_size = size * 25  # Rough estimate based on typical QR code size
                else:
                    # Calculate the approximate size based on size parameter
                    # For segno, we use the total image size rather than box_size
                    pixel_size = size * 25  # Rough estimate based on typical QR code size
                
                # Log metrics for the old path
                logger.info("Using OLD QR generation service path")
                
                response = generate_qr_response(
                    content=data,
                    image_format=image_format,
                    size=pixel_size,
                    fill_color=fill_color,
                    back_color=back_color,
                    border=border,
                    image_quality=image_quality,
                    logo_path=True if include_logo else None,  # Pass logo_path based on include_logo
                    error_level=error_level,
                    svg_title=svg_title,
                    svg_description=svg_description,
                    physical_size=physical_size,
                    physical_unit=physical_unit,
                    dpi=dpi
                )
                
                # Log metrics for successful old path
                duration = time.perf_counter() - start_time
                MetricsLogger.log_qr_generation_path("old", "generate_image", duration, True)
                
                # Log metrics for successful image generation
                MetricsLogger.log_image_generated(image_format, True)
                
                return response
            except Exception as e:
                # Log metrics for failed old path
                duration = time.perf_counter() - start_time
                MetricsLogger.log_qr_generation_path("old", "generate_image", duration, False)
                # Re-raise the exception
                raise
        except Exception as e:
            # Log metrics for failed image generation
            MetricsLogger.log_image_generated(image_format, False)
            raise 