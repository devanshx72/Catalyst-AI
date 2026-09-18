"""
Pydantic schemas for the auth endpoints.

Field names and constraints are derived from the users collection schema
documented in docs/architecture-plan.md Section 2 and the sign_up form
fields at legacy/app/routes/auth.py:21-61.

Rules:
- Request bodies use strict validation (no coercion by default in Pydantic v2).
- Response bodies never include password hashes.
- Optional fields mirror the legacy form's optional= behaviour.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Maps to the POST /sign_up form fields (legacy/app/routes/auth.py:21-61)."""

    # Required (always present on sign-up form)
    username: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=30)
    dob: str = Field(..., description="Date of birth (any string format accepted by the UI)")
    password: str = Field(..., min_length=6)
    confirm_password: str

    # Optional profile fields (architecture-plan.md Section 2 / auth.py:52-61)
    joining_date: Optional[str] = None          # legacy form field: startdate
    career_goal: Optional[str] = None
    entrepreneurship_interest: Optional[str] = None
    interested_industries: Optional[str] = None  # comma-separated string → split to list
    dream_company: Optional[str] = None
    company_preference: Optional[str] = None
    preferred_company: Optional[str] = None
    personal_statement: Optional[str] = None
    github_profile: Optional[str] = None        # legacy form field: githubProfile
    linkedin_profile: Optional[str] = None      # legacy form field: linkedinProfile

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.strip().lower()


class RegisterResponse(BaseModel):
    """Returned on successful registration."""
    message: str = "Account created successfully. Please log in."


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    Accepts either email or user_id in the `username` field,
    matching legacy/app/routes/auth.py:82 behaviour.
    """
    username: str = Field(..., min_length=1, description="Email address or user_id")
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """
    Returned on successful login.
    The session cookie is set on the HTTP response — it is NOT in this body.
    """
    message: str
    user_id: str
    name: str


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutResponse(BaseModel):
    message: str = "Logged out successfully."
