"""
Segno QR Code Adapter Implementations.

This module provides concrete implementations of QR generation and image formatting
interfaces using the Segno library with performance optimizations.
"""

import logging
import math
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
                svg_params = {
                    "kind": "svg",
                    "xmldecl": False,      # Remove XML declaration
                    "svgns": False,        # Remove SVG namespace
                    "svgclass": None,      # Remove CSS classes
                    "lineclass": None,     # Remove line classes  
                    "nl": False,           # Remove newlines
                    "border": image_params.border,
                    "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color),
                    "light": self._handle_transparency(
                        self._get_effective_color(image_params.back_color, image_params.data_light_color), 
                        "svg"
                    )
                }
                
                # Task 0.2.4: Native SVG Unit Support
                if (image_params.physical_unit and 
                    image_params.physical_size and 
                    image_params.dpi):
                    svg_params["unit"] = image_params.physical_unit
                    svg_params["scale"] = image_params.physical_size
                    # Note: omitsize=False (default) when using unit for width/height attributes
                else:
                    svg_params["scale"] = image_params.size
                    svg_params["omitsize"] = True  # Remove size attributes for relative sizing
                
                # Add SVG accessibility attributes if provided
                if image_params.svg_title:
                    svg_params["title"] = image_params.svg_title
                if image_params.svg_description:
                    svg_params["desc"] = image_params.svg_description
                
                qr_data.save(output, **svg_params)
                
            # Handle raster formats (PNG, JPEG, WEBP) 
            elif output_format.lower() in ["png", "jpeg", "webp"]:
                # Task 0.2.5: Precise Scale Calculation for Raster Images
                scale = self._calculate_precise_scale(qr_data, image_params)
                
                # Prepare color parameters with advanced color support
                dark_color = self._get_effective_color(image_params.fill_color, image_params.data_dark_color)
                light_color = self._handle_transparency(
                    self._get_effective_color(image_params.back_color, image_params.data_light_color), 
                    output_format.lower()
                )
                
                # Check if logo embedding is requested
                if hasattr(image_params, 'include_logo') and image_params.include_logo:
                    # DIRECT PILLOW INTEGRATION FOR LOGO (PRIORITY 1, Issue 3)
                    pil_image = qr_data.to_pil(
                        scale=scale,
                        border=image_params.border,
                        dark=dark_color,
                        light=light_color
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
                        scale=scale,
                        border=image_params.border,
                        dark=dark_color,
                        light=light_color
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

    async def get_png_data_uri(self, qr_data: segno.QRCode, image_params: QRImageParameters) -> str:
        """
        Generate QR code as PNG data URI for direct embedding in HTML.
        
        Args:
            qr_data: Segno QRCode object
            image_params: Parameters for image formatting
            
        Returns:
            PNG data URI string
        """
        try:
            # Use Segno's built-in data URI generation with precise scale
            scale = self._calculate_precise_scale(qr_data, image_params)
            dark_color = self._get_effective_color(image_params.fill_color, image_params.data_dark_color)
            light_color = self._get_effective_color(image_params.back_color, image_params.data_light_color)
            
            return qr_data.png_data_uri(
                scale=scale,
                border=image_params.border,
                dark=dark_color,
                light=light_color
            )
        except Exception as e:
            logger.error(f"Failed to generate PNG data URI: {e}")
            raise ValueError(f"PNG data URI generation failed: {e}")

    async def get_svg_data_uri(self, qr_data: segno.QRCode, image_params: QRImageParameters) -> str:
        """
        Generate QR code as SVG data URI for direct embedding in HTML.
        
        Args:
            qr_data: Segno QRCode object
            image_params: Parameters for image formatting
            
        Returns:
            SVG data URI string
        """
        try:
            # Prepare SVG parameters similar to format_qr_image
            svg_params = {
                "xmldecl": False,
                "svgns": False,
                "svgclass": None,
                "lineclass": None,
                "omitsize": True,
                "nl": False,
                "border": image_params.border,
                "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color),
                "light": self._get_effective_color(image_params.back_color, image_params.data_light_color)
            }
            
            # Handle physical dimensions for SVG
            if (image_params.physical_unit and 
                image_params.physical_size and 
                image_params.dpi):
                svg_params["unit"] = image_params.physical_unit
                svg_params["scale"] = image_params.physical_size
                svg_params["omitsize"] = False  # Keep size attributes for physical dimensions
            else:
                svg_params["scale"] = image_params.size
            
            # Add accessibility attributes if provided
            if image_params.svg_title:
                svg_params["title"] = image_params.svg_title
            if image_params.svg_description:
                svg_params["desc"] = image_params.svg_description
            
            return qr_data.svg_data_uri(**svg_params)
        except Exception as e:
            logger.error(f"Failed to generate SVG data URI: {e}")
            raise ValueError(f"SVG data URI generation failed: {e}")

    async def get_svg_inline(self, qr_data: segno.QRCode, image_params: QRImageParameters) -> str:
        """
        Generate QR code as inline SVG string for direct embedding in HTML.
        
        Args:
            qr_data: Segno QRCode object
            image_params: Parameters for image formatting
            
        Returns:
            Inline SVG string
        """
        try:
            # Prepare parameters for minimal inline SVG
            svg_params = {
                "xmldecl": False,      # No XML declaration for inline
                "svgns": False,        # No SVG namespace for inline
                "omitsize": True,      # No size attributes for responsive inline SVG
                "border": image_params.border,
                "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color),
                "light": self._get_effective_color(image_params.back_color, image_params.data_light_color)
            }
            
            # Handle physical dimensions
            if (image_params.physical_unit and 
                image_params.physical_size and 
                image_params.dpi):
                svg_params["unit"] = image_params.physical_unit
                svg_params["scale"] = image_params.physical_size
                svg_params["omitsize"] = False  # Keep size for physical dimensions
            else:
                svg_params["scale"] = image_params.size
            
            # Add accessibility attributes if provided
            if image_params.svg_title:
                svg_params["title"] = image_params.svg_title
            if image_params.svg_description:
                svg_params["desc"] = image_params.svg_description
            
            # Generate inline SVG using BytesIO
            output = BytesIO()
            qr_data.save(output, kind="svg", **svg_params)
            output.seek(0)
            return output.getvalue().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate inline SVG: {e}")
            raise ValueError(f"Inline SVG generation failed: {e}")

    def _get_effective_color(self, base_color: str | None, data_color: str | None) -> str | None:
        """
        Get the effective color, preferring data_color over base_color.
        
        Args:
            base_color: Base color (fill_color or back_color)
            data_color: Data-specific color (data_dark_color or data_light_color)
            
        Returns:
            Effective color to use, or None if both are None
        """
        return data_color if data_color is not None else base_color

    def _calculate_precise_scale(self, qr_data: segno.QRCode, image_params: QRImageParameters) -> float:
        """
        Calculate precise scale for raster images based on target pixel dimensions.
        
        Args:
            qr_data: Segno QRCode object
            image_params: Parameters containing target size and border
            
        Returns:
            Scale value representing pixels per module
        """
        # Task 0.2.5: Precise Scale Calculation for Raster Images
        
        # Calculate target pixel size
        if (image_params.physical_size and 
            image_params.physical_unit and 
            image_params.dpi):
            # Convert physical dimensions to pixels
            if image_params.physical_unit == "in":
                target_pixels = image_params.physical_size * image_params.dpi
            elif image_params.physical_unit == "cm":
                target_pixels = (image_params.physical_size / 2.54) * image_params.dpi
            elif image_params.physical_unit == "mm":
                target_pixels = (image_params.physical_size / 25.4) * image_params.dpi
            else:
                target_pixels = image_params.size * 25  # Fallback to relative sizing
        else:
            # Use relative sizing (size * 25 for pixel dimension)
            target_pixels = image_params.size * 25
        
        # Get QR code module count without border
        module_count_no_border = qr_data.symbol_size(border=0)[0]
        
        # Calculate total module count including border
        # Segno adds border modules on each side
        module_count_with_border = module_count_no_border + (2 * image_params.border)
        
        # Calculate scale as pixels per module
        scale = target_pixels / module_count_with_border
        
        # Ensure scale is at least 1 pixel per module
        scale = max(1.0, scale)
        
        logger.debug(f"Calculated scale: {scale} pixels/module for {target_pixels}px target, {module_count_with_border} modules")
        return scale

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