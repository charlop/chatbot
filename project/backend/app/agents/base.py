"""
Base classes for agents and tools.

This module defines the core abstractions for the Agent/Tool architecture:
- Tool: A reusable operation that can be executed by agents
- Agent: An orchestrator that decides which tools to use and coordinates execution
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from decimal import Decimal


class ToolStatus(str, Enum):
    """Status of a tool execution result."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ToolContext:
    """
    Context provided to tools for execution.

    Contains all information a tool needs to perform its operation,
    including the field being validated and access to related data.
    """

    # Field identification
    field_name: str  # e.g., "gap_insurance_premium"
    field_value: str | Decimal | None  # The extracted value
    field_confidence: Decimal | None  # Confidence score (0-100)
    field_source: dict | None  # Source location from PDF

    # Context for cross-field validation
    all_fields: dict | None = None  # All extracted fields for consistency checks
    document_text: str | None = None  # Full contract text if needed

    # Metadata
    contract_id: str | None = None
    extraction_id: str | None = None


@dataclass
class ToolResult:
    """
    Result returned by a tool after execution.

    Contains the validation status, reasoning, and optional adjustments
    or additional details.
    """

    status: ToolStatus  # pass, warning, fail, skipped, error
    field_name: str  # Which field this result applies to
    message: str  # Human-readable explanation
    tool_name: str | None = None  # Name of the tool that produced this result
    confidence_adjustment: float | None = None  # Optional confidence adjustment
    details: dict[str, Any] | None = None  # Additional structured data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "field_name": self.field_name,
            "message": self.message,
            "tool_name": self.tool_name,
            "confidence_adjustment": self.confidence_adjustment,
            "details": self.details,
        }


class Tool(ABC):
    """
    Abstract base class for tools.

    Tools are reusable operations that can be executed by agents.
    Each tool has a name, description, and an execute method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        pass

    @property
    def applicable_fields(self) -> list[str] | None:
        """
        List of field names this tool applies to.
        None means the tool applies to all fields.
        """
        return None

    @abstractmethod
    async def execute(self, context: ToolContext) -> ToolResult:
        """
        Execute the tool operation.

        Args:
            context: The context containing field data and metadata

        Returns:
            ToolResult with status and reasoning
        """
        pass


@dataclass
class AgentContext:
    """
    Context provided to agents for execution.

    Contains the extraction data and metadata needed for the agent
    to orchestrate tool execution.
    """

    contract_id: str
    extraction_id: str
    extraction_data: dict[str, Any]  # All extracted fields with values/confidence
    document_text: str | None = None  # Full contract text if needed
    user_id: str | None = None  # User who initiated the extraction


@dataclass
class AgentResult:
    """
    Result returned by an agent after execution.

    Aggregates results from multiple tool executions with an overall
    status determination.
    """

    overall_status: str  # "pass", "warning", or "fail"
    field_results: list[dict[str, Any]]  # Results from individual tools
    summary: str | None = None  # Human-readable summary
    metadata: dict[str, Any] | None = None  # Additional agent-specific data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_status": self.overall_status,
            "field_results": self.field_results,
            "summary": self.summary,
            "metadata": self.metadata,
        }


class Agent(ABC):
    """
    Abstract base class for agents.

    Agents orchestrate the execution of multiple tools to accomplish
    a higher-level task. They decide which tools to use and how to
    aggregate their results.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        pass

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's workflow.

        Args:
            context: The context containing extraction data and metadata

        Returns:
            AgentResult with aggregated status and tool results
        """
        pass

    def _compute_overall_status(self, field_results: list[dict[str, Any]]) -> str:
        """
        Compute overall validation status from field results.

        Priority: fail/error > warning > pass

        Args:
            field_results: List of tool results

        Returns:
            Overall status string: "pass", "warning", or "fail"
        """
        statuses = [result.get("status") for result in field_results]

        # Priority: fail/error > warning > pass
        # Treat ERROR as FAIL since it indicates a validation tool failure
        if (
            "fail" in statuses
            or ToolStatus.FAIL.value in statuses
            or "error" in statuses
            or ToolStatus.ERROR.value in statuses
        ):
            return "fail"
        elif "warning" in statuses or ToolStatus.WARNING.value in statuses:
            return "warning"
        else:
            return "pass"
