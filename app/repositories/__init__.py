"""
Repository layer for the QR code generator application.
Provides data access objects that abstract database interactions.
"""

from .base_repository import BaseRepository
from .qr_code_repository import QRCodeRepository
from .scan_log_repository import ScanLogRepository

# Export the repositories
__all__ = ["BaseRepository", "QRCodeRepository", "ScanLogRepository"] 