"""
Custom database types for SQLAlchemy models.
"""

from datetime import UTC

from sqlalchemy import DateTime, TypeDecorator


class UTCDateTime(TypeDecorator):
    """
    Custom SQLAlchemy type that ensures timezone awareness.
    Stores datetime in UTC and retrieves as UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert datetime to UTC before storing."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        return value

    def process_result_value(self, value, dialect):
        """Ensure retrieved datetime is timezone-aware."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        return value
