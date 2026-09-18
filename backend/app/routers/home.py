"""
Home Router — Endpoints for Home dashboard, Articles feed, Notifications, and Mentorship stub:
- GET /api/v1/home
- GET /api/v1/articles
- GET /api/v1/notifications
- GET /api/v1/mentorship

Route handlers are thin:
  Auth-gate (cookie session) → validation → service call → response.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_session
from app.schemas.home import (
    ArticlesResponse,
    HomeResponse,
    MentorshipResponse,
    NotificationItem,
)
from app.services.home_service import (
    get_articles_page,
    get_home_dashboard,
    get_mentorship_status,
    get_user_notifications,
)

router = APIRouter(prefix="/api/v1", tags=["home"])


@router.get(
    "/home",
    response_model=HomeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get home dashboard feed (categories, companies, stories)",
)
async def home_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> HomeResponse:
    """
    Retrieve data for the home page dashboard:
    - 26 standard technical categories
    - Top 5 visiting companies sorted by visit_date
    - Latest technology stories from Medium
    Requires an authenticated session.
    """
    return await get_home_dashboard(db=db)


@router.get(
    "/articles",
    response_model=ArticlesResponse,
    status_code=status.HTTP_200_OK,
    summary="Search and paginate Medium news articles",
)
async def articles(
    q: str = Query(default="technology", description="Article search topic"),
    page: int = Query(default=0, ge=0, description="0-indexed page number"),
    session: dict = Depends(get_current_session),
) -> ArticlesResponse:
    """
    Paginated search of articles from Medium.
    Requires an authenticated session.
    """
    return get_articles_page(query=q, page=page)


@router.get(
    "/notifications",
    response_model=List[NotificationItem],
    status_code=status.HTTP_200_OK,
    summary="Get unread notifications for current user",
)
async def notifications(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> List[NotificationItem]:
    """
    Fetch up to 5 unread notifications for the authenticated user, newest first.
    """
    return await get_user_notifications(db=db, user_id=session["user_id"])


@router.get(
    "/mentorship",
    response_model=MentorshipResponse,
    status_code=status.HTTP_200_OK,
    summary="Mentorship feature status (stubbed)",
)
async def mentorship(
    session: dict = Depends(get_current_session),
) -> MentorshipResponse:
    """
    Stubbed endpoint for mentorship.
    In the legacy codebase, this route crashed because mentorship.html was missing.
    Flagged for product decision.
    """
    return get_mentorship_status()
