"""
Base classes for validation tools.

Provides ValidationTool base class with template method pattern
for common validation logic like skipping N/A fields.
"""

from abc import abstractmethod

from app.agents.base import Tool, ToolContext, ToolResult, ToolStatus


class ValidationTool(Tool):
    """
    Base class for validation tools.

    Implements template method pattern with common logic for:
    - Skipping inapplicable fields
    - Skipping fields with no value
    - Delegating to concrete validate() method
    """

    async def execute(self, context: ToolContext) -> ToolResult:
        """
        Execute validation with built-in skip logic.

        Template method that:
        1. Checks if field is applicable
        2. Checks if field has a value
        3. Delegates to validate() for actual validation logic

        Args:
            context: Tool context with field data

        Returns:
            ToolResult with validation status
        """
        # Skip if field not applicable to this tool
        if self.applicable_fields and context.field_name not in self.applicable_fields:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=context.field_name,
                message=f"Not applicable to {context.field_name}",
                tool_name=self.name,
            )

        # Skip if no value to validate
        if context.field_value is None:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=context.field_name,
                message="No value to validate",
                tool_name=self.name,
            )

        # Delegate to concrete implementation
        try:
            result = await self.validate(context)
            # Ensure tool_name is set
            if result.tool_name is None:
                result.tool_name = self.name
            return result
        except Exception as e:
            # Catch any validation errors and return ERROR status
            return ToolResult(
                status=ToolStatus.ERROR,
                field_name=context.field_name,
                message=f"Validation error: {str(e)}",
                tool_name=self.name,
            )

    @abstractmethod
    async def validate(self, context: ToolContext) -> ToolResult:
        """
        Perform actual validation logic.

        This method must be implemented by concrete validation tools.

        Args:
            context: Tool context with field data (guaranteed to have a value)

        Returns:
            ToolResult with validation status
        """
        pass
