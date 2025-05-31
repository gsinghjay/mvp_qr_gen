"""
Dependency injection functions for the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService
# Import new specialized services
from .services.qr_management_service import QRManagementService
from .services.qr_image_service import QRImageService
from .services.qr_analytics_service import QRAnalyticsService
from .services.qr_validation_service import QRValidationService

# New imports for Observatory-First refactoring (some may be reused or adapted)
from .adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from .services.interfaces.qr_generation_interfaces import QRCodeGenerator, QRImageFormatter
# from .services.interfaces.analytics_interfaces import AnalyticsProvider, ScanEventLogger # Analytics providers might be internal to QRAnalyticsService now
# from .services.interfaces.validation_interfaces import ValidationProvider # Validation providers might be internal to QRValidationService now
from .services.new_qr_generation_service import NewQRGenerationService # This is used by QRImageService
# from .services.new_analytics_service import NewAnalyticsService # This was a placeholder
# from .services.new_validation_service import NewValidationService # This was a placeholder

# Circuit breaker imports
import aiobreaker
from .core.circuit_breaker import get_new_qr_generation_breaker # Used by QRImageService
from .core.config import settings # For passing settings to services if needed


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


def get_scan_log_repository(db: Session = Depends(get_db_with_logging)) -> ScanLogRepository:
    """
    Dependency for getting a ScanLogRepository instance.
    
    Args:
        db: The database session (injected via FastAPI's dependency system)
        
    Returns:
        An instance of ScanLogRepository with the database session
    """
    return ScanLogRepository(db)


# Dependencies for specialized services

def get_qr_validation_service() -> QRValidationService:
    """
    Dependency for getting a QRValidationService instance.
    """
    return QRValidationService()

# NewQRGenerationService and its breaker are direct dependencies for QRImageService
# get_segno_qr_generator and get_pillow_qr_formatter are dependencies for NewQRGenerationService

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
    generator: QRCodeGenerator = Depends(get_segno_qr_generator),
    formatter: QRImageFormatter = Depends(get_pillow_qr_formatter),
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

def get_qr_image_service(
    new_qr_gen_service: NewQRGenerationService = Depends(get_new_qr_generation_service),
    breaker: aiobreaker.CircuitBreaker = Depends(get_new_qr_generation_breaker)
) -> QRImageService:
    """
    Dependency for getting a QRImageService instance.
    """
    return QRImageService(
        new_qr_generation_service=new_qr_gen_service,
        new_qr_generation_breaker=breaker,
        app_settings=settings # Pass global settings
    )

def get_qr_analytics_service(
    qr_repo: QRCodeRepository = Depends(get_qr_code_repository),
    scan_repo: ScanLogRepository = Depends(get_scan_log_repository)
) -> QRAnalyticsService:
    """
    Dependency for getting a QRAnalyticsService instance.
    """
    return QRAnalyticsService(qr_code_repo=qr_repo, scan_log_repo=scan_repo)

def get_qr_management_service(
    qr_repo: QRCodeRepository = Depends(get_qr_code_repository),
    validation_service: QRValidationService = Depends(get_qr_validation_service),
    image_service: QRImageService = Depends(get_qr_image_service)
    # scan_log_repo is not directly needed by QRManagementService if scan updates are in QRAnalyticsService
) -> QRManagementService:
    """
    Dependency for getting a QRManagementService instance.
    """
    return QRManagementService(
        qr_code_repo=qr_repo,
        qr_validation_service=validation_service,
        qr_image_service=image_service
    )

def get_qr_service( # This is the Facade QRCodeService
    qr_management_service: QRManagementService = Depends(get_qr_management_service),
    qr_image_service: QRImageService = Depends(get_qr_image_service),
    qr_analytics_service: QRAnalyticsService = Depends(get_qr_analytics_service),
    qr_validation_service: QRValidationService = Depends(get_qr_validation_service)
) -> QRCodeService:
    """
    Dependency for getting the main QRCodeService facade instance.
    It now aggregates the specialized services.
    
    Args:
        qr_management_service: Instance of QRManagementService
        qr_image_service: Instance of QRImageService
        qr_analytics_service: Instance of QRAnalyticsService
        qr_validation_service: Instance of QRValidationService

    Returns:
        An instance of the QRCodeService facade.
    """
    return QRCodeService(
        qr_management_service=qr_management_service,
        qr_image_service=qr_image_service,
        qr_analytics_service=qr_analytics_service,
        qr_validation_service=qr_validation_service,
        app_settings=settings # Pass global settings if QRCodeService facade needs it
    )

# Remove old get_new_analytics_service and get_new_validation_service
# as they were placeholders and their roles are now covered by the new specialized services.
# The TODOs within them are addressed by the creation of QRAnalyticsService and QRValidationService.
