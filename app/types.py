"""
Type aliases for common dependencies in the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .dependencies import (
    get_qr_code_repository, 
    get_scan_log_repository,
    get_qr_retrieval_service,
    get_qr_creation_service,
    get_qr_update_service,
    get_qr_deletion_service,
    get_qr_image_service,
    get_scan_processing_service
)
from .services.qr_retrieval_service import QRRetrievalService
from .services.qr_creation_service import QRCreationService
from .services.qr_update_service import QRUpdateService
from .services.qr_deletion_service import QRDeletionService
from .services.qr_image_service import QRImageService
from .services.scan_processing_service import ScanProcessingService

# Database session type
DbSessionDep = Annotated[Session, Depends(get_db_with_logging)]

# Repository types
QRCodeRepositoryDep = Annotated[QRCodeRepository, Depends(get_qr_code_repository)]
ScanLogRepositoryDep = Annotated[ScanLogRepository, Depends(get_scan_log_repository)]

# New atomic service types
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]
QRCreationServiceDep = Annotated[QRCreationService, Depends(get_qr_creation_service)]
QRUpdateServiceDep = Annotated[QRUpdateService, Depends(get_qr_update_service)]
QRDeletionServiceDep = Annotated[QRDeletionService, Depends(get_qr_deletion_service)]
QRImageServiceDep = Annotated[QRImageService, Depends(get_qr_image_service)]
ScanProcessingServiceDep = Annotated[ScanProcessingService, Depends(get_scan_processing_service)] 