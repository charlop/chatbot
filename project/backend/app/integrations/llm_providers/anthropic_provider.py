"""
Anthropic Claude LLM Provider

Implements LLM interface using Anthropic's Claude models with tool use.
"""

import time
import logging
import json
from decimal import Decimal
from typing import Optional
from anthropic import (
    AsyncAnthropic,
    APIError,
    RateLimitError as AnthropicRateLimitError,
    APITimeoutError,
)

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


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider using tool use for structured extraction"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)

    def default_model(self) -> str:
        """Default to Claude 3.5 Sonnet"""
        return "claude-3-5-sonnet-20241022"

    def _build_extraction_tool(self) -> dict:
        """Define the extraction tool schema for Claude tool use"""
        return {
            "name": "extract_contract_data",
            "description": "Extract GAP insurance contract data with confidence scores and source references",
            "input_schema": {
                "type": "object",
                "properties": {
                    "gap_insurance_premium": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "number", "null"],
                                "description": "Premium amount as string or number. Use null if not found.",
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence score from 0-100",
                            },
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {
                                        "type": "integer",
                                        "description": "Page number where the text was found",
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "Exact text snippet extracted from the PDF (e.g., 'GAP Insurance Premium: $500.00')",
                                    },
                                    "section": {
                                        "type": "string",
                                        "description": "Section name (optional)",
                                    },
                                    "line": {
                                        "type": "integer",
                                        "description": "Approximate line number (optional)",
                                    },
                                },
                                "required": ["page", "text"],
                                "description": "Source location in the PDF document with exact text snippet",
                            },
                        },
                        "required": ["value", "confidence"],
                    },
                    "refund_calculation_method": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "null"],
                                "description": "Refund method: Pro-Rata, Rule of 78s, Short Rate, or null if not found",
                            },
                            "confidence": {"type": "number"},
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {
                                        "type": "integer",
                                        "description": "Page number where the text was found",
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "Exact text snippet extracted from the PDF",
                                    },
                                    "section": {
                                        "type": "string",
                                        "description": "Section name (optional)",
                                    },
                                    "line": {
                                        "type": "integer",
                                        "description": "Approximate line number (optional)",
                                    },
                                },
                                "required": ["page", "text"],
                                "description": "Source location with exact text snippet",
                            },
                        },
                        "required": ["value", "confidence"],
                    },
                    "cancellation_fee": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": ["string", "number", "null"],
                                "description": "Cancellation/administrative fee amount. Use null if not found.",
                            },
                            "confidence": {"type": "number"},
                            "source": {
                                "type": "object",
                                "properties": {
                                    "page": {
                                        "type": "integer",
                                        "description": "Page number where the text was found",
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "Exact text snippet extracted from the PDF",
                                    },
                                    "section": {
                                        "type": "string",
                                        "description": "Section name (optional)",
                                    },
                                    "line": {
                                        "type": "integer",
                                        "description": "Approximate line number (optional)",
                                    },
                                },
                                "required": ["page", "text"],
                                "description": "Source location with exact text snippet",
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
        Extract contract data using Claude tool use.

        Args:
            document_text: Full text of the contract
            contract_id: Contract identifier for logging

        Returns:
            ExtractionResult with extracted fields

        Raises:
            RateLimitError: If Anthropic rate limit exceeded
            TimeoutError: If request times out
            ValidationError: If response validation fails
            LLMError: For other errors
        """
        start_time = time.time()

        try:
            logger.info(f"Anthropic extraction started for contract {contract_id}")

            # Build prompt
            prompt = f"""Analyze this GAP insurance contract and extract the following information:

1. GAP Insurance Premium - the total cost of GAP coverage
2. Refund Calculation Method - how refunds are calculated (Pro-Rata, Rule of 78s, etc.)
3. Cancellation Fee - any administrative or cancellation fees

For each field, provide:
- The exact value (or null if not found)
- Your confidence level (0-100)
- Source location:
  * page: The page number where you found this information
  * text: The EXACT text snippet from the document as written (e.g., "GAP Insurance Premium: $500.00")
  * section: Optional section name
  * line: Optional approximate line number

IMPORTANT: For the "text" field, copy the exact wording from the document verbatim. Do not paraphrase or summarize.
This text will be used to locate and highlight the information in the PDF viewer.

Be precise and only report high-confidence findings.

CONTRACT DOCUMENT:
{document_text[:100000]}  # Claude has 100k context window

CONTRACT ID: {contract_id}
"""

            # Build tool
            tool = self._build_extraction_tool()

            # Call Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistency
                system="You are a precise financial analyst extracting data from GAP insurance contracts. Use the provided tool to report your findings with confidence scores.",
                messages=[{"role": "user", "content": prompt}],
                tools=[tool],
                timeout=30.0,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract tool use result
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "extract_contract_data":
                    tool_use_block = block
                    break

            if not tool_use_block:
                raise ValidationError("No tool use in response")

            # Parse tool input
            extracted_data = tool_use_block.input

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
            # Claude 3.5 Sonnet pricing: $3/MTok input, $15/MTok output
            prompt_tokens = response.usage.input_tokens if response.usage else 0
            completion_tokens = response.usage.output_tokens if response.usage else 0
            total_cost = Decimal(str((prompt_tokens * 3.0 + completion_tokens * 15.0) / 1_000_000))

            result = ExtractionResult(
                gap_insurance_premium=gap_premium,
                refund_calculation_method=refund_method,
                cancellation_fee=cancel_fee,
                model_version=self.model,
                provider="anthropic",
                processing_time_ms=processing_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost_usd=total_cost,
            )

            logger.info(
                f"Anthropic extraction completed for {contract_id} in {processing_time_ms}ms"
            )
            return result

        except ValidationError:
            # Re-raise ValidationError without wrapping
            raise
        except AnthropicRateLimitError as e:
            logger.error(f"Anthropic rate limit exceeded for {contract_id}: {e}")
            raise RateLimitError(f"Anthropic rate limit exceeded: {e}")
        except APITimeoutError as e:
            logger.error(f"Anthropic timeout for {contract_id}: {e}")
            raise TimeoutError(f"Anthropic request timeout: {e}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse Anthropic response for {contract_id}: {e}")
            raise ValidationError(f"Invalid response format: {e}")
        except APIError as e:
            logger.error(f"Anthropic API error for {contract_id}: {e}")
            raise LLMError(f"Anthropic API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic extraction for {contract_id}: {e}")
            raise LLMError(f"Unexpected error: {e}")

    async def chat(
        self,
        message: str,
        context: dict,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Chat interface using Claude.

        Args:
            message: User's question
            context: Contract and extraction context
            history: Previous chat messages

        Returns:
            dict with response, sources, and metadata
        """
        try:
            # Build context-aware system prompt
            system_prompt = f"""You are a helpful AI assistant that answers questions about GAP insurance contracts.

Context:
- Contract ID: {context.get('contract_id', 'Unknown')}
- Account Number: {context.get('account_number', 'Unknown')}

You have access to the contract data and extracted fields. Provide accurate answers and cite specific sections when possible.
Be concise but thorough. If you're unsure about something, say so."""

            # Build messages with history
            messages = []

            # Add history if present
            if history:
                messages.extend(history)

            # Add current message
            messages.append({"role": "user", "content": message})

            # Call Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=messages,
                timeout=15.0,
            )

            # Extract text content
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text

            return {
                "response": response_text,
                "sources": [],  # TODO: Implement citation extraction
                "model": self.model,
                "provider": "anthropic",
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise LLMError(f"Chat failed: {e}")
