"""
API version 1 router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from ...dependencies import get_qr_service
from ...schemas import QRCodeList, QRCodeResponse, QRCodeUpdate
from ...services.qr_service import QRCodeService
from ..qr.common import logger

router = APIRouter(
    prefix="/api/v1",
    tags=["api-v1"],
)


@router.get("/qr", response_model=QRCodeList)
async def list_qr_codes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    qr_type: str | None = Query(default=None, pattern="^(static|dynamic)$"),
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    List QR codes with pagination and optional filtering.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        qr_type: Optional filter by QR code type (static or dynamic)
        qr_service: The QR code service (injected)

    Returns:
        A paginated list of QR codes
    """
    try:
        qr_codes, total = qr_service.list_qr_codes(skip=skip, limit=limit, qr_type=qr_type)

        # Convert QRCode model objects to dictionaries for Pydantic validation
        qr_code_dicts = [qr.to_dict() for qr in qr_codes]
        
        response = QRCodeList(
            items=qr_code_dicts, total=total, page=skip // limit + 1 if limit else 1, page_size=limit
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error listing QR codes")
        raise HTTPException(status_code=500, detail=f"Error listing QR codes: {str(e)}")


@router.get("/qr/{qr_id}", response_model=QRCodeResponse)
async def get_qr(qr_id: str, qr_service: QRCodeService = Depends(get_qr_service)):
    """
    Get QR code data by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        qr_service: The QR code service (injected)

    Returns:
        The QR code data
    """
    try:
        qr = qr_service.get_qr_by_id(qr_id)
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving QR code")


@router.get("/qr/{qr_id}/image")
async def get_qr_image(
    qr_id: str,
    image_format: str = Query(default="png", pattern="^(png|jpeg|jpg|svg|webp)$"),
    image_quality: int | None = Query(default=None, ge=1, le=100),
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Get QR code image by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        image_format: The format of the image (png, jpeg, jpg, svg, webp)
        image_quality: The quality of the image (1-100, for lossy formats)
        qr_service: The QR code service (injected)

    Returns:
        The QR code image
    """
    try:
        # Get the QR code
        qr = qr_service.get_qr_by_id(qr_id)

        # Generate QR code
        return qr_service.generate_qr(
            data=qr.content,
            size=qr.size,
            border=qr.border,
            fill_color=qr.fill_color,
            back_color=qr.back_color,
            image_format=image_format,
            image_quality=image_quality,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating QR code image")


@router.put("/qr/{qr_id}", response_model=QRCodeResponse)
async def update_qr(
    qr_id: str,
    qr_update: QRCodeUpdate,
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Update QR code data by ID.

    Args:
        qr_id: The ID of the QR code to update
        qr_update: The QR code data to update
        qr_service: The QR code service (injected)

    Returns:
        The updated QR code
    """
    try:
        # Only dynamic QR codes can be updated, which is enforced by the service
        qr = qr_service.update_dynamic_qr(qr_id, qr_update)
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating QR code: {str(e)}")
