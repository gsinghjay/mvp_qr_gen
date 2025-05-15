"""
Database models for the QR code generator application.
"""

from .base import UTCDateTime
from .qr import QRCode
from .scan_log import ScanLog

__all__ = ["QRCode", "UTCDateTime", "ScanLog"]
