"""
Chat API endpoints for AI-powered contract Q&A.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.requests import ChatMessageRequest
from app.schemas.responses import ChatResponse, ErrorResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message about contract",
    description=(
        "AI-powered chat interface for contract Q&A. "
        "Provides context-aware responses using contract and extraction data. "
        "Supports session-based conversation history. "
        "Automatically detects account numbers in messages."
    ),
    responses={
        200: {
            "description": "Chat response generated successfully",
            "model": ChatResponse,
        },
        404: {
            "description": "Contract not found",
            "model": ErrorResponse,
        },
        500: {
            "description": "LLM service error",
            "model": ErrorResponse,
        },
    },
)
async def send_chat_message(
    request_data: ChatMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and receive AI response.

    Args:
        request_data: Chat message request with contract_id, message, and session_id
        request: FastAPI request object (for IP/user-agent)
        db: Database session (injected)

    Returns:
        ChatResponse with AI response, sources, and metadata

    Raises:
        HTTPException 404: If contract not found
        HTTPException 500: If LLM service fails
    """
    logger.info(
        f"POST /chat - contract: {request_data.contract_id}, "
        f"session: {request_data.session_id}, "
        f"message length: {len(request_data.message)}"
    )

    # Initialize chat service
    chat_service = ChatService(db)

    # Extract client metadata
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        # Process chat message
        response = await chat_service.chat(
            message=request_data.message,
            contract_id=request_data.contract_id,
            session_id=request_data.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            f"Chat response generated for session {request_data.session_id} "
            f"in {response['metadata'].get('duration_ms')}ms"
        )

        # Convert to response model
        return ChatResponse(**response)

    except ValueError as e:
        # Contract not found
        logger.warning(f"Contract not found: {request_data.contract_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract not found: {request_data.contract_id}",
        )

    except Exception as e:
        # LLM service error or other unexpected error
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}",
        )


@router.get(
    "/chat/session/{session_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get chat session history",
    description="Retrieve conversation history for a chat session.",
    responses={
        200: {
            "description": "Session history retrieved successfully",
        },
        404: {
            "description": "Session not found or expired",
            "model": ErrorResponse,
        },
    },
)
async def get_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get chat session history.

    Args:
        session_id: Chat session ID
        db: Database session (injected)

    Returns:
        Session data with conversation history

    Raises:
        HTTPException 404: If session not found or expired
    """
    logger.info(f"GET /chat/session/{session_id}")

    # Initialize chat service
    chat_service = ChatService(db)

    try:
        # Get session history
        session_data = await chat_service.get_session_history(session_id)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found or expired: {session_id}",
            )

        logger.info(
            f"Session retrieved: {session_id} with {len(session_data.get('messages', []))} messages"
        )

        return session_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error retrieving session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session: {str(e)}",
        )


@router.delete(
    "/chat/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear chat session",
    description="Delete a chat session and its history from cache.",
    responses={
        204: {
            "description": "Session cleared successfully",
        },
        500: {
            "description": "Error clearing session",
            "model": ErrorResponse,
        },
    },
)
async def clear_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Clear chat session from cache.

    Args:
        session_id: Chat session ID
        db: Database session (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException 500: If error clearing session
    """
    logger.info(f"DELETE /chat/session/{session_id}")

    # Initialize chat service
    chat_service = ChatService(db)

    try:
        # Clear session
        cleared = await chat_service.clear_session(session_id)

        if cleared:
            logger.info(f"Session cleared: {session_id}")
        else:
            logger.warning(f"Session not found or already cleared: {session_id}")

        # Return 204 regardless of whether session existed
        return None

    except Exception as e:
        logger.error(f"Error clearing session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing session: {str(e)}",
        )
