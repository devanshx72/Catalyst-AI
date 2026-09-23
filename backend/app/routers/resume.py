"""
Resume Router — Endpoints for resume uploading, entity extraction, and inspection:
- POST /api/v1/resumes/upload
- GET /api/v1/resumes/active
- PUT /api/v1/resumes/active
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_current_session, get_db
from app.schemas.resume import ResumeResponse, ResumeUpdateRequest
from app.services.resume_service import (
    get_active_resume,
    handle_resume_upload,
    update_user_resume_data,
)

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse resume file (PDF, TXT, DOCX)",
)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> ResumeResponse:
    """Securely upload resume file and extract structured technical entities."""
    return await handle_resume_upload(
        db=db,
        user_id=session["user_id"],
        file=file,
    )


@router.get(
    "/active",
    response_model=Optional[ResumeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user's current active parsed resume",
)
async def get_active(
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> Optional[ResumeResponse]:
    """Retrieve the currently active resume and parsed entities."""
    res = await get_active_resume(db=db, user_id=session["user_id"])
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found.",
        )
    return res


@router.put(
    "/active",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Review and correct extracted resume skills and experience",
)
async def update_parsed_resume(
    payload: ResumeUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    session: dict = Depends(get_current_session),
) -> ResumeResponse:
    """Allow learner to update and verify parsed technical skills and experience."""
    return await update_user_resume_data(
        db=db,
        user_id=session["user_id"],
        payload=payload,
    )
