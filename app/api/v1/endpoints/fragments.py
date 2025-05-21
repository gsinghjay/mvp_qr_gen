"""
Router for HTML fragment endpoints used with HTMX.
"""

import os
import math
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Annotated

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, Response
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
    title: str = Form(...),
    description: str = Form(None),
    redirect_url: str = Form(None),
    error_level: str = Form("M"),
    svg_title: str = Form(None),
    svg_description: str = Form(None),
    include_logo: bool = Form(False),
    # Physical dimension parameters are kept but not used for QR code creation
    # They're only used for response template context if provided
    physical_size: str = Form(None),
    physical_unit: str = Form(None),
    dpi: str = Form(None),
):
    """
    Create a QR code from form submission.
    
    Args:
        request: The FastAPI request object.
        qr_service: The QR code service.
        qr_type: The type of QR code (static or dynamic).
        content: The content to encode in the QR code (for static QR codes).
        title: The user-friendly title for the QR code.
        description: A detailed description of the QR code.
        redirect_url: The URL to redirect to when the QR code is scanned (for dynamic QR codes).
        error_level: The error correction level (L, M, Q, H).
        svg_title: An optional title for SVG format (improves accessibility).
        svg_description: An optional description for SVG format (improves accessibility).
        include_logo: Whether to include the default logo in the QR code.
        
    Returns:
        HTMLResponse: The rendered QR detail fragment or error message.
    """
    try:
        # Validate inputs
        logger.info(f"Creating {qr_type} QR code with title: {title}")
        
        # Convert error level to lowercase for internal processing
        error_level = error_level.lower() if error_level else "m"
        
        # Check if logo is included, if so, set error level to high
        if include_logo:
            error_level = 'h'
        
        # Create the QR code based on type
        if qr_type == "static":
            # Create enum from lowercase error_level
            error_level_enum = ErrorCorrectionLevel(error_level)
            
            # Create parameters object
            params = StaticQRCreateParameters(
                content=content,
                title=title,
                description=description,
                error_level=error_level_enum
            )
            
            qr = qr_service.create_static_qr(params)
        else:
            # Create enum from lowercase error_level
            error_level_enum = ErrorCorrectionLevel(error_level)
            
            # Create parameters object
            params = DynamicQRCreateParameters(
                redirect_url=redirect_url,
                title=title,
                description=description,
                error_level=error_level_enum
            )
            
            qr = qr_service.create_dynamic_qr(params)
        
        # Format dates for better readability
        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M")
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        
        # Handle short_id extraction for dynamic QR codes
        short_id = None
        short_url = None
        if qr.qr_type == "dynamic" and '/r/' in qr.content:
            short_id = qr.content.split('/r/')[-1]
            short_url = f"{settings.BASE_URL}/r/{short_id}"
        
        # Format error level for display (uppercase)
        error_level_display = qr.error_level.upper() if qr.error_level else "M"
        
        # Check if the QR code has been scanned
        has_scan_data = qr.scan_count > 0 if hasattr(qr, 'scan_count') else False
        
        # Return the created QR detail
        response_data = {
            "request": request,
            "qr": qr,
            "created_at_formatted": created_at_formatted,
            "last_scan_formatted": last_scan_formatted,
            "short_id": short_id,
            "short_url": short_url,
            "error_level_display": error_level_display,
            "has_scan_data": has_scan_data,
            "success_message": "QR Code created successfully!"
        }
            
        # For Option B, we return a simple 204 No Content response
        # HTMX will handle the toast and redirect via event listeners
        return Response(status_code=204)
    except ValidationError as e:
        # Return the form with validation errors
        return templates.TemplateResponse(
            "fragments/qr_form.html",
            {
                "request": request,
                "qr_type": qr_type,
                "content": content,
                "title": title,
                "description": description,
                "redirect_url": redirect_url,
                "error_level": error_level.upper() if isinstance(error_level, str) else "M",
                "svg_title": svg_title,
                "svg_description": svg_description,
                "include_logo": include_logo,
                "physical_size": physical_size,
                "physical_unit": physical_unit,
                "dpi": dpi,
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
        
        # Format dates for better readability
        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M")
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        
        # Handle short_id extraction for dynamic QR codes
        short_id = None
        short_url = None
        if qr.qr_type == "dynamic" and '/r/' in qr.content:
            # Handle both cases with and without query parameters
            path_part = qr.content.split('/r/')[-1]
            short_id = path_part.split('?')[0] if '?' in path_part else path_part
            short_url = f"{settings.BASE_URL}/r/{short_id}"
        
        # Format error level for display (uppercase)
        error_level_display = qr.error_level.upper() if qr.error_level else "M"
        
        # Check if the QR code has been scanned
        has_scan_data = qr.scan_count > 0 if hasattr(qr, 'scan_count') else False
        
        # Prepare response data
        response_data = {
            "request": request,
            "qr": qr,
            "created_at_formatted": created_at_formatted,
            "last_scan_formatted": last_scan_formatted,
            "short_id": short_id,
            "short_url": short_url,
            "error_level_display": error_level_display,
            "has_scan_data": has_scan_data
        }
        
        return templates.TemplateResponse(
            "fragments/qr_detail.html",
            response_data
        )
    except QRCodeNotFoundError:
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": f"QR code with ID {qr_id} not found."
            },
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Error retrieving QR code detail: {str(e)}")
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": "An error occurred while retrieving QR code details."
            },
            status_code=500,
        )

@router.get("/qr/{qr_id}/analytics/scan-logs", response_class=HTMLResponse)
async def get_scan_logs_fragment(
    request: Request,
    qr_id: str,
    qr_service: QRServiceDep,
    page: int = 1,
    limit: int = 10,
    genuine_only: bool = False,
):
    """
    Get the scan logs fragment for a specific QR code.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to get scan logs for.
        qr_service: The QR code service.
        page: The page number (for pagination).
        limit: The number of logs per page.
        genuine_only: Whether to include only genuine scans.
        
    Returns:
        HTMLResponse: The rendered scan logs fragment.
    """
    try:
        # Calculate offset from page number
        skip = (page - 1) * limit
        
        # Get scan logs from repository
        scan_logs, total_logs = qr_service.repository.get_scan_logs_for_qr(
            qr_id=qr_id,
            skip=skip,
            limit=limit,
            genuine_only=genuine_only
        )
        
        # Format scan log data for the template
        formatted_logs = []
        for log in scan_logs:
            formatted_logs.append({
                "id": log.id,
                "scanned_at": log.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_genuine_scan": log.is_genuine_scan,
                "device_family": log.device_family or "Unknown",
                "os_family": log.os_family or "Unknown",
                "os_version": log.os_version or "",
                "browser_family": log.browser_family or "Unknown",
                "browser_version": log.browser_version or "",
                "is_mobile": log.is_mobile,
                "is_tablet": log.is_tablet,
                "is_pc": log.is_pc,
                "is_bot": log.is_bot
            })
        
        # Calculate total pages for pagination
        total_pages = math.ceil(total_logs / limit) if total_logs > 0 else 1
        
        return templates.TemplateResponse(
            "fragments/scan_log_table.html",
            {
                "request": request,
                "qr_id": qr_id,
                "scan_logs": formatted_logs,
                "total_logs": total_logs,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "genuine_only": genuine_only
            }
        )
    except QRCodeNotFoundError:
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": f"QR code with ID {qr_id} not found."
            },
            status_code=404,
        )
    except DatabaseError as e:
        logger.error(f"Database error retrieving scan logs for QR {qr_id}: {str(e)}")
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": "An error occurred while retrieving scan logs."
            },
            status_code=500,
        )

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
    redirect_url: str = Form(None),
    title: str = Form(None),
    description: str = Form(None),
):
    """
    Update a QR code.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to update.
        qr_service: The QR code service.
        redirect_url: The new redirect URL for dynamic QR codes.
        title: The updated title for the QR code.
        description: The updated description for the QR code.
        
    Returns:
        HTMLResponse: The rendered QR detail fragment.
    """
    logger.info(f"Updating QR code {qr_id} - Title: '{title}', Description: '{description}', Redirect URL: '{redirect_url}'")
    
    try:
        # Create update parameters
        params = QRUpdateParameters(
            redirect_url=redirect_url if redirect_url else None,
            title=title,
            description=description
        )
        
        # Update the QR code
        qr = qr_service.update_qr(qr_id, params)
        logger.info(f"Successfully updated QR code {qr_id}")
        
        # Format dates for better readability
        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M")
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        
        # Handle short_id extraction for dynamic QR codes
        short_id = None
        short_url = None
        if qr.qr_type == "dynamic" and '/r/' in qr.content:
            # Handle both cases with and without query parameters
            path_part = qr.content.split('/r/')[-1]
            short_id = path_part.split('?')[0] if '?' in path_part else path_part
            short_url = f"{settings.BASE_URL}/r/{short_id}"
        
        # Format error level for display (uppercase)
        error_level_display = qr.error_level.upper() if qr.error_level else "M"
        
        # Check if the QR code has been scanned
        has_scan_data = qr.scan_count > 0 if hasattr(qr, 'scan_count') else False
        
        return templates.TemplateResponse(
            "fragments/qr_detail.html",
            {
                "request": request,
                "qr": qr,
                "created_at_formatted": created_at_formatted,
                "last_scan_formatted": last_scan_formatted,
                "short_id": short_id,
                "short_url": short_url,
                "error_level_display": error_level_display,
                "has_scan_data": has_scan_data,
                "success_message": "QR Code updated successfully!"
            }
        )
    except QRCodeNotFoundError:
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": f"QR code with ID {qr_id} not found."
            },
            status_code=404,
        )
    except ValidationError as e:
        # Get the original QR code for the form
        try:
            qr = qr_service.get_qr_by_id(qr_id)
            return templates.TemplateResponse(
                "fragments/qr_edit.html",
                {
                    "request": request,
                    "qr": qr,
                    "redirect_url": redirect_url,
                    "title": title,
                    "description": description,
                    "error_messages": e.errors()
                }
            )
        except Exception:
            return templates.TemplateResponse(
                "fragments/error.html",
                {
                    "request": request,
                    "error": "An error occurred while retrieving the QR code for editing."
                },
                status_code=500,
            )
    except Exception as e:
        logger.error(f"Error updating QR code: {str(e)}")
        return templates.TemplateResponse(
            "fragments/error.html",
            {
                "request": request,
                "error": f"An error occurred while updating the QR code: {str(e)}"
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