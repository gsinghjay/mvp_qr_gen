import logging
import math # For pagination calculations
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import DatabaseError
# Import specific service dependencies needed
from app.services.qr_retrieval_service import QRRetrievalService
from app.dependencies import get_qr_retrieval_service

# Dependency types
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

# Templates setup
def get_base_template_context(request: Request) -> dict:
    return {
        "request": request,
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR / "fragments"),
    context_processors=[get_base_template_context],
)

logger = logging.getLogger("app.qr_list_fragments")
router = APIRouter(
    prefix="/fragments", # Common prefix
    tags=["Fragments - QR Lists"],
    responses={404: {"description": "Not found"}},
)

@router.get("/qr-list", response_class=HTMLResponse)
async def get_qr_list_fragment(
    request: Request,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed dependency
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    """ Get QR code list fragment. (Moved from fragments.py) """
    try:
        skip = (page - 1) * limit
        # Convert sort_order to sort_desc boolean
        sort_desc = sort_order == "desc"
        
        qr_codes, total_count = await qr_retrieval_service.list_qr_codes(
            skip=skip, limit=limit, search=search, sort_by=sort_by, sort_desc=sort_desc
        )

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        return templates.TemplateResponse(
            "qr_list.html",
            {
                "request": request,
                "qr_codes": qr_codes, 
                "total_count": total_count,
                "total": total_count,  # Template expects 'total'
                "page": page, "limit": limit, "total_pages": total_pages, 
                "search": search, "sort_by": sort_by, "sort_order": sort_order
            }
        )
    except DatabaseError as e:
        logger.error(f"Database error retrieving QR list: {str(e)}")
        return templates.TemplateResponse(
            "qr_list.html",
            {
                "request": request,
                "qr_codes": [], 
                "total_count": 0,
                "total": 0,  # Template expects 'total'
                "page": page, "limit": limit, "total_pages": 1, 
                "search": search, "sort_by": sort_by, "sort_order": sort_order,
                "error": "An error occurred while retrieving QR codes."
            },
            status_code=500
        )

@router.get("/qr-list-pagination", response_class=HTMLResponse)
async def get_qr_list_pagination_fragment(
    request: Request,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed dependency
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    """ Get QR code list pagination fragment. (Moved from fragments.py) """
    try:
        skip = (page - 1) * limit
        _, total_count = await qr_retrieval_service.list_qr_codes(
            skip=skip, limit=limit, search=search
        )

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        return templates.TemplateResponse(
            "pagination.html",
            {
                "request": request,
                "total_count": total_count,
                "page": page, "limit": limit, "total_pages": total_pages, 
                "search": search, "sort_by": sort_by, "sort_order": sort_order
            }
        )
    except DatabaseError as e:
        logger.error(f"Database error retrieving QR list pagination: {str(e)}")
        return templates.TemplateResponse(
            "pagination.html",
            {
                "request": request,
                "total_count": 0,
                "page": page, "limit": limit, "total_pages": 1, 
                "search": search, "sort_by": sort_by, "sort_order": sort_order,
                "error": "An error occurred while retrieving pagination data."
            },
            status_code=500
        )
