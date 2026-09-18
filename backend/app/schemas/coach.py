"""
Pydantic schemas for the Career Coach (Leo) endpoints:
- GET /api/v1/coach/messages
- POST /api/v1/coach/chat
- DELETE /api/v1/coach/history
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CoachMessage(BaseModel):
    """A single turn in the Leo coaching conversation."""

    prompt: str = Field(..., description="User question / prompt")
    response: str = Field(..., description="HTML-formatted coach response")
    raw_response: str = Field(..., description="Raw markdown response")
    time: Optional[str] = Field(None, description="ISO timestamp of interaction")

    model_config = ConfigDict(extra="ignore")


class CoachMessagesResponse(BaseModel):
    """Returned by GET /api/v1/coach/messages."""

    messages: List[CoachMessage] = Field(default_factory=list)
    conversation_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class CoachChatRequest(BaseModel):
    """Payload for POST /api/v1/coach/chat. Accepts both 'message' and legacy 'userQuery'."""

    message: str = Field(..., min_length=1, alias="userQuery", description="Question for Leo")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class CoachChatResponse(BaseModel):
    """Returned by POST /api/v1/coach/chat."""

    prompt: str
    response: str
    raw_response: str
    messages: List[CoachMessage] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class CoachClearHistoryResponse(BaseModel):
    """Returned by DELETE /api/v1/coach/history."""

    status: str = "success"
    message: str = "Conversation history cleared successfully"

    model_config = ConfigDict(extra="ignore")
