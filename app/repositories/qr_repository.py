"""
QR code repository module for database operations related to QR codes.
"""

import logging
from datetime import UTC, datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import update, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import (
    DatabaseError, 
    QRCodeNotFoundError,
    InvalidQRTypeError
)
from ..database import with_retry
from ..models.qr import QRCode
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class QRCodeRepository(BaseRepository[QRCode]):
    """
    Repository for QR code database operations.
    
    Extends the BaseRepository for QR code-specific operations.
    """

    def __init__(self, db: Session):
        """
        Initialize the QR code repository.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, QRCode)

    def get_by_content(self, content: str) -> Optional[QRCode]:
        """
        Get a QR code by its content.
        
        Args:
            content: The content of the QR code
            
        Returns:
            The QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(QRCode).filter(QRCode.content == content).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving QR code by content: {str(e)}")
            raise DatabaseError(f"Database error retrieving QR code by content: {str(e)}")

    @with_retry(max_retries=3, retry_delay=0.2)
    def update_qr(self, qr_id: str, update_data: Dict[str, Any]) -> Optional[QRCode]:
        """
        Update a QR code with the provided data.
        
        Args:
            qr_id: The ID of the QR code to update
            update_data: Dictionary of model attributes to update
            
        Returns:
            The updated QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Get the current QR code
            qr_code = self.get_by_id(qr_id)
            if not qr_code:
                return None
                
            # Update the QR code attributes
            for key, value in update_data.items():
                setattr(qr_code, key, value)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(qr_code)
            
            return qr_code
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error updating QR code: {str(e)}")

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
                # Directly raise the exception instead of in a nested try/except
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

            self.db.commit()
            logger.debug(f"Updated scan count for QR code {qr_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating scan count for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error while updating scan count: {str(e)}")

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
                # Directly raise the exception instead of in a nested try/except
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

    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        """
        List QR codes with optional filtering and sorting.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            qr_type: Filter by QR code type (static/dynamic)
            search: Search term for filtering content, title, description or redirect URL
            sort_by: Field to sort by (created_at, scan_count, etc.)
            sort_desc: Sort in descending order if true
            
        Returns:
            Tuple of (list of QR code objects, total count)
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Build the query
            query = self.db.query(QRCode)

            # Apply filters
            if qr_type:
                # Check if qr_type is valid in the calling service layer
                query = query.filter(QRCode.qr_type == qr_type)
                
            # Apply search if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        QRCode.content.ilike(search_term),
                        QRCode.redirect_url.ilike(search_term),
                        QRCode.title.ilike(search_term),
                        QRCode.description.ilike(search_term)
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

    def find_by_pattern(self, patterns: List[str]) -> Optional[QRCode]:
        """
        Find a QR code by matching any of the provided content patterns.
        
        This method is useful for finding QR codes by their content, supporting various
        formats and backward compatibility for QR code redirection.
        
        Args:
            patterns: List of patterns to match against QR code content
            
        Returns:
            The QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            or_conditions = []
            
            # Create OR conditions for exact matches
            for pattern in patterns:
                if pattern.startswith("%"):
                    # This is a LIKE pattern
                    or_conditions.append(QRCode.content.like(pattern))
                else:
                    # This is an exact match
                    or_conditions.append(QRCode.content == pattern)
                    
            # Execute the query with combined OR conditions
            return self.db.query(QRCode).filter(or_(*or_conditions)).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error finding QR code by pattern: {str(e)}")
            raise DatabaseError(f"Database error finding QR code by pattern: {str(e)}")
    
    def count(self) -> int:
        """
        Get the total count of QR codes in the database.
        
        Returns:
            Total count of QR codes
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(QRCode).count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting QR codes: {str(e)}")
            raise DatabaseError(f"Database error counting QR codes: {str(e)}") 