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
from ..models.scan_log import ScanLog
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

    @with_retry(max_retries=5, retry_delay=0.1)
    def update_and_log_scan_statistics(
        self,
        qr_id: str,
        timestamp: datetime | None = None,
        client_ip: str | None = None,
        raw_user_agent: str | None = None,
        parsed_ua_data: Dict[str, Any] = None,
        is_genuine_scan_signal: bool = False,
    ) -> None:
        """
        Update QR code scan statistics and create a detailed scan log entry.
        
        This method updates scan statistics for a QR code, tracking both overall access
        and genuine scans from QR codes. It also creates a detailed scan log entry with
        the user agent information for analytics.
        
        Args:
            qr_id: The ID of the QR code being scanned
            timestamp: Timestamp of the scan (defaults to current time)
            client_ip: IP address of the client
            raw_user_agent: Raw user agent string from the client
            parsed_ua_data: Dictionary of parsed user agent data
            is_genuine_scan_signal: Whether this is a genuine QR scan (vs direct URL access)
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)
        
        if parsed_ua_data is None:
            parsed_ua_data = {}
        
        try:
            # Begin a transaction
            # Update QR code statistics in the database
            # These updates need to differ based on whether it's a genuine scan or not
            if is_genuine_scan_signal:
                # For genuine scans, update all statistics
                update_values = {
                    # Always increment scan_count for all visits
                    "scan_count": QRCode.scan_count + 1,
                    "last_scan_at": timestamp,
                    # Increment genuine_scan_count only for real QR scans
                    "genuine_scan_count": QRCode.genuine_scan_count + 1,
                    "last_genuine_scan_at": timestamp,
                }
                
                # We also need to set first_genuine_scan_at if it's currently NULL
                # This requires a more complex query
                qr = self.get_by_id(qr_id)
                if not qr:
                    raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
                    
                if qr.first_genuine_scan_at is None:
                    update_values["first_genuine_scan_at"] = timestamp
            else:
                # For non-genuine access (direct URL), only update total counters
                update_values = {
                    "scan_count": QRCode.scan_count + 1,
                    "last_scan_at": timestamp,
                }
            
            # Execute the update
            result = self.db.execute(
                update(QRCode)
                .where(QRCode.id == qr_id)
                .values(**update_values)
            )
            
            if result.rowcount == 0:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
            
            # Create a scan log entry with all the details
            scan_log = ScanLog(
                qr_code_id=qr_id,
                scanned_at=timestamp,
                ip_address=client_ip,
                raw_user_agent=raw_user_agent,
                is_genuine_scan=is_genuine_scan_signal,
                # Add user agent data
                device_family=parsed_ua_data.get("device_family", "Unknown"),
                os_family=parsed_ua_data.get("os_family", "Unknown"),
                os_version=parsed_ua_data.get("os_version", "Unknown"),
                browser_family=parsed_ua_data.get("browser_family", "Unknown"),
                browser_version=parsed_ua_data.get("browser_version", "Unknown"),
                is_mobile=parsed_ua_data.get("is_mobile", False),
                is_tablet=parsed_ua_data.get("is_tablet", False),
                is_pc=parsed_ua_data.get("is_pc", False),
                is_bot=parsed_ua_data.get("is_bot", False),
            )
            
            # Add the scan log to the database
            self.db.add(scan_log)
            
            # Commit both operations
            self.db.commit()
            
            # Log the event
            scan_type = "genuine QR scan" if is_genuine_scan_signal else "URL access"
            logger.info(
                f"Recorded {scan_type} for QR code {qr_id}",
                extra={
                    "qr_id": qr_id,
                    "scan_log_id": scan_log.id,
                    "timestamp": timestamp.isoformat(),
                    "is_genuine": is_genuine_scan_signal,
                    "device": scan_log.device_family,
                    "browser": scan_log.browser_family,
                    "os": scan_log.os_family,
                }
            )
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
            
    def get_scan_logs_for_qr(
        self,
        qr_id: str,
        skip: int = 0,
        limit: int = 100,
        genuine_only: bool = False,
    ) -> Tuple[List[ScanLog], int]:
        """
        Get scan logs for a specific QR code.
        
        Args:
            qr_id: ID of the QR code to get scan logs for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            genuine_only: If True, return only genuine QR scans (not direct URL access)
            
        Returns:
            Tuple of (list of scan log objects, total count)
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Build the query
            query = self.db.query(ScanLog).filter(ScanLog.qr_code_id == qr_id)
            
            # Filter for genuine scans if requested
            if genuine_only:
                query = query.filter(ScanLog.is_genuine_scan == True)
                
            # Get total count
            total = query.count()
            
            # Apply sorting (newest first) and pagination
            query = query.order_by(ScanLog.scanned_at.desc())
            scan_logs = query.offset(skip).limit(limit).all()
            
            return scan_logs, total
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving scan logs for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving scan logs: {str(e)}")
            
    def get_device_statistics(self, qr_id: str) -> Dict[str, Dict[str, int]]:
        """
        Get device statistics for a QR code.
        
        Returns device type counts (mobile, tablet, PC, bot) and top device families.
        
        Args:
            qr_id: ID of the QR code to get statistics for
            
        Returns:
            Dictionary with device statistics
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            from sqlalchemy import func, desc
            
            # Get device type counts
            device_types = {}
            
            # Count mobile devices
            mobile_count = self.db.query(func.count(ScanLog.id)).filter(
                ScanLog.qr_code_id == qr_id,
                ScanLog.is_mobile == True
            ).scalar() or 0
            
            # Count tablets
            tablet_count = self.db.query(func.count(ScanLog.id)).filter(
                ScanLog.qr_code_id == qr_id,
                ScanLog.is_tablet == True
            ).scalar() or 0
            
            # Count PCs
            pc_count = self.db.query(func.count(ScanLog.id)).filter(
                ScanLog.qr_code_id == qr_id,
                ScanLog.is_pc == True
            ).scalar() or 0
            
            # Count bots
            bot_count = self.db.query(func.count(ScanLog.id)).filter(
                ScanLog.qr_code_id == qr_id,
                ScanLog.is_bot == True
            ).scalar() or 0
            
            device_types = {
                "mobile": mobile_count,
                "tablet": tablet_count,
                "pc": pc_count,
                "bot": bot_count
            }
            
            # Get top device families
            device_families = {}
            results = self.db.query(
                ScanLog.device_family,
                func.count(ScanLog.id).label('count')
            ).filter(
                ScanLog.qr_code_id == qr_id
            ).group_by(
                ScanLog.device_family
            ).order_by(
                desc('count')
            ).limit(5).all()
            
            for device_family, count in results:
                device_families[device_family] = count
                
            return {
                "device_types": device_types,
                "device_families": device_families
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving device statistics for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving device statistics: {str(e)}")

    def get_browser_statistics(self, qr_id: str) -> Dict[str, Dict[str, int]]:
        """
        Get browser statistics for a QR code.
        
        Returns top browser families.
        
        Args:
            qr_id: ID of the QR code to get statistics for
            
        Returns:
            Dictionary with browser statistics
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            from sqlalchemy import func, desc
            
            # Get top browser families
            browser_families = {}
            results = self.db.query(
                ScanLog.browser_family,
                func.count(ScanLog.id).label('count')
            ).filter(
                ScanLog.qr_code_id == qr_id
            ).group_by(
                ScanLog.browser_family
            ).order_by(
                desc('count')
            ).limit(5).all()
            
            for browser_family, count in results:
                browser_families[browser_family] = count
                
            return {
                "browser_families": browser_families
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving browser statistics for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving browser statistics: {str(e)}")
            
    def get_os_statistics(self, qr_id: str) -> Dict[str, Dict[str, int]]:
        """
        Get operating system statistics for a QR code.
        
        Returns top OS families.
        
        Args:
            qr_id: ID of the QR code to get statistics for
            
        Returns:
            Dictionary with OS statistics
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            from sqlalchemy import func, desc
            
            # Get top OS families
            os_families = {}
            results = self.db.query(
                ScanLog.os_family,
                func.count(ScanLog.id).label('count')
            ).filter(
                ScanLog.qr_code_id == qr_id
            ).group_by(
                ScanLog.os_family
            ).order_by(
                desc('count')
            ).limit(5).all()
            
            for os_family, count in results:
                os_families[os_family] = count
                
            return {
                "os_families": os_families
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving OS statistics for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving OS statistics: {str(e)}") 