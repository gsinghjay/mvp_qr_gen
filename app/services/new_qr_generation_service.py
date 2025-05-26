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
            logger.debug(f"Creating QR code for content length: {len(content)}")
            
            # Use default error correction if not provided
            if error_correction is None:
                from app.schemas.common import ErrorCorrectionLevel
                error_correction = ErrorCorrectionLevel.M
            
            # Generate QR data
            qr_data = await self.generator.generate_qr_data(content, error_correction)
            
            # Format to image
            image_bytes = await self.formatter.format_qr_image(qr_data, image_params, output_format)
            
            logger.info(f"Successfully created {output_format} QR code: {len(image_bytes)} bytes")
            return image_bytes
            
        except Exception as e:
            logger.error(f"Failed to create and format QR code: {e}")
            raise

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