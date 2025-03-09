"""
API version 1 router.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ...dependencies import get_qr_service
from ...schemas import (
    QRCodeList, 
    QRCodeResponse, 
    QRCodeUpdate,
    QRListParameters,
    QRImageParameters,
    QRUpdateParameters,
)
from ...services.qr_service import QRCodeService
from ..qr.common import logger

router = APIRouter(
    prefix="/api/v1",
    tags=["api-v1"],
)


@router.get("/qr", response_model=QRCodeList)
async def list_qr_codes(
    params: QRListParameters = Depends(),
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    List QR codes with pagination and optional filtering.

    Args:
        params: Query parameters for listing QR codes
        qr_service: The QR code service (injected)

    Returns:
        A paginated list of QR codes
    """
    try:
        qr_codes, total = qr_service.list_qr_codes(
            skip=params.skip, 
            limit=params.limit, 
            qr_type=params.qr_type.value if params.qr_type else None
        )

        # Convert QRCode model objects to dictionaries for Pydantic validation
        qr_code_dicts = [qr.to_dict() for qr in qr_codes]
        
        response = QRCodeList(
            items=qr_code_dicts, 
            total=total, 
            page=params.skip // params.limit + 1 if params.limit else 1, 
            page_size=params.limit
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
    params: QRImageParameters = Depends(),
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Get QR code image by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        params: Query parameters for image generation
        qr_service: The QR code service (injected)

    Returns:
        The QR code image
    """
    try:
        # Add debug logging
        logger.debug(f"Getting QR image for ID: {qr_id}")
        logger.debug(f"Image format: {params.image_format}")
        logger.debug(f"Image format value: {params.image_format.value}")
        logger.debug(f"Image quality: {params.image_quality}")
        
        # Get the QR code
        qr = qr_service.get_qr_by_id(qr_id)
        logger.debug(f"QR code retrieved: {qr.id}")

        # Generate QR code
        return qr_service.generate_qr(
            data=qr.content,
            size=qr.size,
            border=qr.border,
            fill_color=qr.fill_color,
            back_color=qr.back_color,
            image_format=params.image_format.value,
            image_quality=params.image_quality,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating QR code image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating QR code image: {str(e)}")


@router.put("/qr/{qr_id}", response_model=QRCodeResponse)
async def update_qr(
    qr_id: str,
    qr_update: QRUpdateParameters,
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


@router.delete("/qr/{qr_id}", status_code=204, response_class=Response)
async def delete_qr(
    qr_id: str,
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Delete a QR code by ID.

    Args:
        qr_id: The ID of the QR code to delete
        qr_service: The QR code service (injected)

    Returns:
        No content (204)
    """
    try:
        qr_service.delete_qr(qr_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting QR code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting QR code: {str(e)}")
