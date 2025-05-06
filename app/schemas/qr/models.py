"""
QR code Pydantic models.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from ..common import QRType, ErrorCorrectionLevel


class QRCodeBase(BaseModel):
    """Base QR code schema."""

    content: str = Field(..., max_length=2048)
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    fill_color: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    back_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    size: int = Field(default=10, ge=1, le=100)
    border: int = Field(default=4, ge=0, le=20)
    error_level: str = Field(default=ErrorCorrectionLevel.M.value, description="Error correction level")

    @field_validator("fill_color", "back_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate color values (must be hex format)."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return v


class QRCodeCreate(QRCodeBase):
    """Schema for creating a QR code."""

    qr_type: QRType = QRType.STATIC
    redirect_url: HttpUrl | None = None


class QRCodeUpdate(BaseModel):
    """Schema for updating a QR code."""

    redirect_url: HttpUrl | None = None
    title: str | None = None
    description: str | None = None


class QRCodeResponse(QRCodeBase):
    """Schema for QR code response."""

    id: str
    qr_type: QRType
    redirect_url: HttpUrl | None = None
    created_at: datetime
    scan_count: int
    last_scan_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "f7f7f7f7-e8e8-4b4b-9191-2b2b2b2b2b2b",
                "content": "https://example.com",
                "qr_type": "dynamic",
                "redirect_url": "https://example.com",
                "created_at": "2023-01-01T00:00:00Z",
                "scan_count": 42,
                "last_scan_at": "2023-01-02T12:34:56Z",
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
                "size": 10,
                "border": 4,
                "error_level": "m"
            }
        }
    )


class QRCodeList(BaseModel):
    """Schema for list of QR codes response."""

    items: list[QRCodeResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
