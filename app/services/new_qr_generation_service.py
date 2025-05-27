"""
New QR Generation Service Implementation.

This module provides the new QR generation service implementation using
interfaces and adapters in the Observatory-First refactoring architecture.
"""

import logging
from typing import Any, Dict

from app.core.metrics_logger import MetricsLogger
from app.services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter

logger = logging.getLogger(__name__)


class NewQRGenerationService:
    """
    New QR generation service using interface-based architecture.
    
    This service orchestrates QR code generation and formatting using
    injected generator and formatter implementations.
    """

    def __init__(self, generator: QRCodeGenerator, formatter: QRImageFormatter):
        """
        Initialize the service with generator and formatter dependencies.
        
        Args:
            generator: QR code generation implementation
            formatter: QR image formatting implementation
        """
        self.generator = generator
        self.formatter = formatter
        logger.info("NewQRGenerationService initialized")

    @MetricsLogger.time_service_call("NewQRGenerationService", "create_and_format_qr")
    async def create_and_format_qr(
        self, 
        content: str, 
        image_params: Any, 
        output_format: str = "png",
        error_correction: Any = None
    ) -> bytes:
        """
        Create and format a QR code in one operation.
        
        Args:
            content: Content to encode in the QR code
            image_params: Image formatting parameters
            output_format: Target image format
            error_correction: Error correction level
            
        Returns:
            Formatted QR code image as bytes
            
        Raises:
            QRCodeValidationError: If parameters are invalid
            ValueError: If operation fails
        """
        try:
            # Validate format early at service level
            self._validate_service_inputs(content, output_format)
            
            logger.debug(f"Creating QR code for content length: {len(content)}")
            
            # Use default error correction if not provided
            if error_correction is None:
                from app.schemas.common import ErrorCorrectionLevel
                error_correction = ErrorCorrectionLevel.M
            
            # AUTO-UPGRADE ERROR CORRECTION FOR LOGOS
            # When logos are included, high error correction is required for scannability
            if hasattr(image_params, 'include_logo') and image_params.include_logo:
                from app.schemas.common import ErrorCorrectionLevel
                original_level = error_correction
                error_correction = ErrorCorrectionLevel.H
                logger.info(f"Auto-upgraded error correction from {original_level.value} to {error_correction.value} for logo inclusion")
            
            # Generate QR data
            qr_data = await self.generator.generate_qr_data(content, error_correction)
            
            # Format to image
            image_bytes = await self.formatter.format_qr_image(qr_data, image_params, output_format)
            
            logger.info(f"Successfully created {output_format} QR code: {len(image_bytes)} bytes")
            return image_bytes
            
        except Exception as e:
            logger.error(f"Failed to create and format QR code: {e}")
            raise

    @MetricsLogger.time_service_call("NewQRGenerationService", "create_and_format_qr_sync")
    def create_and_format_qr_sync(
        self, 
        content: str, 
        image_params: Any, 
        output_format: str = "png",
        error_correction: Any = None
    ) -> bytes:
        """
        Create and format a QR code in one operation (synchronous version).
        
        This is a simple wrapper around the async version for circuit breaker compatibility.
        
        Args:
            content: Content to encode in the QR code
            image_params: Image formatting parameters
            output_format: Target image format
            error_correction: Error correction level
            
        Returns:
            Formatted QR code image as bytes
            
        Raises:
            QRCodeValidationError: If parameters are invalid
            ValueError: If operation fails
        """
        import asyncio
        
        # Fixed version that works whether there's an existing event loop or not
        try:
            # Get the current event loop or create one if it doesn't exist
            loop = asyncio.get_event_loop()
            
            # Check if the loop is running
            if loop.is_running():
                # Create a new loop for this execution if the current one is running
                # This avoids the "asyncio.run() cannot be called from a running event loop" error
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.create_and_format_qr(
                        content=content,
                        image_params=image_params,
                        output_format=output_format,
                        error_correction=error_correction
                    ))
                finally:
                    new_loop.close()
                    asyncio.set_event_loop(loop)  # Restore the original loop
            else:
                # If we have a loop but it's not running, use it
                return loop.run_until_complete(self.create_and_format_qr(
                    content=content,
                    image_params=image_params,
                    output_format=output_format,
                    error_correction=error_correction
                ))
        except RuntimeError as e:
            # If we can't get a loop or there's another runtime error, log it and try one more approach
            logger.warning(f"Event loop handling error: {e}, trying alternative approach")
            # Last resort approach: create a new thread with its own event loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self.create_and_format_qr(
                        content=content,
                        image_params=image_params,
                        output_format=output_format,
                        error_correction=error_correction
                    ))
                )
                return future.result()

    def _validate_service_inputs(self, content: str, output_format: str) -> None:
        """
        Validate service-level inputs before processing.
        
        Args:
            content: QR code content to validate
            output_format: Output format to validate
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Content validation
        if not content or not content.strip():
            raise ValueError("QR code content cannot be empty")
            
        if len(content) > 2048:  # Reasonable limit for QR codes
            raise ValueError(f"Content too long: {len(content)} characters (max: 2048)")
        
        # Format validation (basic check - detailed validation in formatter)
        if not output_format or not output_format.strip():
            raise ValueError("Output format must be specified")
            
        # Import here to avoid circular imports
        from app.schemas.common import ImageFormat
        try:
            # This will raise ValueError if format is not in enum
            ImageFormat(output_format.lower())
        except ValueError:
            valid_formats = [f.value for f in ImageFormat]
            raise ValueError(
                f"Invalid output format: '{output_format}'. "
                f"Valid formats: {', '.join(valid_formats)}"
            )

    @MetricsLogger.time_service_call("NewQRGenerationService", "validate_generation_params")
    async def validate_generation_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate QR generation parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            True if parameters are valid
            
        Raises:
            QRCodeValidationError: If parameters are invalid
        """
        try:
            # Placeholder validation logic
            logger.debug("Validating QR generation parameters")
            
            # Basic validation
            if not params.get("content"):
                raise ValueError("Content is required")
                
            if len(params.get("content", "")) > 2048:
                raise ValueError("Content too long")
                
            logger.debug("QR generation parameters validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            raise