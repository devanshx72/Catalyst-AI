"""
Profile service — business logic for fetching and updating user profiles.

Business rules (legacy/app/routes/main.py:116-192 & docs/architecture-plan.md):
- GET /api/v1/profile: Retrieves existing user profile from MongoDB, stripping sensitive fields.
- PUT /api/v1/profile: Applies partial updates to profile fields.
- Key field changes (especially career_goal, dream_company, personal_statement, company_preference)
  invalidate the user's active roadmap module progress and trigger $unset on 'active_modules'.

NOTE (LinkedIn Integration):
LinkedIn scraping was dropped as an intentional product decision (docs/manual-fixes.md Section 12).
The profile service is completely self-contained on the 'users' collection with zero dependency
on scraped data or external scrapers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import user_repository
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest


KEY_FIELDS = ["career_goal", "dream_company", "personal_statement", "company_preference"]


def _format_profile_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw MongoDB user document to match ProfileResponse schema."""
    formatted = dict(doc)
    formatted.pop("_id", None)
    formatted.pop("password", None)

    # Resolve legacy camelCase fallbacks for backwards compatibility
    if not formatted.get("linkedin_profile") and formatted.get("linkedinProfile"):
        formatted["linkedin_profile"] = formatted.get("linkedinProfile")
    if not formatted.get("github_profile") and formatted.get("githubProfile"):
        formatted["github_profile"] = formatted.get("githubProfile")
    if not formatted.get("joining_date") and formatted.get("startdate"):
        formatted["joining_date"] = formatted.get("startdate")

    return formatted


async def get_user_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> ProfileResponse:
    """Fetch user profile by user_id."""
    user_doc = await user_repository.find_by_user_id(db, user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    return ProfileResponse(**_format_profile_doc(user_doc))


async def update_user_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
    payload: ProfileUpdateRequest,
) -> ProfileResponse:
    """
    Update profile fields for the authenticated user.
    
    If key career fields (such as career_goal) are changed, unsets 'active_modules'
    in MongoDB to reset the roadmap progress as required by legacy business logic.
    """
    existing_doc = await user_repository.find_by_user_id(db, user_id)
    if not existing_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    # Detect if any key field changed from its current DB value
    unset_fields: List[str] = []
    key_fields_updated = False
    for field in KEY_FIELDS:
        if field in updates:
            new_val = str(updates[field] or "").strip()
            old_val = str(existing_doc.get(field) or "").strip()
            if new_val != old_val:
                key_fields_updated = True
                break

    if key_fields_updated:
        unset_fields.append("active_modules")

    updated_doc = await user_repository.update_user_profile(
        db=db,
        user_id=user_id,
        updates=updates,
        unset_fields=unset_fields if unset_fields else None,
    )

    if not updated_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated profile",
        )

    return ProfileResponse(**_format_profile_doc(updated_doc))
