"""
Router for static QR code operations.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...database import get_db_with_logging
from ...models import QRCode
from ...schemas import QRCodeCreate, QRCodeResponse
from .common import logger

router = APIRouter(
    prefix="/api/v1/qr/static",
    tags=["static-qr"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=QRCodeResponse)
async def create_static_qr(
    data: QRCodeCreate, db: Session = Depends(get_db_with_logging)
):
    """Create a new static QR code."""
    try:
        if data.redirect_url:
            raise HTTPException(
                status_code=422, detail="Static QR codes cannot have a redirect URL"
            )

        qr = QRCode(
            content=data.content,
            qr_type="static",
            fill_color=data.fill_color,
            back_color=data.back_color,
            size=data.size,
            border=data.border,
            created_at=datetime.now(UTC),
        )
        db.add(qr)
        db.commit()
        db.refresh(qr)

        logger.info("Created static QR code", extra={"qr_id": qr.id})
        return qr
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error creating static QR code", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail="Error creating QR code: database error"
        )
    except Exception:
        db.rollback()
        logger.exception("Unexpected error creating static QR code")
        raise HTTPException(
            status_code=500, detail="Error creating QR code: unexpected error"
        )
