"""
QR code service layer for the QR code generator application.
"""

import logging
import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import List, Optional, Tuple, Dict, Any

import qrcode
import qrcode.image.svg
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import AnyUrl, ValidationError
from zoneinfo import ZoneInfo

from ..models.qr import QRCode
from ..schemas.common import QRType
from ..schemas.qr.models import QRCodeCreate, QRCodeUpdate
from ..database import with_retry

# Configure UTC timezone
UTC = ZoneInfo("UTC")

# Configure logger
logger = logging.getLogger(__name__)

# Define supported image formats and their media types
IMAGE_FORMATS = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}


class QRCodeService:
    """Service class for QR code operations."""

    def __init__(self, db: Session):
        """
        Initialize the QR code service.

        Args:
            db: The database session
        """
        self.db = db

    def get_qr_by_id(self, qr_id: str) -> QRCode:
        """
        Get a QR code by its ID.

        Args:
            qr_id: The ID of the QR code to retrieve

        Returns:
            The QR code object

        Raises:
            HTTPException: If the QR code is not found or a database error occurs
        """
        try:
            qr = self.db.query(QRCode).filter(QRCode.id == qr_id).first()
            if not qr:
                raise HTTPException(status_code=404, detail="QR code not found")
            return qr
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving QR code {qr_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error while retrieving QR code")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving QR code {qr_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected error while retrieving QR code")

    def create_static_qr(self, data: QRCodeCreate) -> QRCode:
        """
        Create a new static QR code.

        Args:
            data: The QR code data to create

        Returns:
            The created QR code object

        Raises:
            HTTPException: If there is an error creating the QR code
        """
        try:
            # Validate QR code data
            if data.qr_type != QRType.STATIC:
                data.qr_type = QRType.STATIC
            self.validate_qr_code(data)

            # Create a new QR code
            qr = QRCode(
                content=str(data.content),
                qr_type="static",
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                created_at=datetime.now(UTC),
            )
            self.db.add(qr)
            self.db.commit()
            self.db.refresh(qr)

            logger.info("Created static QR code", extra={"qr_id": qr.id})
            return qr
        except ValueError as e:
            logger.error(f"Validation error creating static QR code: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating static QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating QR code: database error")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error creating static QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating QR code: unexpected error")

    def create_dynamic_qr(self, data: QRCodeCreate) -> QRCode:
        """
        Create a new dynamic QR code.

        Args:
            data: The QR code data to create

        Returns:
            The created QR code object

        Raises:
            HTTPException: If there is an error creating the QR code
        """
        try:
            # Validate QR code data
            if data.qr_type != QRType.DYNAMIC:
                data.qr_type = QRType.DYNAMIC
            self.validate_qr_code(data)

            if not data.redirect_url:
                raise HTTPException(
                    status_code=422, detail="Dynamic QR codes must have a redirect URL"
                )

            # Generate a short unique identifier for the redirect path
            short_id = str(uuid.uuid4())[:8]
            qr = QRCode(
                content=f"/r/{short_id}",
                qr_type="dynamic",
                redirect_url=str(data.redirect_url),
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                created_at=datetime.now(UTC),
            )
            self.db.add(qr)
            self.db.commit()
            self.db.refresh(qr)

            logger.info("Created dynamic QR code", extra={"qr_id": qr.id})
            return qr
        except ValueError as e:
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating dynamic QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating QR code: database error")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error creating dynamic QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating QR code: unexpected error")

    @with_retry(max_retries=3, retry_delay=0.2)
    def update_dynamic_qr(self, qr_id: str, data: QRCodeUpdate) -> QRCode:
        """
        Update a dynamic QR code's redirect URL.
        Uses retry mechanism with exponential backoff to handle concurrent updates.

        Args:
            qr_id: The ID of the QR code to update
            data: The updated QR code data

        Returns:
            The updated QR code object

        Raises:
            HTTPException: If there is an error updating the QR code
        """
        try:
            qr = self.get_qr_by_id(qr_id)

            if qr.qr_type != "dynamic":
                raise HTTPException(status_code=400, detail="Cannot update static QR code")

            # Validate and update the redirect URL
            if not data.redirect_url:
                raise HTTPException(status_code=422, detail="Redirect URL is required")

            try:
                qr.redirect_url = str(data.redirect_url)
                qr.last_scan_at = datetime.now(UTC)
                self.db.add(qr)
                self.db.commit()
                self.db.refresh(qr)

                logger.info(f"Updated QR code {qr_id} with new redirect URL")
                return qr

            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error updating QR code {qr_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Database error while updating QR code")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating QR code {qr_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected error while updating QR code")

    @with_retry(max_retries=5, retry_delay=0.1)
    def update_scan_count(self, qr_id: str, timestamp: datetime | None = None) -> None:
        """
        Update the scan count and last scan timestamp for a QR code.
        Uses retry mechanism with exponential backoff to handle concurrent updates.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan (defaults to current time)

        Raises:
            Exception: If there is an error updating the scan count after retries
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(UTC)

            # Use direct SQL update to avoid race conditions
            stmt = (
                update(QRCode)
                .where(QRCode.id == qr_id)
                .values(scan_count=QRCode.scan_count + 1, last_scan_at=timestamp)
            )
            self.db.execute(stmt)
            self.db.commit()

            # Log at debug level for high-volume operations
            logger.debug(f"Updated scan count for QR code: {qr_id}")

        except Exception as e:
            logger.error(f"Error updating scan count for QR code {qr_id}: {e}")
            self.db.rollback()
            raise

    def validate_qr_code(self, qr_data: QRCodeCreate) -> None:
        """
        Validate QR code data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            ValueError: If the QR code data is invalid
        """
        if qr_data.qr_type == QRType.DYNAMIC and not qr_data.redirect_url:
            raise ValueError("Dynamic QR codes require a redirect URL")

        if qr_data.qr_type == QRType.STATIC and qr_data.redirect_url:
            raise ValueError("Static QR codes cannot have a redirect URL")

        if qr_data.fill_color == qr_data.back_color:
            raise ValueError("Fill color and background color must be different")

    def generate_qr_image(
        self,
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        image_format: str = "PNG",
    ) -> BytesIO:
        """
        Generate a QR code image.

        Args:
            content: The content to encode in the QR code
            fill_color: The color of the QR code (foreground)
            back_color: The background color of the QR code
            box_size: The size of each box/module in the QR code
            border: The size of the border around the QR code
            image_format: The format of the image (PNG, JPEG, etc.)

        Returns:
            A BytesIO object containing the image data

        Raises:
            Exception: If there is an error generating the QR code image
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=border,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            img_buffer = BytesIO()
            img.save(img_buffer, format=image_format)
            img_buffer.seek(0)

            return img_buffer

        except Exception as e:
            logger.error(f"Error generating QR code image: {e}")
            raise

    def generate_qr(
        self,
        data: str,
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_correction: int = qrcode.constants.ERROR_CORRECT_H,
        image_format: str = "png",
        image_quality: int | None = None,
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters.

        Args:
            data: Content to encode in the QR code
            size: Size of each box in the QR code
            border: Border size around the QR code
            fill_color: Color of the QR code pattern
            back_color: Background color
            error_correction: Error correction level
            image_format: Output image format (png, jpeg, svg, webp)
            image_quality: Quality for lossy formats (1-100)

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        # Validate image format
        image_format = image_format.lower()
        if image_format not in IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format. Supported formats: {', '.join(IMAGE_FORMATS.keys())}",
            )

        try:
            # Handle SVG format separately as it requires different processing
            if image_format == "svg":
                # Use the proper SVG factory that supports styling
                factory = qrcode.image.svg.SvgPathImage
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_correction,
                    box_size=size,
                    border=border,
                    image_factory=factory,
                )
                qr.add_data(data)
                qr.make(fit=True)
                # Generate SVG with proper styling
                img = qr.make_image(
                    fill_color=fill_color,
                    back_color=back_color,
                    attrib={"style": f"background-color:{back_color}"},
                )
                # Update the SVG path fill color
                img._img.find("path").set("fill", fill_color)
            else:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_correction,
                    box_size=size,
                    border=border,
                )
                qr.add_data(data)
                qr.make(fit=True)
                # Generate image with specified colors
                img = qr.make_image(fill_color=fill_color, back_color=back_color)

            # Convert to final format
            buf = BytesIO()
            save_kwargs = {}
            if image_format in ["jpeg", "jpg", "webp"] and image_quality is not None:
                save_kwargs["quality"] = max(1, min(100, image_quality))
            if image_format == "webp":
                save_kwargs["lossless"] = image_quality is None

            if image_format != "svg":
                img.save(buf, format=image_format.upper(), **save_kwargs)
            else:
                img.save(buf)
            buf.seek(0)

            return StreamingResponse(
                buf,
                media_type=IMAGE_FORMATS[image_format],
                headers={"Content-Disposition": f'inline; filename="qr.{image_format}"'},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")

    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: Optional[str] = None,
    ) -> Tuple[List[QRCode], int]:
        """
        List QR codes with pagination and optional filtering.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            qr_type: Filter QR codes by type

        Returns:
            A tuple containing the list of QR codes and the total count

        Raises:
            HTTPException: If there is a database error
        """
        try:
            # Start with base query
            query = self.db.query(QRCode)

            # Apply type filter if provided
            if qr_type:
                query = query.filter(QRCode.qr_type == qr_type)

            # Get total count for pagination
            total_count = query.count()

            # Apply pagination and fetch results
            qr_codes = query.order_by(QRCode.created_at.desc()).offset(skip).limit(limit).all()

            return qr_codes, total_count
        except Exception as e:
            logger.error(f"Error listing QR codes: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error while listing QR codes")
