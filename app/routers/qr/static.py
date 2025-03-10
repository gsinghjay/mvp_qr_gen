"""
Router for static QR code operations.
"""

from fastapi import APIRouter, Depends, status

from ...core.exceptions import (
    QRCodeNotFoundError,
    QRCodeValidationError,
    DatabaseError,
    ResourceConflictError,
)
from ...dependencies import get_qr_service
from ...schemas import QRCodeResponse, StaticQRCreateParameters
from ...services.qr_service import QRCodeService
from .common import logger

router = APIRouter(
    prefix="/static",
    tags=["Static QR"],
    responses={
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)


@router.post(
    "", 
    response_model=QRCodeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "QR code created successfully"},
        422: {"description": "Validation error"},
        409: {"description": "Resource conflict"},
        500: {"description": "Database error"},
    },
)
async def create_static_qr(
    data: StaticQRCreateParameters, qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Create a new static QR code.

    Args:
        data: The QR code data to create
        qr_service: The QR code service (injected)

    Returns:
        The created QR code

    Raises:
        QRCodeValidationError: If the QR code data is invalid
        ResourceConflictError: If a QR code with the same content already exists
        DatabaseError: If a database error occurs
    """
    # The service layer will raise appropriate exceptions that will be
    # handled by the exception handlers in main.py
    qr = qr_service.create_static_qr(data)
    logger.info("Created static QR code", extra={"qr_id": qr.id})
    return qr
