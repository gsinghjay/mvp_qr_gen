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


# Health check schemas
class ServiceStatus(str, Enum):
    """Enumeration of possible service check statuses."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class HealthStatus(str, Enum):
    """Enumeration of possible overall health check statuses."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SystemMetrics(BaseModel):
    """System resource metrics."""

    cpu_usage: float = Field(..., description="CPU usage percentage", ge=0, le=100)
    memory_usage: float = Field(
        ..., description="Memory usage percentage", ge=0, le=100
    )
    disk_usage: float = Field(..., description="Disk usage percentage", ge=0, le=100)


class ServiceCheck(BaseModel):
    """Individual service check result."""

    status: ServiceStatus = Field(..., description="Status of the service check")
    latency_ms: float = Field(..., description="Latency of the check in milliseconds")
    message: str | None = Field(None, description="Additional status message")
    last_checked: datetime = Field(..., description="Timestamp of the last check")


class HealthResponse(BaseModel):
    """
    Schema for health check response.

    Attributes:
        status (HealthStatus): The overall health status of the service
        version (str): The current version of the service
        uptime_seconds (float): How long the service has been running
        system_metrics (SystemMetrics): Current system resource metrics
        checks (dict[str, ServiceCheck]): Results of individual service checks
    """

    status: HealthStatus = Field(
        default=HealthStatus.HEALTHY,
        description="The overall health status of the service",
    )
    version: str = Field(..., description="The current version of the service")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    system_metrics: SystemMetrics = Field(..., description="System resource metrics")
    checks: dict[str, ServiceCheck] = Field(
        ..., description="Results of individual service checks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.0,
                "system_metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.7,
                    "disk_usage": 78.1,
                },
                "checks": {
                    "database": {
                        "status": "pass",
                        "latency_ms": 12.3,
                        "message": "Connected successfully",
                        "last_checked": "2024-03-14T12:00:00Z",
                    }
                },
            }
        }
    )


# Define HTTPError schema if it doesn't exist already
class HTTPError(BaseModel):
    """Schema for HTTP error responses."""
    
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Service is currently unhealthy",
                "status_code": 503
            }
        }
    )
