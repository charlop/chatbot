"""
Contract service for business logic related to contract template operations.
Orchestrates template search, retrieval, and external RDB integration with hybrid cache.
"""

import json
import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Contract, Extraction, AuditEvent
from app.schemas.requests import ContractSearchRequest
from app.schemas.responses import ContractResponse, MultiPolicyResponse, PolicySummary
from app.repositories.contract_repository import ContractRepository
from app.repositories.account_mapping_repository import AccountMappingRepository
from app.integrations.external_rdb import ExternalRDBClient, ExternalRDBNotFoundError
from app.utils.cache import cache_get, cache_set
from app.config import settings

logger = logging.getLogger(__name__)


class ContractService:
    """Service for contract template operations with hybrid cache strategy."""

    def __init__(self, db: AsyncSession):
        """Initialize contract service with database session."""
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.mapping_repo = AccountMappingRepository(db)

        # Initialize External RDB client
        self.external_client = ExternalRDBClient(
            api_url=settings.external_rdb_api_url,
            api_key=settings.external_rdb_api_key,
            timeout=settings.external_rdb_timeout,
            retry_attempts=settings.external_rdb_retry_attempts,
            mock_mode=settings.external_rdb_mock_mode,
        )

    async def search_by_account_number(
        self, account_number: str, policy_id: Optional[str] = None
    ) -> Optional[MultiPolicyResponse | ContractResponse]:
        """
        Search for contract templates by account number using hybrid cache strategy.

        Hybrid lookup flow:
        1. Check Redis cache (fast path)
        2. Check account_mappings table (DB cache)
        3. Call external API (fallback)
        4. Cache result in both Redis and DB
        5. Fetch template details from contracts table

        Args:
            account_number: 12-digit customer account number
            policy_id: Optional policy ID to filter to specific policy

        Returns:
            MultiPolicyResponse if no policy_id filter (all policies for account)
            ContractResponse if policy_id filter provided (single policy)
            None if account not found

        Raises:
            ValueError: If account number is invalid
        """
        account_number = account_number.strip()
        logger.info(
            f"Searching template by account number: {account_number}"
            + (f" (policy: {policy_id})" if policy_id else " (all policies)")
        )

        # Step 1: Check Redis cache (fast path)
        cache_key = f"account_policies:{account_number}"
        cached_data = await cache_get(cache_key)
        if cached_data and isinstance(cached_data, list):
            logger.info(
                f"Account policies found in Redis cache: {account_number} → {len(cached_data)} policies"
            )
            # Filter by policy_id if provided
            if policy_id:
                policy_data = next((p for p in cached_data if p["policy_id"] == policy_id), None)
                if policy_data:
                    return await self.get_template_by_id(policy_data["template_id"])
                else:
                    logger.warning(f"Policy {policy_id} not found for account {account_number}")
                    return None
            else:
                # Return all policies as MultiPolicyResponse
                return await self._build_multi_policy_response(account_number, cached_data)

        # Step 2: Check DB cache (account_mappings table)
        mappings = await self.mapping_repo.get_by_account_number(account_number)
        if mappings and await self.mapping_repo.are_all_caches_fresh(
            mappings, ttl_seconds=settings.external_rdb_cache_ttl
        ):
            logger.info(
                f"Account policies found in DB cache: {account_number} → {len(mappings)} policies"
            )

            # Build policy data for Redis cache
            policies_data = [
                {"policy_id": m.policy_id, "template_id": m.contract_template_id} for m in mappings
            ]

            # Cache in Redis for faster subsequent lookups
            await self._cache_policies_in_redis(account_number, policies_data)

            # Log audit event
            await self._log_audit_event(
                contract_id=None,
                event_type="account_lookup",
                event_data={
                    "account_number": account_number,
                    "policy_count": len(mappings),
                    "source": "db_cache",
                },
            )

            # Filter by policy_id if provided
            if policy_id:
                mapping = next((m for m in mappings if m.policy_id == policy_id), None)
                if mapping:
                    return await self.get_template_by_id(mapping.contract_template_id)
                else:
                    logger.warning(f"Policy {policy_id} not found for account {account_number}")
                    return None
            else:
                # Return all policies as MultiPolicyResponse
                return await self._build_multi_policy_response(account_number, policies_data)

        # Step 3: Call External API (cache miss or stale cache)
        if settings.enable_external_rdb:
            try:
                logger.info(f"Calling External RDB API for account: {account_number}")
                result = await self.external_client.lookup_template_by_account(
                    account_number, db_session=self.db
                )

                # Result now contains list of policies
                policies_data = [
                    {"policy_id": p.policy_id, "template_id": p.contract_template_id}
                    for p in result.policies
                ]

                # Step 4: Cache ALL policies in both DB and Redis
                policy_tuples = [(p.policy_id, p.contract_template_id) for p in result.policies]
                await self.mapping_repo.upsert_policies(
                    account_number=account_number,
                    policies=policy_tuples,
                    source="external_api",
                )
                await self._cache_policies_in_redis(account_number, policies_data)

                logger.info(
                    f"External RDB lookup successful: {account_number} → {len(result.policies)} policies"
                )

                # Log audit event
                await self._log_audit_event(
                    contract_id=None,
                    event_type="account_lookup",
                    event_data={
                        "account_number": account_number,
                        "policy_count": len(result.policies),
                        "source": "external_api",
                    },
                )

                # Filter by policy_id if provided
                if policy_id:
                    policy_data = next(
                        (p for p in policies_data if p["policy_id"] == policy_id), None
                    )
                    if policy_data:
                        return await self.get_template_by_id(policy_data["template_id"])
                    else:
                        logger.warning(f"Policy {policy_id} not found for account {account_number}")
                        return None
                else:
                    # Return all policies as MultiPolicyResponse
                    return await self._build_multi_policy_response(account_number, policies_data)

            except ExternalRDBNotFoundError:
                logger.warning(f"Account not found in External RDB: {account_number}")

                # Log audit event (not found)
                await self._log_audit_event(
                    contract_id=None,
                    event_type="account_lookup",
                    event_data={
                        "account_number": account_number,
                        "source": "external_api",
                        "result": "not_found",
                    },
                )
                return None

            except Exception as e:
                logger.error(f"External RDB error for account {account_number}: {e}")

                # Fallback to stale cache if available
                if mappings:
                    logger.warning(
                        f"Using stale cache for account {account_number} due to External API error"
                    )
                    # Build policy data from stale cache
                    policies_data = [
                        {"policy_id": m.policy_id, "template_id": m.contract_template_id}
                        for m in mappings
                    ]

                    # Filter by policy_id if provided
                    if policy_id:
                        mapping = next((m for m in mappings if m.policy_id == policy_id), None)
                        if mapping:
                            return await self.get_template_by_id(mapping.contract_template_id)
                        else:
                            return None
                    else:
                        return await self._build_multi_policy_response(
                            account_number, policies_data
                        )

                return None

        # External RDB disabled or not found
        logger.warning(f"Account not found: {account_number}")
        return None

    async def get_template_by_id(
        self, template_id: str, include_extraction: bool = True
    ) -> Optional[ContractResponse]:
        """
        Retrieve a contract template by ID.

        Args:
            template_id: Contract template ID
            include_extraction: Whether to include extraction data

        Returns:
            ContractResponse if found, None otherwise
        """
        logger.info(f"Retrieving template: {template_id}")

        # Check cache first
        cache_key = f"template:id:{template_id}"
        cached_template = await cache_get(cache_key)
        if cached_template:
            logger.info(f"Template found in cache: {template_id}")
            return ContractResponse(**cached_template)

        # Get template from database (with extraction if requested)
        if include_extraction:
            template = await self.contract_repo.get_with_extraction(template_id)
        else:
            template = await self.contract_repo.get_by_id(template_id)

        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None

        # Log audit event (template view)
        await self._log_audit_event(
            contract_id=template_id,
            event_type="template_view",
            event_data={
                "template_version": template.template_version,
                "include_extraction": include_extraction,
            },
        )

        # Convert to response
        response = await self._template_to_response(template, include_extraction=include_extraction)

        # Cache the result
        await cache_set(cache_key, response.model_dump(), ttl=settings.cache_ttl_contract)

        return response

    async def search_contract(
        self, search_request: ContractSearchRequest
    ) -> Optional[MultiPolicyResponse | ContractResponse]:
        """
        Search for contract template by account number or template ID.

        Args:
            search_request: Search request with account_number or contract_id

        Returns:
            MultiPolicyResponse if searching by account (no policy filter)
            ContractResponse if searching by contract_id or filtered by policy_id
            None if not found
        """
        if search_request.account_number:
            return await self.search_by_account_number(
                search_request.account_number, policy_id=search_request.policy_id
            )
        elif search_request.contract_id:
            return await self.get_template_by_id(search_request.contract_id)
        else:
            raise ValueError("Either account_number or contract_id must be provided")

    async def _cache_policies_in_redis(
        self, account_number: str, policies_data: list[dict]
    ) -> None:
        """
        Cache account → policies mapping in Redis.

        Args:
            account_number: Account number
            policies_data: List of policy dicts with policy_id and template_id
        """
        cache_key = f"account_policies:{account_number}"
        await cache_set(
            cache_key,
            policies_data,
            ttl=settings.external_rdb_cache_ttl,
        )
        logger.debug(f"Cached in Redis: {account_number} → {len(policies_data)} policies")

    async def _build_multi_policy_response(
        self, account_number: str, policies_data: list[dict]
    ) -> MultiPolicyResponse:
        """
        Build MultiPolicyResponse from policies data.

        Args:
            account_number: Account number
            policies_data: List of policy dicts with policy_id and template_id

        Returns:
            MultiPolicyResponse with all policy summaries
        """
        # Fetch contract details for each policy
        policy_summaries = []
        for policy_data in policies_data:
            template = await self.contract_repo.get_by_id(policy_data["template_id"])
            if template:
                policy_summaries.append(
                    PolicySummary(
                        policy_id=policy_data["policy_id"],
                        contract_id=template.contract_id,
                        contract_type=template.contract_type or "UNKNOWN",
                        template_version=template.template_version,
                        is_active=template.is_active,
                    )
                )
            else:
                logger.warning(
                    f"Template {policy_data['template_id']} not found for policy {policy_data['policy_id']}"
                )

        return MultiPolicyResponse(
            account_number=account_number,
            state=None,  # TODO: Add state lookup from account
            policies=policy_summaries,
            total_policies=len(policy_summaries),
        )

    async def _template_to_response(
        self, template: Contract, include_extraction: bool = True
    ) -> ContractResponse:
        """
        Convert ORM template model to response schema.

        Args:
            template: Contract template ORM model
            include_extraction: Whether to include extraction data

        Returns:
            ContractResponse
        """
        # Build base response (template fields)
        response_dict = {
            "contract_id": template.contract_id,
            "s3_bucket": template.s3_bucket,
            "s3_key": template.s3_key,
            "text_extraction_status": template.text_extraction_status,
            "text_extracted_at": template.text_extracted_at,
            "document_repository_id": template.document_repository_id,
            "contract_type": template.contract_type,
            "contract_date": template.contract_date,
            "template_version": template.template_version,
            "effective_date": template.effective_date,
            "deprecated_date": template.deprecated_date,
            "is_active": template.is_active,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "last_synced_at": template.last_synced_at,
        }

        # Include extraction data if requested and available
        if include_extraction and hasattr(template, "extractions") and template.extractions:
            extraction = template.extractions
            response_dict["extracted_data"] = {
                "extraction_id": str(extraction.extraction_id),
                "gap_premium": (
                    float(extraction.gap_insurance_premium)
                    if extraction.gap_insurance_premium is not None
                    else None
                ),
                "gap_premium_confidence": (
                    float(extraction.gap_premium_confidence)
                    if extraction.gap_premium_confidence is not None
                    else None
                ),
                "gap_premium_source": extraction.gap_premium_source,
                "refund_method": extraction.refund_calculation_method,
                "refund_method_confidence": (
                    float(extraction.refund_method_confidence)
                    if extraction.refund_method_confidence is not None
                    else None
                ),
                "refund_method_source": extraction.refund_method_source,
                "cancellation_fee": (
                    float(extraction.cancellation_fee)
                    if extraction.cancellation_fee is not None
                    else None
                ),
                "cancellation_fee_confidence": (
                    float(extraction.cancellation_fee_confidence)
                    if extraction.cancellation_fee_confidence is not None
                    else None
                ),
                "cancellation_fee_source": extraction.cancellation_fee_source,
                "status": extraction.status,
                "llm_model_version": extraction.llm_model_version,
                "llm_provider": extraction.llm_provider,
                "processing_time_ms": extraction.processing_time_ms,
                "extracted_at": extraction.extracted_at,
                "extracted_by": str(extraction.extracted_by) if extraction.extracted_by else None,
                "approved_at": extraction.approved_at,
                "approved_by": str(extraction.approved_by) if extraction.approved_by else None,
            }

        return ContractResponse(**response_dict)

    async def _log_audit_event(
        self,
        event_type: str,
        event_data: dict,
        contract_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Log an audit event for contract operations.

        Args:
            event_type: Event type (account_lookup, template_view, etc.)
            event_data: Additional event data
            contract_id: Optional contract/template ID
            user_id: Optional user ID (for future auth)
        """
        audit_event = AuditEvent(
            contract_id=contract_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
        )

        self.db.add(audit_event)
        await self.db.commit()
        logger.debug(f"Audit event logged: {event_type}")
