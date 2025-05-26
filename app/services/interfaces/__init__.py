"""
Service interfaces for the QR code generator application.

This package contains abstract base classes that define contracts for various
service implementations in the Observatory-First refactoring architecture.
"""

from .qr_generation_interfaces import QRCodeGenerator, QRImageFormatter
from .analytics_interfaces import AnalyticsProvider, ScanEventLogger
from .validation_interfaces import ValidationProvider

__all__ = [
    "QRCodeGenerator",
    "QRImageFormatter", 
    "AnalyticsProvider",
    "ScanEventLogger",
    "ValidationProvider",
] 