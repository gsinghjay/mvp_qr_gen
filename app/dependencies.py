"""
Dependency injection functions for the QR code generator application.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .services.qr_service import QRCodeService


def get_qr_service(db: Session = Depends(get_db_with_logging)) -> QRCodeService:
    """
    Dependency for getting a QRCodeService instance.

    Args:
        db: The database session (injected via FastAPI's dependency system)

    Returns:
        An instance of QRCodeService with the database session
    """
    return QRCodeService(db)
