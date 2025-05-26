"""
Core QR code operations including retrieval, listing, and deletion.
"""

import logging
from typing import List, Optional, Tuple, Union, Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from ...core.exceptions import QRCodeNotFoundError, DatabaseError, InvalidQRTypeError
from ...core.metrics_logger import MetricsLogger
from ...models.qr import QRCode
from ...repositories import QRCodeRepository
from ...schemas.common import QRType

# Configure logger
logger = logging.getLogger(__name__)

class QRCoreService:
    """Service class for core QR code operations."""

    def __init__(self, qr_code_repo: QRCodeRepository):
        """
        Initialize the QR core service with repository.

        Args:
            qr_code_repo: Specialized QRCodeRepository for QR code operations
        """
        self.qr_code_repo = qr_code_repo
        
    @MetricsLogger.time_service_call("QRCoreService", "get_qr_by_id")
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
        qr = self.qr_code_repo.get_by_id(qr_id)
            
        if not qr:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        return qr

    @MetricsLogger.time_service_call("QRCoreService", "get_qr_by_short_id")
    def get_qr_by_short_id(self, short_id: str) -> QRCode:
        """
        Get a QR code by its short ID (used for redirects).

        Args:
            short_id: The short ID of the QR code to retrieve

        Returns:
            The QR code object

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            InvalidQRTypeError: If the QR code is not of type 'dynamic'
            DatabaseError: If a database error occurs
        """
        # Look up QR code directly by short_id
        qr = self.qr_code_repo.get_by_short_id(short_id)

        if not qr:
            logger.warning(f"QR code with short ID {short_id} not found")
            raise QRCodeNotFoundError(f"QR code with short ID {short_id} not found")

        # Ensure the QR code is of type 'dynamic' for redirects
        if qr.qr_type != 'dynamic':
            logger.warning(f"QR code with short ID {short_id} is not dynamic (type: {qr.qr_type})")
            raise InvalidQRTypeError(f"QR code with short ID {short_id} is not dynamic")

        return qr

    @MetricsLogger.time_service_call("QRCoreService", "list_qr_codes")
    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: Union[QRType, str, None] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        """
        List QR codes with optional filtering and sorting.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            qr_type: QR code type to filter by
            search: Search term for filtering
            sort_by: Field to sort by
            sort_desc: Sort in descending order if true

        Returns:
            Tuple of (list of QR codes, total count)

        Raises:
            DatabaseError: If a database error occurs
        """
        # Convert enum to value if it's an enum
        qr_type_str = None
        if qr_type is not None:
            if isinstance(qr_type, QRType):
                qr_type_str = qr_type.value
            else:
                qr_type_str = qr_type

        return self.qr_code_repo.list_qr_codes(
            skip=skip,
            limit=limit,
            qr_type=qr_type_str,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    @MetricsLogger.time_service_call("QRCoreService", "delete_qr")
    def delete_qr(self, qr_id: str) -> None:
        """
        Delete a QR code by ID.

        Args:
            qr_id: The ID of the QR code to delete

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Delete QR code using repository
        deleted = self.qr_code_repo.delete(qr_id)
        if not deleted:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        logger.info(f"Deleted QR code with ID {qr_id}")
    
    @MetricsLogger.time_service_call("QRCoreService", "get_dashboard_data")
    def get_dashboard_data(self) -> Dict[str, Union[int, List[QRCode]]]:
        """
        Get data for the dashboard, including total QR code count and recent QR codes.
        
        Returns:
            Dictionary containing total_qr_codes and recent_qr_codes
            
        Raises:
            DatabaseError: If a database error occurs
        """
        # Get count of all QR codes
        total_qr_codes = self.qr_code_repo.count()
        
        # Get recent QR codes
        recent_qr_codes, _ = self.qr_code_repo.list_qr_codes(
            skip=0,
            limit=5,
            sort_by="created_at",
            sort_desc=True
        )
        
        return {
            "total_qr_codes": total_qr_codes,
            "recent_qr_codes": recent_qr_codes
        } 