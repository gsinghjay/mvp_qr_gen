"""
Service for QR code analytics including scan statistics and user agent tracking.
"""

import logging
from datetime import UTC, datetime
from typing import Dict, Optional, Any, List

from ...core.metrics_logger import MetricsLogger
from ...models.qr import QRCode
from ...repositories import QRCodeRepository, ScanLogRepository
from .qr_core_service import QRCoreService

# Configure logger
logger = logging.getLogger(__name__)

class QRAnalyticsService:
    """Service class for QR code analytics operations."""

    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        scan_log_repo: ScanLogRepository,
        core_service: QRCoreService
    ):
        """
        Initialize the QR analytics service with repositories and dependencies.

        Args:
            qr_code_repo: QRCodeRepository for QR code operations
            scan_log_repo: ScanLogRepository for scan log operations
            core_service: QRCoreService for retrieving QR data
        """
        self.qr_code_repo = qr_code_repo
        self.scan_log_repo = scan_log_repo
        self.core_service = core_service

    @MetricsLogger.time_service_call("QRAnalyticsService", "_parse_user_agent_data")
    def _parse_user_agent_data(self, ua_string: str | None) -> Dict[str, any]:
        """
        Parse a user agent string into structured data for scan log entries.
        
        Args:
            ua_string: Raw user agent string to parse
            
        Returns:
            Dictionary with parsed user agent data
        """
        if not ua_string:
            return {
                "device_family": "Unknown",
                "os_family": "Unknown",
                "os_version": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "Unknown",
                "is_mobile": False,
                "is_tablet": False,
                "is_pc": True,  # Default to PC if unknown
                "is_bot": False
            }
        
        try:
            # Import user_agents here to avoid circular imports
            from user_agents import parse as parse_user_agent
            
            # Parse the user agent string
            user_agent = parse_user_agent(ua_string)
            
            # Extract device information
            is_mobile = user_agent.is_mobile
            is_tablet = user_agent.is_tablet
            is_pc = not (is_mobile or is_tablet)
            is_bot = user_agent.is_bot
            
            # Create structured data dictionary
            return {
                "device_family": user_agent.device.family or "Unknown",
                "os_family": user_agent.os.family or "Unknown",
                "os_version": f"{user_agent.os.version_string}" if user_agent.os.version_string else "Unknown",
                "browser_family": user_agent.browser.family or "Unknown",
                "browser_version": f"{user_agent.browser.version_string}" if user_agent.browser.version_string else "Unknown",
                "is_mobile": is_mobile,
                "is_tablet": is_tablet,
                "is_pc": is_pc,
                "is_bot": is_bot
            }
        except Exception as e:
            # Log the error but return default values rather than failing
            logger.error(f"Error parsing user agent string: {str(e)}")
            return {
                "device_family": "Parse Error",
                "os_family": "Unknown",
                "os_version": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "Unknown",
                "is_mobile": False,
                "is_tablet": False,
                "is_pc": False,
                "is_bot": False
            }

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
            
        # Delegate to repository
        self.qr_code_repo.update_scan_count(qr_id, timestamp, is_genuine_scan_signal=False)

    @MetricsLogger.time_service_call("QRAnalyticsService", "update_scan_statistics")
    def update_scan_statistics(
        self,
        qr_id: str,
        timestamp: datetime | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        is_genuine_scan_signal: bool = False,
    ) -> None:
        """
        Update scan statistics for a QR code.
        
        This method updates the scan count, last scan timestamp, and other
        statistics for a QR code. It is designed to be run as a background
        task to avoid blocking the redirect response.
        
        This implementation orchestrates between QRCodeRepository and ScanLogRepository
        to update QR code statistics and create scan log entries, respectively.
        
        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            client_ip: The IP address of the client that scanned the QR code
            user_agent: The user agent of the client that scanned the QR code
            is_genuine_scan_signal: Whether this is a genuine QR scan (vs. direct URL access)
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(UTC)

            # Parse user agent data
            parsed_ua_data = self._parse_user_agent_data(user_agent)
            
            # 1. Update QR code scan statistics (scan_count, genuine_scan_count, etc.)
            updated_qr = self.qr_code_repo.update_scan_count(qr_id, timestamp, is_genuine_scan_signal)
            if not updated_qr:
                logger.warning(f"Background task: Failed to update scan count for QR ID {qr_id}.")
                return  # Or raise appropriate error
                
            # 2. Create scan log entry
            self.scan_log_repo.create_scan_log(
                qr_id=qr_id,
                timestamp=timestamp,
                ip_address=client_ip,
                raw_user_agent=user_agent,
                parsed_ua_data=parsed_ua_data,
                is_genuine_scan_signal=is_genuine_scan_signal
            )
            logger.info(f"Background task: Scan statistics and log updated for QR ID {qr_id}")
            
        except Exception as e:
            # Log all errors comprehensively but do not re-raise to prevent background task crashes
            logger.exception(f"Background task: Error updating scan statistics for QR ID {qr_id}: {str(e)}")
            # Do not re-raise - allow background task to terminate gracefully

    @MetricsLogger.time_service_call("QRAnalyticsService", "get_scan_analytics_data")
    def get_scan_analytics_data(self, qr_id: str) -> Dict[str, Any]:
        """
        Get detailed scan analytics data for a QR code.
        
        Args:
            qr_id: ID of the QR code to get analytics for
            
        Returns:
            Dictionary containing detailed analytics data
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Get the QR code to verify it exists and get basic info
        qr = self.core_service.get_qr_by_id(qr_id)
        
        # Get scan logs for the QR code
        scan_logs, total_logs = self.scan_log_repo.get_scan_logs_for_qr(qr_id, limit=100)
        
        # Get device statistics
        device_stats = self.scan_log_repo.get_device_statistics(qr_id)
        
        # Get browser statistics
        browser_stats = self.scan_log_repo.get_browser_statistics(qr_id)
        
        # Get OS statistics
        os_stats = self.scan_log_repo.get_os_statistics(qr_id)
        
        # Calculate percentage of genuine scans
        genuine_scan_pct = 0
        if qr.scan_count > 0:
            genuine_scan_pct = round((qr.genuine_scan_count / qr.scan_count) * 100)
        
        # Prepare timestamps for display
        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M")
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        first_genuine_scan_formatted = qr.first_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.first_genuine_scan_at else None
        last_genuine_scan_formatted = qr.last_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_genuine_scan_at else None
        
        # Prepare scan log data for table display
        scan_log_data = []
        for log in scan_logs:
            scan_log_data.append({
                "id": log.id,
                "scanned_at": log.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_genuine_scan": log.is_genuine_scan,
                "device_family": log.device_family,
                "os_family": log.os_family,
                "browser_family": log.browser_family,
                "is_mobile": log.is_mobile,
                "is_tablet": log.is_tablet,
                "is_pc": log.is_pc,
                "is_bot": log.is_bot
            })
        
        # Get time series data for chart (last 7 days)
        time_series_data = self._get_time_series_data(qr_id)
        
        return {
            "qr": qr,
            "created_at_formatted": created_at_formatted,
            "last_scan_formatted": last_scan_formatted,
            "first_genuine_scan_formatted": first_genuine_scan_formatted,
            "last_genuine_scan_formatted": last_genuine_scan_formatted,
            "genuine_scan_pct": genuine_scan_pct,
            "total_logs": total_logs,
            "scan_logs": scan_log_data,
            "device_stats": device_stats,
            "browser_stats": browser_stats,
            "os_stats": os_stats,
            "time_series_data": time_series_data
        }
        
    @MetricsLogger.time_service_call("QRAnalyticsService", "_get_time_series_data")
    def _get_time_series_data(self, qr_id: str) -> Dict[str, List]:
        """
        Get time series scan data for charts (last 7 days).
        
        Args:
            qr_id: ID of the QR code to get time series data for
            
        Returns:
            Dictionary with dates and scan counts
        """
        # Get scan timeseries data
        timeseries_data = self.scan_log_repo.get_scan_timeseries(qr_id, time_range="last7days")
        return timeseries_data 