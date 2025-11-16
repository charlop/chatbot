"""
Schemas package.
Exports all Pydantic request and response schemas.
"""

from app.schemas.requests import (
    ContractSearchRequest,
    ExtractionApprovalRequest,
    ExtractionRejectionRequest,
    ExtractionEditRequest,
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
    "ExtractionApprovalRequest",
    "ExtractionRejectionRequest",
    "ExtractionEditRequest",
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
