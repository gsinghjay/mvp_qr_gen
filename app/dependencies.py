"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService


def get_db() -> Annotated[Session, Depends(get_db_with_logging)]:
    """
    Shorthand dependency for getting a database session.
    
    Returns:
        SQLAlchemy database session
    """
    return Depends(get_db_with_logging)


def get_qr_code_repository(db: Annotated[Session, Depends(get_db_with_logging)]) -> QRCodeRepository:
    """
    Dependency for getting a QRCodeRepository instance.
    
    Args:
        db: The database session (injected via FastAPI's dependency system)
        
    Returns:
        An instance of QRCodeRepository with the database session
    """
    return QRCodeRepository(db)


def get_scan_log_repository(db: Annotated[Session, Depends(get_db_with_logging)]) -> ScanLogRepository:
    """
    Dependency for getting a ScanLogRepository instance.
    
    Args:
        db: The database session (injected via FastAPI's dependency system)
        
    Returns:
        An instance of ScanLogRepository with the database session
    """
    return ScanLogRepository(db)


def get_qr_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    scan_log_repo: Annotated[ScanLogRepository, Depends(get_scan_log_repository)]
) -> QRCodeService:
    """
    Dependency for getting a QRCodeService instance.
    
    Args:
        qr_code_repo: The QRCodeRepository
        scan_log_repo: The ScanLogRepository
        
    Returns:
        An instance of QRCodeService with the repositories
    """
    return QRCodeService(qr_code_repo=qr_code_repo, scan_log_repo=scan_log_repo)
