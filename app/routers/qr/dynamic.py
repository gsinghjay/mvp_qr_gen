"""
Router for dynamic QR code operations.
"""

from fastapi import APIRouter, Depends, HTTPException

from ...dependencies import get_qr_service
from ...schemas import QRCodeResponse, DynamicQRCreateParameters, QRUpdateParameters
from ...services.qr_service import QRCodeService
from .common import logger

router = APIRouter(
    prefix="/api/v1/qr/dynamic",
    tags=["dynamic-qr"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=QRCodeResponse)
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
    """
    try:
        qr = qr_service.create_dynamic_qr(data)
        logger.info("Created dynamic QR code", extra={"qr_id": qr.id})
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error creating dynamic QR code")
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")


@router.put("/{qr_id}", response_model=QRCodeResponse)
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
    """
    try:
        qr = qr_service.update_dynamic_qr(qr_id, data)
        logger.info(f"Updated QR code {qr_id} with new redirect URL")
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating QR code: {str(e)}")
