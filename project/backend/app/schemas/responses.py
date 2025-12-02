"""
Pydantic response schemas for API endpoints.
Handles response serialization and formatting.
"""

from __future__ import annotations

from typing import List, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ContractResponse(BaseModel):
    """
    Response schema for contract template data.
    Includes all template metadata and S3 storage information.

    NOTE: This is a TEMPLATE, not a customer contract.
    Templates contain placeholders like [CUSTOMER NAME], [VIN NUMBER], etc.
    Account numbers are mapped to templates via separate mapping table.

    PDFs are accessed via GET /api/v1/contracts/{contract_id}/pdf endpoint
    (backend proxy with IAM authentication), not via direct URL.
    """

    contract_id: str  # Template ID (e.g., GAP-2024-TEMPLATE-001)

    # S3 Storage (for backend use and debugging)
    s3_bucket: str
    s3_key: str

    # Document Content Status (populated by external ETL)
    text_extraction_status: str | None = None  # 'pending', 'completed', 'failed'
    text_extracted_at: datetime | None = None

    # Template Metadata
    document_repository_id: str | None = None
    contract_type: str  # GAP, VSC, etc.
    contract_date: date | None = None  # When template was created

    # Template Versioning
    template_version: str | None = None  # e.g., "1.0", "2.0"
    effective_date: date | None = None  # When this version became active
    deprecated_date: date | None = None  # When this version was superseded
    is_active: bool = True  # Whether this template version is currently active

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime | None = None

    # Extracted data (flattened for frontend compatibility)
    extracted_data: dict | None = None

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from ORM models
        populate_by_name=True,  # Allow population by field name or alias
        alias_generator=to_camel,  # Convert to camelCase for JSON
        json_schema_extra={
            "examples": [
                {
                    "contractId": "GAP-2024-TEMPLATE-001",
                    "s3Bucket": "contract-templates-dev",
                    "s3Key": "templates/GAP-2024-TEMPLATE-001.pdf",
                    "textExtractionStatus": "completed",
                    "textExtractedAt": "2025-11-15T10:00:00Z",
                    "contractType": "GAP",
                    "contractDate": "2024-01-15",
                    "templateVersion": "1.0",
                    "effectiveDate": "2024-01-15",
                    "deprecatedDate": None,
                    "isActive": True,
                    "createdAt": "2025-11-11T10:00:00Z",
                    "updatedAt": "2025-11-11T10:00:00Z",
                }
            ]
        },
    )


class ExtractedFieldResponse(BaseModel):
    """
    Response schema for a single extracted field with confidence and source.
    """

    value: str | Decimal | None
    confidence: Decimal | None = Field(None, description="Confidence score (0-100)")
    source: dict | None = Field(None, description="Source location in PDF (page, section, line)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "value": "500.00",
                    "confidence": 95.5,
                    "source": {"page": 1, "section": "Pricing", "line": 10},
                }
            ]
        }
    )


class FieldValidationResponse(BaseModel):
    """
    Response schema for field validation result.
    Contains validation status, reasoning, and tool name.
    """

    field_name: str = Field(..., description="Field name that was validated")
    status: Literal["pass", "warning", "fail"] = Field(..., description="Validation status")
    message: str = Field(..., description="Human-readable validation message")
    tool_name: str | None = Field(None, description="Name of the validation tool")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "field_name": "gap_insurance_premium",
                    "status": "pass",
                    "message": "Premium $500.00 is within expected range",
                    "tool_name": "rule_validator",
                }
            ]
        }
    )


class ExtractionResponse(BaseModel):
    """
    Response schema for extraction data.
    Includes all three extracted fields with confidence scores and sources.
    """

    extraction_id: UUID
    contract_id: str

    # Extracted fields
    gap_insurance_premium: ExtractedFieldResponse | None = None
    refund_calculation_method: ExtractedFieldResponse | None = None
    cancellation_fee: ExtractedFieldResponse | None = None

    # LLM metadata
    llm_model_version: str
    llm_provider: str | None = None
    processing_time_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_cost_usd: Decimal | None = None

    # Status and approval
    status: str
    extracted_at: datetime
    extracted_by: UUID | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None

    # Validation results (Phase 1: Validation Agent)
    validation_status: Literal["pass", "warning", "fail"] | None = None
    validation_results: List[FieldValidationResponse] | None = None
    validated_at: datetime | None = None

    # TODO: Add corrections in Day 7
    # corrections: List["CorrectionResponse"] | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, extraction: Any) -> "ExtractionResponse":
        """
        Create response from ORM model, handling field grouping.
        """
        return cls(
            extraction_id=extraction.extraction_id,
            contract_id=extraction.contract_id,
            gap_insurance_premium=(
                ExtractedFieldResponse(
                    value=extraction.gap_insurance_premium,
                    confidence=extraction.gap_premium_confidence,
                    source=extraction.gap_premium_source,
                )
                if extraction.gap_insurance_premium is not None
                else None
            ),
            refund_calculation_method=(
                ExtractedFieldResponse(
                    value=extraction.refund_calculation_method,
                    confidence=extraction.refund_method_confidence,
                    source=extraction.refund_method_source,
                )
                if extraction.refund_calculation_method is not None
                else None
            ),
            cancellation_fee=(
                ExtractedFieldResponse(
                    value=extraction.cancellation_fee,
                    confidence=extraction.cancellation_fee_confidence,
                    source=extraction.cancellation_fee_source,
                )
                if extraction.cancellation_fee is not None
                else None
            ),
            llm_model_version=extraction.llm_model_version,
            llm_provider=extraction.llm_provider,
            processing_time_ms=extraction.processing_time_ms,
            prompt_tokens=extraction.prompt_tokens,
            completion_tokens=extraction.completion_tokens,
            total_cost_usd=extraction.total_cost_usd,
            status=extraction.status,
            extracted_at=extraction.extracted_at,
            extracted_by=extraction.extracted_by,
            approved_at=extraction.approved_at,
            approved_by=extraction.approved_by,
            # Validation results
            validation_status=extraction.validation_status,
            validation_results=(
                [
                    FieldValidationResponse(**result)
                    for result in extraction.validation_results.get("field_results", [])
                ]
                if extraction.validation_results
                else None
            ),
            validated_at=extraction.validated_at,
            # corrections=None,  # Will be populated separately if needed (Day 7)
        )


class CorrectionResponse(BaseModel):
    """
    Response schema for correction data.
    Shows field correction history.
    """

    correction_id: UUID
    extraction_id: UUID
    field_name: str
    original_value: str | None
    corrected_value: str
    correction_reason: str | None
    corrected_by: UUID
    corrected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    """
    Response schema for audit event data.
    Shows system activity log.
    """

    event_id: UUID
    event_type: str
    contract_id: str | None
    extraction_id: UUID | None
    user_id: UUID | None
    event_data: dict | None
    timestamp: datetime
    ip_address: str | None
    user_agent: str | None
    duration_ms: int | None
    cost_usd: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """
    Standardized error response format.
    Used for all API errors.
    """

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: dict | None = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the error occurred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "CONTRACT_NOT_FOUND",
                    "message": "Contract with account number ACC-12345 not found",
                    "details": {"account_number": "ACC-12345"},
                    "timestamp": "2025-11-11T10:00:00Z",
                },
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid field name",
                    "details": {
                        "field": "field_name",
                        "value": "invalid_field",
                        "allowed_values": [
                            "gap_insurance_premium",
                            "refund_calculation_method",
                            "cancellation_fee",
                        ],
                    },
                    "timestamp": "2025-11-11T10:00:00Z",
                },
            ]
        }
    )


class ChatResponse(BaseModel):
    """
    Response schema for AI chat messages.
    Includes AI response, source citations, and session management.
    """

    response: str = Field(..., description="AI's response message")
    sources: List[dict] | None = Field(
        default=None, description="Source citations from contract/extraction"
    )
    metadata: dict = Field(
        ..., description="Response metadata (session_id, contract_id, model, etc.)"
    )
    detected_account_number: str | None = Field(
        default=None, description="Account number detected in user message (if any)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "response": "The GAP insurance premium for this contract is $500.00.",
                    "sources": [
                        {
                            "field": "gap_insurance_premium",
                            "value": "500.00",
                            "confidence": 95.5,
                            "source": {"page": 1, "section": "Pricing"},
                        }
                    ],
                    "metadata": {
                        "session_id": "example-session-id",
                        "contract_id": "TEST-001",
                        "model": "claude-3-5-sonnet",
                        "provider": "anthropic",
                        "duration_ms": 1200,
                        "message_count": 2,
                    },
                    "detected_account_number": None,
                }
            ]
        }
    )


class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint.
    """

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    environment: str = Field(..., description="Environment (development, production)")
    database: str | None = Field(default=None, description="Database connection status")
    redis: str | None = Field(default=None, description="Redis connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "service": "Contract Refund Eligibility System",
                    "environment": "development",
                    "database": "connected",
                    "redis": "not_configured",
                    "timestamp": "2025-11-11T10:00:00Z",
                }
            ]
        }
    )


class MetricsResponse(BaseModel):
    """
    Response schema for system metrics endpoint.
    """

    total_contracts: int
    total_extractions: int
    extractions_pending: int
    extractions_approved: int
    extractions_rejected: int
    average_extraction_time_ms: int | None
    cache_hit_rate: float | None
    daily_counts: dict | None = Field(default=None, description="Daily extraction counts")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_contracts": 150,
                    "total_extractions": 120,
                    "extractions_pending": 25,
                    "extractions_approved": 80,
                    "extractions_rejected": 15,
                    "average_extraction_time_ms": 1500,
                    "cache_hit_rate": 0.75,
                }
            ]
        }
    )


class UserResponse(BaseModel):
    """
    Response schema for user data.
    Returned by user management endpoints.
    """

    user_id: UUID
    auth_provider: str
    auth_provider_user_id: str
    email: str
    username: str | None
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "userId": "user-id-example",
                    "authProvider": "auth0",
                    "authProviderUserId": "auth0|123456789",
                    "email": "john.doe@example.com",
                    "username": None,
                    "firstName": "John",
                    "lastName": "Doe",
                    "role": "user",
                    "isActive": True,
                    "createdAt": "2025-11-11T10:00:00Z",
                    "updatedAt": "2025-11-11T10:00:00Z",
                }
            ]
        },
    )


class UserListResponse(BaseModel):
    """
    Response schema for paginated user list.
    """

    users: List[UserResponse]
    total: int
    offset: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "users": [
                        {
                            "userId": "user-id-example",
                            "authProvider": "auth0",
                            "authProviderUserId": "auth0|123456789",
                            "email": "john.doe@example.com",
                            "username": None,
                            "firstName": "John",
                            "lastName": "Doe",
                            "role": "user",
                            "isActive": True,
                            "createdAt": "2025-11-11T10:00:00Z",
                            "updatedAt": "2025-11-11T10:00:00Z",
                        }
                    ],
                    "total": 1,
                    "offset": 0,
                    "limit": 100,
                }
            ]
        }
    )
