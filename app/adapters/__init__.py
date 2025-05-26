"""
Adapter implementations for the QR code generator application.

This package contains concrete implementations of service interfaces using
specific libraries like Segno and Pillow in the Observatory-First refactoring architecture.
"""

from .segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter

__all__ = [
    "SegnoQRCodeGenerator",
    "PillowQRImageFormatter",
] 