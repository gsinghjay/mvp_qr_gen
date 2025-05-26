"""
Type aliases for common dependencies in the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService
from .dependencies import (
    get_qr_service,
    get_qr_code_repository,
    get_scan_log_repository,
    get_qr_core_service,
    get_qr_validation_service,
    get_static_qr_service,
    get_dynamic_qr_service,
    get_qr_image_service,
    get_qr_analytics_service
)

# Specialized QR service imports
from .services.qr.qr_core_service import QRCoreService
from .services.qr.qr_validation_service import QRValidationService
from .services.qr.static_qr_service import StaticQRService
from .services.qr.dynamic_qr_service import DynamicQRService
from .services.qr.qr_image_service import QRImageService
from .services.qr.qr_analytics_service import QRAnalyticsService

# Database session type
DbSessionDep = Annotated[Session, Depends(get_db_with_logging)]

# Repository types
QRCodeRepositoryDep = Annotated[QRCodeRepository, Depends(get_qr_code_repository)]
ScanLogRepositoryDep = Annotated[ScanLogRepository, Depends(get_scan_log_repository)]

# Service types
QRServiceDep = Annotated[QRCodeService, Depends(get_qr_service)]

# Specialized QR service types
QRCoreServiceDep = Annotated[QRCoreService, Depends(get_qr_core_service)]
QRValidationServiceDep = Annotated[QRValidationService, Depends(get_qr_validation_service)]
StaticQRServiceDep = Annotated[StaticQRService, Depends(get_static_qr_service)]
DynamicQRServiceDep = Annotated[DynamicQRService, Depends(get_dynamic_qr_service)]
QRImageServiceDep = Annotated[QRImageService, Depends(get_qr_image_service)]
QRAnalyticsServiceDep = Annotated[QRAnalyticsService, Depends(get_qr_analytics_service)] 