"""
Custom exception classes for the QR code generator application.

This module defines custom exception classes that can be raised by the application
and handled by the exception handlers in main.py. These exceptions provide a more
specific and consistent way to handle errors across the application.
"""

from typing import Any


class AppBaseException(Exception):
    """
    Base exception class for all application-specific exceptions.

    Attributes:
        status_code: HTTP status code to return
        detail: Error message or details
        headers: Optional HTTP headers to include in the response
    """

    status_code: int = 500

    def __init__(
        self,
        detail: str | list[dict[str, Any]],
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize the exception with detail message, status code, and headers.

        Args:
            detail: Error message or details
            status_code: Optional HTTP status code to override the default
            headers: Optional HTTP headers to include in the response
        """
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        self.headers = headers
        super().__init__(detail)


class QRCodeNotFoundError(AppBaseException):
    """
    Exception raised when a QR code is not found.

    This exception is raised when attempting to retrieve, update, or delete
    a QR code that does not exist in the database.
    """

    status_code = 404

    def __init__(self, detail: str = "QR code not found", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class QRCodeValidationError(AppBaseException):
    """
    Exception raised when QR code data fails validation.

    This exception is raised when the data provided for creating or updating
    a QR code fails validation, such as invalid colors, sizes, or content.
    """

    status_code = 422

    def __init__(
        self,
        detail: str | list[dict[str, Any]] = "QR code validation error",
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message or validation error details
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class DatabaseError(AppBaseException):
    """
    Exception raised when a database operation fails.

    This exception is raised when a database operation fails due to
    connection issues, constraints, or other database-related errors.
    """

    status_code = 500

    def __init__(
        self, detail: str = "Database error occurred", headers: dict[str, str] | None = None
    ):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class InvalidQRTypeError(AppBaseException):
    """
    Exception raised when an invalid QR code type is specified.

    This exception is raised when an invalid QR code type is specified
    in a request, such as when filtering QR codes by type.
    """

    status_code = 400

    def __init__(
        self, detail: str = "Invalid QR type specified", headers: dict[str, str] | None = None
    ):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class RedirectURLError(AppBaseException):
    """
    Exception raised when a redirect URL is invalid.

    This exception is raised when a redirect URL for a dynamic QR code
    is invalid, such as missing a scheme or having an invalid format.
    """

    status_code = 422

    def __init__(self, detail: str = "Invalid redirect URL", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class ResourceConflictError(AppBaseException):
    """
    Exception raised when a resource conflict occurs.

    This exception is raised when attempting to create a resource that
    already exists or would conflict with an existing resource.
    """

    status_code = 409

    def __init__(self, detail: str = "Resource conflict", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)


class RateLimitExceededError(AppBaseException):
    """
    Exception raised when a rate limit is exceeded.

    This exception is raised when a client exceeds a rate limit for
    API requests or other operations.
    """

    status_code = 429

    def __init__(self, detail: str = "Rate limit exceeded", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        if headers is None:
            headers = {}
        # Add Retry-After header if not already present
        if "Retry-After" not in headers:
            headers["Retry-After"] = "60"
        super().__init__(detail=detail, headers=headers)


class ServiceUnavailableError(AppBaseException):
    """
    Exception raised when a service is unavailable.

    This exception is raised when a required service or dependency
    is unavailable, such as a database or external API.
    """

    status_code = 503

    def __init__(self, detail: str = "Service unavailable", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)

class QRCodeGenerationError(AppBaseException):
    """
    Exception raised when QR code image generation fails.

    This exception is raised when there's an error during the process
    of generating the actual QR code image (e.g., from the imaging library).
    """
    status_code = 500 # Internal Server Error, as it's usually a server-side issue

    def __init__(self, detail: str = "QR code image generation failed", headers: dict[str, str] | None = None):
        """
        Initialize the exception with a detail message and headers.

        Args:
            detail: Error message
            headers: Optional HTTP headers to include in the response
        """
        super().__init__(detail=detail, headers=headers)
