"""
New Analytics Service Implementation.

This module provides the new analytics service implementation using
interfaces in the Observatory-First refactoring architecture.
"""

import logging
from typing import Any, Dict, List, Tuple

from app.core.metrics_logger import MetricsLogger
from app.services.interfaces.analytics_interfaces import AnalyticsProvider, ScanEventLogger

logger = logging.getLogger(__name__)


class NewAnalyticsService:
    """
    New analytics service using interface-based architecture.
    
    This service orchestrates analytics data retrieval and scan event logging
    using injected provider and logger implementations.
    """

    def __init__(self, provider: AnalyticsProvider, logger: ScanEventLogger):
        """
        Initialize the service with provider and logger dependencies.
        
        Args:
            provider: Analytics data provider implementation
            logger: Scan event logger implementation
        """
        self.provider = provider
        self.scan_logger = logger
        logger.info("NewAnalyticsService initialized")

    @MetricsLogger.time_service_call("NewAnalyticsService", "fetch_analytics")
    async def fetch_analytics(self, qr_id: str) -> Dict[str, Any]:
        """
        Fetch comprehensive analytics for a QR code.
        
        Args:
            qr_id: ID of the QR code to get analytics for
            
        Returns:
            Dictionary containing analytics data
            
        Raises:
            QRCodeNotFoundError: If QR code doesn't exist
        """
        try:
            logger.debug(f"Fetching analytics for QR code: {qr_id}")
            
            # Get scan summary
            summary = await self.provider.get_scan_summary(qr_id)
            
            logger.info(f"Successfully fetched analytics for QR code: {qr_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to fetch analytics for QR {qr_id}: {e}")
            raise

    @MetricsLogger.time_service_call("NewAnalyticsService", "fetch_detailed_logs")
    async def fetch_detailed_logs(
        self, 
        qr_id: str, 
        page: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Any], int]:
        """
        Fetch detailed scan logs with pagination.
        
        Args:
            qr_id: ID of the QR code to get logs for
            page: Page number (0-based)
            limit: Number of logs per page
            
        Returns:
            Tuple of (logs_list, total_count)
            
        Raises:
            QRCodeNotFoundError: If QR code doesn't exist
            ValueError: If pagination parameters are invalid
        """
        try:
            logger.debug(f"Fetching detailed logs for QR code: {qr_id} (page {page}, limit {limit})")
            
            # Get detailed logs
            logs, total = await self.provider.get_detailed_scan_logs(qr_id, page, limit)
            
            logger.info(f"Successfully fetched {len(logs)} logs for QR code: {qr_id}")
            return logs, total
            
        except Exception as e:
            logger.error(f"Failed to fetch detailed logs for QR {qr_id}: {e}")
            raise

    @MetricsLogger.time_service_call("NewAnalyticsService", "record_scan")
    async def record_scan(self, qr_id: str, scan_details: Dict[str, Any]) -> None:
        """
        Record a QR code scan event.
        
        Args:
            qr_id: ID of the QR code that was scanned
            scan_details: Details about the scan event
            
        Raises:
            QRCodeNotFoundError: If QR code doesn't exist
            ValidationError: If scan details are invalid
        """
        try:
            logger.debug(f"Recording scan for QR code: {qr_id}")
            
            # Log the scan event
            await self.scan_logger.log_scan_event(qr_id, scan_details)
            
            logger.info(f"Successfully recorded scan for QR code: {qr_id}")
            
        except Exception as e:
            logger.error(f"Failed to record scan for QR {qr_id}: {e}")
            raise

    @MetricsLogger.time_service_call("NewAnalyticsService", "validate_analytics_request")
    async def validate_analytics_request(self, qr_id: str, request_params: Dict[str, Any]) -> bool:
        """
        Validate analytics request parameters.
        
        Args:
            qr_id: QR code ID to validate
            request_params: Request parameters to validate
            
        Returns:
            True if request is valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        try:
            logger.debug(f"Validating analytics request for QR code: {qr_id}")
            
            # Basic validation
            if not qr_id or not qr_id.strip():
                raise ValueError("QR ID is required")
                
            # Validate pagination parameters if present
            if "page" in request_params:
                page = request_params["page"]
                if not isinstance(page, int) or page < 0:
                    raise ValueError("Page must be a non-negative integer")
                    
            if "limit" in request_params:
                limit = request_params["limit"]
                if not isinstance(limit, int) or limit <= 0 or limit > 100:
                    raise ValueError("Limit must be between 1 and 100")
                    
            logger.debug("Analytics request validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Analytics request validation failed: {e}")
            raise 