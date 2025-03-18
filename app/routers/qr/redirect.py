"""
Router for QR code redirects.
"""

from datetime import UTC, datetime
import re
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError

from ...database import get_db
from ...dependencies import get_qr_service
from ...models.qr import QRCode
from ...services.qr_service import QRCodeService
from ...core.config import settings
from .common import logger

router = APIRouter(
    prefix="/r",
    tags=["QR Redirects"],
    responses={
        302: {"description": "Redirect to target URL"},
        404: {"description": "QR code not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/{short_id}",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to target URL"},
        404: {"description": "QR code not found"},
        500: {"description": "Internal server error"},
    },
)
async def redirect_qr(
    short_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    qr_service: QRCodeService = Depends(get_qr_service),
    db=Depends(get_db),
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
        # The short path that would be in old QR codes
        relative_path = f"/r/{short_id}"
        
        # The full URL that would be in new QR codes
        full_url = f"{settings.BASE_URL}/r/{short_id}"
        
        # More efficient query to handle both full URLs and relative paths
        try:
            stmt = select(QRCode).where(
                or_(
                    QRCode.content == relative_path,
                    QRCode.content == full_url,
                    # Handle case where content contains just the short_id for very old QR codes
                    QRCode.content == short_id
                )
            )
            result = db.execute(stmt)
            qr = result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error finding QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error finding QR code")

        if not qr:
            # Try matching on partial URLs (backward compatibility)
            try:
                # Find QR codes with content that ends with the short_id
                pattern = f"%/r/{short_id}"
                stmt = select(QRCode).where(QRCode.content.like(pattern))
                result = db.execute(stmt)
                qr = result.scalars().first()
            except SQLAlchemyError as e:
                logger.error(f"Database error in fallback search: {str(e)}")
                pass
            
            if not qr:
                logger.warning(f"QR code not found for path: {relative_path} or {full_url}")
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
            qr_service.update_scan_statistics, qr.id, timestamp, client_ip, user_agent
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
