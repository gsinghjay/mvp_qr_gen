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

from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidQRTypeError
# get_qr_service removed from here
from app.dependencies import get_qr_retrieval_service, get_qr_image_service, get_qr_update_service, get_qr_deletion_service
from app.schemas import (
    DynamicQRCreateParameters,
    QRCodeList,
    QRCodeResponse,
    QRImageParameters,
    QRListParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)
# Import the new atomic service type aliases from types.py
from app.types import (
    QRRetrievalServiceDep,
    QRImageServiceDep,
    QRCreationServiceDep,
    QRUpdateServiceDep,
    QRDeletionServiceDep
)

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
    # qr_service: QRServiceDep, # Old dependency
    qr_retrieval_service: QRRetrievalServiceDep, # New dependency
    params: QRListParameters = Depends(),
):
    """
    List QR codes with pagination and optional filtering.

    Args:
        params: Query parameters for listing QR codes
        qr_retrieval_service: The QR retrieval service (injected)

    Returns:
        A paginated list of QR codes

    Raises:
        InvalidQRTypeError: If an invalid QR type is specified
        DatabaseError: If a database error occurs
    """
    # Validate QR type if provided
    if params.qr_type and params.qr_type.value not in ["static", "dynamic"]: # This validation could also be in the service
        raise InvalidQRTypeError(f"Invalid QR type: {params.qr_type}")

    qr_codes, total = await qr_retrieval_service.list_qr_codes( # Changed to await
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
async def get_qr(qr_id: str, qr_retrieval_service: QRRetrievalServiceDep): # Changed dependency
    """
    Get QR code data by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        qr_retrieval_service: The QR retrieval service (injected)

    Returns:
        The QR code data

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        DatabaseError: If a database error occurs
    """
    return await qr_retrieval_service.get_qr_by_id(qr_id) # Changed to await

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
    qr_retrieval_service: QRRetrievalServiceDep, # Added for fetching QR content
    qr_image_service: QRImageServiceDep,       # Added for generating image
    params: QRImageParameters = Depends(),
):
    """
    Get QR code image by ID.

    Args:
        qr_id: The ID of the QR code to retrieve
        qr_retrieval_service: Service to fetch QR code data.
        qr_image_service: Service to generate QR code image.
        params: Parameters for generating the QR code image

    Returns:
        The QR code image in the requested format

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the image parameters are invalid
        DatabaseError: If a database error occurs
    """
    # Get the QR code
    qr = await qr_retrieval_service.get_qr_by_id(qr_id) # Use retrieval service

    # Generate the QR code image using the new image service
    return await qr_image_service.generate_qr_image_response(
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
        svg_description=params.svg_description,
        physical_size=params.physical_size,
        physical_unit=params.physical_unit,
        dpi=params.dpi
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
    qr_creation_service: QRCreationServiceDep # Changed dependency
):
    """
    Create a new static QR code.

    Args:
        data: The QR code data to create
        qr_creation_service: The QR creation service (injected)

    Returns:
        The created QR code

    Raises:
        QRCodeValidationError: If the QR code data is invalid
        ResourceConflictError: If a QR code with the same content already exists
        DatabaseError: If a database error occurs
    """
    # The service layer will raise appropriate exceptions that will be
    # handled by the exception handlers in main.py
    qr = await qr_creation_service.create_static_qr(data) # Use creation service
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
    qr_creation_service: QRCreationServiceDep # Changed dependency
):
    """
    Create a new dynamic QR code.

    Args:
        data: The QR code data to create
        qr_creation_service: The QR creation service (injected)

    Returns:
        The created QR code

    Raises:
        QRCodeValidationError: If the QR code data is invalid
        RedirectURLError: If the redirect URL is invalid
        DatabaseError: If a database error occurs
    """
    # The service layer will raise appropriate exceptions that will be
    # handled by the exception handlers in main.py
    qr = await qr_creation_service.create_dynamic_qr(data) # Use creation service
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
    qr_update_service: QRUpdateServiceDep, # Changed dependency
):
    """
    Update QR code data by ID.

    For dynamic QR codes, this can update the redirect_url.
    For all QR codes, this can update the title and description.

    Args:
        qr_id: The ID of the QR code to update
        qr_update: The data to update
        qr_update_service: The QR update service (injected)

    Returns:
        The updated QR code data

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        QRCodeValidationError: If the QR code data is invalid
        RedirectURLError: If the redirect URL is invalid
        DatabaseError: If a database error occurs
    """
    qr = await qr_update_service.update_qr(qr_id, qr_update) # Use update service
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
    qr_deletion_service: QRDeletionServiceDep, # Changed dependency
):
    """
    Delete QR code by ID.

    Args:
        qr_id: The ID of the QR code to delete
        qr_deletion_service: The QR deletion service (injected)

    Returns:
        204 No Content on success

    Raises:
        QRCodeNotFoundError: If the QR code is not found
        DatabaseError: If a database error occurs
    """
    qr_deletion_service.delete_qr(qr_id) # Use deletion service
    return Response(status_code=status.HTTP_204_NO_CONTENT)