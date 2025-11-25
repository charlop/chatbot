"""
Test factories for creating test data.
Provides factory methods for creating contract, extraction, and other model instances.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from app.models.database import Contract, Extraction, User, AuditEvent, AccountTemplateMapping


class ContractFactory:
    """Factory for creating Contract TEMPLATE test instances."""

    @staticmethod
    def build(
        contract_id: str = "GAP-2024-TEMPLATE-001",
        contract_type: str = "GAP",
        template_version: str = "1.0",
        is_active: bool = True,
        **kwargs,
    ) -> Contract:
        """
        Build a Contract TEMPLATE instance with default test data.

        Note: This creates templates (not customer contracts).
        For account-template mappings, use AccountMappingFactory.

        Args:
            contract_id: Template ID (e.g., GAP-2024-TEMPLATE-001)
            contract_type: Contract type (GAP or VSC)
            template_version: Template version (e.g., "1.0")
            is_active: Whether template is active
            **kwargs: Additional template fields

        Returns:
            Contract template instance (not persisted)
        """
        defaults = {
            "contract_id": contract_id,
            "s3_bucket": "test-contracts",
            "s3_key": f"templates/{contract_id}.pdf",
            "document_repository_id": f"DOC-{contract_id}",
            "contract_type": contract_type,
            "contract_date": date.today() - timedelta(days=30),
            "template_version": template_version,
            "effective_date": date.today() - timedelta(days=30),
            "is_active": is_active,
            "document_text": f"""
{contract_type} INSURANCE AGREEMENT TEMPLATE
Template ID: {contract_id}
Version: {template_version}

[CUSTOMER NAME]
[CUSTOMER ADDRESS]

VEHICLE INFORMATION:
[YEAR] [MAKE] [MODEL]
VIN: [VIN NUMBER]

COVERAGE DETAILS:
{contract_type} Insurance Premium: [PREMIUM]
Refund Calculation Method: [METHOD]
Cancellation Fee: [FEE]
            """.strip(),
            "text_extraction_status": "completed",
            "text_extracted_at": datetime.utcnow(),
        }
        defaults.update(kwargs)
        return Contract(**defaults)

    @staticmethod
    def build_with_extraction(contract_id: str = "GAP-2024-TEMPLATE-001", **kwargs) -> Contract:
        """
        Build a Contract template instance with an associated Extraction.

        Args:
            contract_id: Template ID
            **kwargs: Additional template fields

        Returns:
            Contract template instance with extraction relationship
        """
        contract = ContractFactory.build(contract_id=contract_id, **kwargs)

        # Create extraction
        extraction = ExtractionFactory.build(contract_id=contract_id)
        contract.extractions = extraction

        return contract


class AccountMappingFactory:
    """Factory for creating AccountTemplateMapping test instances."""

    @staticmethod
    def build(
        account_number: str = "000000000001",
        contract_template_id: str = "GAP-2024-TEMPLATE-001",
        source: str = "migrated",
        **kwargs,
    ) -> AccountTemplateMapping:
        """
        Build an AccountTemplateMapping instance with default test data.

        Args:
            account_number: 12-digit account number
            contract_template_id: Template ID this account maps to
            source: Mapping source (external_api, manual, migrated)
            **kwargs: Additional mapping fields

        Returns:
            AccountTemplateMapping instance (not persisted)
        """
        defaults = {
            "account_number": account_number,
            "contract_template_id": contract_template_id,
            "source": source,
        }
        defaults.update(kwargs)
        return AccountTemplateMapping(**defaults)


class ExtractionFactory:
    """Factory for creating Extraction test instances."""

    @staticmethod
    def build(
        contract_id: str = "GAP-2024-TEMPLATE-001",
        status: str = "pending",
        gap_insurance_premium: Optional[Decimal] = Decimal("500.00"),
        refund_calculation_method: Optional[str] = "Pro-rata",
        cancellation_fee: Optional[Decimal] = Decimal("50.00"),
        **kwargs,
    ) -> Extraction:
        """
        Build an Extraction instance with default test data.

        Args:
            contract_id: Associated contract ID
            status: Extraction status (pending, approved, rejected)
            gap_insurance_premium: GAP premium amount
            refund_calculation_method: Refund method
            cancellation_fee: Cancellation fee
            **kwargs: Additional extraction fields

        Returns:
            Extraction instance (not persisted)
        """
        defaults = {
            "contract_id": contract_id,
            "gap_insurance_premium": gap_insurance_premium,
            "gap_premium_confidence": Decimal("95.5"),
            "gap_premium_source": {"page": 1, "section": "Pricing", "line": 10},
            "refund_calculation_method": refund_calculation_method,
            "refund_method_confidence": Decimal("88.0"),
            "refund_method_source": {"page": 2, "section": "Terms", "line": 5},
            "cancellation_fee": cancellation_fee,
            "cancellation_fee_confidence": Decimal("92.0"),
            "cancellation_fee_source": {"page": 3, "section": "Fees", "line": 2},
            "llm_model_version": "claude-3-5-sonnet-20241022",
            "llm_provider": "anthropic",
            "processing_time_ms": 1500,
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_cost_usd": Decimal("0.015"),
            "status": status,
        }
        defaults.update(kwargs)
        return Extraction(**defaults)


class UserFactory:
    """Factory for creating User test instances."""

    @staticmethod
    def build(
        email: str = "test@example.com",
        username: str = "testuser",
        role: str = "user",
        **kwargs,
    ) -> User:
        """
        Build a User instance with default test data.

        Args:
            email: User email
            username: Username
            role: User role (user, admin)
            **kwargs: Additional user fields

        Returns:
            User instance (not persisted)
        """
        defaults = {
            "auth_provider": "test_provider",
            "auth_provider_user_id": f"test_user_{uuid4().hex[:8]}",
            "email": email,
            "username": username,
            "first_name": "Test",
            "last_name": "User",
            "role": role,
            "is_active": True,
        }
        defaults.update(kwargs)
        return User(**defaults)


class AuditEventFactory:
    """Factory for creating AuditEvent test instances."""

    @staticmethod
    def build(
        contract_id: str = "GAP-2024-TEMPLATE-001",
        event_type: str = "template_view",
        event_data: Optional[dict] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        Build an AuditEvent instance with default test data.

        Args:
            contract_id: Associated template ID
            event_type: Event type (account_lookup, template_view, etc.)
            event_data: Additional event data
            **kwargs: Additional audit event fields

        Returns:
            AuditEvent instance (not persisted)
        """
        if event_data is None:
            event_data = {"test": "data"}

        defaults = {
            "contract_id": contract_id,
            "user_id": None,  # No auth yet
            "event_type": event_type,
            "event_data": event_data,
        }
        defaults.update(kwargs)
        return AuditEvent(**defaults)
