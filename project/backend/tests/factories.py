"""
Test factories for creating test data.
Provides factory methods for creating contract, extraction, and other model instances.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from app.models.database import Contract, Extraction, User, AuditEvent


class ContractFactory:
    """Factory for creating Contract test instances."""

    @staticmethod
    def build(
        contract_id: str = "GAP-2024-TEST",
        account_number: str = "000000000001",
        customer_name: str = "Test Customer",
        contract_type: str = "GAP",
        **kwargs,
    ) -> Contract:
        """
        Build a Contract instance with default test data.

        Args:
            contract_id: Contract ID
            account_number: Account number
            customer_name: Customer name
            contract_type: Contract type (GAP or VSC)
            **kwargs: Additional contract fields

        Returns:
            Contract instance (not persisted)
        """
        defaults = {
            "contract_id": contract_id,
            "account_number": account_number,
            "s3_bucket": "test-contracts",
            "s3_key": f"contracts/{contract_id}.pdf",
            "document_repository_id": f"DOC-{contract_id}",
            "contract_type": contract_type,
            "contract_date": date.today() - timedelta(days=30),
            "customer_name": customer_name,
            "vehicle_info": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "vin": "1HGCM82633A004352",
                "color": "Silver",
            },
        }
        defaults.update(kwargs)
        return Contract(**defaults)

    @staticmethod
    def build_with_extraction(contract_id: str = "GAP-2024-WITH-EXT", **kwargs) -> Contract:
        """
        Build a Contract instance with an associated Extraction.

        Args:
            contract_id: Contract ID
            **kwargs: Additional contract fields

        Returns:
            Contract instance with extraction relationship
        """
        contract = ContractFactory.build(contract_id=contract_id, **kwargs)

        # Create extraction
        extraction = ExtractionFactory.build(contract_id=contract_id)
        contract.extraction = extraction

        return contract


class ExtractionFactory:
    """Factory for creating Extraction test instances."""

    @staticmethod
    def build(
        contract_id: str = "GAP-2024-TEST",
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
        contract_id: str = "GAP-2024-TEST",
        action: str = "contract_view",
        event_data: Optional[dict] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        Build an AuditEvent instance with default test data.

        Args:
            contract_id: Associated contract ID
            action: Action performed
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
            "action": action,
            "event_data": event_data,
        }
        defaults.update(kwargs)
        return AuditEvent(**defaults)
