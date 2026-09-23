"""
Pydantic schemas for Career Goals and Skill-Gap Analysis.
Encapsulates user career direction, durations, availability, and skill gap evaluations.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class GoalCreateRequest(BaseModel):
    goal_title: str = Field(..., min_length=2, max_length=100, description="Target career role or title")
    target_duration_months: int = Field(default=6, ge=1, le=24, description="Desired completion duration in months")
    weekly_hours: int = Field(default=15, ge=2, le=80, description="Weekly hours dedicated to study")
    current_level: str = Field(default="beginner", description="beginner, intermediate, or advanced")
    company_preference: Optional[str] = None
    notes: Optional[str] = None


class GoalUpdateRequest(BaseModel):
    goal_title: Optional[str] = Field(None, min_length=2, max_length=100)
    target_duration_months: Optional[int] = Field(None, ge=1, le=24)
    weekly_hours: Optional[int] = Field(None, ge=2, le=80)
    current_level: Optional[str] = None
    company_preference: Optional[str] = None
    notes: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    user_id: str
    goal_title: str
    target_duration_months: int
    weekly_hours: int
    current_level: str
    company_preference: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


class SkillGapItem(BaseModel):
    skill: str
    category: str = "technical"
    status: str  # "acquired" | "weak" | "missing" | "transferable"
    importance: str  # "critical" | "recommended" | "optional"
    prerequisites: List[str] = Field(default_factory=list)
    rationale: str = ""


class SkillGapResponse(BaseModel):
    goal_title: str
    current_level: str
    acquired_skills: List[str] = Field(default_factory=list)
    gaps: List[SkillGapItem] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_learning_order: List[str] = Field(default_factory=list)
