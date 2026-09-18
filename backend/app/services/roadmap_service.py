"""
Roadmap Service — business logic for fetching roadmaps, generating learning plans,
fetching phase learning plans, and completing daily tasks.

Behavior matches legacy/app/routes/roadmap.py with documented bug fixes:
- Fix 1: Independent dicts for fallback weeks (no `[x] * 4` bug).
- Fix 2: GET /phases/{phase_id}/plan returns 404 when plan is not generated yet
         (legacy redirected GET to a POST-only endpoint, causing a 405 Method Not Allowed).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import user_repository
from app.schemas.roadmap import (
    PhasePlanResponse,
    PlanGenerateResponse,
    RoadmapResponse,
    TaskCompleteRequest,
    TaskCompleteResponse,
)
from app.services.llm_service import generate_learning_plan

logger = logging.getLogger(__name__)


def _parse_roadmap_data(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and parse the 'road_map' field from a user document."""
    raw = user_doc.get("road_map")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return {}


async def get_user_roadmap(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> RoadmapResponse:
    """Fetch roadmap status and data for the authenticated user."""
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    career_goal = (user_doc.get("career_goal") or "").strip()
    has_career_goal = bool(career_goal)

    roadmap_data = _parse_roadmap_data(user_doc)
    has_roadmap = bool(roadmap_data and "phases" in roadmap_data and len(roadmap_data.get("phases", [])) > 0)

    return RoadmapResponse(
        has_career_goal=has_career_goal,
        has_roadmap=has_roadmap,
        career_goal=career_goal if has_career_goal else None,
        roadmap_data=roadmap_data if has_roadmap else None,
    )


async def generate_phase_plan(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
) -> PlanGenerateResponse:
    """
    Generate or return existing learning plan for a specific phase.
    Mirrors legacy POST /generate-plan/<phase_id>.
    """
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    roadmap_data = _parse_roadmap_data(user_doc)
    phases = roadmap_data.get("phases", [])

    if phase_id < 0 or phase_id >= len(phases):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase ID {phase_id}. Must be between 0 and {len(phases) - 1}.",
        )

    phase = phases[phase_id]

    # Return existing plan if already generated
    if phase.get("learning_plan"):
        return PlanGenerateResponse(
            status="exists",
            message="Learning plan already exists",
            phase_id=phase_id,
            learning_plan=phase["learning_plan"],
        )

    phase_name = phase.get("name", "")
    skills = phase.get("skills", [])

    if not phase_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase is missing a name in roadmap data.",
        )

    # Generate plan using Groq LLM (or corrected 4-week fallback)
    learning_plan = generate_learning_plan(phase_name, skills)

    # Initialize completion flag to False for all tasks
    for week in learning_plan.get("weekly_schedule", []):
        for task in week.get("daily_tasks", []):
            task["completed"] = False

    phase["learning_plan"] = learning_plan

    # Persist updated roadmap in MongoDB
    await user_repository.update_user_roadmap(
        db=db,
        user_id=user_id,
        roadmap_json=json.dumps(roadmap_data),
    )

    return PlanGenerateResponse(
        status="success",
        message="Learning plan generated",
        phase_id=phase_id,
        learning_plan=learning_plan,
    )


async def get_phase_plan(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
) -> PhasePlanResponse:
    """
    Get the learning plan for a specific phase.
    
    Fixed bug: Returns 404 if the plan is not generated yet, allowing the frontend
    to prompt the user to generate it, avoiding the legacy GET->POST 405 redirect bug.
    """
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    roadmap_data = _parse_roadmap_data(user_doc)
    phases = roadmap_data.get("phases", [])

    if phase_id < 0 or phase_id >= len(phases):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase {phase_id} not found in roadmap.",
        )

    phase = phases[phase_id]
    learning_plan = phase.get("learning_plan")

    if not learning_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning plan not generated yet for this phase",
        )

    return PhasePlanResponse(
        phase_id=phase_id,
        phase_name=phase.get("name", f"Phase {phase_id + 1}"),
        skills=phase.get("skills", []),
        learning_plan=learning_plan,
    )


async def complete_task(
    db: AsyncIOMotorDatabase,
    user_id: str,
    payload: TaskCompleteRequest,
) -> TaskCompleteResponse:
    """
    Update completion status for a specific task in a phase's learning plan.
    Mirrors legacy POST /complete-task.
    """
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    roadmap_data = _parse_roadmap_data(user_doc)
    phases = roadmap_data.get("phases", [])

    if payload.phase_id < 0 or payload.phase_id >= len(phases):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase_id {payload.phase_id}.",
        )

    phase = phases[payload.phase_id]
    learning_plan = phase.get("learning_plan")
    if not learning_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Learning plan has not been generated for this phase.",
        )

    weekly_schedule = learning_plan.get("weekly_schedule", [])
    if payload.week_index < 0 or payload.week_index >= len(weekly_schedule):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid week_index {payload.week_index}.",
        )

    daily_tasks = weekly_schedule[payload.week_index].get("daily_tasks", [])
    if payload.day_index < 0 or payload.day_index >= len(daily_tasks):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid day_index {payload.day_index}.",
        )

    daily_tasks[payload.day_index]["completed"] = payload.completed

    # Persist updated roadmap in MongoDB
    await user_repository.update_user_roadmap(
        db=db,
        user_id=user_id,
        roadmap_json=json.dumps(roadmap_data),
    )

    return TaskCompleteResponse(
        status="success",
        message="Task updated",
        phase_id=payload.phase_id,
        week_index=payload.week_index,
        day_index=payload.day_index,
        completed=payload.completed,
    )
