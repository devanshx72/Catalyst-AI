"""
Pydantic schemas for AI Tutor endpoints:
- GET /api/v1/tutor/{phase_id}/{module_id}
- POST /api/v1/tutor/{phase_id}/{module_id}/chat (SSE stream request body)
- DELETE /api/v1/tutor/{phase_id}/{module_id}/history
- GET /api/v1/tutor/resources
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Single message in a tutor conversation."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TutorContextResponse(BaseModel):
    """Returned by GET /api/v1/tutor/{phase_id}/{module_id}."""

    user_id: str
    phase_id: int
    module_id: int
    phase_name: str
    topic: str
    objectives: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    resources: Dict[str, Any] = Field(default_factory=dict)
    chat_history: List[ChatMessage] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class TutorChatRequest(BaseModel):
    """Payload for POST /api/v1/tutor/{phase_id}/{module_id}/chat."""

    message: str = Field(..., min_length=1, description="Student's query to the tutor")

    model_config = ConfigDict(extra="ignore")


class ClearHistoryResponse(BaseModel):
    """Returned by DELETE /api/v1/tutor/{phase_id}/{module_id}/history."""

    status: str = "success"
    message: str = "Chat history cleared successfully"

    model_config = ConfigDict(extra="ignore")


class ResourceResponse(BaseModel):
    """Returned by GET /api/v1/tutor/resources."""

    status: str = "success"
    resources: Dict[str, Any]

    model_config = ConfigDict(extra="ignore")
