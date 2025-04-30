"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories.qr_repository import QRCodeRepository
from .services.qr_service import QRCodeService


def get_db() -> Annotated[Session, Depends(get_db_with_logging)]:
    """
    Shorthand dependency for getting a database session.
    
    Returns:
        SQLAlchemy database session
    """
    return Depends(get_db_with_logging)


def get_qr_repository(db: Annotated[Session, Depends(get_db_with_logging)]) -> QRCodeRepository:
    """
    Dependency for getting a QRCodeRepository instance.
    
    Args:
        db: The database session (injected via FastAPI's dependency system)
        
    Returns:
        An instance of QRCodeRepository with the database session
    """
    return QRCodeRepository(db)


def get_qr_service(repo: Annotated[QRCodeRepository, Depends(get_qr_repository)]) -> QRCodeService:
    """
    Dependency for getting a QRCodeService instance.
    
    Args:
        repo: The QRCodeRepository (injected via FastAPI's dependency system)
        
    Returns:
        An instance of QRCodeService with the repository
    """
    return QRCodeService(repo)
