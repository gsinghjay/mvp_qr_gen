"""
Utility functions for QR code image generation.
"""

import io
import os
from typing import Optional, Union, Literal
import segno
from PIL import Image
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

# Default logo path
DEFAULT_LOGO_PATH = "app/static/assets/images/logo_hccc_qr.jpg"

def generate_qr_image(
    content: str,
    image_format: Literal["png", "svg", "jpeg", "webp"] = "png",
    size: int = 200,
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    border: int = 4,
    logo_path: Optional[Union[str, bool]] = None,
    error_level: str = "m",
    svg_title: Optional[str] = None,
    svg_description: Optional[str] = None,
) -> bytes:
    """
    Generate a QR code image with the specified parameters using a hybrid approach:
    1. Generate high-resolution QR code with segno
    2. Resize precisely to requested dimensions with Pillow
    3. Add logo using Pillow if specified
    
    Args:
        content: The content to encode in the QR code.
        image_format: The output image format (png, svg, jpeg, webp)
        size: The size of the QR code in pixels (final output size)
        fill_color: The color of the QR code modules (mapped to segno's dark parameter)
        back_color: The background color of the QR code (mapped to segno's light parameter)
        border: The size of the border around the QR code (mapped directly to segno's border parameter)
        logo_path: Optional path to a logo image to embed in the QR code
            - If None, no logo is added
            - If True, the default logo is used
            - If a string, it's used as the path to the logo
        error_level: Error correction level (l, m, q, h)
            - l: Low (7% of data can be restored)
            - m: Medium (15% of data can be restored)
            - q: Quartile (25% of data can be restored)
            - h: High (30% of data can be restored)
        svg_title: Optional title for SVG format (improves accessibility)
        svg_description: Optional description for SVG format (improves accessibility)
        
    Returns:
        The QR code image as bytes.
    """
    try:
        # Use the specified error correction level if provided, 
        # or determine based on logo presence
        if error_level and error_level in ['l', 'm', 'q', 'h']:
            # Use specific error level if provided
            error = error_level
        else:
            # Default to high error correction when including a logo
            error = "h" if logo_path else "m"
        
        # Resolve logo path
        actual_logo_path = None
        if logo_path:
            if isinstance(logo_path, bool):
                actual_logo_path = DEFAULT_LOGO_PATH
            else:
                actual_logo_path = logo_path
                
            # Verify logo exists
            if not os.path.exists(actual_logo_path):
                raise ValueError(f"Logo file not found: {actual_logo_path}")
        
        # Create QR code with specified error correction level
        qr = segno.make(content, error=error)
        
        # For SVG output, handle differently since it's vector-based
        if image_format.lower() == "svg":
            output = io.BytesIO()
            # Add SVG accessibility options if provided
            svg_options = {
                "scale": 10,
                "dark": fill_color,
                "light": back_color,
                "border": border
            }
            
            # Add SVG title and description if provided (for accessibility)
            if svg_title:
                svg_options["title"] = svg_title
            if svg_description:
                svg_options["desc"] = svg_description
                
            # Generate SVG with accessibility options
            qr.save(output, kind="svg", **svg_options)
            return output.getvalue()
        
        # For raster formats, we'll use Pillow for final processing
        # First generate a high-resolution QR code
        qr_buffer = io.BytesIO()
        # Use a larger scale for better quality when resizing
        scale = max(1, size // 40)  # Estimate a good initial scale
        qr.save(qr_buffer, kind="png", scale=scale, dark=fill_color, light=back_color, border=border)
        qr_buffer.seek(0)
        
        # Open with Pillow
        img = Image.open(qr_buffer)
        img = img.convert('RGB')  # Ensure color mode
        
        # If we have a logo, add it now
        if actual_logo_path:
            # Open and resize logo
            logo_img = Image.open(actual_logo_path)
            # Convert logo to RGB if necessary
            if logo_img.mode != 'RGB':
                logo_img = logo_img.convert('RGB')
            
            # Calculate logo size - use 1/2 of QR code instead of 1/3 for better visibility
            logo_max_size = img.height // 2  # Changed from img.height // 3
            # Maintain aspect ratio
            logo_img.thumbnail((logo_max_size, logo_max_size), Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS)
            
            # Calculate position to center the logo
            box = (
                (img.width - logo_img.size[0]) // 2,
                (img.height - logo_img.size[1]) // 2
            )
            
            # Create a white background slightly larger than the logo
            padding = 5
            bg_size = (logo_img.size[0] + padding*2, logo_img.size[1] + padding*2)
            bg_box = (
                (img.width - bg_size[0]) // 2,
                (img.height - bg_size[1]) // 2
            )
            bg_img = Image.new('RGB', bg_size, (255, 255, 255))
            img.paste(bg_img, bg_box)
            
            # Paste the logo
            img.paste(logo_img, box)
        
        # Resize to final dimensions
        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS)
        
        # Save to bytes
        output = io.BytesIO()
        save_kwargs = {}
        
        if image_format.lower() == "jpeg":
            save_kwargs["quality"] = 95  # High quality JPEG
        elif image_format.lower() == "webp":
            save_kwargs["quality"] = 95
            save_kwargs["method"] = 6  # Highest quality WebP
        
        img.save(output, format=image_format.upper(), **save_kwargs)
        return output.getvalue()
        
    except Exception as e:
        # Handle unexpected exceptions
        raise ValueError(f"Error generating QR code: {str(e)}")


def generate_qr_response(
    content: str,
    image_format: str = "png",
    size: int = 200,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    border: int = 4,
    image_quality: Optional[int] = None,
    logo_path: Optional[Union[str, bool]] = None,
    error_level: str = "m",
    svg_title: Optional[str] = None,
    svg_description: Optional[str] = None,
) -> StreamingResponse:
    """
    Generate a QR code and return it as a StreamingResponse.
    
    Args:
        content: The content to encode in the QR code
        image_format: The output format (png, svg, jpeg, webp)
        size: The size of the image in pixels
        fill_color: Color of the QR code modules
        back_color: Background color
        border: Size of the border around the QR code
        image_quality: Quality for lossy formats (1-100)
        logo_path: Optional path to a logo image
        error_level: Error correction level (l, m, q, h)
        svg_title: Optional title for SVG format (improves accessibility)
        svg_description: Optional description for SVG format (improves accessibility)
        
    Returns:
        StreamingResponse containing the image
        
    Raises:
        HTTPException: If there's an error generating the QR code
    """
    # Media type mapping
    IMAGE_FORMATS = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg", 
        "svg": "image/svg+xml",
        "webp": "image/webp",
    }
    
    # Validate image format
    image_format = image_format.lower()
    if image_format not in IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format. Supported formats: {', '.join(IMAGE_FORMATS.keys())}",
        )
    
    try:
        # Call the image generation function
        img_bytes = generate_qr_image(
            content=content,
            image_format=image_format,
            size=size,
            fill_color=fill_color,
            back_color=back_color,
            border=border,
            logo_path=logo_path,
            error_level=error_level,
            svg_title=svg_title,
            svg_description=svg_description
        )
        
        # Create BytesIO from the generated bytes
        buf = io.BytesIO(img_bytes)
        buf.seek(0)
        
        return StreamingResponse(
            buf,
            media_type=IMAGE_FORMATS[image_format],
            headers={"Content-Disposition": f'inline; filename="qr.{image_format}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}") 