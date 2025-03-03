"""
Pydantic models for request/response validation.
"""

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


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

    @field_validator("fill_color", "back_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate color fields."""
        if not ColorValidator.is_valid_color(v):
            raise ValueError("Invalid hex color format. Must be in #RRGGBB format")
        return v.upper()  # Normalize to uppercase


class QRCodeCreate(QRCodeBase):
    """Schema for creating a QR code."""

    qr_type: QRType = QRType.STATIC
    redirect_url: HttpUrl | None = None


class QRCodeUpdate(BaseModel):
    """Schema for updating a QR code."""

    redirect_url: HttpUrl


class QRCodeResponse(QRCodeBase):
    """Schema for QR code response."""

    id: str
    qr_type: str
    redirect_url: HttpUrl | None = None
    created_at: datetime
    scan_count: int
    last_scan_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.astimezone().isoformat() if dt else None},
    )


class QRCodeList(BaseModel):
    """Schema for list of QR codes response."""

    items: list[QRCodeResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
