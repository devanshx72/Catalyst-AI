"""
AI Tutor Router — Endpoints for module chat, SSE streaming, and resources:
- GET /api/v1/tutor/resources
- GET /api/v1/tutor/{phase_id}/{module_id}
- POST /api/v1/tutor/{phase_id}/{module_id}/chat (Server-Sent Events streaming)
- DELETE /api/v1/tutor/{phase_id}/{module_id}/history

Route handlers are thin:
  Auth-gate (session cookie) → validation → service call → response / stream.
"""
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_session
from app.schemas.tutor import (
    ClearHistoryResponse,
    ResourceResponse,
    TutorChatRequest,
    TutorContextResponse,
)
from app.services.resource_service import get_topic_resources
from app.services.tutor_service import (
    clear_tutor_history,
    get_tutor_context,
    stream_tutor_response,
)

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


@router.get(
    "/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get learning resources for a topic",
)
async def get_resources(
    topic: str = Query(..., min_length=1, description="Search query/topic"),
    type: str = Query(default="all", description="Resource type: 'all', 'youtube', 'papers', or 'web'"),
    session: dict = Depends(get_current_session),
) -> ResourceResponse:
    """
    Proxy educational resources from YouTube, Google Scholar (RapidAPI), and Google Custom Search.
    Requires an authenticated session.
    """
    resources = get_topic_resources(topic=topic, resource_type=type)
    return ResourceResponse(status="success", resources=resources)


@router.get(
    "/{phase_id}/{module_id}",
    response_model=TutorContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tutor context and chat history for a module",
)
async def get_context(
    phase_id: int = Path(..., ge=0, description="0-indexed phase ID"),
    module_id: int = Path(..., ge=1, description="1-indexed module (week) ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> TutorContextResponse:
    """
    Fetch roadmap phase/module info and existing chat history for the AI Tutor.
    """
    return await get_tutor_context(
        db=db,
        user_id=session["user_id"],
        phase_id=phase_id,
        module_id=module_id,
    )


@router.post(
    "/{phase_id}/{module_id}/chat",
    summary="Stream AI Tutor response via Server-Sent Events (SSE)",
)
async def chat_stream(
    payload: TutorChatRequest,
    phase_id: int = Path(..., ge=0, description="0-indexed phase ID"),
    module_id: int = Path(..., ge=1, description="1-indexed module (week) ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> StreamingResponse:
    """
    Stream AI Tutor response incrementally over SSE (LLM Call 5).
    Each event has the format: `data: {"token": "..."}\n\n`
    The stream ends with: `data: [DONE]\n\n`
    Conversation history is automatically persisted to MongoDB upon completion.
    """
    return StreamingResponse(
        stream_tutor_response(
            db=db,
            user_id=session["user_id"],
            phase_id=phase_id,
            module_id=module_id,
            message=payload.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/{phase_id}/{module_id}/history",
    response_model=ClearHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear chat history for a module",
)
async def clear_history(
    phase_id: int = Path(..., ge=0, description="0-indexed phase ID"),
    module_id: int = Path(..., ge=1, description="1-indexed module (week) ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> ClearHistoryResponse:
    """
    Wipe chat history messages for a specific module in user_chat_histories.
    """
    return await clear_tutor_history(
        db=db,
        user_id=session["user_id"],
        phase_id=phase_id,
        module_id=module_id,
    )
