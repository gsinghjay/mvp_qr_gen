import logging
from datetime import UTC, datetime # Ensure UTC is available if used by moved methods
from typing import Dict # For type hinting if necessary

from pydantic import ValidationError # For exception handling if moved

from app.core.config import Settings # If settings are used by moved methods
from app.core.exceptions import (
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError
)
from app.models.qr import QRCode
from app.repositories.qr_code_repository import QRCodeRepository
from app.schemas.common import QRType # If used by moved methods
from app.schemas.qr.parameters import QRUpdateParameters
from app.services.qr_retrieval_service import QRRetrievalService # For get_qr_by_id
from app.services.qr_creation_service import QRCreationService # For _is_safe_redirect_url
from app.core.metrics_logger import MetricsLogger # If used by moved methods

logger = logging.getLogger(__name__)

class QRUpdateService:
    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        qr_retrieval_service: QRRetrievalService,
        qr_creation_service: QRCreationService, # To access _is_safe_redirect_url
        # settings: Settings, # Not directly used by update_qr, but _is_safe_redirect_url in QRCreationService uses its own settings
    ):
        self.qr_code_repo = qr_code_repo
        self.qr_retrieval_service = qr_retrieval_service
        self.qr_creation_service = qr_creation_service
        # self.settings = settings # Settings not directly used by this service's methods

    @MetricsLogger.time_service_call("QRUpdateService", "update_qr") # Updated Metric Tag
    async def update_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a QR code with the provided data.
        (Moved from QRCodeService)
        """
        try:
            # Get the QR code using QRRetrievalService
            qr = await self.qr_retrieval_service.get_qr_by_id(qr_id)

            update_data = {}

            if data.title is not None:
                update_data["title"] = data.title

            if data.description is not None:
                update_data["description"] = data.description

            if data.redirect_url is not None:
                if qr.qr_type != QRType.DYNAMIC.value: # Assuming QRType is available
                    raise QRCodeValidationError(f"Cannot update redirect URL for non-dynamic QR code: {qr_id}")

                redirect_url_str = str(data.redirect_url)
                # Use _is_safe_redirect_url from QRCreationService
                if not self.qr_creation_service._is_safe_redirect_url(redirect_url_str):
                    raise RedirectURLError(f"Redirect URL not allowed: {redirect_url_str}")

                update_data["redirect_url"] = redirect_url_str

            if update_data:
                update_data["updated_at"] = datetime.now(UTC) # Ensure UTC is imported
            else:
                return qr

            updated_qr = self.qr_code_repo.update_qr(qr_id, update_data)
            if not updated_qr:
                # This case should ideally not be reached if get_qr_by_id succeeded,
                # but kept for safety, or if update_qr itself could fail to find.
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found during update")

            logger.info(f"Updated QR code with ID {updated_qr.id}")
            return updated_qr
        except ValidationError as e:
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e: # Catching generic ValueError for URL validation etc.
            if "URL" in str(e): # Heuristic to check if it's a URL error
                logger.error(f"Invalid redirect URL during update: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Value error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(str(e))

    @MetricsLogger.time_service_call("QRUpdateService", "update_dynamic_qr") # Updated Metric Tag
    async def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a dynamic QR code. Alias for update_qr.
        (Moved from QRCodeService)
        """
        return await self.update_qr(qr_id, data)
