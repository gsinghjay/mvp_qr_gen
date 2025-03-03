"""
Common schema functionality and validators.
"""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class QRType(str, Enum):
    """Valid QR code types."""

    STATIC = "static"
    DYNAMIC = "dynamic"


class ImageFormat(str, Enum):
    """Valid image output formats."""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    SVG = "svg"
    WEBP = "webp"


class ColorValidator:
    """Validator for color values."""

    @staticmethod
    def is_valid_color(color: str) -> bool:
        """
        Validate color string.
        Only accepts hex colors (#RRGGBB format)
        """
        # Hex color pattern (case insensitive)
        hex_pattern = r"^#[0-9A-Fa-f]{6}$"
        return bool(re.match(hex_pattern, color))


class HTTPError(BaseModel):
    """Schema for HTTP error responses."""
    
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "An error occurred while processing your request",
                "status_code": 500,
            }
        }
    ) 