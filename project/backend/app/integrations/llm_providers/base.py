"""
Base LLM Provider Interface

Abstract base class defining the interface for all LLM providers.
Supports vendor-agnostic integration with OpenAI, Anthropic, AWS Bedrock, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class FieldExtraction(BaseModel):
    """Single extracted field with confidence and source location"""

    value: str | Decimal | None = Field(..., description="Extracted value")
    confidence: Decimal = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    source: dict | None = Field(
        default=None, description="Source location in PDF (page, section, line)"
    )


class ExtractionResult(BaseModel):
    """
    Result of LLM extraction containing all extracted fields.

    This is the standardized format returned by all LLM providers.
    """

    # Extracted fields
    gap_insurance_premium: FieldExtraction | None = Field(
        default=None, description="GAP insurance premium amount"
    )
    refund_calculation_method: FieldExtraction | None = Field(
        default=None, description="Refund calculation method (pro-rata, rule of 78s, etc.)"
    )
    cancellation_fee: FieldExtraction | None = Field(
        default=None, description="Cancellation/administrative fee"
    )

    # LLM metadata
    model_version: str = Field(..., description="LLM model used (e.g., gpt-4, claude-3-sonnet)")
    provider: str = Field(..., description="Provider name (openai, anthropic, bedrock)")
    processing_time_ms: int | None = Field(default=None, description="Processing time in ms")
    prompt_tokens: int | None = Field(default=None, description="Tokens used in prompt")
    completion_tokens: int | None = Field(default=None, description="Tokens used in completion")
    total_cost_usd: Decimal | None = Field(default=None, description="Estimated cost in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "gap_insurance_premium": {
                    "value": "1249.00",
                    "confidence": 96.5,
                    "source": {"page": 3, "section": "Pricing", "line": 18},
                },
                "refund_calculation_method": {
                    "value": "Pro-Rata",
                    "confidence": 98.2,
                    "source": {"page": 5, "section": "Cancellation", "line": 4},
                },
                "cancellation_fee": {
                    "value": "50.00",
                    "confidence": 87.3,
                    "source": {"page": 5, "section": "Fees", "line": 12},
                },
                "model_version": "gpt-4-turbo-preview",
                "provider": "openai",
                "processing_time_ms": 2341,
                "prompt_tokens": 1523,
                "completion_tokens": 342,
                "total_cost_usd": "0.0234",
            }
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM integrations (OpenAI, Anthropic, Bedrock) must implement this interface.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize LLM provider.

        Args:
            api_key: API key for the provider
            model: Model version to use (provider-specific default if None)
        """
        self.api_key = api_key
        self.model = model or self.default_model()

    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass

    @abstractmethod
    async def extract_contract_data(self, document_text: str, contract_id: str) -> ExtractionResult:
        """
        Extract contract data from document text using LLM.

        Args:
            document_text: Full text extracted from PDF
            contract_id: Contract ID for logging/tracking

        Returns:
            ExtractionResult with extracted fields and metadata

        Raises:
            LLMError: If extraction fails
            RateLimitError: If rate limit exceeded
            TimeoutError: If request times out
        """
        pass

    @abstractmethod
    async def chat(
        self,
        message: str,
        context: dict,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Chat interface for contract Q&A.

        Args:
            message: User's message/question
            context: Contract and extraction context
            history: Previous messages in conversation

        Returns:
            dict with 'response', 'sources', and metadata
        """
        pass


class LLMError(Exception):
    """Base exception for LLM provider errors"""

    pass


class RateLimitError(LLMError):
    """Rate limit exceeded"""

    pass


class TimeoutError(LLMError):
    """Request timeout"""

    pass


class ValidationError(LLMError):
    """Response validation failed"""

    pass
