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
from app.models.database import User, Contract, Extraction
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
    """Seed test contracts."""
    print("Seeding contracts...")

    # Sample contract data
    makes_models = [
        ("Toyota", "Camry"),
        ("Honda", "Accord"),
        ("Ford", "F-150"),
        ("Chevrolet", "Silverado"),
        ("Tesla", "Model 3"),
        ("BMW", "3 Series"),
        ("Mercedes-Benz", "C-Class"),
        ("Audi", "A4"),
        ("Nissan", "Altima"),
        ("Hyundai", "Elantra"),
        ("Mazda", "CX-5"),
        ("Subaru", "Outback"),
        ("Volkswagen", "Jetta"),
        ("Kia", "Sportage"),
        ("Jeep", "Wrangler"),
    ]

    contracts = []
    for i in range(15):
        make, model = makes_models[i]
        year = 2020 + (i % 5)  # 2020-2024

        contract = Contract(
            contract_id=f"GAP-2024-{i+1:04d}",
            account_number=f"ACC-TEST-{i+1:05d}",
            pdf_url=f"https://example.com/contracts/GAP-2024-{i+1:04d}.pdf",
            document_repository_id=f"DOC-REPO-{i+1:06d}",
            contract_type="GAP" if i % 3 != 2 else "VSC",  # Mix of GAP and VSC
            contract_date=date.today() - timedelta(days=i * 30),
            customer_name=f"Test Customer {i+1}",
            vehicle_info={
                "make": make,
                "model": model,
                "year": year,
                "vin": f"1HGCM82633A{i+1:06d}",
                "color": ["Black", "White", "Silver", "Blue", "Red"][i % 5],
            },
        )
        contracts.append(contract)

    # Add contracts (idempotent - check if exists first)
    for contract in contracts:
        existing = await session.get(Contract, contract.contract_id)
        if not existing:
            session.add(contract)
            print(f"  Created contract: {contract.contract_id} ({contract.customer_name})")
        else:
            print(f"  Contract already exists: {contract.contract_id}")

    await session.commit()
    print(f"✅ Contracts seeded")


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
            gap_premium_source={"page": 1, "section": "Pricing", "line": 10 + i},
            refund_calculation_method=methods[i],
            refund_method_confidence=Decimal("88.0"),
            refund_method_source={"page": 2, "section": "Terms", "line": 5 + i},
            cancellation_fee=Decimal(str(fees[i])),
            cancellation_fee_confidence=Decimal("92.0"),
            cancellation_fee_source={"page": 3, "section": "Fees", "line": 2 + i},
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

            # Seed contracts
            await seed_contracts(session)
            print()

            # Optionally seed extractions
            if with_extractions:
                await seed_extractions(session)
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
