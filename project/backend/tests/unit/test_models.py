"""
Unit tests for SQLAlchemy database models.
Tests model creation, relationships, and constraints.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# Import models (will create these next)
from app.models.database.contract import Contract
from app.models.database.extraction import Extraction
from app.models.database.correction import Correction
from app.models.database.audit_event import AuditEvent
from app.models.database.user import User


@pytest.mark.unit
@pytest.mark.db
class TestContractModel:
    """Tests for Contract model."""

    async def test_create_contract(self, db_session: AsyncSession):
        """Test creating a contract with required fields."""
        contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            s3_bucket="test-bucket",
            s3_key="contracts/TEST-001.pdf",
            contract_type="GAP",
        )
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)

        assert contract.contract_id == "TEST-001"
        assert contract.account_number == "ACC-12345"
        assert contract.s3_bucket == "test-bucket"
        assert contract.s3_key == "contracts/TEST-001.pdf"
        assert contract.contract_type == "GAP"
        assert contract.created_at is not None
        assert contract.updated_at is not None

    async def test_contract_with_vehicle_info(self, db_session: AsyncSession):
        """Test contract with JSON vehicle info."""
        vehicle_info = {
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "vin": "1234567890",
        }
        contract = Contract(
            contract_id="TEST-002",
            account_number="ACC-67890",
            s3_bucket="test-bucket",
            s3_key="contracts/TEST-002.pdf",
            vehicle_info=vehicle_info,
        )
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)

        assert contract.vehicle_info == vehicle_info
        assert contract.vehicle_info["make"] == "Toyota"

    async def test_contract_duplicate_id_fails(self, db_session: AsyncSession):
        """Test that duplicate contract_id raises error."""
        contract1 = Contract(
            contract_id="TEST-003",
            account_number="ACC-111",
            s3_bucket="test-bucket",
            s3_key="contracts/TEST-003.pdf",
        )
        contract2 = Contract(
            contract_id="TEST-003",  # Same ID
            account_number="ACC-222",
            s3_bucket="test-bucket",
            s3_key="contracts/TEST-003-dup.pdf",
        )

        db_session.add(contract1)
        await db_session.commit()

        db_session.add(contract2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


@pytest.mark.unit
@pytest.mark.db
class TestExtractionModel:
    """Tests for Extraction model."""

    async def test_create_extraction(self, db_session: AsyncSession, test_contract: Contract):
        """Test creating an extraction with all fields."""
        extraction = Extraction(
            contract_id=test_contract.contract_id,
            gap_insurance_premium=Decimal("500.00"),
            gap_premium_confidence=Decimal("95.50"),
            gap_premium_source={"page": 1, "section": "Pricing", "line": 10},
            refund_calculation_method="Pro-rata",
            refund_method_confidence=Decimal("88.00"),
            refund_method_source={"page": 2, "section": "Terms", "line": 5},
            cancellation_fee=Decimal("50.00"),
            cancellation_fee_confidence=Decimal("92.00"),
            cancellation_fee_source={"page": 3, "section": "Fees", "line": 2},
            llm_model_version="gpt-4-turbo-preview",
            llm_provider="openai",
            processing_time_ms=1500,
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()
        await db_session.refresh(extraction)

        assert extraction.contract_id == test_contract.contract_id
        assert extraction.gap_insurance_premium == Decimal("500.00")
        assert extraction.gap_premium_confidence == Decimal("95.50")
        assert extraction.status == "pending"
        assert extraction.extracted_at is not None

    async def test_extraction_unique_per_contract(
        self, db_session: AsyncSession, test_contract: Contract
    ):
        """Test that only one extraction per contract is allowed."""
        extraction1 = Extraction(
            contract_id=test_contract.contract_id,
            llm_model_version="model-1",
            status="pending",
        )
        extraction2 = Extraction(
            contract_id=test_contract.contract_id,
            llm_model_version="model-2",
            status="pending",
        )

        db_session.add(extraction1)
        await db_session.commit()

        db_session.add(extraction2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_extraction_status_values(
        self, db_session: AsyncSession, test_contract: Contract
    ):
        """Test that extraction status must be valid."""
        extraction = Extraction(
            contract_id=test_contract.contract_id,
            llm_model_version="model-1",
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()

        # Valid statuses: pending, approved, rejected
        extraction.status = "approved"
        await db_session.commit()

        extraction.status = "rejected"
        await db_session.commit()

    async def test_extraction_cascade_delete(
        self, db_session: AsyncSession, test_contract: Contract
    ):
        """Test that deleting contract deletes extraction."""
        extraction = Extraction(
            contract_id=test_contract.contract_id,
            llm_model_version="model-1",
            status="pending",
        )
        db_session.add(extraction)
        await db_session.commit()

        extraction_id = extraction.extraction_id

        # Delete contract
        await db_session.delete(test_contract)
        await db_session.commit()

        # Extraction should be deleted
        result = await db_session.execute(
            select(Extraction).where(Extraction.extraction_id == extraction_id)
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.unit
@pytest.mark.db
class TestCorrectionModel:
    """Tests for Correction model."""

    async def test_create_correction(
        self, db_session: AsyncSession, test_extraction: Extraction, test_user: User
    ):
        """Test creating a correction."""
        correction = Correction(
            extraction_id=test_extraction.extraction_id,
            field_name="gap_insurance_premium",
            original_value="500.00",
            corrected_value="550.00",
            correction_reason="OCR error in original",
            corrected_by=test_user.user_id,
        )
        db_session.add(correction)
        await db_session.commit()
        await db_session.refresh(correction)

        assert correction.extraction_id == test_extraction.extraction_id
        assert correction.field_name == "gap_insurance_premium"
        assert correction.corrected_value == "550.00"
        assert correction.corrected_at is not None

    async def test_correction_valid_field_names(
        self, db_session: AsyncSession, test_extraction: Extraction, test_user: User
    ):
        """Test that field_name must be one of the three valid fields."""
        valid_fields = [
            "gap_insurance_premium",
            "refund_calculation_method",
            "cancellation_fee",
        ]

        for field_name in valid_fields:
            correction = Correction(
                extraction_id=test_extraction.extraction_id,
                field_name=field_name,
                corrected_value="test value",
                corrected_by=test_user.user_id,
            )
            db_session.add(correction)
            await db_session.commit()
            await db_session.rollback()  # Rollback for next iteration


@pytest.mark.unit
@pytest.mark.db
class TestAuditEventModel:
    """Tests for AuditEvent model."""

    async def test_create_audit_event(
        self, db_session: AsyncSession, test_contract: Contract, test_user: User
    ):
        """Test creating an audit event."""
        event = AuditEvent(
            event_type="search",
            contract_id=test_contract.contract_id,
            user_id=test_user.user_id,
            event_data={"query": "ACC-12345"},
            duration_ms=150,
        )
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

        assert event.event_type == "search"
        assert event.contract_id == test_contract.contract_id
        assert event.user_id == test_user.user_id
        assert event.timestamp is not None

    async def test_audit_event_types(self, db_session: AsyncSession, test_user: User):
        """Test valid audit event types."""
        valid_types = [
            "search",
            "view",
            "extract",
            "edit",
            "approve",
            "reject",
            "chat",
        ]

        for event_type in valid_types:
            event = AuditEvent(
                event_type=event_type,
                user_id=test_user.user_id,
                event_data={"test": "data"},
            )
            db_session.add(event)
            await db_session.commit()
            await db_session.rollback()


@pytest.mark.unit
@pytest.mark.db
class TestUserModel:
    """Tests for User model."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|12345",
            email="test@example.com",
            username="testuser",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.created_at is not None

    async def test_user_unique_email(self, db_session: AsyncSession):
        """Test that email must be unique."""
        user1 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|111",
            email="duplicate@example.com",
            role="user",
        )
        user2 = User(
            auth_provider="auth0",
            auth_provider_user_id="auth0|222",
            email="duplicate@example.com",  # Same email
            role="user",
        )

        db_session.add(user1)
        await db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
