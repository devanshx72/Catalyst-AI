"""
Pydantic schemas for Home, Articles, Notifications, and Mentorship endpoints:
- GET /api/v1/home
- GET /api/v1/articles
- GET /api/v1/notifications
- GET /api/v1/mentorship
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

CATEGORIES: List[str] = [
    "Blockchain", "JavaScript", "Education", "Coding", "Books", "Web Development",
    "Marketing", "Deep Learning", "Social Media", "Software Development",
    "Artificial Intelligence", "Culture", "React", "UX", "Software Engineering",
    "Design", "Science", "Health", "Python", "Productivity", "Machine Learning",
    "Writing", "Self Improvement", "Technology", "Data Science", "Programming",
]


class HomeResponse(BaseModel):
    """Returned by GET /api/v1/home."""

    categories: List[str] = Field(default_factory=lambda: CATEGORIES)
    companies: List[Dict[str, Any]] = Field(default_factory=list)
    stories: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ArticlesResponse(BaseModel):
    """Returned by GET /api/v1/articles."""

    query: str
    page: int
    categories: List[str] = Field(default_factory=lambda: CATEGORIES)
    stories: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class NotificationItem(BaseModel):
    """Single notification item."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    read: bool = False
    created_at: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )


class MentorshipResponse(BaseModel):
    """Returned by stubbed GET /api/v1/mentorship."""

    status: str = "not_implemented"
    message: str = (
        "Mentorship service is not yet implemented. In the legacy codebase, "
        "the route crashed because mentorship.html was missing. "
        "A product design decision is required before building this feature."
    )

    model_config = ConfigDict(extra="ignore")
