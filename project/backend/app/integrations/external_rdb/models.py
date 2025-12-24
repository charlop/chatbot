"""
External RDB request and response models.
"""

from pydantic import BaseModel, Field


class PolicyLookup(BaseModel):
    """Single policy lookup result."""

    policy_id: str = Field(..., description="Policy identifier (e.g., DI_F, GAP_O)")
    contract_template_id: str = Field(..., description="Contract template ID for this policy")


class ExternalRDBLookupResponse(BaseModel):
    """Response from external RDB account lookup (multi-policy support)."""

    account_number: str = Field(..., description="Account number that was queried")
    policies: list[PolicyLookup] = Field(
        ..., description="List of all policies associated with this account"
    )
    source: str = Field(
        default="external_api",
        description="Source of the mapping (external_api, manual, migrated)",
    )


class ExternalRDBHealthResponse(BaseModel):
    """Response from external RDB health check."""

    status: str = Field(..., description="Health status (healthy, unhealthy)")
    message: str | None = Field(None, description="Additional health information")
