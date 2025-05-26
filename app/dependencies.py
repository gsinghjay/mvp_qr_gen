"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService

# New imports for specialized QR services
from .services.qr.qr_core_service import QRCoreService
from .services.qr.qr_validation_service import QRValidationService
from .services.qr.static_qr_service import StaticQRService
from .services.qr.dynamic_qr_service import DynamicQRService
from .services.qr.qr_image_service import QRImageService
from .services.qr.qr_analytics_service import QRAnalyticsService

# New imports for Observatory-First refactoring
from .adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from .services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter
from .services.interfaces.analytics_interfaces import AnalyticsProvider, ScanEventLogger
from .services.interfaces.validation_interfaces import ValidationProvider
from .services.new_qr_generation_service import NewQRGenerationService
from .services.new_analytics_service import NewAnalyticsService
from .services.new_validation_service import NewValidationService
from .core.circuit_breaker import get_new_qr_generation_breaker

# Import for type hints
import pybreaker


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


# New dependencies for specialized QR services

def get_qr_core_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)]
) -> QRCoreService:
    """
    Dependency for getting a QRCoreService instance.
    
    Args:
        qr_code_repo: The QRCodeRepository
        
    Returns:
        An instance of QRCoreService
    """
    return QRCoreService(qr_code_repo=qr_code_repo)


def get_qr_validation_service() -> QRValidationService:
    """
    Dependency for getting a QRValidationService instance.
    
    Returns:
        An instance of QRValidationService
    """
    return QRValidationService()


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


def get_static_qr_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    validation_service: Annotated[QRValidationService, Depends(get_qr_validation_service)],
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[pybreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)]
) -> StaticQRService:
    """
    Dependency for getting a StaticQRService instance.
    
    Args:
        qr_code_repo: The QRCodeRepository
        validation_service: The QRValidationService
        new_qr_generation_service: The NewQRGenerationService
        new_qr_generation_breaker: The circuit breaker for NewQRGenerationService
        
    Returns:
        An instance of StaticQRService
    """
    return StaticQRService(
        qr_code_repo=qr_code_repo,
        validation_service=validation_service,
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker
    )


def get_dynamic_qr_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    validation_service: Annotated[QRValidationService, Depends(get_qr_validation_service)],
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[pybreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)]
) -> DynamicQRService:
    """
    Dependency for getting a DynamicQRService instance.
    
    Args:
        qr_code_repo: The QRCodeRepository
        validation_service: The QRValidationService
        new_qr_generation_service: The NewQRGenerationService
        new_qr_generation_breaker: The circuit breaker for NewQRGenerationService
        
    Returns:
        An instance of DynamicQRService
    """
    return DynamicQRService(
        qr_code_repo=qr_code_repo,
        validation_service=validation_service,
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker
    )


def get_qr_image_service(
    core_service: Annotated[QRCoreService, Depends(get_qr_core_service)],
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[pybreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)]
) -> QRImageService:
    """
    Dependency for getting a QRImageService instance.
    
    Args:
        core_service: The QRCoreService
        new_qr_generation_service: The NewQRGenerationService
        new_qr_generation_breaker: The circuit breaker for NewQRGenerationService
        
    Returns:
        An instance of QRImageService
    """
    return QRImageService(
        core_service=core_service,
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker
    )


def get_qr_analytics_service(
    qr_code_repo: Annotated[QRCodeRepository, Depends(get_qr_code_repository)],
    scan_log_repo: Annotated[ScanLogRepository, Depends(get_scan_log_repository)],
    core_service: Annotated[QRCoreService, Depends(get_qr_core_service)]
) -> QRAnalyticsService:
    """
    Dependency for getting a QRAnalyticsService instance.
    
    Args:
        qr_code_repo: The QRCodeRepository
        scan_log_repo: The ScanLogRepository
        core_service: The QRCoreService
        
    Returns:
        An instance of QRAnalyticsService
    """
    return QRAnalyticsService(
        qr_code_repo=qr_code_repo,
        scan_log_repo=scan_log_repo,
        core_service=core_service
    )


def get_qr_service(
    core_service: Annotated[QRCoreService, Depends(get_qr_core_service)],
    validation_service: Annotated[QRValidationService, Depends(get_qr_validation_service)],
    static_qr_service: Annotated[StaticQRService, Depends(get_static_qr_service)],
    dynamic_qr_service: Annotated[DynamicQRService, Depends(get_dynamic_qr_service)],
    image_service: Annotated[QRImageService, Depends(get_qr_image_service)],
    analytics_service: Annotated[QRAnalyticsService, Depends(get_qr_analytics_service)],
    new_qr_generation_service: Annotated[NewQRGenerationService, Depends(get_new_qr_generation_service)],
    new_qr_generation_breaker: Annotated[pybreaker.CircuitBreaker, Depends(get_new_qr_generation_breaker)]
) -> QRCodeService:
    """
    Dependency for getting a QRCodeService instance.
    
    Args:
        core_service: The QRCoreService for core QR operations
        validation_service: The QRValidationService for validation operations
        static_qr_service: The StaticQRService for static QR creation
        dynamic_qr_service: The DynamicQRService for dynamic QR operations
        image_service: The QRImageService for image generation
        analytics_service: The QRAnalyticsService for analytics operations
        new_qr_generation_service: The NewQRGenerationService for feature flag integration
        new_qr_generation_breaker: The circuit breaker for NewQRGenerationService
        
    Returns:
        An instance of QRCodeService with the specialized services
    """
    return QRCodeService(
        core_service=core_service,
        validation_service=validation_service,
        static_qr_service=static_qr_service,
        dynamic_qr_service=dynamic_qr_service,
        image_service=image_service,
        analytics_service=analytics_service,
        new_qr_generation_service=new_qr_generation_service,
        new_qr_generation_breaker=new_qr_generation_breaker
    )


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
    
    Note: Placeholder implementation - concrete providers will be added in future phases.
    
    Returns:
        An instance of NewValidationService (not yet fully functional)
    """
    # TODO: Implement concrete ValidationProvider adapter
    # For now, this is a placeholder that won't be used until Phase 1
    return None  # This will be updated when we have concrete implementation
