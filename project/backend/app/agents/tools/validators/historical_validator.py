"""
Historical Validator - Outlier detection based on historical data.

Compares extracted values against approved historical extractions to flag outliers.
"""

from decimal import Decimal
from statistics import mean, stdev

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import ToolContext, ToolResult, ToolStatus
from app.agents.tools.base import ValidationTool
from app.models.database.extraction import Extraction


class HistoricalValidator(ValidationTool):
    """
    Validates fields against historical data.

    Flags values that are statistical outliers (>2 standard deviations from mean)
    compared to approved extractions.

    Requires database session for querying historical data.
    """

    # Minimum samples needed for statistical validation
    MIN_SAMPLES = 10

    # Number of standard deviations for outlier detection
    OUTLIER_THRESHOLD = 2.0

    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.

        Args:
            db: AsyncSession for querying historical data
        """
        self.db = db

    @property
    def name(self) -> str:
        return "historical_validator"

    @property
    def description(self) -> str:
        return "Validates fields against historical data to detect outliers"

    @property
    def applicable_fields(self) -> list[str]:
        """Only applies to numeric fields with historical data."""
        return ["gap_insurance_premium", "cancellation_fee"]

    async def validate(self, context: ToolContext) -> ToolResult:
        """
        Validate field against historical data.

        Args:
            context: Tool context with field data

        Returns:
            ToolResult with validation status
        """
        field_name = context.field_name
        field_value = context.field_value

        # Convert to Decimal for comparison
        try:
            value = Decimal(str(field_value))
        except (ValueError, TypeError):
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message=f"Cannot perform historical validation on non-numeric value: {field_value}",
            )

        # Get historical data
        historical_values = await self._get_historical_values(field_name)

        # Check if we have enough data
        if len(historical_values) < self.MIN_SAMPLES:
            return ToolResult(
                status=ToolStatus.SKIPPED,
                field_name=field_name,
                message=f"Insufficient historical data ({len(historical_values)} samples, need {self.MIN_SAMPLES})",
                details={"sample_count": len(historical_values), "required": self.MIN_SAMPLES},
            )

        # Calculate statistics
        avg = Decimal(str(mean(historical_values)))
        std = Decimal(str(stdev(historical_values)))

        # Check if value is an outlier (>2 stddev from mean)
        deviation = abs(value - avg)
        threshold = std * Decimal(str(self.OUTLIER_THRESHOLD))

        if deviation > threshold:
            return ToolResult(
                status=ToolStatus.WARNING,
                field_name=field_name,
                message=f"Value ${value} is a statistical outlier (avg: ${avg:.2f}, stddev: ${std:.2f})",
                details={
                    "value": float(value),
                    "mean": float(avg),
                    "stddev": float(std),
                    "deviation": float(deviation),
                    "threshold": float(threshold),
                    "sample_count": len(historical_values),
                },
            )

        return ToolResult(
            status=ToolStatus.PASS,
            field_name=field_name,
            message=f"Value ${value} is within normal range (avg: ${avg:.2f}, stddev: ${std:.2f})",
            details={
                "value": float(value),
                "mean": float(avg),
                "stddev": float(std),
                "sample_count": len(historical_values),
            },
        )

    async def _get_historical_values(self, field_name: str) -> list[float]:
        """
        Query historical values for a specific field from approved extractions.

        Args:
            field_name: Name of the field to query

        Returns:
            List of float values from approved extractions
        """
        # Map field name to database column
        field_column = getattr(Extraction, field_name, None)
        if field_column is None:
            return []

        # Query approved extractions
        stmt = (
            select(field_column)
            .where(Extraction.status == "approved")
            .where(field_column.isnot(None))
        )

        result = await self.db.execute(stmt)
        values = result.scalars().all()

        # Convert to float for statistics calculations
        return [float(val) for val in values if val is not None]
