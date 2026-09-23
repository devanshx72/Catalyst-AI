"""
Career Goal Repository — Direct MongoDB access for the 'career_goals' collection.
Encapsulates career goals, target duration, weekly availability, and goal lifecycle states.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "career_goals"


async def create_goal(db: AsyncIOMotorDatabase, goal_doc: Dict[str, Any]) -> str:
    """Create a new career goal and deactivate prior active goals for this user."""
    now = datetime.now(timezone.utc).isoformat()
    goal_doc.setdefault("created_at", now)
    goal_doc.setdefault("updated_at", now)
    goal_doc.setdefault("is_active", True)
    goal_doc.setdefault("status", "active")

    # Document 3 Section 11: Structured target_duration representation
    if "target_duration" not in goal_doc:
        months_val = goal_doc.get("target_duration_months", 6)
        goal_doc["target_duration"] = {"value": int(months_val), "unit": "months"}
    elif isinstance(goal_doc["target_duration"], (int, float)):
        goal_doc["target_duration"] = {"value": int(goal_doc["target_duration"]), "unit": "months"}

    # Deactivate existing active goals
    await db[COLLECTION].update_many(
        {"user_id": goal_doc["user_id"], "status": "active"},
        {"$set": {"is_active": False, "status": "archived", "updated_at": now}}
    )

    result = await db[COLLECTION].insert_one(goal_doc)
    return str(result.inserted_id)


async def find_active_by_user_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve the currently active career goal for a user."""
    doc = await db[COLLECTION].find_one(
        {"user_id": user_id, "is_active": True},
        sort=[("created_at", -1)]
    )
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def find_by_id(
    db: AsyncIOMotorDatabase,
    goal_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a specific goal by ID ensuring user ownership."""
    try:
        oid = ObjectId(goal_id)
    except Exception:
        return None

    doc = await db[COLLECTION].find_one({"_id": oid, "user_id": user_id})
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def update_goal(
    db: AsyncIOMotorDatabase,
    goal_id: str,
    user_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update fields on an existing career goal."""
    try:
        oid = ObjectId(goal_id)
    except Exception:
        return None

    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now

    await db[COLLECTION].update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": updates}
    )
    return await find_by_id(db, goal_id, user_id)


async def list_goals_by_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> List[Dict[str, Any]]:
    """List all career goals (historical and active) for the user."""
    cursor = db[COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        results.append(doc)
    return results
