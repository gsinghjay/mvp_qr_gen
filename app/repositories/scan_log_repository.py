"""
Repository for scan log database operations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, UTC
from sqlalchemy import func, desc, extract, cast, Date
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseError
from app.models.scan_log import ScanLog
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ScanLogRepository(BaseRepository[ScanLog]):
    """Repository for scan log database operations."""
    
    def __init__(self, db):
        """
        Initialize the scan log repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, ScanLog)

    def create_scan_log(
        self, 
        qr_id: str, 
        timestamp: datetime, 
        ip_address: Optional[str], 
        raw_user_agent: Optional[str], 
        parsed_ua_data: Dict[str, Any], 
        is_genuine_scan_signal: bool
    ) -> ScanLog:
        """
        Create a new scan log entry.
        
        Args:
            qr_id: The ID of the QR code being scanned
            timestamp: Timestamp of the scan (UTC)
            ip_address: IP address of the client
            raw_user_agent: Raw user agent string from the client
            parsed_ua_data: Dictionary of parsed user agent data
            is_genuine_scan_signal: Whether this is a genuine QR scan (vs direct URL access)
            
        Returns:
            The created scan log entry
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            scan_log = ScanLog(
                qr_code_id=qr_id,
                scanned_at=timestamp,  # Ensure timestamp is UTC
                ip_address=ip_address,
                raw_user_agent=raw_user_agent,
                is_genuine_scan=is_genuine_scan_signal,
                device_family=parsed_ua_data.get("device_family", "Unknown"),
                os_family=parsed_ua_data.get("os_family", "Unknown"),
                os_version=parsed_ua_data.get("os_version", "Unknown"),
                browser_family=parsed_ua_data.get("browser_family", "Unknown"),
                browser_version=parsed_ua_data.get("browser_version", "Unknown"),
                is_mobile=parsed_ua_data.get("is_mobile", False),
                is_tablet=parsed_ua_data.get("is_tablet", False),
                is_pc=parsed_ua_data.get("is_pc", False),
                is_bot=parsed_ua_data.get("is_bot", False)
            )
            self.db.add(scan_log)
            self.db.commit()
            self.db.refresh(scan_log)
            return scan_log
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating scan log for QR {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error creating scan log: {str(e)}")

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

    def get_scan_timeseries(
        self,
        qr_id: str,
        time_range: str = "last7days",
    ) -> Dict[str, Any]:
        """
        Get time series data for QR code scans.
        
        Args:
            qr_id: ID of the QR code to get time series data for
            time_range: Time range for data ("today", "yesterday", "last7days", 
                       "last30days", "thisMonth", "lastMonth", "allTime")
            
        Returns:
            Dictionary with time series data for chart rendering
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            from datetime import timedelta
            
            # Calculate date ranges based on time_range
            now = datetime.now(UTC)
            
            if time_range == "today":
                start_date = datetime(now.year, now.month, now.day, tzinfo=UTC)
                end_date = now
                interval = "hour"
                format_str = "%H:00"  # Hour format
            elif time_range == "yesterday":
                yesterday = now - timedelta(days=1)
                start_date = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=UTC)
                end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=UTC)
                interval = "hour"
                format_str = "%H:00"  # Hour format
            elif time_range == "last7days":
                start_date = now - timedelta(days=7)
                end_date = now
                interval = "day"
                format_str = "%m-%d"  # Month-day format
            elif time_range == "last30days":
                start_date = now - timedelta(days=30)
                end_date = now
                interval = "day"
                format_str = "%m-%d"  # Month-day format
            elif time_range == "thisMonth":
                start_date = datetime(now.year, now.month, 1, tzinfo=UTC)
                end_date = now
                interval = "day"
                format_str = "%d"  # Day format
            elif time_range == "lastMonth":
                last_month = now.month - 1 if now.month > 1 else 12
                last_month_year = now.year if now.month > 1 else now.year - 1
                start_date = datetime(last_month_year, last_month, 1, tzinfo=UTC)
                # Last day of last month
                if last_month == 12:
                    end_date = datetime(last_month_year, 12, 31, 23, 59, 59, tzinfo=UTC)
                else:
                    end_date = datetime(now.year, now.month, 1, tzinfo=UTC) - timedelta(seconds=1)
                interval = "day"
                format_str = "%d"  # Day format
            else:  # allTime or default
                # Get first scan date or 90 days ago, whichever is more recent
                first_scan = self.db.query(func.min(ScanLog.scanned_at)).filter(
                    ScanLog.qr_code_id == qr_id
                ).scalar()
                
                if first_scan:
                    start_date = first_scan
                else:
                    start_date = now - timedelta(days=90)  # Default to 90 days if no scans
                    
                end_date = now
                
                # Choose interval based on date range
                days_diff = (end_date - start_date).days
                if days_diff <= 7:
                    interval = "day"
                    format_str = "%m-%d"
                elif days_diff <= 60:
                    interval = "week"
                    format_str = "Week %W"
                else:
                    interval = "month"
                    format_str = "%b %Y"
            
            # Build query based on interval
            if interval == "hour":
                # Group by hour
                all_scans_query = self.db.query(
                    extract('hour', ScanLog.scanned_at).label('time_unit'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date
                ).group_by('time_unit').order_by('time_unit')
                
                genuine_scans_query = self.db.query(
                    extract('hour', ScanLog.scanned_at).label('time_unit'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date,
                    ScanLog.is_genuine_scan == True
                ).group_by('time_unit').order_by('time_unit')
                
                # Generate all hours in range for complete dataset
                all_hours = list(range(24))
                labels = [f"{h:02d}:00" for h in all_hours]
                
            elif interval == "day":
                # Group by day
                all_scans_query = self.db.query(
                    cast(ScanLog.scanned_at, Date).label('time_unit'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date
                ).group_by('time_unit').order_by('time_unit')
                
                genuine_scans_query = self.db.query(
                    cast(ScanLog.scanned_at, Date).label('time_unit'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date,
                    ScanLog.is_genuine_scan == True
                ).group_by('time_unit').order_by('time_unit')
                
                # Generate all days in range for complete dataset
                days_diff = (end_date - start_date).days + 1
                labels = [(start_date + timedelta(days=i)).strftime(format_str) for i in range(days_diff)]
                
            elif interval == "week":
                # Group by week
                all_scans_query = self.db.query(
                    extract('year', ScanLog.scanned_at).label('year'),
                    extract('week', ScanLog.scanned_at).label('week'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date
                ).group_by('year', 'week').order_by('year', 'week')
                
                genuine_scans_query = self.db.query(
                    extract('year', ScanLog.scanned_at).label('year'),
                    extract('week', ScanLog.scanned_at).label('week'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date,
                    ScanLog.is_genuine_scan == True
                ).group_by('year', 'week').order_by('year', 'week')
                
                # Generate week labels
                # This is simplified and might need adjustment for exact week boundaries
                weeks_diff = (end_date - start_date).days // 7 + 1
                labels = [f"Week {i+1}" for i in range(weeks_diff)]
                
            else:  # month
                # Group by month
                all_scans_query = self.db.query(
                    extract('year', ScanLog.scanned_at).label('year'),
                    extract('month', ScanLog.scanned_at).label('month'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date
                ).group_by('year', 'month').order_by('year', 'month')
                
                genuine_scans_query = self.db.query(
                    extract('year', ScanLog.scanned_at).label('year'),
                    extract('month', ScanLog.scanned_at).label('month'),
                    func.count().label('count')
                ).filter(
                    ScanLog.qr_code_id == qr_id,
                    ScanLog.scanned_at >= start_date,
                    ScanLog.scanned_at <= end_date,
                    ScanLog.is_genuine_scan == True
                ).group_by('year', 'month').order_by('year', 'month')
                
                # Generate month labels
                months_diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
                current_date = datetime(start_date.year, start_date.month, 1, tzinfo=UTC)
                labels = []
                for _ in range(months_diff):
                    labels.append(current_date.strftime("%b %Y"))
                    # Move to next month
                    if current_date.month == 12:
                        current_date = datetime(current_date.year + 1, 1, 1, tzinfo=UTC)
                    else:
                        current_date = datetime(current_date.year, current_date.month + 1, 1, tzinfo=UTC)
            
            # Execute queries
            all_scans_results = all_scans_query.all()
            genuine_scans_results = genuine_scans_query.all()
            
            # Process results into datasets
            all_scans_data = [0] * len(labels)
            genuine_scans_data = [0] * len(labels)
            
            # Map results to appropriate indices
            if interval == "hour":
                for result in all_scans_results:
                    hour = int(result.time_unit)
                    if 0 <= hour < len(all_scans_data):
                        all_scans_data[hour] = result.count
                
                for result in genuine_scans_results:
                    hour = int(result.time_unit)
                    if 0 <= hour < len(genuine_scans_data):
                        genuine_scans_data[hour] = result.count
                        
            elif interval == "day":
                # Create a mapping of date strings to indices
                date_to_index = {date: i for i, date in enumerate(labels)}
                
                for result in all_scans_results:
                    date_str = result.time_unit.strftime(format_str)
                    if date_str in date_to_index:
                        all_scans_data[date_to_index[date_str]] = result.count
                
                for result in genuine_scans_results:
                    date_str = result.time_unit.strftime(format_str)
                    if date_str in date_to_index:
                        genuine_scans_data[date_to_index[date_str]] = result.count
                        
            elif interval == "week":
                # For week data, we'll use simple index matching
                # This is simplified and might need adjustment
                for i, result in enumerate(all_scans_results):
                    if i < len(all_scans_data):
                        all_scans_data[i] = result.count
                
                for i, result in enumerate(genuine_scans_results):
                    if i < len(genuine_scans_data):
                        genuine_scans_data[i] = result.count
                        
            else:  # month
                # For month data, we'll use simple index matching
                # This is simplified and might need adjustment
                for i, result in enumerate(all_scans_results):
                    if i < len(all_scans_data):
                        all_scans_data[i] = result.count
                
                for i, result in enumerate(genuine_scans_results):
                    if i < len(genuine_scans_data):
                        genuine_scans_data[i] = result.count
            
            return {
                "labels": labels,
                "datasets": {
                    "all_scans": all_scans_data,
                    "genuine_scans": genuine_scans_data
                },
                "interval": interval,
                "time_range": time_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving time series data for QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Database error retrieving time series data: {str(e)}") 