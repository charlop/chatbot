"""
External RDB integration package.

Provides client for looking up contract template IDs from account numbers
via external database API.
"""

from app.integrations.external_rdb.client import ExternalRDBClient
from app.integrations.external_rdb.exceptions import (
    ExternalRDBAuthenticationError,
    ExternalRDBConnectionError,
    ExternalRDBError,
    ExternalRDBNotFoundError,
    ExternalRDBTimeoutError,
)
from app.integrations.external_rdb.models import (
    ExternalRDBHealthResponse,
    ExternalRDBLookupResponse,
)

__all__ = [
    "ExternalRDBClient",
    "ExternalRDBError",
    "ExternalRDBConnectionError",
    "ExternalRDBTimeoutError",
    "ExternalRDBNotFoundError",
    "ExternalRDBAuthenticationError",
    "ExternalRDBLookupResponse",
    "ExternalRDBHealthResponse",
]
