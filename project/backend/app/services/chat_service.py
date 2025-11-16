"""
Chat Service - AI-powered contract Q&A with session management.

Handles chat interactions with context-aware LLM responses and session storage.
"""

import json
import logging
import re
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.llm_service import LLMService, ProviderType
from app.services.audit_service import AuditService
from app.repositories.contract_repository import ContractRepository
from app.repositories.extraction_repository import ExtractionRepository
from app.utils.cache import get_redis

logger = logging.getLogger(__name__)


class AccountNumberDetector:
    """Detects account numbers in chat messages."""

    # Account number patterns (adjust based on actual format)
    # Example: 12345-67890 or ACC-12345-67890 or 1234567890
    PATTERNS = [
        r"\b\d{5}-\d{5}\b",  # 12345-67890
        r"\bACC-\d{5}-\d{5}\b",  # ACC-12345-67890
        r"\b\d{10}\b",  # 1234567890
    ]

    @classmethod
    def detect(cls, message: str) -> Optional[str]:
        """
        Detect account number in message.

        Args:
            message: User message

        Returns:
            Detected account number or None
        """
        for pattern in cls.PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                account_number = match.group(0)
                logger.info(f"Detected account number: {account_number}")
                return account_number

        return None


class ChatSession:
    """Represents a chat session with history."""

    def __init__(self, session_id: str, contract_id: str | None = None):
        """
        Initialize chat session.

        Args:
            session_id: Unique session identifier
            contract_id: Associated contract ID (optional)
        """
        self.session_id = session_id
        self.contract_id = contract_id
        self.messages: List[dict] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def add_message(self, role: str, content: str, metadata: dict | None = None):
        """
        Add message to session history.

        Args:
            role: Message role (user/assistant)
            content: Message content
            metadata: Optional metadata
        """
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
        )
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert session to dictionary for Redis storage."""
        return {
            "session_id": self.session_id,
            "contract_id": self.contract_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        """Create session from dictionary."""
        session = cls(session_id=data["session_id"], contract_id=data.get("contract_id"))
        session.messages = data.get("messages", [])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        return session


class ChatService:
    """
    Chat service for contract Q&A with LLM integration.

    Provides context-aware responses using contract and extraction data.
    Manages chat sessions with Redis-based storage (4-hour TTL).
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize chat service.

        Args:
            db: Database session
        """
        self.db = db
        self.contract_repo = ContractRepository(db)
        self.extraction_repo = ExtractionRepository(db)
        self.audit_service = AuditService(db)

        # Initialize LLM service
        self.llm_service = LLMService(
            primary_provider=ProviderType(settings.llm_provider),
            fallback_provider=ProviderType.OPENAI if settings.llm_provider != "openai" else None,
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            max_retries=settings.llm_max_retries,
            circuit_breaker_threshold=settings.llm_circuit_breaker_threshold,
        )

    async def _get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get chat session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            ChatSession or None if not found
        """
        redis = await get_redis()
        if not redis:
            logger.warning("Redis not available, sessions disabled")
            return None

        try:
            session_key = f"chat:session:{session_id}"
            session_data = await redis.get(session_key)

            if session_data:
                session_dict = json.loads(session_data)
                return ChatSession.from_dict(session_dict)

            return None

        except Exception as e:
            logger.error(f"Error getting session from Redis: {e}")
            return None

    async def _save_session(self, session: ChatSession) -> bool:
        """
        Save chat session to Redis with TTL.

        Args:
            session: Chat session to save

        Returns:
            True if saved successfully, False otherwise
        """
        redis = await get_redis()
        if not redis:
            logger.warning("Redis not available, session not saved")
            return False

        try:
            session_key = f"chat:session:{session.session_id}"
            session_data = json.dumps(session.to_dict())

            # Save with TTL (4 hours by default)
            await redis.setex(session_key, settings.cache_ttl_session, session_data)

            logger.debug(f"Session saved: {session.session_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")
            return False

    async def _build_context(self, contract_id: str) -> dict:
        """
        Build context dictionary for LLM from contract and extraction data.

        Args:
            contract_id: Contract ID

        Returns:
            Context dictionary
        """
        # Get contract
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")

        # Get extraction (if exists)
        extraction = await self.extraction_repo.get_by_contract_id(contract_id)

        # Build context
        context = {
            "contract_id": contract.contract_id,
            "account_number": contract.account_number,
            "policy_number": contract.policy_number,
            "purchase_date": contract.purchase_date.isoformat() if contract.purchase_date else None,
        }

        # Add extraction data if available
        if extraction:
            context["extraction"] = {
                "gap_insurance_premium": (
                    str(extraction.gap_insurance_premium)
                    if extraction.gap_insurance_premium
                    else None
                ),
                "refund_calculation_method": extraction.refund_calculation_method,
                "cancellation_fee": (
                    str(extraction.cancellation_fee) if extraction.cancellation_fee else None
                ),
                "status": extraction.status,
            }

        # Add document text (truncated if too long)
        if contract.document_text:
            # Limit context to first 10,000 characters to avoid token limits
            context["document_text"] = contract.document_text[:10000]
            if len(contract.document_text) > 10000:
                context["document_text_truncated"] = True

        return context

    async def chat(
        self,
        message: str,
        contract_id: str,
        session_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Process chat message and generate response.

        Args:
            message: User message
            contract_id: Contract ID for context
            session_id: Chat session ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            dict with response, sources, metadata, and optional account number detection
        """
        start_time = datetime.utcnow()

        # Get or create session
        session = await self._get_session(session_id)
        if not session:
            session = ChatSession(session_id=session_id, contract_id=contract_id)
            logger.info(f"Created new chat session: {session_id}")
        else:
            logger.info(f"Retrieved existing session: {session_id}")

        # Check for account number in message
        detected_account_number = AccountNumberDetector.detect(message)
        if detected_account_number:
            logger.info(f"Account number detected in message: {detected_account_number}")

        # Add user message to session
        session.add_message("user", message)

        # Build context from contract data
        context = await self._build_context(contract_id)

        # Convert session messages to LLM format
        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session.messages[:-1]  # Exclude current message
        ]

        # Call LLM service
        llm_response = await self.llm_service.chat(
            message=message,
            context=context,
            history=history if history else None,
        )

        # Add assistant response to session
        session.add_message(
            "assistant",
            llm_response["response"],
            metadata={
                "model": llm_response.get("model"),
                "provider": llm_response.get("provider"),
            },
        )

        # Save session
        await self._save_session(session)

        # Calculate duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log audit event
        await self.audit_service.log_chat(
            contract_id=contract_id,
            session_id=UUID(session_id),
            message_length=len(message),
            duration_ms=duration_ms,
            cost_usd=llm_response.get("cost_usd"),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Build response
        response = {
            "response": llm_response["response"],
            "sources": llm_response.get("sources", []),
            "metadata": {
                "session_id": session_id,
                "contract_id": contract_id,
                "model": llm_response.get("model"),
                "provider": llm_response.get("provider"),
                "duration_ms": duration_ms,
                "message_count": len(session.messages),
            },
        }

        # Add account number detection if found
        if detected_account_number:
            response["detected_account_number"] = detected_account_number
            response["metadata"]["account_number_detected"] = True

        logger.info(f"Chat response generated in {duration_ms}ms")

        return response

    async def get_session_history(self, session_id: str) -> Optional[dict]:
        """
        Get chat session history.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        session = await self._get_session(session_id)
        if not session:
            return None

        return session.to_dict()

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear chat session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            True if cleared successfully
        """
        redis = await get_redis()
        if not redis:
            return False

        try:
            session_key = f"chat:session:{session_id}"
            await redis.delete(session_key)
            logger.info(f"Session cleared: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False
