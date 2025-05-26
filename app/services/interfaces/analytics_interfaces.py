"""
Analytics and Scan Event Logging Interface Definitions.

This module defines abstract base classes for analytics data provision and scan event logging
to establish clear contracts for future implementations in the Observatory-First architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class AnalyticsProvider(ABC):
    """
    Abstract base class for analytics data provision.
    
    This interface defines the contract for retrieving analytics data
    about QR code usage and scan statistics.
    """

    @abstractmethod
    async def get_scan_summary(self, qr_id: str) -> Dict[str, Any]:
        """
        Get scan summary statistics for a specific QR code.
        
        Args:
            qr_id: The ID of the QR code to get statistics for
            
        Returns:
            Dictionary containing scan summary data including counts, dates, etc.
            
        Raises:
            QRCodeNotFoundError: If QR code with given ID doesn't exist
        """
        pass

    @abstractmethod
    async def get_detailed_scan_logs(self, qr_id: str, page: int, limit: int) -> Tuple[List[Any], int]:
        """
        Get detailed scan logs for a specific QR code with pagination.
        
        Args:
            qr_id: The ID of the QR code to get logs for
            page: Page number for pagination (0-based)
            limit: Maximum number of logs to return per page
            
        Returns:
            Tuple of (scan_logs_list, total_count)
            
        Raises:
            QRCodeNotFoundError: If QR code with given ID doesn't exist
            ValueError: If page or limit parameters are invalid
        """
        pass


class ScanEventLogger(ABC):
    """
    Abstract base class for scan event logging.
    
    This interface defines the contract for logging QR code scan events
    with detailed analytics information.
    """

    @abstractmethod
    async def log_scan_event(self, qr_id: str, scan_details: Dict[str, Any]) -> None:
        """
        Log a QR code scan event with detailed information.
        
        Args:
            qr_id: The ID of the QR code that was scanned
            scan_details: Dictionary containing scan details such as:
                - ip_address: Client IP address
                - user_agent: User agent string
                - is_genuine_scan: Whether this is a genuine QR scan
                - device info: Parsed device/browser information
                
        Raises:
            QRCodeNotFoundError: If QR code with given ID doesn't exist
            ValidationError: If scan_details contains invalid data
        """
        pass 