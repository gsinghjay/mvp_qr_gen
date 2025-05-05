"""
Router for HTML fragment endpoints used with HTMX.
"""

import os
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Annotated

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.types import DbSessionDep, QRServiceDep
from app.core.config import settings
from app.core.exceptions import DatabaseError, QRCodeNotFoundError
from app.models import QRCode
from app.schemas.qr.parameters import ErrorCorrectionLevel, StaticQRCreateParameters, DynamicQRCreateParameters, QRUpdateParameters

# Configure logger
import logging
logger = logging.getLogger("app.api.fragments")

# Configure templates
templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
)

router = APIRouter(
    prefix="/fragments",
    tags=["HTMX Fragments"],
    responses={404: {"description": "Not found"}},
)

@router.get("/qr-list", response_class=HTMLResponse)
async def get_qr_list_fragment(
    request: Request,
    qr_service: QRServiceDep,
    page: int = 1,
    limit: int = 10,
    search: str = "",
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """
    Get the QR code list fragment.
    
    Args:
        request: The FastAPI request object.
        qr_service: The QR code service.
        page: The page number.
        limit: The number of items per page.
        search: The search query.
        sort_by: The field to sort by.
        sort_order: The sort order.
        
    Returns:
        HTMLResponse: The rendered QR list fragment.
    """
    try:
        # Get QR codes with pagination, filtering, and sorting
        qr_codes, total = qr_service.list_qr_codes(
            skip=(page - 1) * limit, 
            limit=limit, 
            search=search,
            sort_by=sort_by,
            sort_desc=sort_order.lower() == "desc"  # Convert sort_order to sort_desc boolean
        )
        
        return templates.TemplateResponse(
            "fragments/qr_list.html",
            {
                "request": request,
                "qr_codes": qr_codes,
                "page": page,
                "limit": limit,
                "search": search,
                "total": total,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "total_pages": math.ceil(total / limit)
            }
        )
    except DatabaseError as e:
        logger.error("Database error in QR list fragment", extra={"error": str(e)})
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": "Unable to load QR code data"
            },
            status_code=500,
        )

@router.get("/qr-form/{qr_type}", response_class=HTMLResponse)
async def get_qr_form_fragment(
    request: Request,
    qr_type: str,
):
    """
    Get the QR code creation form fragment.
    
    Args:
        request: The FastAPI request object.
        qr_type: The type of QR code to create ("static" or "dynamic").
        
    Returns:
        HTMLResponse: The rendered QR form fragment.
    """
    if qr_type not in ["static", "dynamic"]:
        raise HTTPException(status_code=400, detail="Invalid QR type")
    
    return templates.TemplateResponse(
        "fragments/qr_form.html",
        {
            "request": request,
            "qr_type": qr_type,
            # Note: We display uppercase error levels in the UI for better readability,
            # but they are converted to lowercase in the create_qr_code endpoint
            # to match the ErrorCorrectionLevel enum values
            "error_levels": ["L", "M", "Q", "H"]
        }
    )

@router.post("/qr-create", response_class=HTMLResponse)
async def create_qr_code(
    request: Request,
    qr_service: QRServiceDep,
    qr_type: str = Form(...),
    content: str = Form(None),
    redirect_url: str = Form(None),
    error_level: str = Form("M"),
    svg_title: str = Form(None),
    svg_description: str = Form(None),
    include_logo: bool = Form(False),
):
    """
    Create a new QR code.
    
    Args:
        request: The FastAPI request object.
        qr_service: The QR code service.
        qr_type: The type of QR code to create ("static" or "dynamic").
        content: The content for static QR codes.
        redirect_url: The redirect URL for dynamic QR codes.
        error_level: The error correction level.
        svg_title: The SVG title for accessibility.
        svg_description: The SVG description for accessibility.
        include_logo: Whether to include the organization logo.
        
    Returns:
        HTMLResponse: The rendered QR detail fragment.
    """
    try:
        # Convert error_level to lowercase to match the enum values
        error_level = error_level.lower()
        
        # Force high error correction level if including logo
        if include_logo and error_level != 'h':
            error_level = 'h'
        
        # Create the QR code based on type
        if qr_type == "static":
            # Create enum from lowercase error_level
            error_level_enum = ErrorCorrectionLevel(error_level)
            
            # Create parameters object
            params = StaticQRCreateParameters(
                content=content,
                error_level=error_level_enum
            )
            
            qr = qr_service.create_static_qr(params)
        else:
            # Create enum from lowercase error_level
            error_level_enum = ErrorCorrectionLevel(error_level)
            
            # Create parameters object
            params = DynamicQRCreateParameters(
                redirect_url=redirect_url,
                error_level=error_level_enum
            )
            
            qr = qr_service.create_dynamic_qr(params)
        
        # Return the created QR detail
        return templates.TemplateResponse(
            "fragments/qr_detail.html",
            {
                "request": request,
                "qr": qr,
                "success_message": "QR Code created successfully!"
            }
        )
    except ValidationError as e:
        # Return the form with validation errors
        return templates.TemplateResponse(
            "fragments/qr_form.html",
            {
                "request": request,
                "qr_type": qr_type,
                "content": content,
                "redirect_url": redirect_url,
                "error_level": error_level.upper(),
                "svg_title": svg_title,
                "svg_description": svg_description,
                "include_logo": include_logo,
                "error_messages": e.errors(),
                "error_levels": ["L", "M", "Q", "H"]
            }
        )
    except Exception as e:
        logger.error(f"Error creating QR code: {str(e)}")
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": str(e)
            },
            status_code=500,
        )

@router.get("/qr-detail/{qr_id}", response_class=HTMLResponse)
async def get_qr_detail_fragment(
    request: Request,
    qr_id: str,
    qr_service: QRServiceDep,
):
    """
    Get the QR code detail fragment.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code.
        qr_service: The QR code service.
        
    Returns:
        HTMLResponse: The rendered QR detail fragment.
    """
    try:
        qr = qr_service.get_qr_by_id(qr_id)
        return templates.TemplateResponse(
            "fragments/qr_detail.html",
            {
                "request": request,
                "qr": qr
            }
        )
    except QRCodeNotFoundError:
        raise HTTPException(status_code=404, detail="QR code not found")

@router.get("/qr-edit/{qr_id}", response_class=HTMLResponse)
async def get_qr_edit_fragment(
    request: Request,
    qr_id: str,
    qr_service: QRServiceDep,
):
    """
    Get the QR code edit form fragment.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code.
        qr_service: The QR code service.
        
    Returns:
        HTMLResponse: The rendered QR edit form fragment.
    """
    try:
        qr = qr_service.get_qr_by_id(qr_id)
        if qr.qr_type != "dynamic":
            raise HTTPException(status_code=400, detail="Only dynamic QR codes can be edited")
        
        return templates.TemplateResponse(
            "fragments/qr_edit.html",
            {
                "request": request,
                "qr": qr
            }
        )
    except QRCodeNotFoundError:
        raise HTTPException(status_code=404, detail="QR code not found")

@router.post("/qr-update/{qr_id}", response_class=HTMLResponse)
async def update_qr_code(
    request: Request,
    qr_id: str,
    qr_service: QRServiceDep,
    redirect_url: str = Form(...),
):
    """
    Update a QR code.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code.
        qr_service: The QR code service.
        redirect_url: The new redirect URL.
        
    Returns:
        HTMLResponse: The rendered QR detail fragment.
    """
    try:
        # Create update parameters object
        params = QRUpdateParameters(
            redirect_url=redirect_url
        )
        
        # Update QR code using service
        qr = qr_service.update_dynamic_qr(qr_id, params)
        
        return templates.TemplateResponse(
            "fragments/qr_detail.html",
            {
                "request": request,
                "qr": qr,
                "success_message": "QR Code updated successfully!"
            }
        )
    except ValidationError as e:
        qr = qr_service.get_qr_by_id(qr_id)
        return templates.TemplateResponse(
            "fragments/qr_edit.html",
            {
                "request": request,
                "qr": qr,
                "redirect_url": redirect_url,
                "error_messages": e.errors()
            }
        )
    except Exception as e:
        logger.error(f"Error updating QR code: {str(e)}")
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": str(e)
            },
            status_code=500,
        )

@router.get("/pagination", response_class=HTMLResponse)
async def get_pagination_fragment(
    request: Request,
    page: int = 1,
    limit: int = 10,
    total: int = 0,
    resource: str = "qr-list",
):
    """
    Get the pagination fragment.
    
    Args:
        request: The FastAPI request object.
        page: The current page number.
        limit: The number of items per page.
        total: The total number of items.
        resource: The resource being paginated.
        
    Returns:
        HTMLResponse: The rendered pagination fragment.
    """
    total_pages = math.ceil(total / limit)
    
    return templates.TemplateResponse(
        "fragments/pagination.html",
        {
            "request": request,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "resource": resource
        }
    ) 