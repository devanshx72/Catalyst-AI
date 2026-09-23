"""
Resume Repository — Direct MongoDB access for the 'resumes' collection.
Stores resume metadata, raw extracted text, structured parsed entities, and parsing statuses.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "resumes"


async def insert_resume(db: AsyncIOMotorDatabase, resume_doc: Dict[str, Any]) -> str:
    """Insert a new resume document. Sets timestamps and active status."""
    now = datetime.now(timezone.utc).isoformat()
    resume_doc.setdefault("created_at", now)
    resume_doc.setdefault("updated_at", now)
    resume_doc.setdefault("is_active", True)
    resume_doc.setdefault("status", "uploaded")
    resume_doc.setdefault("parsing_status", "uploaded")
    resume_doc.setdefault("parser_version", "2.0")
    resume_doc.setdefault("analysis_version", "2.0")
    
    # Deactivate previous active resumes for this user
    await db[COLLECTION].update_many(
        {"user_id": resume_doc["user_id"], "is_active": True},
        {"$set": {"is_active": False, "updated_at": now}}
    )

    result = await db[COLLECTION].insert_one(resume_doc)
    return str(result.inserted_id)


async def find_active_by_user_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve the currently active resume for a user."""
    doc = await db[COLLECTION].find_one(
        {"user_id": user_id, "is_active": True},
        sort=[("created_at", -1)]
    )
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def find_by_id(
    db: AsyncIOMotorDatabase,
    resume_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a specific resume document ensuring ownership by user_id."""
    try:
        oid = ObjectId(resume_id)
    except Exception:
        return None

    doc = await db[COLLECTION].find_one({"_id": oid, "user_id": user_id})
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def update_parsed_data(
    db: AsyncIOMotorDatabase,
    resume_id: str,
    user_id: str,
    parsed_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update user-reviewed parsed resume data and set status to ready."""
    try:
        oid = ObjectId(resume_id)
    except Exception:
        return None

    now = datetime.now(timezone.utc).isoformat()
    await db[COLLECTION].update_one(
        {"_id": oid, "user_id": user_id},
        {
            "$set": {
                "parsed_data": parsed_data,
                "structured_resume": parsed_data,
                "status": "ready",
                "parsing_status": "completed",
                "updated_at": now,
            }
        }
    )
    return await find_by_id(db, resume_id, user_id)


async def update_parsing_status(
    db: AsyncIOMotorDatabase,
    resume_id: str,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """Update the parsing state of the resume (uploaded, processing, parsed, ready, failed)."""
    try:
        oid = ObjectId(resume_id)
    except Exception:
        return

    now = datetime.now(timezone.utc).isoformat()
    # Map status to both fields
    canonical_status = "ready" if status == "completed" else status
    updates: Dict[str, Any] = {
        "status": canonical_status,
        "parsing_status": status,
        "updated_at": now,
    }
    if error_message is not None:
        updates["error_message"] = error_message

    await db[COLLECTION].update_one({"_id": oid}, {"$set": updates})

