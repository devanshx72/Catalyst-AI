"""
Career Goals Router — Endpoints for setting goals, availability, and analyzing skill gaps:
- GET /api/v1/goals/active
- POST /api/v1/goals
- PATCH /api/v1/goals/{goal_id}
- GET /api/v1/goals/skill-gap
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_current_session, get_db
from app.schemas.goals import (
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
    SkillGapResponse,
)
from app.services.goal_service import (
    create_career_goal,
    get_active_goal,
    get_active_skill_gap,
    update_career_goal,
)

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


@router.get(
    "/active",
    response_model=Optional[GoalResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user's current active career goal",
)
async def get_current_goal(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> Optional[GoalResponse]:
    """Retrieve active career goal, duration, and weekly hours."""
    goal = await get_active_goal(db=db, user_id=session["user_id"])
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active career goal found."
        )
    return goal


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or activate a new career goal",
)
async def create_goal(
    payload: GoalCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> GoalResponse:
    """Create a new career goal with desired duration and weekly study availability."""
    return await create_career_goal(
        db=db,
        user_id=session["user_id"],
        payload=payload,
    )


@router.patch(
    "/{goal_id}",
    response_model=GoalResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing career goal",
)
async def update_goal(
    goal_id: str = Path(..., description="Career goal ID"),
    payload: GoalUpdateRequest = ...,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> GoalResponse:
    """Update goal parameters like availability, timeline, or current level."""
    return await update_career_goal(
        db=db,
        user_id=session["user_id"],
        goal_id=goal_id,
        payload=payload,
    )


@router.get(
    "/skill-gap",
    response_model=SkillGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate skill gap between active resume and career goal",
)
async def get_skill_gap(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> SkillGapResponse:
    """Compute missing, weak, and acquired skills against target role matrix."""
    return await get_active_skill_gap(
        db=db,
        user_id=session["user_id"],
    )
