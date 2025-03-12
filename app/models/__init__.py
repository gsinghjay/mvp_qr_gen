"""
Database models for the QR code generator application.
"""

from .base import UTCDateTime
from .qr import QRCode

__all__ = ["QRCode", "UTCDateTime"]
