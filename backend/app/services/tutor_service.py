"""
AI Tutor Service — business logic for module context, SSE chat streaming, and chat history management.

Rules & Features:
- GET /tutor/{phase_id}/{module_id}: Loads module context + persisted history.
- POST /tutor/{phase_id}/{module_id}/chat: Real SSE streaming via Groq (LLM Call 5).
  Sends incremental tokens to client over Server-Sent Events, and commits user + assistant
  messages to MongoDB upon stream completion.
- Conversation context: Uses last 10 messages from user_chat_histories for the module.
- DELETE /tutor/{phase_id}/{module_id}/history: Wipes the module chat history array.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import chat_repository, roadmap_repository, user_repository
from app.schemas.tutor import (
    ChatMessage,
    ClearHistoryResponse,
    TutorContextResponse,
)
from app.services.llm_service import get_groq_tutor_stream
from app.services.roadmap_service import _parse_roadmap_data

logger = logging.getLogger(__name__)


def _extract_phase_and_module(
    roadmap_data: Dict[str, Any],
    phase_id: int,
    module_id: int,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Validate and extract phase and module dictionaries from roadmap data."""
    phases = roadmap_data.get("phases", [])
    if phase_id < 0 or phase_id >= len(phases):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase {phase_id} not found in user roadmap.",
        )

    phase = phases[phase_id]
    learning_plan = phase.get("learning_plan", {})
    weekly_schedule = learning_plan.get("weekly_schedule", [])

    # Legacy handles module_id as 1-indexed week number (e.g. week 1 = module_id 1)
    mod_idx = module_id - 1 if 1 <= module_id <= len(weekly_schedule) else module_id

    if mod_idx < 0 or mod_idx >= len(weekly_schedule):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found in phase {phase_id}.",
        )

    module = weekly_schedule[mod_idx]
    return phase, module


async def get_tutor_context(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
) -> TutorContextResponse:
    """Fetch roadmap module context and historical chat messages for the module."""
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    if active_roadmap and "phases" in active_roadmap:
        roadmap_data = active_roadmap
    else:
        user_doc = await user_repository.find_by_user_id(db, user_id)
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        roadmap_data = _parse_roadmap_data(user_doc)

    phase, module = _extract_phase_and_module(roadmap_data, phase_id, module_id)

    objectives = module.get("learning_objectives", [])
    topic = f"{phase.get('name', '')} - Week {module.get('week', module_id)}: {', '.join(objectives)}"

    raw_history = await chat_repository.get_module_chat_history(
        db, user_id, phase_id, module_id
    )
    formatted_history = [
        ChatMessage(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            timestamp=str(msg.get("timestamp", "")) if msg.get("timestamp") else None,
        )
        for msg in raw_history
    ]

    return TutorContextResponse(
        user_id=user_id,
        phase_id=phase_id,
        module_id=module_id,
        phase_name=phase.get("name", ""),
        topic=topic,
        objectives=objectives,
        skills=phase.get("skills", []),
        resources=phase.get("resources", {}),
        chat_history=formatted_history,
    )


async def stream_tutor_response(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
    message: str,
) -> AsyncGenerator[str, None]:
    """
    Execute streaming LLM call and yield SSE data chunks.
    Persists full conversation to MongoDB after the stream completes.
    """
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    if active_roadmap and "phases" in active_roadmap:
        roadmap_data = active_roadmap
    else:
        user_doc = await user_repository.find_by_user_id(db, user_id)
        if not user_doc:
            yield f"data: {json.dumps({'error': 'User not found'})}\n\n"
            yield "data: [DONE]\n\n"
            return
        roadmap_data = _parse_roadmap_data(user_doc)

    try:
        phase, module = _extract_phase_and_module(roadmap_data, phase_id, module_id)
    except HTTPException as e:
        yield f"data: {json.dumps({'error': e.detail})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Fetch last 10 turns for context (Section 3 LLM Call 4/5)
    history = await chat_repository.get_module_chat_history(
        db, user_id, phase_id, module_id
    )
    recent = history[-10:] if history else []
    conversation_context = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in recent
        if "role" in msg and "content" in msg
    ]

    topic = f"{phase.get('name', '')} - Week {module.get('week', module_id)}"
    objectives = module.get("learning_objectives", [])
    skills = phase.get("skills", [])
    resources = phase.get("resources", {})

    full_response_parts: List[str] = []

    try:
        # Run sync generator in executor/iterator to allow async streaming
        generator = get_groq_tutor_stream(
            message=message,
            topic=topic,
            objectives=objectives,
            skills=skills,
            resources=resources,
            conversation_context=conversation_context,
        )

        for token in generator:
            if token:
                full_response_parts.append(token)
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0)  # Yield control to event loop

    except Exception as e:
        logger.error("Error during tutor stream: %s", e)
        err_payload = json.dumps({"error": str(e)})
        yield f"data: {err_payload}\n\n"

    # End-of-stream delimiter
    yield "data: [DONE]\n\n"

    # Persist user query and full assistant answer to MongoDB
    full_response = "".join(full_response_parts).strip()
    if full_response:
        new_messages = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": full_response},
        ]
        try:
            await chat_repository.append_module_messages(
                db, user_id, phase_id, module_id, new_messages
            )
        except Exception as e:
            logger.error("Failed to persist tutor chat history: %s", e)


async def clear_tutor_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
) -> ClearHistoryResponse:
    """Clear chat history for a specific phase/module."""
    await chat_repository.clear_module_chat_history(db, user_id, phase_id, module_id)
    return ClearHistoryResponse()
