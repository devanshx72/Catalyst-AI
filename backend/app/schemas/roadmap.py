"""
Pydantic schemas for Roadmap & Learning Plan endpoints:
- GET /api/v1/roadmap
- POST /api/v1/roadmap/phases/{phase_id}/plan
- GET /api/v1/roadmap/phases/{phase_id}/plan
- PATCH /api/v1/roadmap/tasks/complete
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RoadmapResponse(BaseModel):
    """Returned by GET /api/v1/roadmap."""

    has_career_goal: bool
    has_roadmap: bool
    career_goal: Optional[str] = None
    roadmap_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class DailyTask(BaseModel):
    """Daily task inside a weekly schedule."""

    day: int
    tasks: List[str]
    resources: Optional[List[str]] = Field(default_factory=list)
    duration_hours: Optional[int] = 2
    completed: Optional[bool] = False

    model_config = ConfigDict(extra="ignore")


class WeeklyScheduleItem(BaseModel):
    """Single week schedule inside a learning plan."""

    week: int
    learning_objectives: List[str] = Field(default_factory=list)
    daily_tasks: List[DailyTask] = Field(default_factory=list)
    assessment: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class LearningPlan(BaseModel):
    """Full 4-week learning plan for a roadmap phase."""

    weekly_schedule: List[WeeklyScheduleItem]

    model_config = ConfigDict(extra="ignore")


class PhasePlanResponse(BaseModel):
    """Returned by GET /api/v1/roadmap/phases/{phase_id}/plan."""

    phase_id: int
    phase_name: str
    skills: List[str] = Field(default_factory=list)
    learning_plan: Dict[str, Any]

    model_config = ConfigDict(extra="ignore")


class PlanGenerateResponse(BaseModel):
    """Returned by POST /api/v1/roadmap/phases/{phase_id}/plan."""

    status: str
    message: str
    phase_id: int
    learning_plan: Dict[str, Any]

    model_config = ConfigDict(extra="ignore")


class TaskCompleteRequest(BaseModel):
    """Payload for PATCH /api/v1/roadmap/tasks/complete."""

    phase_id: int = Field(..., ge=0, description="0-indexed phase index")
    week_index: int = Field(..., ge=0, description="0-indexed week index")
    day_index: int = Field(..., ge=0, description="0-indexed day index")
    completed: bool = Field(default=True, description="Completion status flag")

    model_config = ConfigDict(extra="ignore")


class TaskCompleteResponse(BaseModel):
    """Returned by PATCH /api/v1/roadmap/tasks/complete."""

    status: str = "success"
    message: str = "Task updated"
    phase_id: int
    week_index: int
    day_index: int
    completed: bool

    model_config = ConfigDict(extra="ignore")
