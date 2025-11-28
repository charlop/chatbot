"""
Database seeding script with test data.
Creates sample contracts, users, and optionally extractions for testing.

Usage:
    uv run python scripts/seed_db.py
    uv run python scripts/seed_db.py --with-extractions
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_async_engine, get_session_local, init_database
from app.models.database import (
    User,
    Contract,
    Extraction,
    AuditEvent,
    Correction,
    AccountTemplateMapping,
)
from app.config import settings


async def seed_users(session):
    """Seed test users."""
    print("Seeding users...")

    users = [
        User(
            auth_provider="test_provider",
            auth_provider_user_id="admin_user_001",
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_active=True,
        ),
        User(
            auth_provider="test_provider",
            auth_provider_user_id="test_user_001",
            email="user1@example.com",
            username="testuser1",
            first_name="Test",
            last_name="User One",
            role="user",
            is_active=True,
        ),
        User(
            auth_provider="test_provider",
            auth_provider_user_id="test_user_002",
            email="user2@example.com",
            username="testuser2",
            first_name="Test",
            last_name="User Two",
            role="user",
            is_active=True,
        ),
    ]

    for user in users:
        # Check if user already exists
        existing = await session.get(User, user.user_id)
        if not existing:
            # Check by email
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.email == user.email))
            existing = result.scalar_one_or_none()

        if not existing:
            session.add(user)
            print(f"  Created user: {user.email}")
        else:
            print(f"  User already exists: {user.email}")

    await session.commit()
    print(f"✅ Users seeded")


async def seed_contracts(session):
    """Seed contract TEMPLATES (not customer contracts)."""
    print("Seeding contract templates...")

    # Sample extraction values for templates
    template_data = [
        ("GAP", 500.00, "Pro-rata", 50.00, "1.0"),
        ("GAP", 750.00, "Flat-rate", 75.00, "1.0"),
        ("GAP", 625.00, "Short-rate", 60.00, "1.1"),
        ("VSC", 550.00, "Pro-rata", 55.00, "1.0"),
        ("VSC", 800.00, "Flat-rate", 80.00, "1.0"),
        ("GAP", 675.00, "Pro-rata", 65.00, "2.0"),
        ("VSC", 700.00, "Short-rate", 70.00, "1.1"),
    ]

    templates = []
    for i, (contract_type, premium, method, fee, version) in enumerate(template_data):
        template = Contract(
            contract_id=f"{contract_type}-2024-TEMPLATE-{i+1:03d}",
            s3_bucket="test-contract-documents",
            s3_key=f"templates/{contract_type}-2024-TEMPLATE-{i+1:03d}.pdf",
            document_repository_id=f"DOC-REPO-TEMPLATE-{i+1:06d}",
            contract_type=contract_type,
            contract_date=date.today() - timedelta(days=i * 60),
            template_version=version,
            effective_date=date.today() - timedelta(days=i * 60),
            is_active=True,
            # Template text with placeholders (no customer/vehicle data)
            document_text=f"""
{contract_type} INSURANCE AGREEMENT TEMPLATE
Template ID: {contract_type}-2024-TEMPLATE-{i+1:03d}
Version: {version}

[CUSTOMER NAME]
[CUSTOMER ADDRESS]

VEHICLE INFORMATION:
[YEAR] [MAKE] [MODEL]
VIN: [VIN NUMBER]

COVERAGE DETAILS:
{contract_type} Insurance Premium: ${premium:.2f}
Refund Calculation Method: {method}
Cancellation Fee: ${fee:.2f}

This agreement provides {"Guaranteed Asset Protection (GAP)" if contract_type == "GAP" else "Vehicle Service Contract (VSC)"} coverage for the above vehicle.
The premium amount includes all applicable fees and charges.

REFUND POLICY:
Refunds will be calculated using the {method} method as outlined below:
- Pro-rata: Refund based on unused portion of coverage period
- Flat-rate: Fixed refund amount regardless of usage
- Short-rate: Pro-rata refund minus administrative fee

A cancellation fee of ${fee:.2f} will apply to all cancellations.
This fee covers administrative costs associated with contract termination.

TERMS AND CONDITIONS:
[Standard terms and conditions apply per state regulations]

Effective Date: {(date.today() - timedelta(days=i * 60)).isoformat()}
            """.strip(),
            text_extraction_status="completed",
            text_extracted_at=datetime.utcnow(),
        )
        templates.append(template)

    # Add templates (idempotent - check if exists first)
    for template in templates:
        existing = await session.get(Contract, template.contract_id)
        if not existing:
            session.add(template)
            print(f"  Created template: {template.contract_id} (v{template.template_version})")
        else:
            print(f"  Template already exists: {template.contract_id}")

    await session.commit()
    print(f"✅ Contract templates seeded ({len(templates)} templates)")


async def seed_account_mappings(session):
    """Seed account number to template ID mappings."""
    print("Seeding account-template mappings...")

    # Get all templates
    from sqlalchemy import select

    result = await session.execute(select(Contract))
    templates = result.scalars().all()

    if not templates:
        print("  ⚠️ No templates found, skipping mapping seeding")
        return

    # Create 100 account mappings pointing to our templates
    # This simulates many customers using the same templates
    mappings = []
    for i in range(100):
        # 12-digit account number (with leading zeros)
        account_number = f"{i+1:012d}"

        # Round-robin assign templates (many accounts per template)
        template = templates[i % len(templates)]

        mapping = AccountTemplateMapping(
            account_number=account_number,
            contract_template_id=template.contract_id,
            source="migrated",  # Simulating pre-populated data
        )
        mappings.append(mapping)

    # Add mappings (idempotent - check if exists first)
    added = 0
    for mapping in mappings:
        existing_result = await session.execute(
            select(AccountTemplateMapping).where(
                AccountTemplateMapping.account_number == mapping.account_number
            )
        )
        existing = existing_result.scalar_one_or_none()

        if not existing:
            session.add(mapping)
            added += 1
        else:
            pass  # Silently skip existing

    await session.commit()
    print(f"✅ Account mappings seeded ({added} new mappings, {len(mappings) - added} existing)")


async def seed_extractions(session):
    """Seed test extractions for some contracts."""
    print("Seeding extractions...")

    # Get first 5 contracts
    from sqlalchemy import select

    result = await session.execute(select(Contract).limit(5))
    contracts = result.scalars().all()

    # Get admin user for extracted_by
    result = await session.execute(select(User).where(User.email == "admin@example.com"))
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        print("  ⚠️ Admin user not found, skipping extraction seeding")
        return

    # Sample extraction data
    premiums = [500.00, 750.00, 625.00, 550.00, 800.00]
    methods = ["Pro-rata", "Flat-rate", "Short-rate", "Pro-rata", "Flat-rate"]
    fees = [50.00, 75.00, 60.00, 55.00, 80.00]
    statuses = ["pending", "approved", "approved", "rejected", "pending"]

    for i, contract in enumerate(contracts):
        # Check if extraction already exists
        result = await session.execute(
            select(Extraction).where(Extraction.contract_id == contract.contract_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Extraction already exists for contract: {contract.contract_id}")
            continue

        extraction = Extraction(
            contract_id=contract.contract_id,
            gap_insurance_premium=Decimal(str(premiums[i])),
            gap_premium_confidence=Decimal("95.5"),
            gap_premium_source={"page": 1, "text": f"${premiums[i]:.2f}"},
            refund_calculation_method=methods[i],
            refund_method_confidence=Decimal("88.0"),
            refund_method_source={"page": 1, "text": methods[i]},
            cancellation_fee=Decimal(str(fees[i])),
            cancellation_fee_confidence=Decimal("92.0"),
            cancellation_fee_source={"page": 1, "text": f"${fees[i]:.2f}"},
            llm_model_version="claude-3-5-sonnet-20241022",
            llm_provider="anthropic",
            processing_time_ms=1500 + i * 100,
            prompt_tokens=1000 + i * 50,
            completion_tokens=500 + i * 25,
            total_cost_usd=Decimal("0.015"),
            status=statuses[i],
            extracted_by=admin_user.user_id if admin_user else None,
        )

        # Set approval/rejection fields based on status
        if extraction.status == "approved":
            extraction.approved_at = datetime.utcnow() - timedelta(days=i)
            extraction.approved_by = admin_user.user_id if admin_user else None
        elif extraction.status == "rejected":
            extraction.rejected_at = datetime.utcnow() - timedelta(days=i)
            extraction.rejected_by = admin_user.user_id if admin_user else None
            extraction.rejection_reason = "Test rejection - sample data"

        session.add(extraction)
        print(
            f"  Created extraction for contract: {contract.contract_id} (status: {extraction.status})"
        )

    await session.commit()
    print(f"✅ Extractions seeded")


async def seed_audit_events(session):
    """Seed test audit events."""
    print("Seeding audit events...")

    # Get first user for event attribution
    from sqlalchemy import select

    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        print("  ⚠️ No users found, skipping audit event seeding")
        return

    # Get first template
    result = await session.execute(select(Contract).limit(1))
    template = result.scalar_one_or_none()

    if not template:
        print("  ⚠️ No templates found, skipping audit event seeding")
        return

    # Get first account mapping for search event
    result = await session.execute(select(AccountTemplateMapping).limit(1))
    mapping = result.scalar_one_or_none()

    # Sample audit events
    events = [
        AuditEvent(
            event_type="account_lookup",
            contract_id=template.contract_id if mapping else None,
            user_id=user.user_id,
            event_data={
                "account_number": mapping.account_number if mapping else "000000000001",
                "template_id": template.contract_id,
                "source": "search",
            },
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            duration_ms=150,
        ),
        AuditEvent(
            event_type="template_view",
            contract_id=template.contract_id,
            user_id=user.user_id,
            event_data={"source": "search_results", "template_version": template.template_version},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            duration_ms=300,
        ),
    ]

    for event in events:
        session.add(event)
        print(f"  Created audit event: {event.event_type}")

    await session.commit()
    print(f"✅ Audit events seeded")


async def seed_corrections(session):
    """Seed test corrections for extractions."""
    print("Seeding corrections...")

    # Get first approved extraction
    from sqlalchemy import select

    result = await session.execute(
        select(Extraction).where(Extraction.status == "approved").limit(1)
    )
    extraction = result.scalar_one_or_none()

    if not extraction:
        print("  ⚠️ No approved extractions found, skipping correction seeding")
        return

    # Get admin user
    result = await session.execute(select(User).where(User.role == "admin").limit(1))
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        print("  ⚠️ Admin user not found, skipping correction seeding")
        return

    # Check if correction already exists
    result = await session.execute(
        select(Correction).where(Correction.extraction_id == extraction.extraction_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  Correction already exists for extraction: {extraction.extraction_id}")
        return

    # Create sample correction
    correction = Correction(
        extraction_id=extraction.extraction_id,
        field_name="gap_insurance_premium",
        original_value=str(extraction.gap_insurance_premium),
        corrected_value=str(extraction.gap_insurance_premium + Decimal("100.00")),
        correction_reason="Manual verification - corrected based on page 3 of source document",
        corrected_by=admin_user.user_id,
    )

    session.add(correction)
    print(f"  Created correction for extraction: {extraction.extraction_id}")

    await session.commit()
    print(f"✅ Corrections seeded")


async def main():
    """Main seeding function."""
    print("=" * 60)
    print("DATABASE SEEDING SCRIPT")
    print("=" * 60)
    print(f"Database: {settings.get_database_url()}")
    print()

    # Check command line args
    with_extractions = "--with-extractions" in sys.argv

    try:
        # Initialize database (create tables if they don't exist)
        print("Initializing database...")
        await init_database()
        print("✅ Database initialized")
        print()

        # Create session
        session_local = get_session_local()
        async with session_local() as session:
            # Seed users
            await seed_users(session)
            print()

            # Seed contract templates
            await seed_contracts(session)
            print()

            # Seed account-template mappings
            await seed_account_mappings(session)
            print()

            # Optionally seed extractions
            if with_extractions:
                await seed_extractions(session)
                print()

                # Seed audit events
                await seed_audit_events(session)
                print()

                # Seed corrections
                await seed_corrections(session)
                print()
            else:
                print("ℹ️  Skipping extractions (use --with-extractions to seed)")
                print()

        print("=" * 60)
        print("✅ SEEDING COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
