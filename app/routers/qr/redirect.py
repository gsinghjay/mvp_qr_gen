"""
Router for QR code redirects.
"""

from datetime import UTC, datetime
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse

from ...dependencies import get_qr_service
from ...database import get_db
from ...models.qr import QRCode
from ...services.qr_service import QRCodeService
from ...database import with_retry
from .common import logger

router = APIRouter(
    prefix="/r",
    tags=["QR Redirects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{short_id}")
async def redirect_qr(
    short_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    qr_service: QRCodeService = Depends(get_qr_service),
    db = Depends(get_db),
):
    """
    Redirect a QR code scan to the target URL.

    Args:
        short_id: The short ID from the QR code
        request: The FastAPI request object
        background_tasks: FastAPI background tasks
        qr_service: The QR code service (injected)
        db: Database session (injected)

    Returns:
        A redirect response to the target URL
    """
    try:
        # The full path that would be in the QR code content
        full_path = f"/r/{short_id}"

        # More efficient direct query instead of listing all QRs
        try:
            stmt = select(QRCode).where(QRCode.content == full_path)
            result = db.execute(stmt)
            qr = result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error finding QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error finding QR code") 

        if not qr:
            logger.warning(f"QR code not found for path: {full_path}")
            raise HTTPException(status_code=404, detail="QR code not found")

        # Validate QR code type and redirect URL
        if qr.qr_type != "dynamic" or not qr.redirect_url:
            logger.error(f"Invalid QR code type or missing redirect URL: {qr.id}")
            raise HTTPException(status_code=400, detail="Invalid QR code")

        # Get redirect URL before any background tasks run
        redirect_url = qr.redirect_url
        
        # Update scan statistics in a background task to improve response time
        timestamp = datetime.now(UTC)
        
        # Get client information for analytics
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Add the background task to update scan statistics with client info
        background_tasks.add_task(
            qr_service.update_scan_statistics, 
            qr.id, 
            timestamp,
            client_ip,
            user_agent
        )

        # Log the scan event
        logger.info(
            f"QR code scan: {qr.id}",
            extra={
                "qr_id": qr.id,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "timestamp": timestamp.isoformat(),
            },
        )

        # Redirect to the target URL
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing QR code redirect: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing QR code redirect")
