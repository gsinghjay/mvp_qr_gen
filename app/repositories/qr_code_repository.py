"""
QR code repository module for QR code specific database operations.
"""

import logging
from datetime import timezone, datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import update, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.exceptions import (
    DatabaseError, 
    QRCodeNotFoundError,
    InvalidQRTypeError
)
from ..core.metrics_logger import MetricsLogger
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

    @MetricsLogger.time_service_call("QRCodeRepository", "get_by_id")
    def get_by_id(self, id: Any) -> Optional[QRCode]:
        """
        Get a QR code by its ID.
        
        Overrides BaseRepository.get_by_id to add timing metrics.
        
        Args:
            id: The ID of the QR code to retrieve
            
        Returns:
            The QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        return super().get_by_id(id)

    @MetricsLogger.time_service_call("QRCodeRepository", "create")
    def create(self, model_data: Dict[str, Any]) -> QRCode:
        """
        Create a new QR code.
        
        Overrides BaseRepository.create to add timing metrics.
        
        Args:
            model_data: Dictionary of QR code attributes to create the instance
            
        Returns:
            The created QR code instance
            
        Raises:
            DatabaseError: If a database error occurs
        """
        return super().create(model_data)

    @MetricsLogger.time_service_call("QRCodeRepository", "get_by_content")
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

    @MetricsLogger.time_service_call("QRCodeRepository", "get_by_short_id")
    def get_by_short_id(self, short_id: str) -> Optional[QRCode]:
        """
        Get a QR code by its short_id.
        
        Args:
            short_id: The short_id of the QR code
            
        Returns:
            The QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            return self.db.query(QRCode).filter(QRCode.short_id == short_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving QR code by short_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving QR code by short_id: {str(e)}")

    @MetricsLogger.time_service_call("QRCodeRepository", "update_qr")
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

    @MetricsLogger.time_service_call("QRCodeRepository", "update_scan_count")
    @with_retry(max_retries=5, retry_delay=0.1)
    def update_scan_count(self, qr_id: str, timestamp: datetime, is_genuine_scan_signal: bool = False) -> Optional[QRCode]:
        """
        Updates scan count, last_scan_at, genuine_scan_count, 
        first_genuine_scan_at, and last_genuine_scan_at for a QR code.
        This method focuses *only* on updating the QRCode model.
        Logging the scan event itself is handled by ScanLogRepository.
        
        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan
            is_genuine_scan_signal: Whether this is a genuine QR scan (vs direct URL access)
            
        Returns:
            The updated QR code if found, None otherwise
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            qr_code = self.get_by_id(qr_id)
            if not qr_code:
                return None

            qr_code.scan_count += 1
            qr_code.last_scan_at = timestamp

            if is_genuine_scan_signal:
                qr_code.genuine_scan_count += 1
                qr_code.last_genuine_scan_at = timestamp
                if qr_code.first_genuine_scan_at is None:
                    qr_code.first_genuine_scan_at = timestamp
            
            self.db.commit()
            self.db.refresh(qr_code)
            return qr_code
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating scan count for QR {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error updating scan count: {str(e)}")

    @MetricsLogger.time_service_call("QRCodeRepository", "list_qr_codes")
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

    @MetricsLogger.time_service_call("QRCodeRepository", "count")
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