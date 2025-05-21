"""
Repository layer for the QR code generator application.
Provides data access objects that abstract database interactions.
"""

from .base_repository import BaseRepository
from .qr_repository import QRCodeRepository # Original repository (deprecated)
from .qr_code_repository import QRCodeRepository as NewQRCodeRepository
from .scan_log_repository import ScanLogRepository

# Re-export with alias for backward compatibility
__all__ = ["BaseRepository", "QRCodeRepository", "NewQRCodeRepository", "ScanLogRepository"] 