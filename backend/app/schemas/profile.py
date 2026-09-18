"""
Pydantic schemas for the Profile endpoints (GET /api/v1/profile, PUT /api/v1/profile).

Derived from:
- users collection schema (docs/architecture-plan.md Section 2)
- legacy student_profile route (legacy/app/routes/main.py:116-192)
- legacy student_profile.html form fields

Security & Hygiene:
- Never returns password or internal MongoDB ObjectIds.
- Canonicalizes snake_case field names (linkedin_profile, github_profile, joining_date)
  while accepting camelCase aliases for backwards compatibility with legacy payloads.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProfileResponse(BaseModel):
    """Full user profile response (safe for client, no password hash)."""

    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    joining_date: Optional[str] = None
    enddate: Optional[str] = None
    career_goal: Optional[str] = None
    learning_duration: Optional[str] = None
    learning_duration_unit: Optional[str] = "months"
    dream_company: Optional[str] = None
    company_preference: Optional[str] = None
    preferred_company: Optional[str] = None
    entrepreneurship_interest: Optional[str] = None
    key_interests: Optional[List[str]] = None
    interested_industries: Optional[str] = None
    personal_statement: Optional[str] = None
    github_profile: Optional[str] = None
    linkedin_profile: Optional[str] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    road_map: Optional[Any] = None
    active_modules: Optional[List[Any]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class ProfileUpdateRequest(BaseModel):
    """Payload for PUT /api/v1/profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    dob: Optional[str] = None
    gender: Optional[str] = None
    joining_date: Optional[str] = Field(None, alias="startdate")
    enddate: Optional[str] = None
    career_goal: Optional[str] = None
    learning_duration: Optional[str] = None
    learning_duration_unit: Optional[str] = None
    dream_company: Optional[str] = None
    company_preference: Optional[str] = None
    preferred_company: Optional[str] = None
    entrepreneurship_interest: Optional[str] = None
    key_interests: Optional[List[str]] = None
    interested_industries: Optional[str] = None
    personal_statement: Optional[str] = None
    github_profile: Optional[str] = Field(None, alias="githubProfile")
    linkedin_profile: Optional[str] = Field(None, alias="linkedinProfile")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )
