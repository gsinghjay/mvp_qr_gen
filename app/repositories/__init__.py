"""
Repository layer for the QR code generator application.
Provides data access objects that abstract database interactions.
"""

from .base_repository import BaseRepository
# Import the original repository (deprecated) for backward compatibility
from .qr_repository import QRCodeRepository as OriginalQRCodeRepository  
from .qr_code_repository import QRCodeRepository
from .scan_log_repository import ScanLogRepository

# Re-export with alias for backward compatibility
__all__ = ["BaseRepository", "QRCodeRepository", "ScanLogRepository", "OriginalQRCodeRepository"] 