"""
Pydantic request schemas for API endpoints.
Handles request validation and serialization.
"""

import re
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ContractSearchRequest(BaseModel):
    """
    Request schema for contract template search endpoint.
    Supports searching by account number OR template ID (mutually exclusive).
    """

    account_number: str | None = Field(
        default=None,
        description="Account number to search for (12 digits, e.g., 000000000001)",
    )
    contract_id: str | None = Field(
        default=None,
        description="Contract template ID to search for (e.g., GAP-2024-TEMPLATE-001)",
    )

    @field_validator("account_number", mode="before")
    @classmethod
    def validate_account_number(cls, v: str | None) -> str | None:
        """
        Validate account number is exactly 12 digits.
        Format: 12 numeric digits (e.g., 000000000001)
        Strips whitespace before validation.
        """
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("Account number must be a string")

        v = v.strip()

        # Check if empty
        if not v:
            raise ValueError("Account number cannot be empty or whitespace")

        # Check if exactly 12 digits
        if not re.match(r"^[0-9]{12}$", v):
            raise ValueError(
                "Account number must be exactly 12 digits (e.g., 000000000001). "
                f"Got '{v}' with length {len(v)}"
            )

        return v

    @field_validator("contract_id", mode="before")
    @classmethod
    def validate_contract_id(cls, v: str | None) -> str | None:
        """
        Validate contract template ID format.
        """
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("Contract ID must be a string")

        v = v.strip()

        if not v:
            raise ValueError("Contract ID cannot be empty or whitespace")

        # Validate length
        if len(v) > 100:
            raise ValueError(f"Contract ID too long (max 100 chars), got {len(v)}")

        return v

    def model_post_init(self, __context):
        """Validate exactly one search parameter is provided."""
        if not self.account_number and not self.contract_id:
            raise ValueError("Either account_number or contract_id must be provided")
        if self.account_number and self.contract_id:
            raise ValueError("Cannot provide both account_number and contract_id")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"account_number": "000000000001"},
                {"contract_id": "GAP-2024-TEMPLATE-001"},
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


class UserCreateRequest(BaseModel):
    """
    Request schema for creating a new user.
    Admin-only operation.
    """

    auth_provider: str = Field(
        ...,
        description="Authentication provider (e.g., 'auth0', 'okta')",
    )
    auth_provider_user_id: str = Field(
        ...,
        description="User ID from auth provider",
    )
    email: str = Field(
        ...,
        description="User's email address",
    )
    first_name: str | None = Field(
        default=None,
        description="User's first name",
    )
    last_name: str | None = Field(
        default=None,
        description="User's last name",
    )
    role: str = Field(
        default="user",
        description="User role ('admin' or 'user')",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        v = v.strip().lower()
        if not v:
            raise ValueError("Email cannot be empty")
        # Basic email validation
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is admin or user."""
        if v not in {"admin", "user"}:
            raise ValueError("Role must be 'admin' or 'user'")
        return v

    @field_validator("auth_provider")
    @classmethod
    def validate_auth_provider(cls, v: str) -> str:
        """Validate auth provider is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Auth provider cannot be empty")
        return v

    @field_validator("auth_provider_user_id")
    @classmethod
    def validate_auth_provider_user_id(cls, v: str) -> str:
        """Validate auth provider user ID is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Auth provider user ID cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "auth_provider": "auth0",
                    "auth_provider_user_id": "auth0|123456789",
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "user",
                }
            ]
        }
    }


class UserUpdateRequest(BaseModel):
    """
    Request schema for updating a user.
    Admin-only operation. All fields are optional.
    """

    email: str | None = Field(
        default=None,
        description="User's email address",
    )
    first_name: str | None = Field(
        default=None,
        description="User's first name",
    )
    last_name: str | None = Field(
        default=None,
        description="User's last name",
    )
    role: str | None = Field(
        default=None,
        description="User role ('admin' or 'user')",
    )
    is_active: bool | None = Field(
        default=None,
        description="User active status",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format."""
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            raise ValueError("Email cannot be empty")
        # Basic email validation
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        """Validate role is admin or user."""
        if v is None:
            return v
        if v not in {"admin", "user"}:
            raise ValueError("Role must be 'admin' or 'user'")
        return v

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both camelCase and snake_case
        alias_generator=to_camel,  # Accept camelCase from frontend
        json_schema_extra={
            "examples": [
                {
                    "role": "admin",
                },
                {
                    "email": "updated.email@example.com",
                    "firstName": "Jane",
                    "isActive": False,
                },
            ]
        },
    )
