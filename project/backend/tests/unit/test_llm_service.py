"""
Unit tests for LLM Service Layer.

Tests circuit breaker, retry logic, provider fallback, and service orchestration.
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_service import (
    LLMService,
    CircuitBreaker,
    CircuitBreakerState,
    ProviderType,
)
from app.integrations.llm_providers.base import (
    ExtractionResult,
    FieldExtraction,
    LLMError,
    RateLimitError,
    TimeoutError,
)


# Circuit Breaker Tests
class TestCircuitBreaker:
    """Test circuit breaker pattern implementation"""

    def test_initial_state_closed(self):
        """Test circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.can_attempt() is True

    def test_record_success_resets_failures(self):
        """Test successful request resets failure count"""
        cb = CircuitBreaker(failure_threshold=5)
        cb.failure_count = 3
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    def test_record_failure_increments_count(self):
        """Test failure increments counter"""
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED

    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold"""
        cb = CircuitBreaker(failure_threshold=3)

        # Record failures up to threshold
        for i in range(3):
            cb.record_failure()

        assert cb.failure_count == 3
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_attempt() is False

    def test_circuit_half_open_after_recovery_timeout(self):
        """Test circuit enters HALF_OPEN after recovery timeout"""
        import time

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_attempt() is False

        # Wait for recovery timeout
        time.sleep(0.2)

        # Should transition to HALF_OPEN
        assert cb.can_attempt() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_allows_single_attempt(self):
        """Test HALF_OPEN state allows attempt"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
        cb.state = CircuitBreakerState.HALF_OPEN
        assert cb.can_attempt() is True

    def test_half_open_success_closes_circuit(self):
        """Test successful request in HALF_OPEN closes circuit"""
        cb = CircuitBreaker(failure_threshold=2)
        cb.state = CircuitBreakerState.HALF_OPEN
        cb.failure_count = 2

        cb.record_success()

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0


# LLM Service Tests
class TestLLMService:
    """Test LLM service orchestration"""

    @pytest.fixture
    def mock_extraction_result(self):
        """Create mock extraction result"""
        return ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value="495.00", confidence=Decimal("95"), source=None
            ),
            refund_calculation_method=FieldExtraction(
                value="Pro-Rata", confidence=Decimal("90"), source=None
            ),
            cancellation_fee=FieldExtraction(value="50.00", confidence=Decimal("92"), source=None),
            model_version="claude-3-5-sonnet",
            provider="anthropic",
            processing_time_ms=1500,
            prompt_tokens=1000,
            completion_tokens=200,
            total_cost_usd=Decimal("0.018"),
        )

    @pytest.fixture
    def llm_service(self):
        """Create LLM service with test API keys"""
        return LLMService(
            primary_provider=ProviderType.ANTHROPIC,
            fallback_provider=ProviderType.OPENAI,
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            max_retries=3,
            circuit_breaker_threshold=5,
        )

    def test_service_initialization(self, llm_service):
        """Test service initializes correctly"""
        assert llm_service.primary_provider_type == ProviderType.ANTHROPIC
        assert llm_service.fallback_provider_type == ProviderType.OPENAI
        assert llm_service.max_retries == 3
        assert ProviderType.ANTHROPIC in llm_service.providers
        assert ProviderType.OPENAI in llm_service.providers
        assert ProviderType.ANTHROPIC in llm_service.circuit_breakers
        assert ProviderType.OPENAI in llm_service.circuit_breakers

    def test_get_provider(self, llm_service):
        """Test provider retrieval"""
        provider = llm_service.get_provider(ProviderType.ANTHROPIC)
        assert provider is not None

        provider = llm_service.get_provider(ProviderType.OPENAI)
        assert provider is not None

        provider = llm_service.get_provider(ProviderType.BEDROCK)
        assert provider is None

    @pytest.mark.asyncio
    async def test_extract_with_retry_success_first_attempt(
        self, llm_service, mock_extraction_result
    ):
        """Test successful extraction on first attempt"""
        mock_provider = AsyncMock()
        mock_provider.extract_contract_data.return_value = mock_extraction_result

        result = await llm_service.extract_with_retry(mock_provider, "contract text", "TEST-001")

        assert result == mock_extraction_result
        assert mock_provider.extract_contract_data.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_with_retry_rate_limit_backoff(self, llm_service):
        """Test retry with exponential backoff on rate limit"""
        mock_provider = AsyncMock()

        # First two calls raise RateLimitError, third succeeds
        mock_extraction = MagicMock()
        mock_provider.extract_contract_data.side_effect = [
            RateLimitError("Rate limit"),
            RateLimitError("Rate limit"),
            mock_extraction,
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await llm_service.extract_with_retry(
                mock_provider, "contract text", "TEST-001"
            )

            # Should have retried twice (2^1=2s, 2^2=4s)
            assert mock_provider.extract_contract_data.call_count == 3
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)  # First retry: 2^1
            mock_sleep.assert_any_call(4)  # Second retry: 2^2

    @pytest.mark.asyncio
    async def test_extract_with_retry_timeout_backoff(self, llm_service):
        """Test retry with shorter backoff on timeout"""
        mock_provider = AsyncMock()

        # First call times out, second succeeds
        mock_extraction = MagicMock()
        mock_provider.extract_contract_data.side_effect = [
            TimeoutError("Timeout"),
            mock_extraction,
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await llm_service.extract_with_retry(
                mock_provider, "contract text", "TEST-001"
            )

            # Should have retried once with 2^0=1s backoff
            assert mock_provider.extract_contract_data.call_count == 2
            mock_sleep.assert_called_once_with(1)  # 2^(1-1)

    @pytest.mark.asyncio
    async def test_extract_with_retry_max_retries_exceeded(self, llm_service):
        """Test all retries exhausted raises error"""
        mock_provider = AsyncMock()
        mock_provider.extract_contract_data.side_effect = RateLimitError("Rate limit")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RateLimitError):
                await llm_service.extract_with_retry(mock_provider, "contract text", "TEST-001")

            # Should attempt max_retries times
            assert mock_provider.extract_contract_data.call_count == 3

    @pytest.mark.asyncio
    async def test_extract_with_retry_non_retryable_error(self, llm_service):
        """Test non-retryable errors are not retried"""
        mock_provider = AsyncMock()
        mock_provider.extract_contract_data.side_effect = LLMError("Non-retryable error")

        with pytest.raises(LLMError, match="Non-retryable"):
            await llm_service.extract_with_retry(mock_provider, "contract text", "TEST-001")

        # Should not retry
        assert mock_provider.extract_contract_data.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_primary_provider_success(self, llm_service, mock_extraction_result):
        """Test successful extraction with primary provider"""
        with patch.object(
            llm_service,
            "extract_with_retry",
            new_callable=AsyncMock,
            return_value=mock_extraction_result,
        ):
            result = await llm_service.extract_contract_data("contract text", "TEST-001")

            assert result == mock_extraction_result

            # Circuit breaker should record success
            cb = llm_service.circuit_breakers[ProviderType.ANTHROPIC]
            assert cb.failure_count == 0
            assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_extract_fallback_on_primary_failure(self, llm_service, mock_extraction_result):
        """Test fallback to secondary provider on primary failure"""
        mock_extraction_result.provider = "openai"

        with patch.object(llm_service, "extract_with_retry", new_callable=AsyncMock) as mock_retry:
            # Primary fails, fallback succeeds
            mock_retry.side_effect = [
                LLMError("Primary failed"),
                mock_extraction_result,
            ]

            result = await llm_service.extract_contract_data("contract text", "TEST-001")

            assert result == mock_extraction_result
            assert mock_retry.call_count == 2

            # Primary circuit breaker should record failure
            primary_cb = llm_service.circuit_breakers[ProviderType.ANTHROPIC]
            assert primary_cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_extract_all_providers_fail(self, llm_service):
        """Test error when all providers fail"""
        with patch.object(llm_service, "extract_with_retry", new_callable=AsyncMock) as mock_retry:
            mock_retry.side_effect = LLMError("Failed")

            with pytest.raises(LLMError, match="All LLM providers failed"):
                await llm_service.extract_contract_data("contract text", "TEST-001")

            # Should have tried both providers
            assert mock_retry.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_circuit_breaker_open_skips_provider(
        self, llm_service, mock_extraction_result
    ):
        """Test circuit breaker OPEN skips provider"""
        # Open primary circuit breaker
        primary_cb = llm_service.circuit_breakers[ProviderType.ANTHROPIC]
        for _ in range(5):
            primary_cb.record_failure()
        assert primary_cb.state == CircuitBreakerState.OPEN

        mock_extraction_result.provider = "openai"

        with patch.object(
            llm_service,
            "extract_with_retry",
            new_callable=AsyncMock,
            return_value=mock_extraction_result,
        ) as mock_retry:
            result = await llm_service.extract_contract_data("contract text", "TEST-001")

            # Should skip primary (circuit open) and use fallback
            assert result.provider == "openai"
            assert mock_retry.call_count == 1  # Only called for fallback

    @pytest.mark.asyncio
    async def test_chat_primary_provider(self, llm_service):
        """Test chat with primary provider"""
        mock_response = {
            "response": "The premium is $495.00",
            "sources": [],
            "model": "claude-3-5-sonnet",
            "provider": "anthropic",
        }

        primary_provider = llm_service.get_provider(ProviderType.ANTHROPIC)
        with patch.object(
            primary_provider, "chat", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await llm_service.chat(
                message="What is the premium?",
                context={"contract_id": "TEST-001"},
                history=None,
            )

            assert result["response"] == "The premium is $495.00"
            assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_chat_fallback_on_error(self, llm_service):
        """Test chat falls back on primary error"""
        mock_response = {
            "response": "The premium is $495.00",
            "sources": [],
            "model": "gpt-4-turbo",
            "provider": "openai",
        }

        primary_provider = llm_service.get_provider(ProviderType.ANTHROPIC)
        fallback_provider = llm_service.get_provider(ProviderType.OPENAI)

        with patch.object(
            primary_provider, "chat", new_callable=AsyncMock, side_effect=LLMError("Failed")
        ):
            with patch.object(
                fallback_provider, "chat", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await llm_service.chat(
                    message="What is the premium?",
                    context={"contract_id": "TEST-001"},
                    history=None,
                )

                assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_chat_specific_provider(self, llm_service):
        """Test chat with specific provider override"""
        mock_response = {
            "response": "The premium is $495.00",
            "sources": [],
            "model": "gpt-4-turbo",
            "provider": "openai",
        }

        openai_provider = llm_service.get_provider(ProviderType.OPENAI)
        with patch.object(
            openai_provider, "chat", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await llm_service.chat(
                message="What is the premium?",
                context={"contract_id": "TEST-001"},
                history=None,
                provider_type=ProviderType.OPENAI,
            )

            assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_chat_provider_not_configured(self, llm_service):
        """Test chat with unconfigured provider raises error"""
        with pytest.raises(LLMError, match="not configured"):
            await llm_service.chat(
                message="Test",
                context={},
                history=None,
                provider_type=ProviderType.BEDROCK,
            )


# Integration Tests
class TestLLMServiceIntegration:
    """Integration tests for LLM service with multiple scenarios"""

    @pytest.mark.asyncio
    async def test_degraded_operation_scenario(self):
        """Test service operates in degraded mode when primary is down"""
        service = LLMService(
            primary_provider=ProviderType.ANTHROPIC,
            fallback_provider=ProviderType.OPENAI,
            openai_api_key="test-openai",
            anthropic_api_key="test-anthropic",
            max_retries=2,
            circuit_breaker_threshold=3,
        )

        mock_result = ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value="495.00", confidence=Decimal("95"), source=None
            ),
            refund_calculation_method=None,
            cancellation_fee=None,
            model_version="gpt-4-turbo",
            provider="openai",
            processing_time_ms=1000,
            prompt_tokens=800,
            completion_tokens=150,
            total_cost_usd=Decimal("0.012"),
        )

        with patch.object(service, "extract_with_retry", new_callable=AsyncMock) as mock_retry:
            # Primary always fails, fallback succeeds
            mock_retry.side_effect = lambda provider, *args: (
                mock_result
                if provider == service.get_provider(ProviderType.OPENAI)
                else (_ for _ in ()).throw(LLMError("Primary down"))
            )

            # Make 5 requests to open circuit
            for i in range(5):
                result = await service.extract_contract_data("test", f"CONTRACT-{i}")
                assert result.provider == "openai"

            # Circuit should be open now
            primary_cb = service.circuit_breakers[ProviderType.ANTHROPIC]
            assert primary_cb.state == CircuitBreakerState.OPEN

            # Subsequent requests should skip primary entirely
            result = await service.extract_contract_data("test", "CONTRACT-6")
            assert result.provider == "openai"

    @pytest.mark.asyncio
    async def test_recovery_scenario(self):
        """Test service recovers when primary comes back online"""
        import time

        service = LLMService(
            primary_provider=ProviderType.ANTHROPIC,
            fallback_provider=ProviderType.OPENAI,
            openai_api_key="test-openai",
            anthropic_api_key="test-anthropic",
            max_retries=1,
            circuit_breaker_threshold=2,
        )

        # Open the circuit
        primary_cb = service.circuit_breakers[ProviderType.ANTHROPIC]
        primary_cb.record_failure()
        primary_cb.record_failure()
        assert primary_cb.state == CircuitBreakerState.OPEN

        # Manually set recovery timeout to 0 for testing
        primary_cb.recovery_timeout = 0.0
        primary_cb.last_failure_time = time.time() - 1  # 1 second ago

        mock_result = ExtractionResult(
            gap_insurance_premium=FieldExtraction(
                value="495.00", confidence=Decimal("95"), source=None
            ),
            refund_calculation_method=None,
            cancellation_fee=None,
            model_version="claude-3-5-sonnet",
            provider="anthropic",
            processing_time_ms=1200,
            prompt_tokens=1000,
            completion_tokens=180,
            total_cost_usd=Decimal("0.018"),
        )

        with patch.object(
            service,
            "extract_with_retry",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            # Circuit should transition to HALF_OPEN and try primary
            result = await service.extract_contract_data("test", "CONTRACT-1")

            assert result.provider == "anthropic"
            assert primary_cb.state == CircuitBreakerState.CLOSED
            assert primary_cb.failure_count == 0
