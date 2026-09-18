"""
Profile router — GET /api/v1/profile and PUT /api/v1/profile.

Route handlers are intentionally thin:
  Auth-gate with session dependency → request validation → service call → response.
No business logic or database queries in this file.
"""
from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_session
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.profile_service import get_user_profile, update_user_profile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_profile(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> ProfileResponse:
    """
    Fetch the profile of the currently authenticated user.
    Requires an active session cookie (returns 401 if missing/invalid).
    """
    return await get_user_profile(db=db, user_id=session["user_id"])


@router.put(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_profile(
    payload: ProfileUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> ProfileResponse:
    """
    Update profile fields for the currently authenticated user.
    Requires an active session cookie (returns 401 if missing/invalid).
    
    If key career fields (e.g., career_goal) change, active roadmap progress
    is invalidated in MongoDB per legacy business rules.
    """
    return await update_user_profile(
        db=db,
        user_id=session["user_id"],
        payload=payload,
    )
