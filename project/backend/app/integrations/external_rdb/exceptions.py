"""
External RDB exceptions.
"""


class ExternalRDBError(Exception):
    """Base exception for External RDB errors."""

    pass


class ExternalRDBConnectionError(ExternalRDBError):
    """Raised when connection to external RDB fails."""

    pass


class ExternalRDBTimeoutError(ExternalRDBError):
    """Raised when external RDB request times out."""

    pass


class ExternalRDBNotFoundError(ExternalRDBError):
    """Raised when account number is not found in external RDB."""

    pass


class ExternalRDBAuthenticationError(ExternalRDBError):
    """Raised when authentication with external RDB fails."""

    pass
