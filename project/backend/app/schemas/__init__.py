"""
Schemas package.
Exports all Pydantic request and response schemas.
"""

from app.schemas.requests import (
    ContractSearchRequest,
    ExtractionSubmitRequest,
    FieldCorrection,
    ChatMessageRequest,
    ExtractionCreateRequest,
)

from app.schemas.responses import (
    ContractResponse,
    ExtractedFieldResponse,
    ExtractionResponse,
    CorrectionResponse,
    AuditEventResponse,
    ErrorResponse,
    ChatResponse,
    HealthResponse,
    MetricsResponse,
)

__all__ = [
    # Requests
    "ContractSearchRequest",
    "ExtractionSubmitRequest",
    "FieldCorrection",
    "ChatMessageRequest",
    "ExtractionCreateRequest",
    # Responses
    "ContractResponse",
    "ExtractedFieldResponse",
    "ExtractionResponse",
    "CorrectionResponse",
    "AuditEventResponse",
    "ErrorResponse",
    "ChatResponse",
    "HealthResponse",
    "MetricsResponse",
]
