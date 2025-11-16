"""
OpenAI LLM Provider

Implements LLM interface using OpenAI's GPT models with function calling.
"""

import time
import logging
import json
from decimal import Decimal
from typing import Optional
from openai import AsyncOpenAI, APIError, RateLimitError as OpenAIRateLimitError, APITimeoutError

from .base import (
    LLMProvider,
    ExtractionResult,
    FieldExtraction,
    LLMError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider using function calling for structured extraction"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)

    def default_model(self) -> str:
        """Default to GPT-4 Turbo"""
        return "gpt-4-turbo-preview"

    def _build_extraction_prompt(self, document_text: str, contract_id: str) -> str:
        """Build the extraction prompt"""
        return f"""You are a financial analyst reviewing GAP insurance contracts to extract refund eligibility data.

Contract ID: {contract_id}

Please analyze the following contract document and extract these specific fields:

1. **GAP Insurance Premium**: The total amount charged for GAP insurance coverage
2. **Refund Calculation Method**: How refunds are calculated (e.g., Pro-Rata, Rule of 78s, Short Rate)
3. **Cancellation Fee**: Any administrative or cancellation fees charged

For each field, provide:
- The exact value
- Your confidence level (0-100)
- Source location (page, section, line reference)

If a value cannot be found with confidence, mark it as null.

CONTRACT DOCUMENT:
{document_text[:15000]}  # Limit to ~15k chars to stay within context window
"""

    def _build_extraction_function(self) -> dict:
        """Define the extraction function schema for OpenAI function calling"""
        return {
            "name": "extract_contract_data",
            "description": "Extract GAP insurance contract data with confidence scores",
            "parameters": {
                "type": "object",
                "properties": {
                    "gap_insurance_premium": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "number", "null"],
                                "description": "Premium amount as string or number",
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence score 0-100",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {"type": "integer"},
                                    "section": {"type": "string"},
                                    "line": {"type": "integer"},
                                },
                            },
                        },
                        "required": ["value", "confidence"],
                    },
                    "refund_calculation_method": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "null"],
                                "description": "Refund method (Pro-Rata, Rule of 78s, etc.)",
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {"type": "integer"},
                                    "section": {"type": "string"},
                                    "line": {"type": "integer"},
                                },
                            },
                        },
                        "required": ["value", "confidence"],
                    },
                    "cancellation_fee": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "number", "null"],
                                "description": "Cancellation fee amount",
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {"type": "integer"},
                                    "section": {"type": "string"},
                                    "line": {"type": "integer"},
                                },
                            },
                        },
                        "required": ["value", "confidence"],
                    },
                },
                "required": [
                    "gap_insurance_premium",
                    "refund_calculation_method",
                    "cancellation_fee",
                ],
            },
        }

    async def extract_contract_data(self, document_text: str, contract_id: str) -> ExtractionResult:
        """
        Extract contract data using OpenAI function calling.

        Args:
            document_text: Full text of the contract
            contract_id: Contract identifier for logging

        Returns:
            ExtractionResult with extracted fields

        Raises:
            RateLimitError: If OpenAI rate limit exceeded
            TimeoutError: If request times out
            ValidationError: If response validation fails
            LLMError: For other errors
        """
        start_time = time.time()

        try:
            logger.info(f"OpenAI extraction started for contract {contract_id}")

            # Build prompt and function
            prompt = self._build_extraction_prompt(document_text, contract_id)
            function = self._build_extraction_function()

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise financial analyst extracting data from contracts.",
                    },
                    {"role": "user", "content": prompt},
                ],
                functions=[function],
                function_call={"name": "extract_contract_data"},
                temperature=0.1,  # Low temperature for consistency
                timeout=30.0,  # 30 second timeout
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract function call result
            message = response.choices[0].message
            if not message.function_call:
                raise ValidationError("No function call in response")

            # Parse function arguments
            extracted_data = json.loads(message.function_call.arguments)

            # Build FieldExtraction objects
            gap_premium = None
            if extracted_data.get("gap_insurance_premium"):
                gap_data = extracted_data["gap_insurance_premium"]
                gap_premium = FieldExtraction(
                    value=gap_data.get("value"),
                    confidence=Decimal(str(gap_data["confidence"])),
                    source=gap_data.get("source"),
                )

            refund_method = None
            if extracted_data.get("refund_calculation_method"):
                refund_data = extracted_data["refund_calculation_method"]
                refund_method = FieldExtraction(
                    value=refund_data.get("value"),
                    confidence=Decimal(str(refund_data["confidence"])),
                    source=refund_data.get("source"),
                )

            cancel_fee = None
            if extracted_data.get("cancellation_fee"):
                fee_data = extracted_data["cancellation_fee"]
                cancel_fee = FieldExtraction(
                    value=fee_data.get("value"),
                    confidence=Decimal(str(fee_data["confidence"])),
                    source=fee_data.get("source"),
                )

            # Calculate cost (approximate)
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            # GPT-4 Turbo pricing: $0.01/1K prompt, $0.03/1K completion
            total_cost = Decimal(str((prompt_tokens * 0.01 + completion_tokens * 0.03) / 1000))

            result = ExtractionResult(
                gap_insurance_premium=gap_premium,
                refund_calculation_method=refund_method,
                cancellation_fee=cancel_fee,
                model_version=self.model,
                provider="openai",
                processing_time_ms=processing_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost_usd=total_cost,
            )

            logger.info(f"OpenAI extraction completed for {contract_id} in {processing_time_ms}ms")
            return result

        except ValidationError:
            # Re-raise ValidationError without wrapping
            raise
        except OpenAIRateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded for {contract_id}: {e}")
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except APITimeoutError as e:
            logger.error(f"OpenAI timeout for {contract_id}: {e}")
            raise TimeoutError(f"OpenAI request timeout: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response for {contract_id}: {e}")
            raise ValidationError(f"Invalid JSON response: {e}")
        except APIError as e:
            logger.error(f"OpenAI API error for {contract_id}: {e}")
            raise LLMError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI extraction for {contract_id}: {e}")
            raise LLMError(f"Unexpected error: {e}")

    async def chat(
        self,
        message: str,
        context: dict,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Chat interface using OpenAI.

        Args:
            message: User's question
            context: Contract and extraction context
            history: Previous chat messages

        Returns:
            dict with response, sources, and metadata
        """
        try:
            # Build context-aware prompt
            system_prompt = f"""You are a helpful AI assistant that answers questions about GAP insurance contracts.

Context:
- Contract ID: {context.get('contract_id', 'Unknown')}
- Account Number: {context.get('account_number', 'Unknown')}

You have access to the contract data and extracted fields. Provide accurate answers and cite specific sections when possible.
"""

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add history
            if history:
                messages.extend(history)

            # Add current message
            messages.append({"role": "user", "content": message})

            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                timeout=15.0,
            )

            return {
                "response": response.choices[0].message.content,
                "sources": [],  # TODO: Implement citation extraction
                "model": self.model,
                "provider": "openai",
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise LLMError(f"Chat failed: {e}")
