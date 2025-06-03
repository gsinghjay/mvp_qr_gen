import logging

from app.core.exceptions import QRCodeNotFoundError
from app.repositories.qr_code_repository import QRCodeRepository
from app.core.metrics_logger import MetricsLogger

logger = logging.getLogger(__name__)

class QRDeletionService:
    def __init__(self, qr_code_repo: QRCodeRepository):
        self.qr_code_repo = qr_code_repo

    @MetricsLogger.time_service_call("QRDeletionService", "delete_qr")
    def delete_qr(self, qr_id: str) -> None:
        """
        Delete a QR code by ID.
        (Moved from QRCodeService)
        """
        # Delete QR code using repository
        deleted = self.qr_code_repo.delete(qr_id)
        if not deleted:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        logger.info(f"Deleted QR code with ID {qr_id}")
