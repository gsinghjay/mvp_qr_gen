"""
Router for static QR code operations.
"""

from fastapi import APIRouter, Depends, HTTPException

from ...dependencies import get_qr_service
from ...schemas import QRCodeCreate, QRCodeResponse
from ...services.qr_service import QRCodeService
from .common import logger

router = APIRouter(
    prefix="/api/v1/qr/static",
    tags=["static-qr"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=QRCodeResponse)
async def create_static_qr(data: QRCodeCreate, qr_service: QRCodeService = Depends(get_qr_service)):
    """
    Create a new static QR code.

    Args:
        data: The QR code data to create
        qr_service: The QR code service (injected)

    Returns:
        The created QR code
    """
    try:
        qr = qr_service.create_static_qr(data)
        logger.info("Created static QR code", extra={"qr_id": qr.id})
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error creating static QR code")
        raise HTTPException(status_code=500, detail=f"Error creating QR code: {str(e)}")
