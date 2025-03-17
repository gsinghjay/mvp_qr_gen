"""
Parameter models for QR code endpoints.

This module defines Pydantic models for query parameters used in QR code endpoints.
These models provide consistent validation and documentation for API parameters.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from ..common import ImageFormat, QRType


class QRListParameters(BaseModel):
    """Parameters for listing QR codes."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip (for pagination)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of records to return")
    qr_type: QRType | None = Field(
        default=None, description="Filter by QR code type (static or dynamic)"
    )
    search: str | None = Field(
        default=None, description="Search term for filtering content or redirect URL"
    )
    sort_by: str | None = Field(
        default=None, description="Field to sort by (created_at, scan_count, etc.)"
    )
    sort_desc: bool = Field(
        default=False, description="Sort in descending order if true"
    )


class QRImageParameters(BaseModel):
    """Parameters for QR code image generation."""

    image_format: ImageFormat = Field(
        default=ImageFormat.PNG, description="The format of the image (png, jpeg, jpg, svg, webp)"
    )
    image_quality: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="The quality of the image (1-100, for lossy formats)",
    )
    size: int = Field(default=10, ge=1, le=100, description="QR code size (1-100)")
    border: int = Field(default=4, ge=0, le=20, description="QR code border width (0-20)")
    fill_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code fill color in hex format (#RRGGBB)",
    )
    back_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code background color in hex format (#RRGGBB)",
    )


class QRCreateParameters(BaseModel):
    """Common parameters for creating QR codes."""

    fill_color: str = Field(
        default="#000000",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code fill color in hex format (#RRGGBB)",
    )
    back_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code background color in hex format (#RRGGBB)",
    )
    size: int = Field(default=10, ge=1, le=100, description="QR code size (1-100)")
    border: int = Field(default=4, ge=0, le=20, description="QR code border width (0-20)")

    @model_validator(mode="after")
    def validate_colors_are_different(self) -> "QRCreateParameters":
        """Validate that fill_color and back_color are different."""
        if self.fill_color.upper() == self.back_color.upper():
            raise ValueError("Fill color and background color must be different")
        return self


class StaticQRCreateParameters(QRCreateParameters):
    """Parameters for creating static QR codes."""

    content: str = Field(..., max_length=2048, description="Content to encode in the QR code")
    redirect_url: HttpUrl | None = Field(
        default=None, description="Not allowed for static QR codes"
    )

    @field_validator("redirect_url")
    @classmethod
    def validate_no_redirect_url(cls, v: HttpUrl | None) -> None:
        """Validate that static QR codes don't have a redirect URL."""
        if v is not None:
            raise ValueError("Static QR codes cannot have a redirect URL")
        return v


class DynamicQRCreateParameters(QRCreateParameters):
    """Parameters for creating dynamic QR codes."""

    content: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional custom content (if not provided, will be generated)",
    )
    redirect_url: HttpUrl = Field(..., description="URL to redirect to when the QR code is scanned")


class QRUpdateParameters(BaseModel):
    """Parameters for updating QR codes."""

    redirect_url: HttpUrl = Field(
        ..., description="New URL to redirect to when the QR code is scanned"
    )
