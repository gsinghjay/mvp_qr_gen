"""
API version 1 router.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...models import QRCode
from ...schemas import QRCodeList, QRCodeResponse, QRCodeUpdate
from ..qr.common import get_db_with_logging, get_qr_by_id, logger, qr_service

router = APIRouter(
    prefix="/api/v1",
    tags=["api-v1"],
)


@router.get("/qr", response_model=QRCodeList)
async def list_qr_codes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    qr_type: str | None = Query(default=None, pattern="^(static|dynamic)$"),
    db: Session = Depends(get_db_with_logging),
):
    """List QR codes with pagination and optional filtering."""
    try:
        query = db.query(QRCode)
        if qr_type:
            query = query.filter(QRCode.qr_type == qr_type)

        total = query.count()
        qr_codes = query.order_by(QRCode.created_at.desc()).offset(skip).limit(limit).all()

        response = QRCodeList(items=qr_codes, total=total, page=skip // limit + 1, page_size=limit)

        return response
    except SQLAlchemyError as e:
        logger.error("Database error listing QR codes", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Error listing QR codes: database error")
    except Exception:
        logger.exception("Unexpected error listing QR codes")
        raise HTTPException(status_code=500, detail="Error listing QR codes: unexpected error")


@router.get("/qr/{qr_id}", response_model=QRCodeResponse)
async def get_qr(qr_id: str, db: Session = Depends(get_db_with_logging)):
    """Get QR code data by ID."""
    try:
        qr = get_qr_by_id(qr_id, db)
        return qr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving QR code")


@router.get("/qr/{qr_id}/image")
async def get_qr_image(
    qr_id: str,
    image_format: str = Query(default="png", pattern="^(png|jpeg|jpg|svg|webp)$"),
    image_quality: int | None = Query(default=None, ge=1, le=100),
    db: Session = Depends(get_db_with_logging),
):
    """Get QR code image by ID."""
    try:
        qr = get_qr_by_id(qr_id, db)

        # Generate QR code
        return qr_service.generate_qr(
            data=qr.content,
            size=qr.size,
            border=qr.border,
            fill_color=qr.fill_color,
            back_color=qr.back_color,
            image_format=image_format,
            image_quality=image_quality,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating QR code image")


@router.put("/qr/{qr_id}", response_model=QRCodeResponse)
async def update_qr(
    qr_id: str, qr_update: QRCodeUpdate, db: Session = Depends(get_db_with_logging)
):
    """Update QR code data by ID."""
    try:
        qr = get_qr_by_id(qr_id, db)

        # Only dynamic QR codes can be updated
        if qr.qr_type != "dynamic":
            raise HTTPException(status_code=400, detail="Only dynamic QR codes can be updated")

        # Update only the redirect_url field
        if qr_update.redirect_url is not None:
            qr.redirect_url = str(qr_update.redirect_url)

        db.commit()
        db.refresh(qr)
        return qr

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating QR code")
    except Exception as e:
        logger.error(f"Error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating QR code")
