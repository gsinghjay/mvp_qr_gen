import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.schemas.qr import QRListParameters # For pagination params
from app.services.qr_retrieval_service import QRRetrievalService
from app.dependencies import get_qr_retrieval_service
from app.core.exceptions import InvalidQRTypeError, DatabaseError # For error handling

# Dependency type
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

import math # For pagination
from datetime import datetime # For current_year

# Templates setup
def get_base_template_context(request: Request) -> dict:
    return {
        "request": request,
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year, # Corrected
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR / "fragments"),
    context_processors=[get_base_template_context],
)

logger = logging.getLogger("app.qr_list_fragments")
router = APIRouter(
    prefix="/fragments",
    tags=["Fragments - QR List"],
    responses={404: {"description": "Not found"}},
)

@router.get("/qr-list", response_class=HTMLResponse)
async def get_qr_list_fragment(
    request: Request,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed from qr_service
    page: int = 1,
    limit: int = 10,
    search: str = "",
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """ Get the QR code list fragment. (Moved from fragments.py) """
    try:
        qr_codes, total = await qr_retrieval_service.list_qr_codes( # Changed from qr_service and added await
            skip=(page - 1) * limit,
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_order.lower() == "desc"
        )

        return templates.TemplateResponse(
            "qr_list.html", # Assuming template name is qr_list.html in fragments folder
            {
                "qr_codes": qr_codes,
                "page": page,
                "limit": limit,
                "search": search,
                "total": total,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "total_pages": math.ceil(total / limit) if limit > 0 else 1
            }
        )
    except DatabaseError as e: # Assuming DatabaseError is relevant here
        logger.error("Database error in QR list fragment", extra={"error": str(e)})
        return templates.TemplateResponse(
            "error.html", # Assuming error.html in fragments folder
            {"error": "Unable to load QR code data"},
            status_code=500,
        )

@router.get("/pagination", response_class=HTMLResponse)
async def get_pagination_fragment(
    request: Request,
    page: int = 1,
    limit: int = 10,
    total: int = 0,
    resource: str = "qr-list", # Default resource, can be overridden
):
    """ Get the pagination fragment. (Moved from fragments.py) """
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    return templates.TemplateResponse(
        "pagination.html", # Assuming pagination.html in fragments folder
        {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "resource": resource
        }
    )
