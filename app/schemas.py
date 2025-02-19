"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from typing import Optional, Literal, List
import re
from enum import Enum

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

class QRCodeBase(BaseModel):
    """Base QR code schema."""
    content: str = Field(..., max_length=2048)
    fill_color: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    back_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    size: int = Field(default=10, ge=1, le=100)
    border: int = Field(default=4, ge=0, le=20)

    @validator("fill_color", "back_color")
    def validate_color(cls, v):
        """Validate color fields."""
        if not ColorValidator.is_valid_color(v):
            raise ValueError("Invalid hex color format. Must be in #RRGGBB format")
        return v.upper()  # Normalize to uppercase

class QRCodeCreate(QRCodeBase):
    """Schema for creating a QR code."""
    redirect_url: Optional[HttpUrl] = None

class QRCodeUpdate(BaseModel):
    """Schema for updating a QR code."""
    redirect_url: HttpUrl

class QRCodeResponse(QRCodeBase):
    """Schema for QR code response."""
    id: str
    qr_type: str
    redirect_url: Optional[HttpUrl] = None
    created_at: datetime
    scan_count: int
    last_scan_at: Optional[datetime] = None

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
        json_encoders = {
            # Ensure datetime fields are serialized with timezone info
            datetime: lambda dt: dt.astimezone().isoformat()
        }

class QRCodeList(BaseModel):
    """Schema for list of QR codes response."""
    items: List[QRCodeResponse]
    total: int
    page: int
    page_size: int

    class Config:
        """Pydantic model configuration."""
        from_attributes = True 