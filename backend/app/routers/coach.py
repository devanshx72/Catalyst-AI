"""
Career Coach (Leo) Router — Endpoints for coaching conversation:
- GET /api/v1/coach/messages
- POST /api/v1/coach/chat
- DELETE /api/v1/coach/history

Route handlers are thin:
  Auth-gate (cookie session) → validation → service call → response.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_session
from app.schemas.coach import (
    CoachChatRequest,
    CoachChatResponse,
    CoachClearHistoryResponse,
    CoachMessagesResponse,
)
from app.services.coach_service import (
    chat_with_coach,
    clear_coach_history,
    get_coach_messages,
)

router = APIRouter(prefix="/api/v1/coach", tags=["coach"])


@router.get(
    "/messages",
    response_model=CoachMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history with Leo",
)
async def get_messages(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> CoachMessagesResponse:
    """
    Retrieve full conversation history with Leo (the Career Coach AI).
    Requires active session.
    """
    return await get_coach_messages(db=db, user_id=session["user_id"])


@router.post(
    "/chat",
    response_model=CoachChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to Leo",
)
async def chat(
    payload: CoachChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> CoachChatResponse:
    """
    Chat with Leo the Career Coach.
    Invokes Mistral with a privacy-redacted prompt and persists turn in MongoDB.
    """
    return await chat_with_coach(
        db=db,
        user_id=session["user_id"],
        user_query=payload.message,
    )


@router.delete(
    "/history",
    response_model=CoachClearHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear conversation history with Leo",
)
async def clear_history(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> CoachClearHistoryResponse:
    """
    Clear all messages with Leo for a clean slate.
    """
    return await clear_coach_history(db=db, user_id=session["user_id"])
