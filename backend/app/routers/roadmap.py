"""
Roadmap Router — Endpoints for user roadmaps and learning plans:
- GET /api/v1/roadmap
- POST /api/v1/roadmap/phases/{phase_id}/plan
- GET /api/v1/roadmap/phases/{phase_id}/plan
- PATCH /api/v1/roadmap/tasks/complete

Route handlers are thin:
  Auth-gate (cookie session) → validation → service call → response.
"""
from fastapi import APIRouter, Depends, Path, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_session
from app.schemas.roadmap import (
    PhasePlanResponse,
    PlanGenerateResponse,
    RoadmapResponse,
    TaskCompleteRequest,
    TaskCompleteResponse,
)
from app.services.roadmap_service import (
    complete_task,
    generate_phase_plan,
    get_phase_plan,
    get_user_roadmap,
)

router = APIRouter(prefix="/api/v1/roadmap", tags=["roadmap"])


@router.get(
    "",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user roadmap and career goal status",
)
async def get_roadmap(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> RoadmapResponse:
    """
    Fetch the roadmap for the authenticated user.
    Returns flags `has_career_goal` and `has_roadmap` along with roadmap data.
    """
    return await get_user_roadmap(db=db, user_id=session["user_id"])


@router.post(
    "/phases/{phase_id}/plan",
    response_model=PlanGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate learning plan for a roadmap phase",
)
async def generate_plan(
    phase_id: int = Path(..., ge=0, description="0-indexed phase ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> PlanGenerateResponse:
    """
    Generate or retrieve the weekly learning plan for a specific roadmap phase.
    If the plan already exists, returns it without regenerating.
    """
    return await generate_phase_plan(
        db=db,
        user_id=session["user_id"],
        phase_id=phase_id,
    )


@router.get(
    "/phases/{phase_id}/plan",
    response_model=PhasePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get learning plan for a specific phase",
)
async def get_plan(
    phase_id: int = Path(..., ge=0, description="0-indexed phase ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> PhasePlanResponse:
    """
    Fetch the generated learning plan for a specific roadmap phase.
    Returns 404 if the learning plan has not been generated yet.
    """
    return await get_phase_plan(
        db=db,
        user_id=session["user_id"],
        phase_id=phase_id,
    )


@router.patch(
    "/tasks/complete",
    response_model=TaskCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a daily task in a learning plan as completed or incomplete",
)
async def update_task_completion(
    payload: TaskCompleteRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> TaskCompleteResponse:
    """
    Update the completion status of a daily task within a phase's weekly schedule.
    """
    return await complete_task(
        db=db,
        user_id=session["user_id"],
        payload=payload,
    )
