"""
QR code database models.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base

from .base import UTCDateTime


class QRCode(Base):
    """
    QR Code model representing a generated QR code in the database.

    Attributes:
        id (str): Unique identifier for the QR code (UUID)
        content (str): The content encoded in the QR code (for static) or target URL (for dynamic)
        qr_type (str): Type of QR code (static/dynamic)
        redirect_url (str): The URL where dynamic QR codes redirect to (None for static)
        created_at (datetime): Timestamp of creation (UTC)
        scan_count (int): Number of times the QR code has been scanned
        last_scan_at (datetime): Timestamp of last scan (UTC)
        fill_color (str): Color of the QR code pattern
        back_color (str): Background color of the QR code
        size (int): Size of QR code boxes
        border (int): Border size around QR code
    """

    __tablename__ = "qr_codes"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    content: str = Column(String(2048), nullable=False, index=True)
    qr_type: str = Column(String(50), nullable=False, index=True)
    redirect_url: str = Column(Text, nullable=True)
    created_at: datetime = Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.datetime(func.utcnow()),
        index=True,
    )
    scan_count: int = Column(Integer, nullable=False, default=0)
    last_scan_at: datetime = Column(UTCDateTime, nullable=True)

    # QR code appearance settings
    fill_color: str = Column(String(50), nullable=False, default="#000000")
    back_color: str = Column(String(50), nullable=False, default="#FFFFFF")
    size: int = Column(Integer, nullable=False, default=10)
    border: int = Column(Integer, nullable=False, default=4)

    def __init__(self, **kwargs):
        """Initialize a QR code with timezone-aware datetime fields."""
        # Ensure created_at is timezone-aware
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(UTC)
        elif kwargs["created_at"].tzinfo is None:
            # Convert naive datetime to UTC
            kwargs["created_at"] = kwargs["created_at"].replace(tzinfo=UTC)

        # Set default scan_count if not provided
        if "scan_count" not in kwargs:
            kwargs["scan_count"] = 0

        # Ensure last_scan_at is timezone-aware if provided
        if "last_scan_at" in kwargs and kwargs["last_scan_at"] is not None:
            if kwargs["last_scan_at"].tzinfo is None:
                kwargs["last_scan_at"] = kwargs["last_scan_at"].replace(tzinfo=UTC)

        super().__init__(**kwargs)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "qr_type": self.qr_type,
            "redirect_url": self.redirect_url if self.qr_type == "dynamic" else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scan_count": self.scan_count,
            "last_scan_at": (self.last_scan_at.isoformat() if self.last_scan_at else None),
            "fill_color": self.fill_color,
            "back_color": self.back_color,
            "size": self.size,
            "border": self.border,
        }
