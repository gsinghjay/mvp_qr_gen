"""
QR code schemas package.
"""

from .models import (
    QRCodeBase,
    QRCodeCreate,
    QRCodeList,
    QRCodeResponse,
    QRCodeUpdate,
)
from .parameters import (
    DynamicQRCreateParameters,
    QRCreateParameters,
    QRImageParameters,
    QRListParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)

__all__ = [
    # Model schemas
    "QRCodeBase",
    "QRCodeCreate",
    "QRCodeList",
    "QRCodeResponse",
    "QRCodeUpdate",
    # Parameter schemas
    "QRListParameters",
    "QRImageParameters",
    "QRCreateParameters",
    "StaticQRCreateParameters",
    "DynamicQRCreateParameters",
    "QRUpdateParameters",
]
