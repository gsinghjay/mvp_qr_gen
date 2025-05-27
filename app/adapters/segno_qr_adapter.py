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

    # Define supported formats at class level for consistency
    SUPPORTED_FORMATS = {
        "png": {"supports_transparency": True, "is_raster": True},
        "jpeg": {"supports_transparency": False, "is_raster": True},  
        "jpg": {"supports_transparency": False, "is_raster": True},
        "svg": {"supports_transparency": True, "is_raster": False},
        "webp": {"supports_transparency": True, "is_raster": True},   # Will be deprecated in the future
        "eps": {"supports_transparency": True, "is_raster": False},   # Encapsulated PostScript (needs `format_qr_image` implementation)
        "txt": {"supports_transparency": False, "is_raster": False},  # Text/ASCII art (needs `format_qr_image` implementation)
        "gif": {"supports_transparency": True, "is_raster": True}     # GIF format (needs `format_qr_image` implementation)
    }

    def _validate_output_format(self, output_format: str) -> str:
        """
        Validate and normalize output format.
        
        Args:
            output_format: The requested output format
            
        Returns:
            Normalized format string (lowercase)
            
        Raises:
            ValueError: If format is not supported
        """
        if not output_format:
            raise ValueError("Output format cannot be empty")
            
        normalized_format = output_format.lower().strip()
        
        if normalized_format not in self.SUPPORTED_FORMATS:
            supported_list = ", ".join(sorted(self.SUPPORTED_FORMATS.keys()))
            raise ValueError(
                f"Unsupported output format: '{output_format}'. "
                f"Supported formats: {supported_list}"
            )
        
        return normalized_format

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
            # Validate and normalize format first
            validated_format = self._validate_output_format(output_format)
            format_info = self.SUPPORTED_FORMATS[validated_format]
            
            output = BytesIO()
            
            # Handle SVG format with optimizations
            if validated_format == "svg":
                # SEGNO SVG OPTIMIZATIONS (PRIORITY 1, Issue 2)
                svg_params = {
                    "kind": "svg",
                    "xmldecl": False,      # Remove XML declaration
                    "svgns": False,        # Remove SVG namespace
                    "svgclass": None,      # Remove CSS classes
                    "lineclass": None,     # Remove line classes  
                    "nl": False,           # Remove newlines
                    "border": image_params.border,
                    "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color, is_dark=True),
                    "light": self._handle_transparency(
                        self._get_effective_color(image_params.back_color, image_params.data_light_color, is_dark=False), 
                        "svg"
                    )
                }
                
                # Task 0.2.4: Native SVG Unit Support
                if (image_params.physical_unit and 
                    image_params.physical_size and 
                    image_params.dpi):
                    svg_params["unit"] = image_params.physical_unit
                    # Calculate scale per module for SVG (total size / module count)
                    module_count_with_border = qr_data.symbol_size(border=image_params.border)[0]
                    svg_params["scale"] = image_params.physical_size / module_count_with_border
                    # Note: omitsize=False (default) when using unit for width/height attributes
                else:
                    svg_params["scale"] = image_params.size
                    # Keep size attributes for better browser compatibility (omitsize=False is default)
                
                # Add SVG accessibility attributes if provided
                if image_params.svg_title:
                    svg_params["title"] = image_params.svg_title
                if image_params.svg_description:
                    svg_params["desc"] = image_params.svg_description
                
                qr_data.save(output, **svg_params)
                
            # Handle raster formats (PNG, JPEG, WEBP) 
            elif validated_format in ["png", "jpeg", "webp"]:
                # Task 0.2.5: Precise Scale Calculation for Raster Images
                scale = self._calculate_precise_scale(qr_data, image_params)
                
                # Prepare color parameters with advanced color support
                dark_color = self._get_effective_color(image_params.fill_color, image_params.data_dark_color, is_dark=True)
                light_color = self._handle_transparency(
                    self._get_effective_color(image_params.back_color, image_params.data_light_color, is_dark=False), 
                    validated_format
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
                    if validated_format == "jpeg":
                        # JPEG doesn't support transparency
                        if pil_image.mode in ("RGBA", "LA", "P"):
                            background = Image.new("RGB", pil_image.size, "white")
                            if pil_image.mode == "P":
                                pil_image = pil_image.convert("RGBA")
                            background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == "RGBA" else None)
                            pil_image = background
                        # Handle JPEG quality following Segno documentation pattern
                        if image_params.image_quality is not None:
                            pil_image.save(output, format="JPEG", quality=image_params.image_quality)
                        else:
                            pil_image.save(output, format="JPEG")  # Use Pillow's default quality
                    else:
                        pil_image.save(output, format=validated_format.upper())
                else:
                    # Direct Segno save for raster without logo
                    qr_data.save(
                        output,
                        kind=validated_format,
                        scale=scale,
                        border=image_params.border,
                        dark=dark_color,
                        light=light_color
                    )
            else:
                raise ValueError(f"Unsupported output format: {validated_format}")
                
            output.seek(0)
            image_bytes = output.getvalue()
            
            logger.debug(f"Generated {validated_format} image: {len(image_bytes)} bytes")
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
            dark_color = self._get_effective_color(image_params.fill_color, image_params.data_dark_color, is_dark=True)
            light_color = self._get_effective_color(image_params.back_color, image_params.data_light_color, is_dark=False)
            
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
                "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color, is_dark=True),
                "light": self._handle_transparency(
                    self._get_effective_color(image_params.back_color, image_params.data_light_color, is_dark=False), 
                    "svg"
                )
            }
            
            # Handle physical dimensions for SVG
            if (image_params.physical_unit and 
                image_params.physical_size and 
                image_params.dpi):
                svg_params["unit"] = image_params.physical_unit
                # Calculate scale per module for SVG (total size / module count)
                module_count_with_border = qr_data.symbol_size(border=image_params.border)[0]
                svg_params["scale"] = image_params.physical_size / module_count_with_border
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
            # Note: svg_inline() sets xmldecl=False, svgns=False, nl=False by default
            svg_params = {
                "omitsize": True,      # No size attributes for responsive inline SVG
                "border": image_params.border,
                "dark": self._get_effective_color(image_params.fill_color, image_params.data_dark_color, is_dark=True),
                "light": self._handle_transparency(
                    self._get_effective_color(image_params.back_color, image_params.data_light_color, is_dark=False), 
                    "svg"
                )
            }
            
            # Handle physical dimensions
            if (image_params.physical_unit and 
                image_params.physical_size and 
                image_params.dpi):
                svg_params["unit"] = image_params.physical_unit
                # Calculate scale per module for SVG (total size / module count)
                module_count_with_border = qr_data.symbol_size(border=image_params.border)[0]
                svg_params["scale"] = image_params.physical_size / module_count_with_border
                svg_params["omitsize"] = False  # Keep size for physical dimensions
            else:
                svg_params["scale"] = image_params.size
            
            # Add accessibility attributes if provided
            if image_params.svg_title:
                svg_params["title"] = image_params.svg_title
            if image_params.svg_description:
                svg_params["desc"] = image_params.svg_description
            
            # Use Segno's built-in svg_inline method
            return qr_data.svg_inline(**svg_params)
        except Exception as e:
            logger.error(f"Failed to generate inline SVG: {e}")
            raise ValueError(f"Inline SVG generation failed: {e}")

    def _get_effective_color(self, base_color: str | None, data_color: str | None, is_dark: bool = False) -> str | None:
        """
        Get the effective color, preferring data_color over base_color with fallbacks.
        
        Args:
            base_color: Base color (fill_color or back_color)
            data_color: Data-specific color (data_dark_color or data_light_color)
            is_dark: Whether this is for dark modules (True) or light/background (False)
            
        Returns:
            Effective color to use, with fallback to Segno defaults if both are None
        """
        effective_color = data_color if data_color is not None else base_color
        
        # Apply Segno default fallbacks when both are None
        if effective_color is None:
            if is_dark:
                return "#000000"  # Default black for dark modules
            else:
                return "#FFFFFF"  # Default white for light/background
        
        return effective_color

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

    def _add_logo_to_image(self, qr_image: Image.Image, logo_path_override: str | None = None) -> Image.Image:
        """
        Add logo to QR code image using Pillow.
        
        Args:
            qr_image: The base QR code image
            logo_path_override: Optional path to override the default logo
            
        Returns:
            QR code image with logo embedded
        """
        try:
            # Use override path if provided, otherwise use default
            if logo_path_override:
                logo_path = Path(logo_path_override)
            else:
                logo_path = Path(settings.DEFAULT_LOGO_PATH) if hasattr(settings, 'DEFAULT_LOGO_PATH') else None
            
            if not logo_path or not logo_path.exists():
                logger.warning("Logo file not found, returning QR image without logo")
                return qr_image
                
            # Calculate logo size as 25% of the QR image (smaller than Segno's recommendation for better aesthetics)
            qr_width, qr_height = qr_image.size
            logo_size = min(qr_width, qr_height) // 4  # 25% of QR size (smaller than Segno's recommendation of 1/3)
            
            # Load regular image formats
            logo = Image.open(logo_path)
                
            # Convert logo to RGBA for proper blending
            logo = logo.convert("RGBA")
            
            # Resize logo maintaining aspect ratio
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate center position
            logo_x = (qr_width - logo.size[0]) // 2
            logo_y = (qr_height - logo.size[1]) // 2
            
            # Ensure QR image is in RGBA mode for proper blending
            if qr_image.mode != "RGBA":
                qr_image = qr_image.convert("RGBA")
            
            # Sample the background color from the QR code (center point should be light/background)
            # Use the corner pixel which is always the background color
            bg_color = qr_image.getpixel((0, 0))
            
            # Create a background with the same color as the QR code background
            background_size = max(logo.size) + 3  # Add padding
            background = Image.new("RGBA", (background_size, background_size), bg_color)
            
            # Center the logo on the background
            bg_x = (background_size - logo.size[0]) // 2
            bg_y = (background_size - logo.size[1]) // 2
            background.paste(logo, (bg_x, bg_y), logo)
            
            # Paste the background with logo onto QR code
            final_x = (qr_width - background_size) // 2
            final_y = (qr_height - background_size) // 2
            qr_image.paste(background, (final_x, final_y), background)
                
            logger.debug(f"Successfully added logo to QR image (logo size: {logo.size}, background: {background_size}px)")
            return qr_image
            
        except Exception as e:
            logger.error(f"Failed to add logo to QR image: {e}")
            return qr_image  # Return original image if logo addition fails 