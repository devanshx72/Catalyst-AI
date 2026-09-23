"""
Roadmap Service — Business logic for versioned roadmaps, learning plan generation,
and hierarchical progress tracking.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import (
    goal_repository,
    learning_plan_repository,
    notification_repository,
    resume_repository,
    roadmap_repository,
    user_repository,
)
from app.schemas.roadmap import (
    PhasePlanResponse,
    PlanGenerateResponse,
    RoadmapEvaluationScore,
    RoadmapGenerateResponse,
    RoadmapResponse,
    RoadmapValidationReport,
    TaskCompleteRequest,
    TaskCompleteResponse,
)
from app.services.llm_service import generate_learning_plan
from app.services.roadmap_engine.planner import plan_and_orchestrate_roadmap
from app.services.skill_gap_service import analyze_skill_gaps

logger = logging.getLogger(__name__)


def _parse_legacy_roadmap(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback helper to extract legacy serialized string from users collection."""
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


_parse_roadmap_data = _parse_legacy_roadmap


async def get_user_roadmap(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> RoadmapResponse:
    """
    Fetch active roadmap status and curriculum.
    Prioritizes dedicated 'roadmaps' collection with fallback to legacy user document.
    """
    # 1. Look up active career goal
    active_goal = await goal_repository.find_active_by_user_id(db, user_id)
    goal_title = active_goal.get("goal_title") if active_goal else None

    # Fallback to user doc career_goal if no goal document exists yet
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not goal_title and user_doc:
        goal_title = (user_doc.get("career_goal") or "").strip() or None

    has_career_goal = bool(goal_title)

    # 2. Look up active roadmap from roadmaps collection
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    
    if active_roadmap:
        roadmap_id = active_roadmap.get("id")
        phases = active_roadmap.get("phases", [])
        has_roadmap = len(phases) > 0
        progress = await roadmap_repository.compute_roadmap_progress(db, user_id, roadmap_id) if roadmap_id else None

        val_data = active_roadmap.get("validation_report")
        eval_data = active_roadmap.get("evaluation_score")

        return RoadmapResponse(
            has_career_goal=has_career_goal,
            has_roadmap=has_roadmap,
            career_goal=goal_title,
            roadmap_id=roadmap_id,
            version=active_roadmap.get("version", 1),
            target_duration_months=active_roadmap.get("target_duration_months", 6),
            weekly_hours=active_roadmap.get("weekly_hours", 15),
            roadmap_data=active_roadmap,
            validation_report=RoadmapValidationReport(**val_data) if val_data else None,
            evaluation_score=RoadmapEvaluationScore(**eval_data) if eval_data else None,
            progress_summary=progress,
        )

    # Legacy migration fallback: check user_doc.road_map
    legacy_data = _parse_legacy_roadmap(user_doc) if user_doc else {}
    has_legacy_roadmap = bool(legacy_data and "phases" in legacy_data and len(legacy_data.get("phases", [])) > 0)

    return RoadmapResponse(
        has_career_goal=has_career_goal,
        has_roadmap=has_legacy_roadmap,
        career_goal=goal_title,
        roadmap_data=legacy_data if has_legacy_roadmap else None,
    )


async def generate_user_roadmap(
    db: AsyncIOMotorDatabase,
    user_id: str,
    force_regenerate: bool = False,
) -> RoadmapGenerateResponse:
    """
    Generate or regenerate a verified 4-phase milestone roadmap for the active career goal.
    Coordinates skill gap analysis, deterministic validation, evaluation, and persistence.
    """
    # 1. Fetch active goal
    active_goal = await goal_repository.find_active_by_user_id(db, user_id)
    goal_title = active_goal.get("goal_title") if active_goal else None

    # Fallback to user_doc
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not goal_title and user_doc:
        goal_title = (user_doc.get("career_goal") or "").strip()
        if goal_title:
            # Create a goal record on the fly for consistency
            await goal_repository.create_goal(db, {
                "user_id": user_id,
                "goal_title": goal_title,
                "target_duration_months": 6,
                "weekly_hours": 15,
                "current_level": "beginner",
            })
            active_goal = await goal_repository.find_active_by_user_id(db, user_id)

    if not goal_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate roadmap: Please set your career goal first."
        )

    duration_months = int(active_goal.get("target_duration_months", 6)) if active_goal else 6
    weekly_hours = int(active_goal.get("weekly_hours", 15)) if active_goal else 15
    current_level = active_goal.get("current_level", "beginner") if active_goal else "beginner"

    # 2. Fetch user's active resume skills
    active_resume = await resume_repository.find_active_by_user_id(db, user_id)
    user_skills = []
    if active_resume and "parsed_data" in active_resume:
        user_skills = active_resume["parsed_data"].get("skills", [])

    # 3. Analyze skill gaps
    gap_result = analyze_skill_gaps(
        user_skills=user_skills,
        career_goal_title=goal_title,
        current_level=current_level,
    )

    # 4. Orchestrate Roadmap Generation, Validation, Evaluation & Repair
    roadmap_draft, val_report, eval_score = plan_and_orchestrate_roadmap(
        career_goal=goal_title,
        target_duration_months=duration_months,
        weekly_hours=weekly_hours,
        current_level=current_level,
        acquired_skills=gap_result.acquired_skills,
        missing_skills=gap_result.missing_skills,
        learning_order=gap_result.recommended_learning_order,
    )

    # 5. Determine version number and persist
    next_ver = await roadmap_repository.get_next_version(db, user_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    goal_id = active_goal.get("id") if active_goal else None
    resume_id = active_resume.get("id") if active_resume else None

    roadmap_doc = {
        "user_id": user_id,
        "goal_id": goal_id,
        "career_goal_id": goal_id,
        "resume_id": resume_id,
        "career_goal": goal_title,
        "title": f"Career Roadmap: {goal_title}",
        "version": next_ver,
        "status": "active",
        "target_duration_months": duration_months,
        "weekly_hours": weekly_hours,
        "current_level": current_level,
        "goal_snapshot": {
            "target_role": goal_title,
            "current_level": current_level,
            "target_duration": {"value": duration_months, "unit": "months"},
            "weekly_hours": weekly_hours,
        },
        "skill_gap_snapshot": {
            "acquired_skills": gap_result.acquired_skills,
            "missing_skills": gap_result.missing_skills,
            "recommended_learning_order": gap_result.recommended_learning_order,
        },
        "phases": roadmap_draft.get("phases", []),
        "generation": {
            "workflow_version": "2.0",
            "prompt_version": "2.0",
            "schema_version": "2.0",
            "model": "groq/llama-3.3-70b-versatile",
            "generated_at": now_iso,
        },
        "validation": {
            "status": "passed" if val_report.is_valid else "failed",
            "deterministic_passed": val_report.is_valid,
            "checks": [c.model_dump() for c in val_report.checks],
            "validated_at": now_iso,
        },
        "validation_report": val_report.model_dump(),
        "evaluation": {
            "status": "accepted" if eval_score.score >= 0.70 else "rejected",
            "accepted": eval_score.score >= 0.70,
            "score": eval_score.score,
            "alignment": eval_score.alignment,
            "coverage": eval_score.coverage,
            "feasibility": eval_score.feasibility,
            "feedback": eval_score.feedback,
            "evaluated_at": now_iso,
        },
        "evaluation_score": eval_score.model_dump(),
        "repair": {
            "attempt_count": 0,
        },
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    roadmap_id = await roadmap_repository.save_roadmap(db, roadmap_doc)

    # Link active roadmap to the goal if active_goal exists
    if active_goal and goal_id:
        await goal_repository.update_goal(db, goal_id, user_id, {"active_roadmap_id": roadmap_id})

    # Record notification per Document 3 Section 31
    try:
        await notification_repository.create_notification(
            db=db,
            user_id=user_id,
            notification_type="roadmap_ready",
            title="Roadmap Ready",
            message=f"Your personalized career roadmap for {goal_title} (v{next_ver}) is ready.",
            entity_type="roadmap",
            entity_id=roadmap_id,
        )
    except Exception as e:
        logger.warning(f"Failed to record roadmap_ready notification: {e}")

    return RoadmapGenerateResponse(
        status="success",
        message="Roadmap generated and validated successfully.",
        roadmap_id=roadmap_id,
        version=next_ver,
        validation=val_report,
        evaluation=eval_score,
    )


async def generate_phase_plan(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
) -> PlanGenerateResponse:
    """Generate or retrieve learning plan for a specific phase."""
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    if not active_roadmap:
        # Check legacy fallback
        user_doc = await user_repository.find_by_user_id(db, user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        legacy_data = _parse_legacy_roadmap(user_doc)
        if not legacy_data or "phases" not in legacy_data:
            raise HTTPException(status_code=404, detail="No active roadmap found. Please generate one.")
        active_roadmap = legacy_data
        active_roadmap["id"] = "legacy"

    phases = active_roadmap.get("phases", [])
    if phase_id < 0 or phase_id >= len(phases):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase ID {phase_id}. Must be between 0 and {len(phases) - 1}.",
        )

    phase = phases[phase_id]
    if phase.get("learning_plan"):
        return PlanGenerateResponse(
            status="exists",
            message="Learning plan already exists",
            phase_id=phase_id,
            learning_plan=phase["learning_plan"],
        )

    phase_name = phase.get("name", f"Phase {phase_id + 1}")
    skills = phase.get("skills", [])

    # Generate plan with Groq LLM (with deterministic 4-week fallback)
    learning_plan = generate_learning_plan(phase_name, skills)

    # Initialize completed flag to False
    for week in learning_plan.get("weekly_schedule", []):
        for task in week.get("daily_tasks", []):
            task["completed"] = False

    phase["learning_plan"] = learning_plan

    # Persist in roadmaps collection if first-class, else legacy user doc
    if active_roadmap.get("id") != "legacy":
        await roadmap_repository.update_phase_plan(
            db=db,
            roadmap_id=active_roadmap["id"],
            phase_id=phase_id,
            learning_plan=learning_plan,
        )

        # Also persist first-class learning plan in learning_plans collection (Doc 3 Section 21)
        plan_items = []
        for w_idx, week in enumerate(learning_plan.get("weekly_schedule", [])):
            for d_idx, task in enumerate(week.get("daily_tasks", [])):
                plan_items.append({
                    "item_id": f"p{phase_id}_w{w_idx}_d{d_idx}",
                    "roadmap_phase_id": str(phase_id),
                    "roadmap_module_id": f"m_{w_idx}",
                    "roadmap_task_id": f"t_{w_idx}_{d_idx}",
                    "title": task.get("task", f"Task {d_idx+1}"),
                    "description": task.get("resource", ""),
                    "estimated_hours": 2,
                    "status": "pending",
                    "completed_at": None,
                })

        plan_doc = {
            "user_id": user_id,
            "goal_id": active_roadmap.get("goal_id") or active_roadmap.get("career_goal_id"),
            "roadmap_id": active_roadmap["id"],
            "phase_id": phase_id,
            "status": "active",
            "items": plan_items,
            "generation": {
                "workflow_version": "2.0",
                "prompt_version": "2.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        await learning_plan_repository.create_learning_plan(db, plan_doc)
    else:
        await user_repository.update_user_roadmap(
            db=db,
            user_id=user_id,
            roadmap_json=json.dumps(active_roadmap),
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
    """Get the learning plan for a specific phase."""
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    if not active_roadmap:
        user_doc = await user_repository.find_by_user_id(db, user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        active_roadmap = _parse_legacy_roadmap(user_doc)

    phases = active_roadmap.get("phases", [])
    if phase_id < 0 or phase_id >= len(phases):
        raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found.")

    phase = phases[phase_id]
    learning_plan = phase.get("learning_plan")
    if not learning_plan:
        raise HTTPException(status_code=404, detail="Learning plan not generated yet for this phase.")

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
    """Update task completion status in both the roadmap and progress collections."""
    active_roadmap = await roadmap_repository.find_active_by_user_id(db, user_id)
    if not active_roadmap:
        user_doc = await user_repository.find_by_user_id(db, user_id)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        active_roadmap = _parse_legacy_roadmap(user_doc)
        active_roadmap["id"] = "legacy"

    phases = active_roadmap.get("phases", [])
    if payload.phase_id < 0 or payload.phase_id >= len(phases):
        raise HTTPException(status_code=400, detail=f"Invalid phase_id {payload.phase_id}.")

    phase = phases[payload.phase_id]
    learning_plan = phase.get("learning_plan")
    if not learning_plan:
        raise HTTPException(status_code=400, detail="Learning plan not generated for this phase.")

    weekly_schedule = learning_plan.get("weekly_schedule", [])
    if payload.week_index < 0 or payload.week_index >= len(weekly_schedule):
        raise HTTPException(status_code=400, detail=f"Invalid week_index {payload.week_index}.")

    daily_tasks = weekly_schedule[payload.week_index].get("daily_tasks", [])
    if payload.day_index < 0 or payload.day_index >= len(daily_tasks):
        raise HTTPException(status_code=400, detail=f"Invalid day_index {payload.day_index}.")

    daily_tasks[payload.day_index]["completed"] = payload.completed

    if active_roadmap.get("id") != "legacy":
        await roadmap_repository.record_task_status(
            db=db,
            user_id=user_id,
            roadmap_id=active_roadmap["id"],
            phase_id=payload.phase_id,
            week_index=payload.week_index,
            day_index=payload.day_index,
            completed=payload.completed,
        )
    else:
        await user_repository.update_user_roadmap(
            db=db,
            user_id=user_id,
            roadmap_json=json.dumps(active_roadmap),
        )

    return TaskCompleteResponse(
        status="success",
        message="Task updated",
        phase_id=payload.phase_id,
        week_index=payload.week_index,
        day_index=payload.day_index,
        completed=payload.completed,
    )
