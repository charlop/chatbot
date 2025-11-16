"""
Unit tests for ChatService.
Tests chat interactions, session management, and account number detection.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from app.services.chat_service import ChatService, ChatSession, AccountNumberDetector
from app.models.database.contract import Contract
from app.models.database.extraction import Extraction


@pytest.mark.unit
class TestAccountNumberDetector:
    """Tests for AccountNumberDetector - strictly 12 digits."""

    def test_detect_12_digit_with_leading_zeros(self):
        """Test detection of 12-digit account number with leading zeros."""
        message = "My account number is 000123456789"
        result = AccountNumberDetector.detect(message)
        assert result == "000123456789"

    def test_detect_12_digit_no_leading_zeros(self):
        """Test detection of 12-digit account without leading zeros."""
        message = "Account 423567890112 needs review"
        result = AccountNumberDetector.detect(message)
        assert result == "423567890112"

    def test_detect_no_match_too_short(self):
        """Test no detection for numbers too short."""
        message = "Check account 12345678 please"
        result = AccountNumberDetector.detect(message)
        assert result is None

    def test_detect_no_match_too_long(self):
        """Test no detection for numbers too long."""
        message = "Account 1234567890123 invalid"
        result = AccountNumberDetector.detect(message)
        assert result is None

    def test_detect_no_match_no_numbers(self):
        """Test no account number detected in general message."""
        message = "Hello, I need help with my contract"
        result = AccountNumberDetector.detect(message)
        assert result is None


@pytest.mark.unit
class TestChatSession:
    """Tests for ChatSession."""

    def test_create_session(self):
        """Test creating a new chat session."""
        session = ChatSession(session_id="test-session", contract_id="TEST-001")
        assert session.session_id == "test-session"
        assert session.contract_id == "TEST-001"
        assert len(session.messages) == 0
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_add_message(self):
        """Test adding messages to session."""
        session = ChatSession(session_id="test-session")

        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")

        assert len(session.messages) == 2
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"
        assert session.messages[1]["role"] == "assistant"
        assert session.messages[1]["content"] == "Hi there!"

    def test_add_message_with_metadata(self):
        """Test adding message with metadata."""
        session = ChatSession(session_id="test-session")

        metadata = {"model": "gpt-4", "provider": "openai"}
        session.add_message("assistant", "Response", metadata=metadata)

        assert session.messages[0]["metadata"] == metadata

    def test_to_dict(self):
        """Test converting session to dictionary."""
        session = ChatSession(session_id="test-session", contract_id="TEST-001")
        session.add_message("user", "Test message")

        result = session.to_dict()

        assert result["session_id"] == "test-session"
        assert result["contract_id"] == "TEST-001"
        assert len(result["messages"]) == 1
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self):
        """Test creating session from dictionary."""
        data = {
            "session_id": "test-session",
            "contract_id": "TEST-001",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {},
                }
            ],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:01",
        }

        session = ChatSession.from_dict(data)

        assert session.session_id == "test-session"
        assert session.contract_id == "TEST-001"
        assert len(session.messages) == 1
        assert session.messages[0]["content"] == "Hello"


@pytest.mark.unit
class TestChatServiceSessionManagement:
    """Tests for ChatService session management."""

    @pytest.mark.asyncio
    async def test_get_session_found(self):
        """Test getting existing session from Redis."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        session_data = {
            "session_id": "test-session",
            "contract_id": "TEST-001",
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data).encode()

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await service._get_session("test-session")

        assert result is not None
        assert result.session_id == "test-session"
        mock_redis.get.assert_awaited_once_with("chat:session:test-session")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test getting non-existent session."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await service._get_session("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_redis_unavailable(self):
        """Test getting session when Redis unavailable."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        with patch("app.utils.cache.get_redis", return_value=None):
            result = await service._get_session("test-session")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_session_success(self):
        """Test saving session to Redis."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        session = ChatSession(session_id="test-session", contract_id="TEST-001")
        session.add_message("user", "Test")

        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True

        with (
            patch("app.utils.cache.get_redis", return_value=mock_redis),
            patch("app.services.chat_service.settings.cache_ttl_session", 14400),
        ):
            result = await service._save_session(session)

        assert result is True
        mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_session_redis_unavailable(self):
        """Test saving session when Redis unavailable."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        session = ChatSession(session_id="test-session")

        with patch("app.utils.cache.get_redis", return_value=None):
            result = await service._save_session(session)

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_session_success(self):
        """Test clearing session from Redis."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await service.clear_session("test-session")

        assert result is True
        mock_redis.delete.assert_awaited_once_with("chat:session:test-session")

    @pytest.mark.asyncio
    async def test_clear_session_redis_unavailable(self):
        """Test clearing session when Redis unavailable."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        with patch("app.utils.cache.get_redis", return_value=None):
            result = await service.clear_session("test-session")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_history_found(self):
        """Test getting session history."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        session_data = {
            "session_id": "test-session",
            "contract_id": "TEST-001",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(session_data).encode()

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await service.get_session_history("test-session")

        assert result is not None
        assert result["session_id"] == "test-session"
        assert len(result["messages"]) == 1

    @pytest.mark.asyncio
    async def test_get_session_history_not_found(self):
        """Test getting non-existent session history."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("app.utils.cache.get_redis", return_value=mock_redis):
            result = await service.get_session_history("nonexistent")

        assert result is None


@pytest.mark.unit
class TestChatServiceContext:
    """Tests for ChatService context building."""

    @pytest.mark.asyncio
    async def test_build_context_with_extraction(self):
        """Test building context with contract and extraction data."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        # Mock contract
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            policy_number="POL-123",
            purchase_date=date(2024, 1, 1),
            document_text="Sample contract text for testing",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        # Mock extraction
        mock_extraction = Extraction(
            extraction_id=uuid4(),
            contract_id="TEST-001",
            gap_insurance_premium=Decimal("1500.00"),
            refund_calculation_method="Pro-rata",
            cancellation_fee=Decimal("50.00"),
            status="approved",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=mock_extraction)

        result = await service._build_context("TEST-001")

        assert result["contract_id"] == "TEST-001"
        assert result["account_number"] == "ACC-12345"
        assert result["policy_number"] == "POL-123"
        assert result["purchase_date"] == "2024-01-01"
        assert "extraction" in result
        assert result["extraction"]["gap_insurance_premium"] == "1500.00"
        assert result["extraction"]["refund_calculation_method"] == "Pro-rata"
        assert "document_text" in result

    @pytest.mark.asyncio
    async def test_build_context_without_extraction(self):
        """Test building context without extraction data."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            policy_number="POL-123",
            purchase_date=date(2024, 1, 1),
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=None)

        result = await service._build_context("TEST-001")

        assert result["contract_id"] == "TEST-001"
        assert "extraction" not in result

    @pytest.mark.asyncio
    async def test_build_context_contract_not_found(self):
        """Test building context when contract doesn't exist."""
        mock_db = AsyncMock()
        service = ChatService(mock_db)

        service.contract_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await service._build_context("NONEXISTENT")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_build_context_truncates_long_text(self):
        """Test that long document text is truncated."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        # Create a long document text (over 10,000 characters)
        long_text = "x" * 15000

        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            policy_number="POL-123",
            purchase_date=date(2024, 1, 1),
            document_text=long_text,
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=None)

        result = await service._build_context("TEST-001")

        assert len(result["document_text"]) == 10000
        assert result["document_text_truncated"] is True


@pytest.mark.unit
class TestChatServiceChat:
    """Tests for ChatService chat functionality."""

    @pytest.mark.asyncio
    async def test_chat_with_new_session(self):
        """Test chat with new session creation."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        # Mock contract
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            policy_number="POL-123",
            purchase_date=date(2024, 1, 1),
            document_text="Sample text",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=None)

        # Mock LLM response
        mock_llm_response = {
            "response": "I can help you with your contract.",
            "sources": ["contract_text"],
            "model": "gpt-4",
            "provider": "openai",
            "cost_usd": 0.001,
        }

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # No existing session
        mock_redis.setex.return_value = True

        with (
            patch("app.utils.cache.get_redis", return_value=mock_redis),
            patch.object(service.llm_service, "chat", return_value=mock_llm_response),
            patch.object(service.audit_service, "log_chat", new=AsyncMock()),
            patch("app.services.chat_service.settings.cache_ttl_session", 14400),
        ):
            result = await service.chat(
                message="Hello",
                contract_id="TEST-001",
                session_id="new-session",
                ip_address="127.0.0.1",
                user_agent="test-agent",
            )

        assert result["response"] == "I can help you with your contract."
        assert result["metadata"]["session_id"] == "new-session"
        assert result["metadata"]["contract_id"] == "TEST-001"
        assert result["metadata"]["message_count"] == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_chat_with_existing_session(self):
        """Test chat with existing session."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        # Mock contract
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="ACC-12345",
            policy_number="POL-123",
            purchase_date=date(2024, 1, 1),
            document_text="Sample text",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=None)

        # Mock existing session
        existing_session_data = {
            "session_id": "existing-session",
            "contract_id": "TEST-001",
            "messages": [
                {
                    "role": "user",
                    "content": "Previous message",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {},
                },
                {
                    "role": "assistant",
                    "content": "Previous response",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {},
                },
            ],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Mock LLM response
        mock_llm_response = {
            "response": "Based on previous context...",
            "sources": [],
            "model": "gpt-4",
            "provider": "openai",
        }

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(existing_session_data).encode()
        mock_redis.setex.return_value = True

        with (
            patch("app.utils.cache.get_redis", return_value=mock_redis),
            patch.object(service.llm_service, "chat", return_value=mock_llm_response),
            patch.object(service.audit_service, "log_chat", new=AsyncMock()),
            patch("app.services.chat_service.settings.cache_ttl_session", 14400),
        ):
            result = await service.chat(
                message="Follow-up question",
                contract_id="TEST-001",
                session_id="existing-session",
            )

        assert result["response"] == "Based on previous context..."
        assert result["metadata"]["message_count"] == 4  # 2 previous + 2 new

    @pytest.mark.asyncio
    async def test_chat_detects_account_number(self):
        """Test chat detects account number in message."""
        from datetime import date

        mock_db = AsyncMock()
        service = ChatService(mock_db)

        # Mock contract
        mock_contract = Contract(
            contract_id="TEST-001",
            account_number="000123456789",
            s3_bucket="test-bucket",
            s3_key="test.pdf",
            contract_type="GAP",
            document_text="Sample text",
        )

        service.contract_repo.get_by_id = AsyncMock(return_value=mock_contract)
        service.extraction_repo.get_by_contract_id = AsyncMock(return_value=None)

        # Mock LLM response
        mock_llm_response = {
            "response": "I found your account",
            "sources": [],
            "model": "gpt-4",
            "provider": "openai",
        }

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        with (
            patch("app.utils.cache.get_redis", return_value=mock_redis),
            patch.object(service.llm_service, "chat", return_value=mock_llm_response),
            patch.object(service.audit_service, "log_chat", new=AsyncMock()),
            patch("app.services.chat_service.settings.cache_ttl_session", 14400),
        ):
            result = await service.chat(
                message="My account number is 000123456789",
                contract_id="TEST-001",
                session_id="test-session",
            )

        assert "detected_account_number" in result
        assert result["detected_account_number"] == "000123456789"
        assert result["metadata"]["account_number_detected"] is True
