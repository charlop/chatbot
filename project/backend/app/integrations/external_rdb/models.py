"""
External RDB request and response models.
"""

from pydantic import BaseModel, Field


class ExternalRDBLookupResponse(BaseModel):
    """Response from external RDB account lookup."""

    contract_template_id: str = Field(
        ..., description="Contract template ID associated with the account"
    )
    account_number: str = Field(..., description="Account number that was queried")
    source: str = Field(
        default="external_api",
        description="Source of the mapping (external_api, manual, migrated)",
    )


class ExternalRDBHealthResponse(BaseModel):
    """Response from external RDB health check."""

    status: str = Field(..., description="Health status (healthy, unhealthy)")
    message: str | None = Field(None, description="Additional health information")
