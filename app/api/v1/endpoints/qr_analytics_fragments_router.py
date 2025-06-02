import logging
import math # For pagination if any list fragments are moved here later
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse # JSONResponse for scan-timeseries
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.core.config import settings
# Import specific service dependencies needed
from app.services.scan_processing_service import ScanProcessingService
from app.dependencies import get_scan_processing_service
from app.services.qr_retrieval_service import QRRetrievalService
from app.dependencies import get_qr_retrieval_service
from app.core.exceptions import QRCodeNotFoundError, DatabaseError

# Dependency types
ScanProcessingServiceDep = Annotated[ScanProcessingService, Depends(get_scan_processing_service)]
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

from app.models import QRCode # For type hint if get_qr_by_id returns this directly

logger = logging.getLogger("app.qr_analytics_fragments")
router = APIRouter(
    prefix="/fragments", # Common prefix
    tags=["Fragments - QR Analytics & Options"],
    responses={404: {"description": "Not found"}},
)

@router.get("/qr/{qr_id}/analytics/scan-logs", response_class=HTMLResponse)
async def get_scan_logs_fragment(
    request: Request,
    qr_id: str,
    scan_processing_service: ScanProcessingServiceDep, # Changed dependency
    page: int = 1,
    limit: int = 10,
    genuine_only: bool = False,
):
    """ Get scan logs fragment. (Moved from fragments.py) """
    try:
        skip = (page - 1) * limit
        # Assuming ScanProcessingService will have a method to get scan logs
        # or direct access to scan_log_repo is maintained if ScanProcessingService doesn't wrap this exact call.
        # For now, using scan_log_repo directly via the service as in original fragments.py.
        # This might be further refactored in ScanProcessingService itself.
        scan_logs, total_logs = scan_processing_service.scan_log_repo.get_scan_logs_for_qr(
            qr_id=qr_id, skip=skip, limit=limit, genuine_only=genuine_only
        )

        formatted_logs = [{
            "id": log.id, "scanned_at": log.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_genuine_scan": log.is_genuine_scan, "device_family": log.device_family or "Unknown",
            "os_family": log.os_family or "Unknown", "os_version": log.os_version or "",
            "browser_family": log.browser_family or "Unknown", "browser_version": log.browser_version or "",
            "is_mobile": log.is_mobile, "is_tablet": log.is_tablet, "is_pc": log.is_pc, "is_bot": log.is_bot
        } for log in scan_logs]

        total_pages = math.ceil(total_logs / limit) if total_logs > 0 else 1

        return templates.TemplateResponse(
            "scan_log_table.html",
            {
                "request": request,
                "qr_id": qr_id, "scan_logs": formatted_logs, "total_logs": total_logs,
                "page": page, "limit": limit, "total_pages": total_pages, "genuine_only": genuine_only
            }
        )
    except QRCodeNotFoundError:
        return templates.TemplateResponse("error.html", {"request": request, "error": f"QR code with ID {qr_id} not found."}, status_code=404)
    except DatabaseError as e:
        logger.error(f"Database error retrieving scan logs for QR {qr_id}: {str(e)}")
        return templates.TemplateResponse("error.html", {"request": request, "error": "An error occurred while retrieving scan logs."}, status_code=500)

@router.get("/qr/{qr_id}/analytics/device-stats", response_class=HTMLResponse)
async def get_device_stats_fragment(
    request: Request,
    qr_id: str,
    scan_processing_service: ScanProcessingServiceDep, # Changed dependency
    genuine_only: bool = False, # genuine_only was not in original signature but makes sense
):
    """ Get device/browser/OS stats fragment. (Moved from fragments.py) """
    try:
        # Using scan_log_repo directly via the service as in original.
        device_stats = scan_processing_service.scan_log_repo.get_device_statistics(qr_id)
        browser_stats = scan_processing_service.scan_log_repo.get_browser_statistics(qr_id)
        os_stats = scan_processing_service.scan_log_repo.get_os_statistics(qr_id)

        stats = {
            "device_types": device_stats.get("device_types", {}),
            "device_families": device_stats.get("device_families", {}),
            "browser_families": browser_stats.get("browser_families", {}),
            "os_families": os_stats.get("os_families", {})
        }
        device_total = sum(stats["device_types"].values())

        return templates.TemplateResponse(
            "device_os_browser_stats.html",
            {"request": request, "qr_id": qr_id, "stats": stats, "device_total": device_total, "genuine_only": genuine_only}
        )
    except QRCodeNotFoundError:
        return templates.TemplateResponse("error.html", {"request": request, "error": f"QR code with ID {qr_id} not found."}, status_code=404)
    except DatabaseError as e:
        logger.error(f"Database error retrieving device stats for QR {qr_id}: {str(e)}")
        return templates.TemplateResponse("error.html", {"request": request, "error": "An error occurred while retrieving device stats."}, status_code=500)

@router.get("/qr/{qr_id}/download-options", response_class=HTMLResponse)
async def get_qr_download_options_fragment(
    request: Request,
    qr_id: str,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed dependency
):
    """ Get download options fragment. (Moved from fragments.py) """
    try:
        qr = await qr_retrieval_service.get_qr_by_id(qr_id)
        return templates.TemplateResponse("qr_download_options.html", {"request": request, "qr": qr})
    except QRCodeNotFoundError:
        return templates.TemplateResponse("error.html", {"request": request, "error": f"QR code with ID {qr_id} not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error getting QR download options: {str(e)}")
        return templates.TemplateResponse("error.html", {"request": request, "error": "Unable to load QR download options"}, status_code=500)

@router.get("/qr/{qr_id}/analytics/scan-timeseries", response_class=JSONResponse) # Returns JSON
async def get_scan_timeseries_data( # Renamed from get_scan_timeseries
    qr_id: str,
    scan_processing_service: ScanProcessingServiceDep, # Changed dependency
    time_range: str = "last7days",
):
    """ Get time series data for QR scans. (Moved from fragments.py) """
    try:
        # Using scan_log_repo directly via the service as in original.
        # This could be refactored into a ScanProcessingService method.
        time_series_data = scan_processing_service.scan_log_repo.get_scan_timeseries(
            qr_id=qr_id, time_range=time_range
        )
        return time_series_data # Already a dict/JSON structure
    except QRCodeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"QR code with ID {qr_id} not found")
    except DatabaseError as e:
        logger.error(f"Database error retrieving time series for QR {qr_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving time series data")
