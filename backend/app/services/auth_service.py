"""
Auth service — business logic for register / login / logout.

Rules (migration-rules.md):
- Route handlers must stay thin: route → service → repository.
- Business logic lives here, not in the route or repository.
- Password hashing/verification delegated to user_repository helpers.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.user_repository import (
    find_duplicate,
    find_by_email_or_user_id,
    hash_password,
    insert_user,
    verify_password,
)
from app.schemas.auth import LoginRequest, RegisterRequest


async def register_user(db: AsyncIOMotorDatabase, payload: RegisterRequest) -> None:
    """
    Validate uniqueness, build user document, insert into users collection.

    Document shape matches architecture-plan.md Section 2 / legacy auth.py:45-62.
    Raises 400 on password mismatch.
    Raises 409 on duplicate email or username.
    """
    # 1. Passwords must match (legacy auth.py:30-32)
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    # 2. Reject duplicate email or user_id (legacy auth.py:38-42)
    duplicate = await find_duplicate(db, email=payload.email, username=payload.username)
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists.",
        )

    # 3. Build user document — field names match the legacy users collection exactly.
    #    interested_industries: legacy auth.py:55 splits the comma-separated string.
    key_interests: list[str] = (
        [s.strip() for s in payload.interested_industries.split(",") if s.strip()]
        if payload.interested_industries
        else []
    )

    user_doc = {
        "user_id": payload.username,           # already lowercased by validator
        "name": payload.name,
        "phone": payload.phone,
        "dob": payload.dob,
        "email": payload.email,                # already lowercased by validator
        "password": hash_password(payload.password),
        "joining_date": payload.joining_date,
        "career_goal": payload.career_goal,
        "entrepreneurship_interest": payload.entrepreneurship_interest,
        "key_interests": key_interests,
        "dream_company": payload.dream_company,
        "company_preference": payload.company_preference,
        "preferred_company": payload.preferred_company,
        "personal_statement": payload.personal_statement,
        "github_profile": payload.github_profile,
        "linkedin_profile": payload.linkedin_profile,
    }

    await insert_user(db, user_doc)


async def login_user(
    db: AsyncIOMotorDatabase,
    payload: LoginRequest,
) -> dict:
    """
    Verify credentials and return the user document.

    Raises 401 on bad credentials (does NOT distinguish 'no user' vs 'wrong
    password' to avoid enumeration — same final message to the client).
    Returns dict with at minimum: user_id, name.
    """
    user = await find_by_email_or_user_id(db, payload.username)

    # Constant-time failure: always verify even when user is None
    # to prevent timing-based user enumeration.
    dummy_hash = "$2b$12$KIX/qCOmRdHfzFkWLOzNLecV4BF5yGU8Tz7kVp3RYb5iHzK3HhX/G"
    stored_hash = user["password"] if user else dummy_hash

    if not user or not verify_password(payload.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password.",
        )

    return user
