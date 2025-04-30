"""
Repository layer for the QR code generator application.
Provides data access objects that abstract database interactions.
"""

from .base_repository import BaseRepository
from .qr_repository import QRCodeRepository

__all__ = ["BaseRepository", "QRCodeRepository"] 