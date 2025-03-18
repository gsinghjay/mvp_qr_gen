"""
QR code service layer for the QR code generator application.
"""

import logging
import uuid
from datetime import UTC, datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import qrcode
import qrcode.image.svg
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import update, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import (
    DatabaseError,
    InvalidQRTypeError,
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError,
)
from ..core.config import settings
from ..database import with_retry
from ..models.qr import QRCode
from ..schemas.common import QRType
from ..schemas.qr.models import QRCodeCreate
from ..schemas.qr.parameters import (
    DynamicQRCreateParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)

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
        Initialize the QR code service with a database session.

        Args:
            db: SQLAlchemy database session
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
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        try:
            qr = self.db.query(QRCode).filter(QRCode.id == qr_id).first()
            if not qr:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
            return qr
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while retrieving QR code: {str(e)}")
        except QRCodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while retrieving QR code: {str(e)}")

    def create_static_qr(self, data: StaticQRCreateParameters) -> QRCode:
        """
        Create a new static QR code.

        Args:
            data: Parameters for creating a static QR code

        Returns:
            The created QR code object

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=data.content,
                qr_type=QRType.STATIC,
                fill_color=data.fill_color,
                back_color=data.back_color,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code in database
            qr = QRCode(**qr_data.model_dump())
            self.db.add(qr)
            self.db.commit()
            self.db.refresh(qr)

            logger.info(f"Created static QR code with ID {qr.id}")
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating static QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating static QR code: {str(e)}")
            raise DatabaseError(f"Database error while creating QR code: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating static QR code: {str(e)}")
            raise DatabaseError(f"Unexpected error while creating QR code: {str(e)}")

    def create_dynamic_qr(self, data: DynamicQRCreateParameters) -> QRCode:
        """
        Create a dynamic QR code.

        Args:
            data: Parameters for creating a dynamic QR code

        Returns:
            The created QR code object

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Generate a short unique identifier for the redirect path
            short_id = str(uuid.uuid4())[:8]
            
            # Create full URL with BASE_URL
            full_url = f"{settings.BASE_URL}/r/{short_id}"

            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=str(data.redirect_url),  # Explicitly convert to string
                fill_color=data.fill_color,
                back_color=data.back_color,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code in database - ensure model_dump() converts HttpUrl to string
            model_data = qr_data.model_dump()
            # Double check that redirect_url is a string
            if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                model_data["redirect_url"] = str(model_data["redirect_url"])

            qr = QRCode(**model_data)
            self.db.add(qr)
            self.db.commit()
            self.db.refresh(qr)

            logger.info(f"Created dynamic QR code with ID {qr.id} and redirect path {qr.content}")
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating dynamic QR code: {str(e)}")
            raise DatabaseError(f"Database error while creating QR code: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating dynamic QR code: {str(e)}")
            raise DatabaseError(f"Unexpected error while creating QR code: {str(e)}")

    @with_retry(max_retries=3, retry_delay=0.2)
    def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a dynamic QR code.

        Args:
            qr_id: The ID of the QR code to update
            data: Parameters for updating the QR code

        Returns:
            The updated QR code object

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Get the QR code
            qr = self.get_qr_by_id(qr_id)

            # Verify it's a dynamic QR code
            if qr.qr_type != QRType.DYNAMIC.value:
                raise QRCodeValidationError(f"Cannot update non-dynamic QR code: {qr_id}")

            # Update the redirect URL
            if data.redirect_url:
                # Ensure redirect_url is a string
                qr.redirect_url = str(data.redirect_url)

            # Update the QR code in the database
            self.db.commit()
            self.db.refresh(qr)

            logger.info(f"Updated dynamic QR code with ID {qr.id}")
            return qr
        except ValidationError as e:
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while updating QR code: {str(e)}")
        except (QRCodeNotFoundError, QRCodeValidationError, RedirectURLError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while updating QR code: {str(e)}")

    @with_retry(max_retries=5, retry_delay=0.1)
    def update_scan_count(self, qr_id: str, timestamp: datetime | None = None) -> None:
        """
        Update the scan count for a QR code.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        try:
            # Use atomic update to avoid race conditions
            result = self.db.execute(
                update(QRCode)
                .where(QRCode.id == qr_id)
                .values(
                    scan_count=QRCode.scan_count + 1,
                    last_scan_at=timestamp,
                )
            )

            if result.rowcount == 0:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

            self.db.commit()
            logger.debug(f"Updated scan count for QR code {qr_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating scan count for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while updating scan count: {str(e)}")
        except QRCodeNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating scan count for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while updating scan count: {str(e)}")

    @with_retry(max_retries=5, retry_delay=0.1)
    def update_scan_statistics(
        self,
        qr_id: str,
        timestamp: datetime | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Update scan statistics for a QR code.

        This method updates the scan count, last scan timestamp, and other
        statistics for a QR code. It is designed to be run as a background
        task to avoid blocking the redirect response.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            client_ip: The IP address of the client that scanned the QR code
            user_agent: The user agent of the client that scanned the QR code

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        try:
            # Use atomic update to avoid race conditions
            result = self.db.execute(
                update(QRCode)
                .where(QRCode.id == qr_id)
                .values(
                    scan_count=QRCode.scan_count + 1,
                    last_scan_at=timestamp,
                )
            )

            if result.rowcount == 0:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

            self.db.commit()

            # Log the scan event with client information
            log_data = {
                "qr_id": qr_id,
                "timestamp": timestamp.isoformat(),
                "event": "scan",
            }

            if client_ip:
                log_data["client_ip"] = client_ip
            if user_agent:
                log_data["user_agent"] = user_agent

            logger.info("QR code scan", extra=log_data)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating scan statistics for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while updating scan statistics: {str(e)}")
        except QRCodeNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating scan statistics for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while updating scan statistics: {str(e)}")

    def validate_qr_code(self, qr_data: QRCodeCreate) -> None:
        """
        Validate QR code data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
        """
        # Validate content
        if not qr_data.content:
            raise QRCodeValidationError("QR code content cannot be empty")

        # Validate redirect URL for dynamic QR codes
        if qr_data.qr_type == QRType.DYNAMIC and not qr_data.redirect_url:
            raise RedirectURLError("Redirect URL is required for dynamic QR codes")

        # Validate colors
        try:
            # Simple validation for hex color format
            if not qr_data.fill_color.startswith("#") or len(qr_data.fill_color) != 7:
                raise QRCodeValidationError(f"Invalid fill color format: {qr_data.fill_color}")
            if not qr_data.back_color.startswith("#") or len(qr_data.back_color) != 7:
                raise QRCodeValidationError(
                    f"Invalid background color format: {qr_data.back_color}"
                )
        except Exception as e:
            raise QRCodeValidationError(f"Color validation error: {str(e)}")

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
        qr_type: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> tuple[list[QRCode], int]:
        """
        List QR codes with pagination and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            qr_type: Optional QR code type to filter by
            search: Optional search term for filtering content or redirect URL
            sort_by: Optional field to sort by
            sort_desc: Sort in descending order if true

        Returns:
            A tuple of (list of QR codes, total count)

        Raises:
            InvalidQRTypeError: If an invalid QR type is specified
            DatabaseError: If a database error occurs
        """
        try:
            # Build the query
            query = self.db.query(QRCode)

            # Apply filters
            if qr_type:
                if qr_type not in [QRType.STATIC.value, QRType.DYNAMIC.value]:
                    raise InvalidQRTypeError(f"Invalid QR type: {qr_type}")
                query = query.filter(QRCode.qr_type == qr_type)
                
            # Apply search if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        QRCode.content.ilike(search_term),
                        QRCode.redirect_url.ilike(search_term)
                    )
                )

            # Get total count
            total = query.count()

            # Apply sorting
            if sort_by:
                if hasattr(QRCode, sort_by):
                    sort_column = getattr(QRCode, sort_by)
                    if sort_desc:
                        sort_column = sort_column.desc()
                    else:
                        sort_column = sort_column.asc()
                    query = query.order_by(sort_column)
                else:
                    # Default sort if invalid column specified
                    query = query.order_by(QRCode.created_at.desc())
            else:
                # Default sort by creation date, newest first
                query = query.order_by(QRCode.created_at.desc())

            # Apply pagination
            qr_codes = query.offset(skip).limit(limit).all()

            return qr_codes, total
        except SQLAlchemyError as e:
            logger.error(f"Database error listing QR codes: {str(e)}")
            raise DatabaseError(f"Database error while listing QR codes: {str(e)}")
        except InvalidQRTypeError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing QR codes: {str(e)}")
            raise DatabaseError(f"Unexpected error while listing QR codes: {str(e)}")

    @with_retry(max_retries=3, retry_delay=0.2)
    def delete_qr(self, qr_id: str) -> None:
        """
        Delete a QR code by ID.

        Args:
            qr_id: The ID of the QR code to delete

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        try:
            # First, check if the QR code exists
            qr = self.get_qr_by_id(qr_id)

            # Delete the QR code
            self.db.delete(qr)
            self.db.commit()

            logger.info(f"Deleted QR code with ID {qr_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while deleting QR code: {str(e)}")
        except QRCodeNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error deleting QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while deleting QR code: {str(e)}")
