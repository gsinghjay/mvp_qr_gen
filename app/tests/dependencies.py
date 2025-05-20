"""
Test-specific dependency injection functions for the QR code generator application.

These functions mirror the main application dependencies but with test-specific overrides.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.repositories.qr_repository import QRCodeRepository
from app.services.qr_service import QRCodeService
from .conftest import TestSessionLocal


def get_test_db() -> Session:
    """
    Provides a database session for testing.
    
    Returns:
        SQLAlchemy database session for testing
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_test_db_with_logging() -> Session:
    """
    Provides a database session with logging for testing.
    
    Returns:
        SQLAlchemy database session for testing
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_qr_repository(db: Annotated[Session, Depends(get_test_db_with_logging)]) -> QRCodeRepository:
    """
    Test dependency for getting a QRCodeRepository instance.
    
    Args:
        db: The test database session (injected via FastAPI's dependency system)
        
    Returns:
        An instance of QRCodeRepository with the test database session
    """
    return QRCodeRepository(db)


def get_qr_service(repo: Annotated[QRCodeRepository, Depends(get_qr_repository)]) -> QRCodeService:
    """
    Test dependency for getting a QRCodeService instance.
    
    Args:
        repo: The QRCodeRepository (injected via FastAPI's dependency system)
        
    Returns:
        An instance of QRCodeService with the repository
    """
    return QRCodeService(repo) 