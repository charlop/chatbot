"""
Pydantic request schemas for API endpoints.
Handles request validation and serialization.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class ContractSearchRequest(BaseModel):
    """
    Request schema for contract search endpoint.
    Validates account number format.
    """

    account_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Account number to search for",
    )

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Validate account number is not empty and trim whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Account number cannot be empty or whitespace")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"account_number": "ACC-12345"},
                {"account_number": "GAP-2023-001"},
            ]
        }
    }


class FieldCorrection(BaseModel):
    """
    Schema for a single field correction.
    """

    field_name: str = Field(
        ...,
        description="Name of field to correct (gap_insurance_premium, refund_calculation_method, cancellation_fee)",
    )
    corrected_value: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Corrected value for the field",
    )
    correction_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional reason for the correction",
    )

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Validate field name is one of the three extracted fields."""
        valid_fields = {
            "gap_insurance_premium",
            "refund_calculation_method",
            "cancellation_fee",
        }
        if v not in valid_fields:
            raise ValueError(f"field_name must be one of {valid_fields}, got '{v}'")
        return v

    @field_validator("corrected_value")
    @classmethod
    def validate_corrected_value(cls, v: str) -> str:
        """Validate corrected value is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Corrected value cannot be empty or whitespace")
        return v


class ExtractionSubmitRequest(BaseModel):
    """
    Request schema for submitting an extraction with optional corrections.
    Combines approval with inline field corrections.
    """

    corrections: List[FieldCorrection] = Field(
        default_factory=list,
        description="List of field corrections (if any)",
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes about the submission",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "corrections": [],
                    "notes": "All values look correct",
                },
                {
                    "corrections": [
                        {
                            "field_name": "gap_insurance_premium",
                            "corrected_value": "550.00",
                            "correction_reason": "OCR misread the decimal point",
                        }
                    ],
                    "notes": "Corrected premium amount",
                },
            ]
        }
    }


class ChatMessageRequest(BaseModel):
    """
    Request schema for AI chat messages.
    Supports conversation history and session management.
    """

    contract_id: str = Field(
        ...,
        description="Contract ID for context",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message to the AI",
    )
    session_id: str = Field(
        ...,
        description="Chat session ID (UUID v4 format recommended)",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty or whitespace")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contract_id": "TEST-001",
                    "message": "What is the GAP premium for this contract?",
                    "session_id": "example-session-uuid-string",
                },
                {
                    "contract_id": "TEST-001",
                    "message": "And what is the cancellation fee?",
                    "session_id": "example-session-uuid-string",
                },
            ]
        }
    }


class ExtractionCreateRequest(BaseModel):
    """
    Request schema for triggering extraction on a contract.
    Optional parameters for LLM configuration.
    """

    contract_id: str = Field(
        ...,
        description="Contract ID to extract data from",
    )
    llm_provider: str | None = Field(
        default=None,
        description="LLM provider to use (openai, anthropic, bedrock). Defaults to config setting.",
    )
    force_reextract: bool = Field(
        default=False,
        description="Force re-extraction even if extraction already exists",
    )

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str | None) -> str | None:
        """Validate LLM provider if specified."""
        if v is None:
            return v
        valid_providers = {"openai", "anthropic", "bedrock"}
        if v.lower() not in valid_providers:
            raise ValueError(f"llm_provider must be one of {valid_providers}, got '{v}'")
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contract_id": "TEST-001",
                    "llm_provider": None,
                    "force_reextract": False,
                },
                {
                    "contract_id": "TEST-001",
                    "llm_provider": "anthropic",
                    "force_reextract": True,
                },
            ]
        }
    }
