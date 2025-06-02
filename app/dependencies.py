"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
# from .services.qr_service import QRCodeService # QRCodeService and get_qr_service removed

# New imports for Observatory-First refactoring
from .adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from .services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter
from .services.interfaces.analytics_interfaces import AnalyticsProvider, ScanEventLogger
from .services.interfaces.validation_interfaces import ValidationProvider
from .services.new_qr_generation_service import NewQRGenerationService
from .services.qr_retrieval_service import QRRetrievalService
from .services.scan_processing_service import ScanProcessingService
from .services.qr_creation_service import QRCreationService
from .services.qr_image_service import QRImageService
from .services.qr_update_service import QRUpdateService
from .services.qr_deletion_service import QRDeletionService # Added
from .services.new_analytics_service import NewAnalyticsService
from .services.new_validation_service import NewValidationService

# Circuit breaker imports
import aiobreaker
from .core.circuit_breaker import get_new_qr_generation_breaker
from .core.config import settings, Settings # Added settings for injection


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


def get_qr_retrieval_service(qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)]) -> QRRetrievalService:
    """
    Dependency for getting a QRRetrievalService instance.

    Args:
        qr_code_repo: The QRCodeRepository

    Returns:
        An instance of QRRetrievalService
    """
    return QRRetrievalService(qr_code_repo=qr_code_repo)


# New dependencies for Observatory-First refactoring - moved up to avoid forward references

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


def get_scan_processing_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    scan_log_repo: Annotated[ScanLogRepository, Depends(get_scan_log_repository)],
    qr_retrieval_service: Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)],
) -> ScanProcessingService:
    """
    Dependency for getting a ScanProcessingService instance.

    Args:
        qr_code_repo: The QRCodeRepository
        scan_log_repo: The ScanLogRepository
        qr_retrieval_service: The QRRetrievalService

    Returns:
        An instance of ScanProcessingService
    """
    return ScanProcessingService(
        qr_code_repo=qr_code_repo,
        scan_log_repo=scan_log_repo,
        qr_retrieval_service=qr_retrieval_service,
    )


def get_qr_creation_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[aiobreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)],
    # settings: Annotated[Settings, Depends(get_settings)] # This would be ideal if get_settings existed
) -> QRCreationService:
    """
    Dependency for getting a QRCreationService instance.

    Args:
        qr_code_repo: The QRCodeRepository.
        new_qr_generation_service: The NewQRGenerationService for enhanced QR generation.
        new_qr_generation_breaker: Circuit breaker for NewQRGenerationService protection.
        # settings: The application settings object.

    Returns:
        An instance of QRCreationService.
    """
    return QRCreationService(
        qr_code_repo=qr_code_repo,
        settings=settings, # Directly using imported settings
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker,
    )


def get_qr_image_service(
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[aiobreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)],
    # settings: Annotated[Settings, Depends(get_settings)] # This would be ideal if get_settings existed
) -> QRImageService:
    """
    Dependency for getting a QRImageService instance.

    Args:
        new_qr_generation_service: The NewQRGenerationService for enhanced QR generation.
        new_qr_generation_breaker: Circuit breaker for NewQRGenerationService protection.
        # settings: The application settings object.

    Returns:
        An instance of QRImageService.
    """
    return QRImageService(
        settings=settings, # Directly using imported settings
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker,
    )


def get_qr_update_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    qr_retrieval_service: Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)],
    qr_creation_service: Annotated[QRCreationService, Depends(get_qr_creation_service)],
) -> QRUpdateService:
    """
    Dependency for getting a QRUpdateService instance.

    Args:
        qr_code_repo: The QRCodeRepository.
        qr_retrieval_service: The QRRetrievalService.
        qr_creation_service: The QRCreationService (for validation helpers).

    Returns:
        An instance of QRUpdateService.
    """
    return QRUpdateService(
        qr_code_repo=qr_code_repo,
        qr_retrieval_service=qr_retrieval_service,
        qr_creation_service=qr_creation_service,
    )


def get_qr_deletion_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
) -> QRDeletionService:
    """
    Dependency for getting a QRDeletionService instance.

    Args:
        qr_code_repo: The QRCodeRepository.

    Returns:
        An instance of QRDeletionService.
    """
    return QRDeletionService(qr_code_repo=qr_code_repo)


# def get_qr_service removed

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
