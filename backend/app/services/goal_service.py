"""
Goal Service — Career goal lifecycle management, availability configuration,
and skill gap analysis integration.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import goal_repository, resume_repository, user_repository
from app.schemas.goals import GoalCreateRequest, GoalResponse, GoalUpdateRequest, SkillGapResponse
from app.services.skill_gap_service import analyze_skill_gaps

logger = logging.getLogger(__name__)


async def get_active_goal(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[GoalResponse]:
    """Retrieve active career goal for a user."""
    doc = await goal_repository.find_active_by_user_id(db, user_id)
    if doc:
        return GoalResponse(**doc)

    # Fallback to user_doc
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if user_doc and user_doc.get("career_goal"):
        goal_title = user_doc.get("career_goal")
        new_doc = {
            "user_id": user_id,
            "goal_title": goal_title,
            "target_duration_months": 6,
            "weekly_hours": 15,
            "current_level": "beginner",
            "company_preference": user_doc.get("dream_company"),
        }
        goal_id = await goal_repository.create_goal(db, new_doc)
        new_doc["id"] = goal_id
        return GoalResponse(**new_doc)

    return None


async def create_career_goal(
    db: AsyncIOMotorDatabase,
    user_id: str,
    payload: GoalCreateRequest,
) -> GoalResponse:
    """
    Create a new career goal and set it as active.
    Syncs the career_goal field on the user profile.
    """
    doc = {
        "user_id": user_id,
        "goal_title": payload.goal_title.strip(),
        "target_duration_months": payload.target_duration_months,
        "weekly_hours": payload.weekly_hours,
        "current_level": payload.current_level,
        "company_preference": payload.company_preference,
        "notes": payload.notes,
    }

    goal_id = await goal_repository.create_goal(db, doc)
    doc["id"] = goal_id

    # Sync user document for backwards compatibility
    await user_repository.update_user_profile(
        db=db,
        user_id=user_id,
        updates={"career_goal": payload.goal_title.strip()}
    )

    return GoalResponse(**doc)


async def update_career_goal(
    db: AsyncIOMotorDatabase,
    user_id: str,
    goal_id: str,
    payload: GoalUpdateRequest,
) -> GoalResponse:
    """Update properties of an existing career goal."""
    updates = payload.model_dump(exclude_unset=True)
    updated = await goal_repository.update_goal(db, goal_id, user_id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career goal not found or ownership mismatch."
        )

    if "goal_title" in updates and updates["goal_title"]:
        await user_repository.update_user_profile(
            db=db,
            user_id=user_id,
            updates={"career_goal": updates["goal_title"]}
        )

    return GoalResponse(**updated)


async def get_active_skill_gap(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> SkillGapResponse:
    """
    Calculate skill gap for the user's active career goal using their active resume.
    """
    active_goal = await get_active_goal(db, user_id)
    if not active_goal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active career goal found. Please create a career goal first."
        )

    active_resume = await resume_repository.find_active_by_user_id(db, user_id)
    user_skills = []
    if active_resume and "parsed_data" in active_resume:
        user_skills = active_resume["parsed_data"].get("skills", [])

    return analyze_skill_gaps(
        user_skills=user_skills,
        career_goal_title=active_goal.goal_title,
        current_level=active_goal.current_level,
    )
