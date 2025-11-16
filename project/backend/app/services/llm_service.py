"""
LLM Service Layer

Orchestrates LLM provider selection, retry logic, circuit breaker, and fallback strategies.
"""

import logging
import asyncio
from typing import Optional
from enum import Enum

from app.integrations.llm_providers.base import (
    LLMProvider,
    ExtractionResult,
    LLMError,
    RateLimitError,
    TimeoutError,
)
from app.integrations.llm_providers.openai_provider import OpenAIProvider
from app.integrations.llm_providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"  # Future implementation


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit broken, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for LLM providers.

    Opens after N consecutive failures, closes after successful health check.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time: Optional[float] = None

    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Record failed request"""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

    def can_attempt(self) -> bool:
        """Check if request should be attempted"""
        import time

        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout elapsed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow single attempt
        return True


class LLMService:
    """
    LLM Service with provider selection, retry logic, and circuit breaker.
    """

    def __init__(
        self,
        primary_provider: ProviderType = ProviderType.ANTHROPIC,
        fallback_provider: Optional[ProviderType] = ProviderType.OPENAI,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
    ):
        """
        Initialize LLM service.

        Args:
            primary_provider: Primary LLM provider to use
            fallback_provider: Fallback provider if primary fails
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            max_retries: Maximum retry attempts per provider
            circuit_breaker_threshold: Failures before opening circuit
        """
        self.primary_provider_type = primary_provider
        self.fallback_provider_type = fallback_provider
        self.max_retries = max_retries

        # Initialize providers
        self.providers: dict[ProviderType, LLMProvider] = {}

        if openai_api_key:
            self.providers[ProviderType.OPENAI] = OpenAIProvider(openai_api_key)

        if anthropic_api_key:
            self.providers[ProviderType.ANTHROPIC] = AnthropicProvider(anthropic_api_key)

        # Circuit breakers per provider
        self.circuit_breakers: dict[ProviderType, CircuitBreaker] = {
            provider_type: CircuitBreaker(failure_threshold=circuit_breaker_threshold)
            for provider_type in self.providers.keys()
        }

        logger.info(
            f"LLM Service initialized: primary={primary_provider}, "
            f"fallback={fallback_provider}, available_providers={list(self.providers.keys())}"
        )

    def get_provider(self, provider_type: ProviderType) -> Optional[LLMProvider]:
        """Get provider instance by type"""
        return self.providers.get(provider_type)

    async def extract_with_retry(
        self, provider: LLMProvider, document_text: str, contract_id: str
    ) -> ExtractionResult:
        """
        Extract contract data with exponential backoff retry.

        Args:
            provider: LLM provider instance
            document_text: Contract text
            contract_id: Contract identifier

        Returns:
            ExtractionResult

        Raises:
            LLMError: If all retries exhausted
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Extraction attempt {attempt}/{self.max_retries}")
                result = await provider.extract_contract_data(document_text, contract_id)
                return result

            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff: 2^attempt seconds
                    backoff = 2**attempt
                    logger.warning(f"Rate limit hit, retrying in {backoff}s (attempt {attempt})")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Rate limit exhausted after {self.max_retries} attempts")
                    raise

            except TimeoutError as e:
                last_error = e
                if attempt < self.max_retries:
                    backoff = 2 ** (attempt - 1)  # Shorter backoff for timeouts
                    logger.warning(f"Timeout, retrying in {backoff}s (attempt {attempt})")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Timeouts exhausted after {self.max_retries} attempts")
                    raise

            except LLMError as e:
                # Don't retry non-transient errors
                logger.error(f"Non-retryable error: {e}")
                raise

        # Should not reach here, but just in case
        raise last_error or LLMError("Extraction failed after retries")

    async def extract_contract_data(self, document_text: str, contract_id: str) -> ExtractionResult:
        """
        Extract contract data using configured providers with fallback.

        Tries primary provider first, falls back to secondary if available.

        Args:
            document_text: Contract text to extract from
            contract_id: Contract identifier

        Returns:
            ExtractionResult from successful provider

        Raises:
            LLMError: If all providers fail
        """
        providers_to_try = [self.primary_provider_type]
        if self.fallback_provider_type:
            providers_to_try.append(self.fallback_provider_type)

        last_error = None

        for provider_type in providers_to_try:
            provider = self.get_provider(provider_type)
            if not provider:
                logger.warning(f"Provider {provider_type} not configured, skipping")
                continue

            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(provider_type)
            if circuit_breaker and not circuit_breaker.can_attempt():
                logger.warning(f"Circuit breaker OPEN for {provider_type}, skipping")
                continue

            try:
                logger.info(f"Attempting extraction with {provider_type}")
                result = await self.extract_with_retry(provider, document_text, contract_id)

                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()

                logger.info(f"Extraction successful with {provider_type}")
                return result

            except (LLMError, RateLimitError, TimeoutError) as e:
                last_error = e
                logger.error(f"Extraction failed with {provider_type}: {e}")

                # Record failure
                if circuit_breaker:
                    circuit_breaker.record_failure()

                # Continue to fallback provider
                if provider_type != providers_to_try[-1]:
                    logger.info(f"Falling back to next provider")
                continue

        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise LLMError(error_msg)

    async def chat(
        self,
        message: str,
        context: dict,
        history: list[dict] | None = None,
        provider_type: Optional[ProviderType] = None,
    ) -> dict:
        """
        Chat interface with fallback.

        Args:
            message: User message
            context: Contract context
            history: Chat history
            provider_type: Specific provider to use (optional)

        Returns:
            dict with response, sources, metadata

        Raises:
            LLMError: If chat fails
        """
        # Use specified provider or primary
        target_provider = provider_type or self.primary_provider_type
        provider = self.get_provider(target_provider)

        if not provider:
            raise LLMError(f"Provider {target_provider} not configured")

        try:
            return await provider.chat(message, context, history)
        except Exception as e:
            # Try fallback if available
            if self.fallback_provider_type and not provider_type:
                logger.warning(f"Chat failed with {target_provider}, trying fallback")
                fallback_provider = self.get_provider(self.fallback_provider_type)
                if fallback_provider:
                    return await fallback_provider.chat(message, context, history)

            raise LLMError(f"Chat failed: {e}")
