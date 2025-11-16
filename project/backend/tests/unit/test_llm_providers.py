"""
Unit tests for LLM providers (OpenAI and Anthropic).

Tests structured extraction, error handling, and provider-specific implementations.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.integrations.llm_providers.base import (
    FieldExtraction,
    ExtractionResult,
    LLMError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from app.integrations.llm_providers.openai_provider import OpenAIProvider
from app.integrations.llm_providers.anthropic_provider import AnthropicProvider


# Test Fixtures
@pytest.fixture
def sample_contract_text():
    """Sample contract text for extraction testing"""
    return """
    GAP INSURANCE CONTRACT

    Contract ID: TEST-001
    Account Number: ACC-12345

    PRICING DETAILS
    GAP Insurance Premium: $495.00

    REFUND POLICY
    Refunds are calculated using the Pro-Rata method.

    CANCELLATION TERMS
    Administrative Fee: $50.00
    """


@pytest.fixture
def expected_extraction_data():
    """Expected extraction result structure"""
    return {
        "gap_insurance_premium": {
            "value": "495.00",
            "confidence": 95,
            "source": {"page": 1, "section": "Pricing", "line": 7},
        },
        "refund_calculation_method": {
            "value": "Pro-Rata",
            "confidence": 90,
            "source": {"page": 1, "section": "Refund Policy", "line": 10},
        },
        "cancellation_fee": {
            "value": "50.00",
            "confidence": 92,
            "source": {"page": 1, "section": "Cancellation", "line": 13},
        },
    }


# OpenAI Provider Tests
class TestOpenAIProvider:
    """Test suite for OpenAI provider"""

    @pytest.fixture
    def openai_provider(self):
        """Create OpenAI provider instance"""
        return OpenAIProvider(api_key="test-api-key")

    @pytest.fixture
    def mock_openai_response(self, expected_extraction_data):
        """Mock OpenAI API response"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.arguments = json.dumps(
            expected_extraction_data
        )
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.completion_tokens = 200
        return mock_response

    def test_default_model(self, openai_provider):
        """Test default model is GPT-4 Turbo"""
        assert openai_provider.model == "gpt-4-turbo-preview"

    def test_custom_model(self):
        """Test custom model can be specified"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        assert provider.model == "gpt-4"

    def test_build_extraction_function(self, openai_provider):
        """Test extraction function schema is correct"""
        function = openai_provider._build_extraction_function()

        assert function["name"] == "extract_contract_data"
        assert "parameters" in function
        assert "gap_insurance_premium" in function["parameters"]["properties"]
        assert "refund_calculation_method" in function["parameters"]["properties"]
        assert "cancellation_fee" in function["parameters"]["properties"]

    @pytest.mark.asyncio
    async def test_extract_contract_data_success(
        self, openai_provider, sample_contract_text, mock_openai_response
    ):
        """Test successful contract extraction"""
        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_openai_response,
        ):
            result = await openai_provider.extract_contract_data(sample_contract_text, "TEST-001")

            # Verify result structure
            assert isinstance(result, ExtractionResult)
            assert result.provider == "openai"
            assert result.model_version == "gpt-4-turbo-preview"

            # Verify extracted fields
            assert result.gap_insurance_premium is not None
            assert result.gap_insurance_premium.value == "495.00"
            assert result.gap_insurance_premium.confidence == Decimal("95")

            assert result.refund_calculation_method is not None
            assert result.refund_calculation_method.value == "Pro-Rata"

            assert result.cancellation_fee is not None
            assert result.cancellation_fee.value == "50.00"

            # Verify metadata
            assert result.prompt_tokens == 1000
            assert result.completion_tokens == 200
            assert result.total_cost_usd > 0

    @pytest.mark.asyncio
    async def test_extract_rate_limit_error(self, openai_provider, sample_contract_text):
        """Test rate limit error handling"""
        from openai import RateLimitError as OpenAIRateLimitError

        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=OpenAIRateLimitError(
                "Rate limit exceeded", response=MagicMock(), body=None
            ),
        ):
            with pytest.raises(RateLimitError, match="rate limit"):
                await openai_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_extract_timeout_error(self, openai_provider, sample_contract_text):
        """Test timeout error handling"""
        from openai import APITimeoutError

        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            side_effect=APITimeoutError(request=MagicMock()),
        ):
            with pytest.raises(TimeoutError, match="timeout"):
                await openai_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_extract_invalid_json_response(self, openai_provider, sample_contract_text):
        """Test invalid JSON response handling"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.function_call = MagicMock()
        mock_response.choices[0].message.function_call.arguments = "invalid json {{"

        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ValidationError, match="Invalid JSON"):
                await openai_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_extract_no_function_call(self, openai_provider, sample_contract_text):
        """Test response without function call"""
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.function_call = None
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_response.usage = None

        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ValidationError, match="No function call"):
                await openai_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_chat_interface(self, openai_provider):
        """Test chat interface"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "The premium is $495.00"

        with patch.object(
            openai_provider.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await openai_provider.chat(
                message="What is the premium?",
                context={"contract_id": "TEST-001", "account_number": "ACC-12345"},
                history=None,
            )

            assert result["response"] == "The premium is $495.00"
            assert result["provider"] == "openai"
            assert result["model"] == "gpt-4-turbo-preview"


# Anthropic Provider Tests
class TestAnthropicProvider:
    """Test suite for Anthropic provider"""

    @pytest.fixture
    def anthropic_provider(self):
        """Create Anthropic provider instance"""
        return AnthropicProvider(api_key="test-api-key")

    @pytest.fixture
    def mock_anthropic_response(self, expected_extraction_data):
        """Mock Anthropic API response"""
        mock_response = MagicMock()

        # Create tool use block
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "extract_contract_data"
        tool_block.input = expected_extraction_data

        mock_response.content = [tool_block]
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 1000
        mock_response.usage.output_tokens = 200

        return mock_response

    def test_default_model(self, anthropic_provider):
        """Test default model is Claude 3.5 Sonnet"""
        assert anthropic_provider.model == "claude-3-5-sonnet-20241022"

    def test_custom_model(self):
        """Test custom model can be specified"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-opus-20240229")
        assert provider.model == "claude-3-opus-20240229"

    def test_build_extraction_tool(self, anthropic_provider):
        """Test extraction tool schema is correct"""
        tool = anthropic_provider._build_extraction_tool()

        assert tool["name"] == "extract_contract_data"
        assert "input_schema" in tool
        assert "gap_insurance_premium" in tool["input_schema"]["properties"]
        assert "refund_calculation_method" in tool["input_schema"]["properties"]
        assert "cancellation_fee" in tool["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_extract_contract_data_success(
        self, anthropic_provider, sample_contract_text, mock_anthropic_response
    ):
        """Test successful contract extraction"""
        with patch.object(
            anthropic_provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_anthropic_response,
        ):
            result = await anthropic_provider.extract_contract_data(
                sample_contract_text, "TEST-001"
            )

            # Verify result structure
            assert isinstance(result, ExtractionResult)
            assert result.provider == "anthropic"
            assert result.model_version == "claude-3-5-sonnet-20241022"

            # Verify extracted fields
            assert result.gap_insurance_premium is not None
            assert result.gap_insurance_premium.value == "495.00"
            assert result.gap_insurance_premium.confidence == Decimal("95")

            assert result.refund_calculation_method is not None
            assert result.refund_calculation_method.value == "Pro-Rata"

            assert result.cancellation_fee is not None
            assert result.cancellation_fee.value == "50.00"

            # Verify metadata
            assert result.prompt_tokens == 1000
            assert result.completion_tokens == 200
            assert result.total_cost_usd > 0

    @pytest.mark.asyncio
    async def test_extract_rate_limit_error(self, anthropic_provider, sample_contract_text):
        """Test rate limit error handling"""
        from anthropic import RateLimitError as AnthropicRateLimitError

        with patch.object(
            anthropic_provider.client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=AnthropicRateLimitError(
                "Rate limit exceeded", response=MagicMock(), body=None
            ),
        ):
            with pytest.raises(RateLimitError, match="rate limit"):
                await anthropic_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_extract_timeout_error(self, anthropic_provider, sample_contract_text):
        """Test timeout error handling"""
        from anthropic import APITimeoutError

        with patch.object(
            anthropic_provider.client.messages,
            "create",
            new_callable=AsyncMock,
            side_effect=APITimeoutError(request=MagicMock()),
        ):
            with pytest.raises(TimeoutError, match="timeout"):
                await anthropic_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_extract_no_tool_use(self, anthropic_provider, sample_contract_text):
        """Test response without tool use"""
        mock_response = MagicMock()
        text_block = MagicMock()
        text_block.type = "text"
        mock_response.content = [text_block]
        mock_response.usage = None

        with patch.object(
            anthropic_provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with pytest.raises(ValidationError, match="No tool use"):
                await anthropic_provider.extract_contract_data(sample_contract_text, "TEST-001")

    @pytest.mark.asyncio
    async def test_chat_interface(self, anthropic_provider):
        """Test chat interface"""
        mock_response = MagicMock()
        text_block = MagicMock()
        text_block.text = "The premium is $495.00"
        text_block.type = "text"
        mock_response.content = [text_block]

        with patch.object(
            anthropic_provider.client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await anthropic_provider.chat(
                message="What is the premium?",
                context={"contract_id": "TEST-001", "account_number": "ACC-12345"},
                history=None,
            )

            assert result["response"] == "The premium is $495.00"
            assert result["provider"] == "anthropic"
            assert result["model"] == "claude-3-5-sonnet-20241022"


# Field Extraction Tests
class TestFieldExtraction:
    """Test FieldExtraction model"""

    def test_valid_field_extraction(self):
        """Test valid field extraction creation"""
        field = FieldExtraction(
            value="495.00",
            confidence=Decimal("95.5"),
            source={"page": 1, "section": "Pricing"},
        )
        assert field.value == "495.00"
        assert field.confidence == Decimal("95.5")
        assert field.source == {"page": 1, "section": "Pricing"}

    def test_confidence_validation_low(self):
        """Test confidence must be >= 0"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FieldExtraction(value="test", confidence=Decimal("-1"), source=None)

    def test_confidence_validation_high(self):
        """Test confidence must be <= 100"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FieldExtraction(value="test", confidence=Decimal("101"), source=None)

    def test_null_value_allowed(self):
        """Test null values are allowed"""
        field = FieldExtraction(value=None, confidence=Decimal("0"), source=None)
        assert field.value is None


# Extraction Result Tests
class TestExtractionResult:
    """Test ExtractionResult model"""

    def test_complete_extraction_result(self):
        """Test complete extraction result"""
        result = ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value="495.00", confidence=Decimal("95"), source=None
            ),
            refund_calculation_method=FieldExtraction(
                value="Pro-Rata", confidence=Decimal("90"), source=None
            ),
            cancellation_fee=FieldExtraction(value="50.00", confidence=Decimal("92"), source=None),
            model_version="gpt-4-turbo",
            provider="openai",
            processing_time_ms=1500,
            prompt_tokens=1000,
            completion_tokens=200,
            total_cost_usd=Decimal("0.016"),
        )

        assert result.provider == "openai"
        assert result.model_version == "gpt-4-turbo"
        assert result.processing_time_ms == 1500
        assert result.total_cost_usd == Decimal("0.016")

    def test_partial_extraction_result(self):
        """Test extraction result with some null fields"""
        result = ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value="495.00", confidence=Decimal("95"), source=None
            ),
            refund_calculation_method=None,
            cancellation_fee=None,
            model_version="claude-3-5-sonnet",
            provider="anthropic",
            processing_time_ms=None,
            prompt_tokens=None,
            completion_tokens=None,
            total_cost_usd=None,
        )

        assert result.gap_insurance_premium is not None
        assert result.refund_calculation_method is None
        assert result.cancellation_fee is None
