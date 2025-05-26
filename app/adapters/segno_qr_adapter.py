"""
Segno QR Code Adapter Implementations.

This module provides concrete implementations of QR generation and image formatting
interfaces using the Segno library with performance optimizations.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

import segno
from PIL import Image

from app.core.config import settings
from app.schemas.common import ErrorCorrectionLevel
from app.schemas.qr.parameters import QRImageParameters
from app.services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter

logger = logging.getLogger(__name__)


class SegnoQRCodeGenerator(QRCodeGenerator):
    """
    Segno-based implementation of QR code generation.
    
    Uses the Segno library with optimizations for enhanced error correction.
    """

    async def generate_qr_data(self, content: str, error_correction: ErrorCorrectionLevel) -> segno.QRCode:
        """
        Generate QR code data using Segno with optimizations.
        
        Args:
            content: The content to encode in the QR code
            error_correction: The error correction level to use
            
        Returns:
            Segno QRCode object
            
        Raises:
            QRCodeValidationError: If content is invalid for QR encoding
        """
        try:
            # SEGNO OPTIMIZATION: Use boost_error=True (PRIORITY 1, Issue 4)
            # This enhances error correction when possible
            qr = segno.make(
                content, 
                error=error_correction.value, 
                boost_error=True
            )
            
            logger.debug(f"Generated QR code for content length: {len(content)}")
            return qr
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise ValueError(f"QR code generation failed: {e}")


class PillowQRImageFormatter(QRImageFormatter):
    """
    Pillow-based implementation of QR image formatting.
    
    Uses Segno's built-in formatters with Pillow integration for advanced features
    like logo embedding and optimized output formats.
    """

    async def format_qr_image(
        self, 
        qr_data: segno.QRCode, 
        image_params: QRImageParameters, 
        output_format: str
    ) -> bytes:
        """
        Format QR code data into an image with Segno optimizations.
        
        Args:
            qr_data: Segno QRCode object from SegnoQRCodeGenerator
            image_params: Parameters for image formatting
            output_format: Target image format (png, svg, jpeg, webp)
            
        Returns:
            Formatted image as bytes
            
        Raises:
            QRCodeValidationError: If image parameters are invalid
            ValueError: If output format is not supported
        """
        try:
            output = BytesIO()
            
            # Handle SVG format with optimizations
            if output_format.lower() == "svg":
                # SEGNO SVG OPTIMIZATIONS (PRIORITY 1, Issue 2)
                qr_data.save(
                    output, 
                    kind="svg",
                    xmldecl=False,      # Remove XML declaration
                    svgns=False,        # Remove SVG namespace
                    svgclass=None,      # Remove CSS classes
                    lineclass=None,     # Remove line classes  
                    omitsize=True,      # Remove size attributes
                    nl=False,           # Remove newlines
                    scale=image_params.size,
                    border=image_params.border,
                    dark=image_params.fill_color,
                    light=self._handle_transparency(image_params.back_color, "svg")
                )
                
            # Handle raster formats (PNG, JPEG, WEBP)
            elif output_format.lower() in ["png", "jpeg", "webp"]:
                # Check if logo embedding is requested
                if hasattr(image_params, 'include_logo') and image_params.include_logo:
                    # DIRECT PILLOW INTEGRATION FOR LOGO (PRIORITY 1, Issue 3)
                    pil_image = qr_data.to_pil(
                        scale=image_params.size,
                        border=image_params.border,
                        dark=image_params.fill_color,
                        light=self._handle_transparency(image_params.back_color, output_format.lower())
                    )
                    
                    # Add logo if available
                    pil_image = self._add_logo_to_image(pil_image)
                    
                    # Save with format-specific options
                    if output_format.lower() == "jpeg":
                        # JPEG doesn't support transparency
                        if pil_image.mode in ("RGBA", "LA", "P"):
                            background = Image.new("RGB", pil_image.size, "white")
                            if pil_image.mode == "P":
                                pil_image = pil_image.convert("RGBA")
                            background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == "RGBA" else None)
                            pil_image = background
                        pil_image.save(output, format="JPEG", quality=getattr(image_params, 'image_quality', 90))
                    else:
                        pil_image.save(output, format=output_format.upper())
                else:
                    # Direct Segno save for raster without logo
                    qr_data.save(
                        output,
                        kind=output_format.lower(),
                        scale=image_params.size,
                        border=image_params.border,
                        dark=image_params.fill_color,
                        light=self._handle_transparency(image_params.back_color, output_format.lower())
                    )
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
                
            output.seek(0)
            image_bytes = output.getvalue()
            
            logger.debug(f"Generated {output_format} image: {len(image_bytes)} bytes")
            return image_bytes
            
        except Exception as e:
            logger.error(f"Failed to format QR image: {e}")
            raise ValueError(f"QR image formatting failed: {e}")

    def _handle_transparency(self, color: str, format_type: str) -> str | None:
        """
        Handle transparent background support based on format.
        
        Args:
            color: The background color
            format_type: The image format
            
        Returns:
            Color value or None for transparency
        """
        # TRANSPARENT BACKGROUND SUPPORT (PRIORITY 2, Item 7)
        if color and color.lower() in ["transparent", "none"]:
            if format_type in ["png", "svg"]:
                return None  # Segno uses None for transparent background
            else:
                return "#FFFFFF"  # Fallback for formats that don't support transparency
        return color

    def _add_logo_to_image(self, qr_image: Image.Image) -> Image.Image:
        """
        Add logo to QR code image using Pillow.
        
        Args:
            qr_image: The base QR code image
            
        Returns:
            QR code image with logo embedded
        """
        try:
            # Check if default logo exists
            logo_path = Path(settings.DEFAULT_LOGO_PATH) if hasattr(settings, 'DEFAULT_LOGO_PATH') else None
            
            if not logo_path or not logo_path.exists():
                logger.warning("Logo file not found, returning QR image without logo")
                return qr_image
                
            # Load and resize logo
            with Image.open(logo_path) as logo:
                # Convert logo to RGBA for proper blending
                logo = logo.convert("RGBA")
                
                # Resize logo to 20-25% of QR image size
                qr_width, qr_height = qr_image.size
                logo_size = min(qr_width, qr_height) // 4  # 25% of the smaller dimension
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Calculate center position
                logo_x = (qr_width - logo_size) // 2
                logo_y = (qr_height - logo_size) // 2
                
                # Paste logo onto QR code
                if qr_image.mode != "RGBA":
                    qr_image = qr_image.convert("RGBA")
                    
                qr_image.paste(logo, (logo_x, logo_y), logo)
                
            logger.debug("Successfully added logo to QR image")
            return qr_image
            
        except Exception as e:
            logger.error(f"Failed to add logo to QR image: {e}")
            return qr_image  # Return original image if logo addition fails 