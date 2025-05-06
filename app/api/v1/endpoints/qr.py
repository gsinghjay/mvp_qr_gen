"""
QR code API endpoints.

This module consolidates all QR code-related operations including:
- Listing QR codes
- Getting QR code details
- Creating static and dynamic QR codes
- Updating QR codes
- Deleting QR codes
- Generating QR code images
"""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidQRTypeError
from app.dependencies import get_qr_service
from app.schemas import (
    DynamicQRCreateParameters,
    QRCodeList,
    QRCodeResponse,
    QRImageParameters,
    QRListParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)
from app.services.qr_service import QRCodeService
from app.types import QRServiceDep

# Configure logger for QR code routes
logger = logging.getLogger("app.qr")

router = APIRouter(
    responses={
        404: {"description": "QR code not found"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)

# List QR Codes
@router.get(
    "",
    response_model=QRCodeList,
    responses={
        200: {"description": "List of QR codes"},
        400: {"description": "Invalid QR type"},
        500: {"description": "Database error"},
    },
)
async def list_qr_codes(
    qr_service: QRServiceDep,
    params: QRListParameters = Depends(),
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
        search=params.search,
        sort_by=params.sort_by,
        sort_desc=params.sort_desc,
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

# Get QR Code by ID
@router.get(
    "/{qr_id}",
    response_model=QRCodeResponse,
    responses={
        200: {"description": "QR code details"},
        404: {"description": "QR code not found"},
        500: {"description": "Database error"},
    },
)
async def get_qr(qr_id: str, qr_service: QRServiceDep):
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

# Get QR Code Image
@router.get(
    "/{qr_id}/image",
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
    qr_service: QRServiceDep,
    params: QRImageParameters = Depends(),
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
        include_logo=params.include_logo,
        error_level=params.error_level.value,
        svg_title=params.svg_title,
        svg_description=params.svg_description
    )

# Get QR Code Image (alternative URL format to support both patterns)
@router.get(
    "/image/{qr_id}",
    responses={
        200: {
            "description": "QR code image (alternative URL format)",
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
async def get_qr_image_alt(
    qr_id: str,
    qr_service: QRServiceDep,
    format: str = "png",
    size: int = 10,
    border: int = 4,
    fill_color: str | None = None,
    back_color: str | None = None,
    quality: int | None = None,
    include_logo: bool = False,
    error_level: str = "M",
    svg_title: str | None = None,
    svg_description: str | None = None,
):
    """
    Get QR code image by ID (alternative URL format).
    
    This endpoint serves the same function as /{qr_id}/image but with a different URL pattern
    to support clients that expect /image/{qr_id}.
    
    Args:
        qr_id: The ID of the QR code to retrieve
        format: Image format (png, svg, jpeg, webp)
        size: QR code size (1-100)
        border: QR code border width (0-20)
        fill_color: QR code fill color in hex format (#RRGGBB)
        back_color: QR code background color in hex format (#RRGGBB)
        quality: Image quality (1-100, for lossy formats)
        include_logo: Whether to include a logo in the QR code
        error_level: Error correction level (L, M, Q, H)
        svg_title: Title for SVG format (improves accessibility)
        svg_description: Description for SVG format (improves accessibility)
        qr_service: The QR code service (injected)
        
    Returns:
        The QR code image in the requested format
        
    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the image parameters are invalid
        DatabaseError: If a database error occurs
    """
    from app.schemas.common import ImageFormat, ErrorCorrectionLevel
    
    # Get the QR code
    qr = qr_service.get_qr_by_id(qr_id)
    
    # Map format string to ImageFormat enum
    try:
        image_format = ImageFormat(format.lower())
    except ValueError:
        image_format = ImageFormat.PNG
    
    # Map error level string to ErrorCorrectionLevel enum
    try:
        error_correction = ErrorCorrectionLevel(error_level.upper())
    except ValueError:
        error_correction = ErrorCorrectionLevel.M
    
    # Generate the QR code image
    return qr_service.generate_qr(
        data=qr.content,
        size=size,
        border=border,
        fill_color=fill_color or qr.fill_color,
        back_color=back_color or qr.back_color,
        image_format=image_format.value,
        image_quality=quality,
        include_logo=include_logo,
        error_level=error_correction.value,
        svg_title=svg_title,
        svg_description=svg_description
    )

# Create Static QR Code
@router.post(
    "/static",
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
    data: StaticQRCreateParameters, 
    qr_service: QRServiceDep
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

# Create Dynamic QR Code
@router.post(
    "/dynamic",
    response_model=QRCodeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "QR code created successfully"},
        422: {"description": "Validation error"},
        500: {"description": "Database error"},
    },
)
async def create_dynamic_qr(
    data: DynamicQRCreateParameters, 
    qr_service: QRServiceDep
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

# Update QR Code
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
async def update_qr(
    qr_id: str,
    qr_update: QRUpdateParameters,
    qr_service: QRServiceDep,
):
    """
    Update QR code data by ID.

    For dynamic QR codes, this can update the redirect_url.
    For all QR codes, this can update the title and description.

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
    qr = qr_service.update_qr(qr_id, qr_update)
    logger.info(f"Updated QR code {qr_id}")
    return qr

# Delete QR Code
@router.delete(
    "/{qr_id}",
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
    qr_service: QRServiceDep,
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