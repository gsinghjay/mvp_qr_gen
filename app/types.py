"""
Type aliases for common dependencies in the QR code generator application.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db_with_logging
from .repositories.qr_repository import QRCodeRepository
from .services.qr_service import QRCodeService
from .dependencies import get_qr_repository, get_qr_service

# Database session type
DbSessionDep = Annotated[Session, Depends(get_db_with_logging)]

# Repository types
QRRepositoryDep = Annotated[QRCodeRepository, Depends(get_qr_repository)]

# Service types
QRServiceDep = Annotated[QRCodeService, Depends(get_qr_service)] 