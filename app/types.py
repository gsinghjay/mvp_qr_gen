"""
Type aliases for common dependencies in the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories import QRCodeRepository, ScanLogRepository
from .services.qr_service import QRCodeService
from .dependencies import get_qr_service, get_qr_code_repository, get_scan_log_repository

# Database session type
DbSessionDep = Annotated[Session, Depends(get_db_with_logging)]

# Repository types
QRCodeRepositoryDep = Annotated[QRCodeRepository, Depends(get_qr_code_repository)]
ScanLogRepositoryDep = Annotated[ScanLogRepository, Depends(get_scan_log_repository)]

# Service types
QRServiceDep = Annotated[QRCodeService, Depends(get_qr_service)] 