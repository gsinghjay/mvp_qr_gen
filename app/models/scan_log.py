"""
Scan log database models for enhanced QR code tracking.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.sql import func

from app.database import Base
from .base import UTCDateTime


class ScanLog(Base):
    """
    Scan log model for tracking QR code scans with detailed analytics.

    Attributes:
        id (str): Unique identifier for the scan log (UUID)
        qr_code_id (str): Foreign key reference to the QR code being scanned
        scanned_at (datetime): Timestamp of the scan (UTC)
        ip_address (str): IP address of the client that scanned the QR code
        raw_user_agent (str): Raw user agent string from the client
        is_genuine_scan (bool): Whether this is a genuine QR scan (vs. direct URL access)
        device_family (str): Device family (e.g., iPhone, Samsung Galaxy)
        os_family (str): Operating system family (e.g., iOS, Android, Windows)
        os_version (str): Operating system version
        browser_family (str): Browser family (e.g., Chrome, Safari, Firefox)
        browser_version (str): Browser version
        is_mobile (bool): Whether the device is a mobile device
        is_tablet (bool): Whether the device is a tablet
        is_pc (bool): Whether the device is a PC
        is_bot (bool): Whether the user agent appears to be a bot
    """

    __tablename__ = "scan_logs"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    qr_code_id: str = Column(String, ForeignKey("qr_codes.id", ondelete="CASCADE"), nullable=False, index=True)
    scanned_at: datetime = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )
    ip_address: str = Column(String(50), nullable=True)
    raw_user_agent: str = Column(Text, nullable=True)
    is_genuine_scan: bool = Column(Boolean, nullable=False, default=False, index=True)
    
    # Parsed user agent data
    device_family: str = Column(String(100), nullable=True, index=True)
    os_family: str = Column(String(50), nullable=True, index=True)
    os_version: str = Column(String(50), nullable=True)
    browser_family: str = Column(String(50), nullable=True, index=True)
    browser_version: str = Column(String(50), nullable=True)
    is_mobile: bool = Column(Boolean, nullable=False, default=False, index=True)
    is_tablet: bool = Column(Boolean, nullable=False, default=False, index=True)
    is_pc: bool = Column(Boolean, nullable=False, default=False, index=True)
    is_bot: bool = Column(Boolean, nullable=False, default=False, index=True)

    def __init__(self, **kwargs):
        """Initialize a scan log with timezone-aware datetime fields."""
        # Ensure scanned_at is timezone-aware
        if "scanned_at" not in kwargs:
            kwargs["scanned_at"] = datetime.now(UTC)
        elif kwargs["scanned_at"].tzinfo is None:
            # Convert naive datetime to UTC
            kwargs["scanned_at"] = kwargs["scanned_at"].replace(tzinfo=UTC)

        super().__init__(**kwargs) 