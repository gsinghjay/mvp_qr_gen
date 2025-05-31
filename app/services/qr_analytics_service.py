"""
Service for QR code analytics and scan tracking.
"""
import logging
from datetime import timezone, datetime # Changed UTC import
from typing import Optional, Dict, List, Any

from user_agents import parse as parse_user_agent

from ..models.qr import QRCode
from ..repositories.qr_code_repository import QRCodeRepository
from ..repositories.scan_log_repository import ScanLogRepository
from ..core.metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)

class QRAnalyticsService:
    """Service class for QR code analytics operations."""

    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        scan_log_repo: ScanLogRepository
    ):
        self.qr_code_repo = qr_code_repo
        self.scan_log_repo = scan_log_repo

    @MetricsLogger.time_service_call("QRAnalyticsService", "_parse_user_agent_data")
    def _parse_user_agent_data(self, ua_string: str | None) -> Dict[str, Any]:
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
            user_agent = parse_user_agent(ua_string)
            return {
                "device_family": user_agent.device.family or "Unknown",
                "os_family": user_agent.os.family or "Unknown",
                "os_version": str(user_agent.os.version_string) if user_agent.os.version_string else "Unknown",
                "browser_family": user_agent.browser.family or "Unknown",
                "browser_version": str(user_agent.browser.version_string) if user_agent.browser.version_string else "Unknown",
                "is_mobile": user_agent.is_mobile,
                "is_tablet": user_agent.is_tablet,
                "is_pc": not (user_agent.is_mobile or user_agent.is_tablet), # Corrected logic
                "is_bot": user_agent.is_bot
            }
        except Exception as e:
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

    @MetricsLogger.time_service_call("QRAnalyticsService", "record_scan_event")
    def record_scan_event(
        self,
        qr_id: str,
        timestamp: Optional[datetime] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_genuine_scan_signal: bool = False,
    ) -> None:
        """
        Records a scan event: updates QR code scan statistics and creates a scan log entry.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            client_ip: The IP address of the client that scanned the QR code
            user_agent: The user agent of the client that scanned the QR code
            is_genuine_scan_signal: Whether this is a genuine QR scan

        Raises:
            QRCodeNotFoundError: If the QR code is not found (from repository)
            DatabaseError: If a database error occurs
        """
        try:
            scan_timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc) # Changed UTC

            parsed_ua_data = self._parse_user_agent_data(user_agent)

            # 1. Update QR code scan statistics (scan_count, genuine_scan_count, etc.)
            # This now directly calls the repository method.
            updated_qr = self.qr_code_repo.update_scan_count(qr_id, scan_timestamp, is_genuine_scan_signal)
            if not updated_qr:
                # This case should be rare if qr_id is valid, as update_scan_count also fetches the QR.
                # However, if it occurs, it implies the QR was deleted between initial fetch and this update.
                logger.warning(f"Failed to update scan count for QR ID {qr_id} during scan event recording (QR not found or update failed).")
                # Depending on desired behavior, could raise QRCodeNotFoundError here or just log and proceed.
                # For now, we'll log and attempt to create scan log entry anyway if other data is present.

            # 2. Create scan log entry
            self.scan_log_repo.create_scan_log(
                qr_id=qr_id,
                timestamp=scan_timestamp,
                ip_address=client_ip,
                raw_user_agent=user_agent,
                parsed_ua_data=parsed_ua_data,
                is_genuine_scan_signal=is_genuine_scan_signal
            )
            logger.info(f"Scan event recorded and statistics updated for QR ID {qr_id}")

        except Exception as e:
            logger.exception(f"Error recording scan event for QR ID {qr_id}: {str(e)}")
            # Do not re-raise to prevent background task crashes if this is used in one.
            # If used synchronously, the caller might expect an exception.
            # For now, matching original behavior of update_scan_statistics.


    @MetricsLogger.time_service_call("QRAnalyticsService", "update_qr_scan_count_stats")
    def update_qr_scan_count_stats(self, qr_id: str, timestamp: Optional[datetime] = None, is_genuine_scan_signal: bool = False) -> None:
        """
        Update the scan count and related timestamps for a QR code.
        This method is a more direct wrapper around the repository's update_scan_count.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            is_genuine_scan_signal: Whether this scan is considered genuine

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        scan_timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc) # Changed UTC
        self.qr_code_repo.update_scan_count(qr_id, scan_timestamp, is_genuine_scan_signal)
        logger.info(f"Scan count stats updated for QR ID {qr_id}")


    @MetricsLogger.time_service_call("QRAnalyticsService", "get_dashboard_summary")
    def get_dashboard_summary(self) -> Dict[str, Any]: # Changed Union to Any for simplicity
        """
        Get data for the dashboard, including total QR code count and recent QR codes.

        Returns:
            Dictionary containing total_qr_codes and recent_qr_codes

        Raises:
            DatabaseError: If a database error occurs
        """
        total_qr_codes = self.qr_code_repo.count()
        recent_qr_codes, _ = self.qr_code_repo.list_qr_codes(
            skip=0,
            limit=5, # Standard limit for dashboard recent items
            sort_by="created_at",
            sort_desc=True
        )
        return {
            "total_qr_codes": total_qr_codes,
            "recent_qr_codes": recent_qr_codes
        }

    @MetricsLogger.time_service_call("QRAnalyticsService", "get_detailed_scan_analytics")
    def get_detailed_scan_analytics(self, qr_id: str) -> Dict[str, Any]:
        """
        Get detailed scan analytics data for a QR code.

        Args:
            qr_id: ID of the QR code to get analytics for

        Returns:
            Dictionary containing detailed analytics data

        Raises:
            QRCodeNotFoundError: If the QR code is not found (from get_by_id)
            DatabaseError: If a database error occurs
        """
        qr = self.qr_code_repo.get_by_id(qr_id) # Ensures QR exists first
        if not qr:
            # This should ideally be caught by the repository's get_by_id if it raises an error.
            # If get_by_id returns None, then this check is needed.
            from ..core.exceptions import QRCodeNotFoundError # Local import to avoid circularity at module level
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found for analytics.")

        scan_logs, total_logs = self.scan_log_repo.get_scan_logs_for_qr(qr_id, limit=100) # Configurable limit?

        device_stats = self.scan_log_repo.get_device_statistics(qr_id)
        browser_stats = self.scan_log_repo.get_browser_statistics(qr_id)
        os_stats = self.scan_log_repo.get_os_statistics(qr_id)

        genuine_scan_pct = 0
        if qr.scan_count > 0: # Ensure scan_count is not zero to avoid DivisionByZero
            genuine_scan_pct = round((qr.genuine_scan_count / qr.scan_count) * 100) if qr.genuine_scan_count else 0

        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M") if qr.created_at else "N/A"
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        first_genuine_scan_formatted = qr.first_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.first_genuine_scan_at else None
        last_genuine_scan_formatted = qr.last_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_genuine_scan_at else None

        scan_log_data = [{
            "id": log.id,
            "scanned_at": log.scanned_at.strftime("%Y-%m-%d %H:%M:%S") if log.scanned_at else "N/A",
            "is_genuine_scan": log.is_genuine_scan,
            "device_family": log.device_family,
            "os_family": log.os_family,
            "browser_family": log.browser_family,
            "is_mobile": log.is_mobile,
            "is_tablet": log.is_tablet,
            "is_pc": log.is_pc,
            "is_bot": log.is_bot
        } for log in scan_logs]

        time_series_data = self._get_scan_timeseries_data(qr_id)

        return {
            "qr": qr.to_dict(), # Return as dict for easier frontend consumption
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

    @MetricsLogger.time_service_call("QRAnalyticsService", "_get_scan_timeseries_data")
    def _get_scan_timeseries_data(self, qr_id: str) -> Dict[str, List[Any]]: # Ensure List item type if known
        """
        Get time series scan data for charts (e.g., last 7 days).

        Args:
            qr_id: ID of the QR code to get time series data for

        Returns:
            Dictionary with dates/labels and scan counts
        """
        # Defaulting to last7days, could be parameterized
        timeseries_data = self.scan_log_repo.get_scan_timeseries(qr_id, time_range="last7days")
        return timeseries_data
