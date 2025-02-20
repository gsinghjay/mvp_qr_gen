"""
Router for QR code redirect operations.
"""

import json
from datetime import UTC, datetime
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from sqlalchemy.orm import Session

from ...core.config import settings
from ...models import QRCode
from .common import get_db_with_logging, logger

router = APIRouter(
    tags=["redirects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/r/{short_id}")
async def redirect_qr(short_id: str, request: Request, db: Session = Depends(get_db_with_logging)):
    """Redirect endpoint for dynamic QR codes."""
    try:
        qr = db.query(QRCode).filter(QRCode.content == f"/r/{short_id}").first()
        if not qr:
            raise HTTPException(status_code=404, detail="QR code not found")

        if not qr.redirect_url:
            raise HTTPException(status_code=400, detail="No redirect URL set")

        # Validate redirect URL
        try:
            parsed_url = urlparse(str(qr.redirect_url))
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(status_code=400, detail="Invalid redirect URL")
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid redirect URL")

        # Update scan statistics atomically using SQL update
        try:
            current_time = datetime.now(UTC)
            stmt = (
                update(QRCode)
                .where(QRCode.id == qr.id)
                .values(scan_count=QRCode.scan_count + 1, last_scan_at=current_time)
            )
            db.execute(stmt)
            db.commit()

            # Refresh the QR code object to get updated values
            db.refresh(qr)

        except Exception as e:
            logger.error(f"Error updating scan statistics: {str(e)}")
            db.rollback()
            # Continue with redirect even if statistics update fails

        # Get client IP from various possible headers
        client_ip = (
            request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        # Log scan event with metadata
        scan_metadata = {
            "qr_id": qr.id,
            "timestamp": current_time.isoformat(),
            "ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }
        logger.info(f"QR code scan: {json.dumps(scan_metadata)}")

        # Ensure HTTPS for production redirects
        redirect_url = str(qr.redirect_url)
        if settings.ENVIRONMENT == "production" and redirect_url.startswith("http://"):
            redirect_url = "https://" + redirect_url[7:]

        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing redirect: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing redirect")
