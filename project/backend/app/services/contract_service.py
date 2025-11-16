"""
Contract service for business logic related to contract operations.
Orchestrates contract search, retrieval, and external RDB integration.
"""

import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Contract, Extraction, AuditEvent
from app.schemas.requests import ContractSearchRequest
from app.schemas.responses import ContractResponse
from app.repositories.contract_repository import ContractRepository
from app.utils.cache import cache_get, cache_set, cache_delete
from app.config import settings

logger = logging.getLogger(__name__)


class ContractService:
    """Service for contract-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize contract service with database session."""
        self.db = db
        self.contract_repo = ContractRepository(db)

    async def search_contract(
        self, search_request: ContractSearchRequest
    ) -> Optional[ContractResponse]:
        """
        Search for a contract by account number.

        Flow:
        1. Validate account number
        2. Check cache (Redis) - 15-minute TTL
        3. Query database for contract
        4. If not found, query external RDB (mocked for now)
        5. Store in database if found externally
        6. Cache the result
        7. Log audit event
        8. Return contract metadata

        Args:
            search_request: Contract search request with account number

        Returns:
            ContractResponse if found, None if not found

        Raises:
            ValueError: If account number is invalid
        """
        account_number = search_request.account_number.strip()

        # Log search attempt
        logger.info(f"Searching for contract with account number: {account_number}")

        # Check cache first
        cache_key = f"contract:account:{account_number}"
        cached_contract = await cache_get(cache_key)
        if cached_contract:
            logger.info(f"Contract found in cache: {account_number}")
            return ContractResponse(**cached_contract)

        # Query database
        contract = await self.contract_repo.get_by_account_number(account_number)

        if contract:
            logger.info(f"Contract found in database: {contract.contract_id}")

            # Log audit event (search)
            await self._log_audit_event(
                contract_id=contract.contract_id,
                event_type="search",
                event_data={
                    "account_number": account_number,
                    "source": "database",
                },
            )

            # Convert to response
            response = await self._contract_to_response(contract)

            # Cache the result (15-minute TTL)
            await cache_set(cache_key, response.model_dump(), ttl=settings.cache_ttl_contract)

            return response

        # Contract not found in database
        # TODO: Query external RDB API (Day 4 - mock for now)
        logger.info(f"Contract not found in database for account: {account_number}")

        # Mock external RDB response (for now)
        # In production, this would call the external RDB API
        external_contract = await self._mock_external_rdb_lookup(account_number)

        if external_contract:
            # Store in our database
            logger.info(f"Contract found in external RDB: {external_contract.contract_id}")
            created_contract = await self.contract_repo.create(external_contract)

            # Log audit event
            await self._log_audit_event(
                contract_id=created_contract.contract_id,
                event_type="search",
                event_data={
                    "account_number": account_number,
                    "source": "external_rdb",
                    "imported": True,
                },
            )

            # Convert to response
            response = await self._contract_to_response(created_contract)

            # Cache the result (15-minute TTL)
            await cache_set(cache_key, response.model_dump(), ttl=settings.cache_ttl_contract)

            return response

        # Contract not found anywhere
        logger.warning(f"Contract not found anywhere for account: {account_number}")
        return None

    async def get_contract(
        self, contract_id: str, include_extraction: bool = True
    ) -> Optional[ContractResponse]:
        """
        Retrieve a contract by ID.

        Args:
            contract_id: Contract ID
            include_extraction: Whether to include extraction data

        Returns:
            ContractResponse if found, None otherwise
        """
        logger.info(f"Retrieving contract: {contract_id}")

        # Check cache first
        cache_key = f"contract:id:{contract_id}"
        cached_contract = await cache_get(cache_key)
        if cached_contract:
            logger.info(f"Contract found in cache: {contract_id}")
            return ContractResponse(**cached_contract)

        # Get contract from database
        contract = await self.contract_repo.get_by_id(contract_id)

        if not contract:
            logger.warning(f"Contract not found: {contract_id}")
            return None

        # Log audit event (view)
        await self._log_audit_event(
            contract_id=contract_id,
            event_type="view",
            event_data={"include_extraction": include_extraction},
        )

        # Convert to response
        response = await self._contract_to_response(contract, include_extraction=include_extraction)

        # Cache the result (15-minute TTL)
        await cache_set(cache_key, response.model_dump(), ttl=settings.cache_ttl_contract)

        return response

    async def _contract_to_response(
        self, contract: Contract, include_extraction: bool = True
    ) -> ContractResponse:
        """
        Convert ORM contract model to response schema.

        Args:
            contract: Contract ORM model
            include_extraction: Whether to include extraction data (placeholder for Day 6)

        Returns:
            ContractResponse
        """
        # NOTE: Extraction will be added in Day 6
        # For now, just return contract data without extraction

        return ContractResponse(
            contract_id=contract.contract_id,
            account_number=contract.account_number,
            s3_bucket=contract.s3_bucket,
            s3_key=contract.s3_key,
            text_extraction_status=contract.text_extraction_status,
            text_extracted_at=contract.text_extracted_at,
            document_repository_id=contract.document_repository_id,
            contract_type=contract.contract_type,
            contract_date=contract.contract_date,
            customer_name=contract.customer_name,
            vehicle_info=contract.vehicle_info,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
            last_synced_at=contract.last_synced_at,
        )

    async def _log_audit_event(
        self, contract_id: str, event_type: str, event_data: dict, user_id: Optional[UUID] = None
    ) -> None:
        """
        Log an audit event for contract operations.

        Args:
            contract_id: Contract ID
            event_type: Event type (search, view, extract, etc.)
            event_data: Additional event data
            user_id: Optional user ID (for future auth)
        """
        audit_event = AuditEvent(
            contract_id=contract_id,
            user_id=user_id,  # Will be None until auth is implemented
            event_type=event_type,
            event_data=event_data,
        )

        self.db.add(audit_event)
        await self.db.commit()
        logger.debug(f"Audit event logged: {event_type} for contract {contract_id}")

    async def _mock_external_rdb_lookup(self, account_number: str) -> Optional[Contract]:
        """
        Mock external RDB lookup (placeholder for actual API call).
        Returns None to simulate "not found" until external API is integrated.

        Args:
            account_number: Account number to search

        Returns:
            Contract if found in external RDB, None otherwise
        """
        # TODO: Day 4 - Implement actual external RDB API call
        # For now, return None to simulate "not found"
        logger.debug(f"Mock external RDB lookup for account: {account_number}")
        return None
