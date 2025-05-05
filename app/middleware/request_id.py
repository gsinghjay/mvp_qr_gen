"""
Middleware for adding request IDs to all requests.
"""

import uuid
from datetime import UTC, datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import logging

logger = logging.getLogger("app.middleware.request_id")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.

    This middleware adds a unique ID to each request and includes it in the response headers.
    This helps with tracing requests through logs and metrics.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        """
        Process a request and add a request ID to it.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler to call.

        Returns:
            The response from the next middleware or route handler.
        """
        request_id = str(uuid.uuid4())
        # Add request id to request state
        request.state.request_id = request_id
        # Add timestamp to request state
        request.state.start_time = datetime.now(UTC)
        # Process the request
        response = await call_next(request)
        # Add request id to response headers
        response.headers["X-Request-ID"] = request_id
        return response 