"""
Pydantic response schemas for API endpoints.
Handles response serialization and formatting.
"""

from __future__ import annotations

from typing import List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class ContractResponse(BaseModel):
    """
    Response schema for contract data.
    Includes all contract metadata and S3 storage information.

    NOTE: PDFs are accessed via GET /api/v1/contracts/{contract_id}/pdf endpoint
    (backend proxy with IAM authentication), not via direct URL.
    """

    contract_id: str
    account_number: str

    # S3 Storage (for backend use and debugging)
    s3_bucket: str
    s3_key: str

    # Document Content Status (populated by external ETL)
    text_extraction_status: str | None = None  # 'pending', 'completed', 'failed'
    text_extracted_at: datetime | None = None

    # Contract Metadata
    document_repository_id: str | None = None
    contract_type: str
    contract_date: date | None = None
    customer_name: str | None = None
    vehicle_info: dict | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime | None = None

    # NOTE: Extraction relationship will be added in Day 6
    # extraction: ExtractionResponse | None = None

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from ORM models
        json_schema_extra={
            "examples": [
                {
                    "contract_id": "TEST-001",
                    "account_number": "ACC-12345",
                    "s3_bucket": "contracts-production",
                    "s3_key": "contracts/2024/11/TEST-001.pdf",
                    "text_extraction_status": "completed",
                    "text_extracted_at": "2025-11-15T10:00:00Z",
                    "contract_type": "GAP",
                    "customer_name": "John Doe",
                    "vehicle_info": {
                        "make": "Toyota",
                        "model": "Camry",
                        "year": 2020,
                    },
                    "created_at": "2025-11-11T10:00:00Z",
                    "updated_at": "2025-11-11T10:00:00Z",
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
    Includes AI response and source citations.
    """

    message: str = Field(..., description="AI's response message")
    sources: List[dict] | None = Field(
        default=None, description="Source citations from contract/extraction"
    )
    context: dict | None = Field(default=None, description="Additional context used in response")
    llm_provider: str | None = None
    processing_time_ms: int | None = None
    cost_usd: Decimal | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "The GAP insurance premium for this contract is $500.00.",
                    "sources": [
                        {
                            "field": "gap_insurance_premium",
                            "value": "500.00",
                            "confidence": 95.5,
                            "source": {"page": 1, "section": "Pricing"},
                        }
                    ],
                    "llm_provider": "anthropic",
                    "processing_time_ms": 1200,
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
