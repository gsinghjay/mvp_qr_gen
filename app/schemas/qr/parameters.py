"""
Parameter models for QR code endpoints.

This module defines Pydantic models for query parameters used in QR code endpoints.
These models provide consistent validation and documentation for API parameters.
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from ..common import ImageFormat, QRType, ErrorCorrectionLevel


class QRListParameters(BaseModel):
    """Parameters for listing QR codes."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip (for pagination)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of records to return")
    qr_type: QRType | None = Field(
        default=None, description="Filter by QR code type (static or dynamic)"
    )
    search: str | None = Field(
        default=None, description="Search term for filtering content, title, description or redirect URL"
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
        default=ImageFormat.PNG, 
        description="The format of the image (png, jpeg, jpg, svg, webp)",
        alias="format"
    )
    image_quality: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="The quality of the image (1-100, for lossy formats)",
    )
    size: int = Field(
        default=10, 
        ge=1, 
        le=500, 
        description="QR code size (1-500) - relative unit that gets multiplied by 25 to determine pixel size; ignored if physical dimensions are provided"
    )
    border: int = Field(default=4, ge=0, le=20, description="QR code border width (0-20)")
    fill_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code fill color in hex format (#RRGGBB)",
    )
    back_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="QR code background color in hex format (#RRGGBB)",
    )
    data_dark_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description="Color for dark data modules in hex format (#RRGGBB or #RRGGBBAA). Overrides fill_color for data modules."
    )
    data_light_color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$",
        description="Color for light data modules in hex format (#RRGGBB or #RRGGBBAA). Overrides back_color for data modules."
    )
    include_logo: bool = Field(
        default=False,
        description="Whether to include the default logo in the QR code"
    )
    error_level: ErrorCorrectionLevel = Field(
        default=ErrorCorrectionLevel.M,
        description="Error correction level determines how much of the QR code can be damaged while still being scannable"
    )
    svg_title: str | None = Field(
        default=None,
        description="Title for SVG format (improves accessibility)",
        max_length=100
    )
    svg_description: str | None = Field(
        default=None,
        description="Description for SVG format (improves accessibility)",
        max_length=500
    )
    # New fields for physical dimensions and DPI
    physical_size: float | None = Field(
        default=None,
        ge=0.1,
        le=100,
        description="Physical size of the QR code in physical_unit (0.1-100)"
    )
    physical_unit: str | None = Field(
        default=None,
        pattern=r"^(in|cm|mm)$",
        description="Physical unit for size (in, cm, mm)"
    )
    dpi: int | None = Field(
        default=None,
        ge=72,
        le=1200,
        description="DPI (dots per inch) for physical output (72-1200)"
    )

    @model_validator(mode='after')
    def validate_physical_dimensions(self) -> 'QRImageParameters':
        """Validate that physical dimensions are properly specified."""
        # If any physical dimension parameter is provided, all must be provided
        physical_params = [self.physical_size, self.physical_unit, self.dpi]
        
        if any(param is not None for param in physical_params):
            if self.physical_size is None:
                raise ValueError("physical_size must be specified when any physical dimension parameter is provided")
            if self.physical_unit is None:
                raise ValueError("physical_unit must be specified when any physical dimension parameter is provided")
            if self.dpi is None:
                raise ValueError("dpi must be specified when any physical dimension parameter is provided")
        
        return self


class QRCreateParameters(BaseModel):
    """Common parameters for creating QR codes."""

    title: str = Field(
        ..., 
        max_length=100, 
        description="User-friendly title for the QR code"
    )
    description: str | None = Field(
        None, 
        max_length=500, 
        description="Detailed description of the QR code"
    )
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
    size: int = Field(
        default=10, 
        ge=1, 
        le=500, 
        description="QR code size (1-500) - relative unit that gets multiplied by 25 to determine pixel size"
    )
    border: int = Field(default=4, ge=0, le=20, description="QR code border width (0-20)")
    error_level: ErrorCorrectionLevel = Field(
        default=ErrorCorrectionLevel.M,
        description="Error correction level determines how much of the QR code can be damaged while still being scannable"
    )

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

    redirect_url: HttpUrl | None = Field(
        None, description="New URL to redirect to when the QR code is scanned (for dynamic QR codes only)"
    )
    title: str | None = Field(
        None, 
        max_length=100, 
        description="Updated title for the QR code"
    )
    description: str | None = Field(
        None, 
        max_length=500, 
        description="Updated description for the QR code"
    )
