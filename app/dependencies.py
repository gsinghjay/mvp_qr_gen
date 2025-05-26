"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService

# New imports for Observatory-First refactoring
from .adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from .services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter
from .services.interfaces.analytics_interfaces import AnalyticsProvider, ScanEventLogger
from .services.interfaces.validation_interfaces import ValidationProvider
from .services.new_qr_generation_service import NewQRGenerationService
from .services.new_analytics_service import NewAnalyticsService
from .services.new_validation_service import NewValidationService


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


# New dependencies for Observatory-First refactoring

def get_segno_qr_generator() -> SegnoQRCodeGenerator:
    """
    Dependency for getting a SegnoQRCodeGenerator adapter instance.
    
    Returns:
        An instance of SegnoQRCodeGenerator
    """
    return SegnoQRCodeGenerator()


def get_pillow_qr_formatter() -> PillowQRImageFormatter:
    """
    Dependency for getting a PillowQRImageFormatter adapter instance.
    
    Returns:
        An instance of PillowQRImageFormatter
    """
    return PillowQRImageFormatter()


def get_new_qr_generation_service(
    generator: Annotated[QRCodeGenerator, Depends(get_segno_qr_generator)],
    formatter: Annotated[QRImageFormatter, Depends(get_pillow_qr_formatter)],
) -> NewQRGenerationService:
    """
    Dependency for getting a NewQRGenerationService instance.
    
    Args:
        generator: QR code generation implementation
        formatter: QR image formatting implementation
        
    Returns:
        An instance of NewQRGenerationService with injected adapters
    """
    return NewQRGenerationService(generator=generator, formatter=formatter)


def get_new_analytics_service(
    # Note: For now, we don't have concrete implementations of AnalyticsProvider and ScanEventLogger
    # These will be added in future phases when we create concrete adapters
) -> NewAnalyticsService:
    """
    Dependency for getting a NewAnalyticsService instance.
    
    Note: Placeholder implementation - concrete providers will be added in future phases.
    
    Returns:
        An instance of NewAnalyticsService (not yet fully functional)
    """
    # TODO: Implement concrete AnalyticsProvider and ScanEventLogger adapters
    # For now, this is a placeholder that won't be used until Phase 1
    return None  # This will be updated when we have concrete implementations


def get_new_validation_service(
    # Note: For now, we don't have concrete implementation of ValidationProvider
    # This will be added in future phases when we create concrete adapters
) -> NewValidationService:
    """
    Dependency for getting a NewValidationService instance.
    
    Note: Placeholder implementation - concrete provider will be added in future phases.
    
    Returns:
        An instance of NewValidationService (not yet fully functional)
    """
    # TODO: Implement concrete ValidationProvider adapter
    # For now, this is a placeholder that won't be used until Phase 1
    return None  # This will be updated when we have concrete implementations
