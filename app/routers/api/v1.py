"""
API version 1 router.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from ...core.exceptions import (
    InvalidQRTypeError,
)
from ...dependencies import get_qr_service
from ...schemas import (
    QRCodeList,
    QRCodeResponse,
    QRImageParameters,
    QRListParameters,
    QRUpdateParameters,
)
from ...services.qr_service import QRCodeService

router = APIRouter(
    prefix="/v1",
    tags=["API v1"],
    responses={
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)


@router.get(
    "/qr",
    response_model=QRCodeList,
    responses={
        200: {"description": "List of QR codes"},
        400: {"description": "Invalid QR type"},
        500: {"description": "Database error"},
    },
)
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

    Raises:
        InvalidQRTypeError: If an invalid QR type is specified
        DatabaseError: If a database error occurs
    """
    # Validate QR type if provided
    if params.qr_type and params.qr_type.value not in ["static", "dynamic"]:
        raise InvalidQRTypeError(f"Invalid QR type: {params.qr_type}")

    qr_codes, total = qr_service.list_qr_codes(
        skip=params.skip,
        limit=params.limit,
        qr_type=params.qr_type.value if params.qr_type else None,
    )

    # Convert QRCode model objects to dictionaries for Pydantic validation
    qr_code_dicts = [qr.to_dict() for qr in qr_codes]

    # Calculate page and page_size for pagination
    page = (params.skip // params.limit) + 1 if params.limit > 0 else 1
    page_size = params.limit

    return {
        "items": qr_code_dicts,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/qr/{qr_id}",
    response_model=QRCodeResponse,
    responses={
        200: {"description": "QR code details"},
        404: {"description": "QR code not found"},
        500: {"description": "Database error"},
    },
)
async def get_qr(qr_id: str, qr_service: QRCodeService = Depends(get_qr_service)):
    """
    Get QR code data by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        qr_service: The QR code service (injected)

    Returns:
        The QR code data

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        DatabaseError: If a database error occurs
    """
    return qr_service.get_qr_by_id(qr_id)


@router.get(
    "/qr/{qr_id}/image",
    responses={
        200: {
            "description": "QR code image",
            "content": {
                "image/png": {},
                "image/jpeg": {},
                "image/svg+xml": {},
                "image/webp": {},
            },
        },
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)
async def get_qr_image(
    qr_id: str,
    params: QRImageParameters = Depends(),
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Get QR code image by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        params: Parameters for generating the QR code image
        qr_service: The QR code service (injected)

    Returns:
        The QR code image in the requested format

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the image parameters are invalid
        DatabaseError: If a database error occurs
    """
    # Get the QR code
    qr = qr_service.get_qr_by_id(qr_id)

    # Generate the QR code image
    return qr_service.generate_qr(
        data=qr.content,
        size=params.size,
        border=params.border,
        fill_color=params.fill_color or qr.fill_color,
        back_color=params.back_color or qr.back_color,
        image_format=params.image_format.value,
        image_quality=params.image_quality,
    )


@router.put(
    "/qr/{qr_id}",
    response_model=QRCodeResponse,
    responses={
        200: {"description": "QR code updated successfully"},
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)
async def update_qr(
    qr_id: str,
    qr_update: QRUpdateParameters,
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Update QR code data by ID.

    Currently only supports updating the redirect_url field for dynamic QR codes.

    Args:
        qr_id: The ID of the QR code to update
        qr_update: The data to update
        qr_service: The QR code service (injected)

    Returns:
        The updated QR code data

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the QR code data is invalid
        RedirectURLError: If the redirect URL is invalid
        DatabaseError: If a database error occurs
    """
    return qr_service.update_dynamic_qr(qr_id, qr_update)


@router.delete(
    "/qr/{qr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        204: {"description": "QR code deleted successfully"},
        404: {"description": "QR code not found"},
        500: {"description": "Database error"},
    },
)
async def delete_qr(
    qr_id: str,
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Delete QR code by ID.

    Args:
        qr_id: The ID of the QR code to delete
        qr_service: The QR code service (injected)

    Returns:
        204 No Content on success

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        DatabaseError: If a database error occurs
    """
    qr_service.delete_qr(qr_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
