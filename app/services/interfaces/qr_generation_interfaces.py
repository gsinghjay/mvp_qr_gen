"""
QR Generation and Image Formatting Interface Definitions.

This module defines abstract base classes for QR code generation and image formatting
to establish clear contracts for future implementations in the Observatory-First architecture.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.common import ErrorCorrectionLevel
from app.schemas.qr.parameters import QRImageParameters


class QRCodeGenerator(ABC):
    """
    Abstract base class for QR code generation.
    
    This interface defines the contract for generating QR code data structures
    that can be later formatted into various image formats.
    """

    @abstractmethod
    async def generate_qr_data(self, content: str, error_correction: ErrorCorrectionLevel) -> Any:
        """
        Generate QR code data for the given content and error correction level.
        
        Args:
            content: The content to encode in the QR code
            error_correction: The error correction level to use
            
        Returns:
            QR code data structure (implementation-specific, e.g., Segno QRCode object)
            
        Raises:
            QRCodeValidationError: If content is invalid for QR encoding
        """
        pass


class QRImageFormatter(ABC):
    """
    Abstract base class for QR code image formatting.
    
    This interface defines the contract for converting QR code data into
    various image formats with customization options.
    """

    @abstractmethod
    async def format_qr_image(
        self, 
        qr_data: Any, 
        image_params: QRImageParameters, 
        output_format: str
    ) -> bytes:
        """
        Format QR code data into an image with the specified parameters.
        
        Args:
            qr_data: QR code data from QRCodeGenerator (implementation-specific type)
            image_params: Parameters for image formatting (size, colors, etc.)
            output_format: Target image format (png, svg, jpeg, webp)
            
        Returns:
            Formatted image as bytes
            
        Raises:
            QRCodeValidationError: If image parameters are invalid
            ValueError: If output format is not supported
        """
        pass
    
    @abstractmethod
    async def get_png_data_uri(self, qr_data: Any, image_params: QRImageParameters) -> str:
        """
        Generate a PNG data URI for direct HTML embedding.
        
        Args:
            qr_data: QR code data from QRCodeGenerator (implementation-specific type)
            image_params: Parameters for image formatting (size, colors, etc.)
            
        Returns:
            PNG data URI string (e.g., "data:image/png;base64,...")
            
        Raises:
            QRCodeValidationError: If image parameters are invalid
        """
        pass
    
    @abstractmethod
    async def get_svg_data_uri(self, qr_data: Any, image_params: QRImageParameters) -> str:
        """
        Generate an SVG data URI for direct HTML embedding.
        
        Args:
            qr_data: QR code data from QRCodeGenerator (implementation-specific type)
            image_params: Parameters for image formatting (size, colors, etc.)
            
        Returns:
            SVG data URI string (e.g., "data:image/svg+xml;charset=utf-8,...")
            
        Raises:
            QRCodeValidationError: If image parameters are invalid
        """
        pass
    
    @abstractmethod
    async def get_svg_inline(self, qr_data: Any, image_params: QRImageParameters) -> str:
        """
        Generate inline SVG markup for responsive HTML integration.
        
        Args:
            qr_data: QR code data from QRCodeGenerator (implementation-specific type)
            image_params: Parameters for image formatting (size, colors, etc.)
            
        Returns:
            Inline SVG markup string with accessibility attributes
            
        Raises:
            QRCodeValidationError: If image parameters are invalid
        """
        pass 