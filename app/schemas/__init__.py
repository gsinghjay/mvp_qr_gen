"""
Pydantic models for request/response validation.
"""

from .common import HTTPError, ImageFormat, QRType
from .health import HealthResponse, HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics
from .qr import (
    DynamicQRCreateParameters,
    QRCodeBase,
    QRCodeCreate,
    QRCodeList,
    QRCodeResponse,
    QRCodeUpdate,
    QRCreateParameters,
    QRImageParameters,
    # Parameter models
    QRListParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)

__all__ = [
    # Health schemas
    "HealthResponse",
    "HealthStatus",
    "ServiceCheck",
    "ServiceStatus",
    "SystemMetrics",
    # Common schemas
    "HTTPError",
    "ImageFormat",
    "QRType",
    # QR code model schemas
    "QRCodeBase",
    "QRCodeCreate",
    "QRCodeList",
    "QRCodeResponse",
    "QRCodeUpdate",
    # QR code parameter schemas
    "QRListParameters",
    "QRImageParameters",
    "QRCreateParameters",
    "StaticQRCreateParameters",
    "DynamicQRCreateParameters",
    "QRUpdateParameters",
]
