"""
Learning Plan Repository — Direct MongoDB access for the 'learning_plans' collection.
Conforms to Catalyst AI Doc 3 (Sections 21-23).
Traceable to roadmap phases, modules, and tasks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "learning_plans"


async def create_learning_plan(
    db: AsyncIOMotorDatabase,
    plan_doc: Dict[str, Any],
) -> str:
    """
    Persist a newly generated learning plan linked to an active roadmap.
    Deactivates prior active learning plans for the same roadmap or goal.
    """
    now = datetime.now(timezone.utc).isoformat()
    plan_doc.setdefault("created_at", now)
    plan_doc.setdefault("updated_at", now)
    plan_doc.setdefault("status", "active")

    user_id = plan_doc.get("user_id")
    roadmap_id = plan_doc.get("roadmap_id")

    # Deactivate existing active plans for this roadmap
    if user_id and roadmap_id:
        await db[COLLECTION].update_many(
            {"user_id": user_id, "roadmap_id": roadmap_id, "status": "active"},
            {"$set": {"status": "archived", "updated_at": now}},
        )

    result = await db[COLLECTION].insert_one(plan_doc)
    return str(result.inserted_id)


async def find_active_by_roadmap(
    db: AsyncIOMotorDatabase,
    user_id: str,
    roadmap_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve the current active learning plan for a specific roadmap."""
    doc = await db[COLLECTION].find_one(
        {"user_id": user_id, "roadmap_id": roadmap_id, "status": "active"},
        sort=[("created_at", -1)],
    )
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def find_by_id(
    db: AsyncIOMotorDatabase,
    plan_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a specific learning plan by ID with user ownership check."""
    try:
        oid = ObjectId(plan_id)
    except Exception:
        return None

    doc = await db[COLLECTION].find_one({"_id": oid, "user_id": user_id})
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def update_item_status(
    db: AsyncIOMotorDatabase,
    user_id: str,
    plan_id: str,
    item_id: str,
    status: str,
) -> bool:
    """
    Update the execution status of a specific item in the learning plan.
    Status can be 'pending', 'in_progress', 'completed', or 'skipped'.
    """
    try:
        oid = ObjectId(plan_id)
    except Exception:
        return False

    now = datetime.now(timezone.utc).isoformat()
    update_fields = {
        "items.$.status": status,
        "updated_at": now,
    }
    if status == "completed":
        update_fields["items.$.completed_at"] = now

    result = await db[COLLECTION].update_one(
        {"_id": oid, "user_id": user_id, "items.item_id": item_id},
        {"$set": update_fields},
    )
    return result.modified_count > 0


async def list_plans_for_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """List recent learning plans for a user."""
    cursor = db[COLLECTION].find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    plans = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        plans.append(doc)
    return plans
