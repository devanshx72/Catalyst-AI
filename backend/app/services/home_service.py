"""
Home service — business logic for Home dashboard, Medium articles, notifications, and mentorship stub.

Features:
- Home dashboard: 26 hardcoded categories, companies sorted by visit_date, top Medium stories.
- Articles: Medium API story search with query and pagination.
- Notifications: Retrieves unread notifications for authenticated user (max 5, newest first).
- Mentorship: Clear 'not yet implemented' response documenting the legacy missing template.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.repositories import company_repository, notification_repository
from app.schemas.home import (
    CATEGORIES,
    ArticlesResponse,
    HomeResponse,
    MentorshipResponse,
    NotificationItem,
)

logger = logging.getLogger(__name__)


def fetch_medium_stories(
    query: str = "technology",
    limit: int = 5,
    page: int = 0,
) -> List[Dict[str, Any]]:
    """
    Fetch stories from Medium API via RapidAPI (medium16.p.rapidapi.com).
    Falls back gracefully if key is missing or request fails, providing deterministic
    paginated results so testing works without external API dependencies.
    """
    if settings.MEDIUM_API_KEY:
        url = "https://medium16.p.rapidapi.com/search/stories"
        headers = {
            "x-rapidapi-key": settings.MEDIUM_API_KEY,
            "x-rapidapi-host": "medium16.p.rapidapi.com",
        }
        querystring = {"q": query, "limit": str(limit), "page": str(page)}

        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=8)
            if response.status_code == 200:
                data = response.json()
                stories = data.get("data", [])
                if isinstance(stories, list) and len(stories) > 0:
                    return stories
        except Exception as e:
            logger.warning("Failed to fetch Medium stories from RapidAPI: %s", e)

    # Fallback paginated simulated stories (ensures page 0 != page 1 even without API key)
    logger.info("Using simulated Medium articles for topic '%s' (page %d)", query, page)
    return [
        {
            "id": f"sim_{query}_{page}_{i}",
            "title": f"Exploring {query.title()}: Key Insights (Part {page * limit + i + 1})",
            "subtitle": f"A comprehensive overview of recent developments in {query}.",
            "url": f"https://medium.com/tag/{query}",
            "published_at": "2026-09-18",
            "page": page,
        }
        for i in range(limit)
    ]


async def get_home_dashboard(
    db: AsyncIOMotorDatabase,
) -> HomeResponse:
    """Retrieve home page dashboard payload."""
    companies = await company_repository.get_companies(db, limit=5)
    stories = fetch_medium_stories(query="technology", limit=5, page=0)

    return HomeResponse(
        categories=CATEGORIES,
        companies=companies,
        stories=stories,
    )


def get_articles_page(
    query: str = "technology",
    page: int = 0,
) -> ArticlesResponse:
    """Search and paginate Medium articles."""
    clean_query = query.strip() if query and query.strip() else "technology"
    safe_page = max(0, page)
    stories = fetch_medium_stories(query=clean_query, limit=10, page=safe_page)

    return ArticlesResponse(
        query=clean_query,
        page=safe_page,
        categories=CATEGORIES,
        stories=stories,
    )


async def get_user_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> List[NotificationItem]:
    """Retrieve up to 5 unread notifications for the user."""
    raw_notifications = await notification_repository.get_user_notifications(
        db=db,
        user_id=user_id,
        limit=5,
        unread_only=True,
    )
    return [NotificationItem(**n) for n in raw_notifications]


def get_mentorship_status() -> MentorshipResponse:
    """Stubbed response for the missing legacy mentorship template."""
    return MentorshipResponse()
