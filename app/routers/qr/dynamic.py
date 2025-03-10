"""
Router for dynamic QR code operations.
"""

from fastapi import APIRouter, Depends, status

from ...core.exceptions import (
    QRCodeNotFoundError,
    QRCodeValidationError,
    DatabaseError,
    RedirectURLError,
)
from ...dependencies import get_qr_service
from ...schemas import QRCodeResponse, DynamicQRCreateParameters, QRUpdateParameters
from ...services.qr_service import QRCodeService
from .common import logger

router = APIRouter(
    prefix="/api/v1/qr/dynamic",
    tags=["dynamic-qr"],
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
        500: {"description": "Database error"},
    },
)
async def create_dynamic_qr(
    data: DynamicQRCreateParameters, qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Create a new dynamic QR code.

    Args:
        data: The QR code data to create
        qr_service: The QR code service (injected)

    Returns:
        The created QR code

    Raises:
        QRCodeValidationError: If the QR code data is invalid
        RedirectURLError: If the redirect URL is invalid
        DatabaseError: If a database error occurs
    """
    # The service layer will raise appropriate exceptions that will be
    # handled by the exception handlers in main.py
    qr = qr_service.create_dynamic_qr(data)
    logger.info("Created dynamic QR code", extra={"qr_id": qr.id})
    return qr


@router.put(
    "/{qr_id}", 
    response_model=QRCodeResponse,
    responses={
        200: {"description": "QR code updated successfully"},
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)
async def update_dynamic_qr(
    qr_id: str, data: QRUpdateParameters, qr_service: QRCodeService = Depends(get_qr_service)
):
    """
    Update a dynamic QR code's redirect URL.

    Args:
        qr_id: The ID of the QR code to update
        data: The QR code data to update
        qr_service: The QR code service (injected)

    Returns:
        The updated QR code

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the QR code data is invalid
        RedirectURLError: If the redirect URL is invalid
        DatabaseError: If a database error occurs
    """
    # The service layer will raise appropriate exceptions that will be
    # handled by the exception handlers in main.py
    qr = qr_service.update_dynamic_qr(qr_id, data)
    logger.info(f"Updated QR code {qr_id} with new redirect URL")
    return qr
