"""
Notification repository — database operations for the 'notifications' collection.

Collection: notifications (docs/architecture-plan.md Section 2):
- user_id: string
- read: bool
- created_at: datetime
- _id: ObjectId

OPEN DESIGN QUESTION:
add_notification() and mark_notification_read() exist in legacy/app/utils/db_utils.py:111-128
but are never called from any route or background task in legacy. They are ported here as
available repository functions without inventing an ad-hoc trigger mechanism.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "notifications"


async def get_user_notifications(
    db: AsyncIOMotorDatabase,
    user_id: str,
    limit: int = 5,
    unread_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch notifications for a user, sorted by created_at descending.
    Mirrors legacy main.py:107-113 and db_utils.py:115-121.
    """
    query: Dict[str, Any] = {"user_id": user_id}
    if unread_only:
        query["read"] = False

    cursor = db[COLLECTION].find(query).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    for n in notifications:
        if "_id" in n:
            n["_id"] = str(n["_id"])
        if isinstance(n.get("created_at"), datetime):
            n["created_at"] = n["created_at"].isoformat()
    return notifications


async def create_notification(
    db: AsyncIOMotorDatabase,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> str:
    """
    Create a typed notification conforming to Document 3 Section 31.
    Types: 'roadmap_ready', 'roadmap_failed', 'learning_task_due', 'learning_milestone'.
    """
    now = datetime.now(timezone.utc).isoformat()
    doc: Dict[str, Any] = {
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "read": False,
        "created_at": now,
    }
    if entity_type and entity_id:
        doc["entity"] = {
            "type": entity_type,
            "id": entity_id,
        }

    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def add_notification(
    db: AsyncIOMotorDatabase,
    notification_data: Dict[str, Any],
) -> str:
    """
    Insert a new notification document. Supports legacy and structured fields.
    """
    doc = dict(notification_data)
    if "created_at" not in doc:
        doc["created_at"] = datetime.now(tz=timezone.utc).isoformat()
    elif isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()

    if "read" not in doc:
        doc["read"] = False

    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def mark_notification_read(
    db: AsyncIOMotorDatabase,
    notification_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """
    Mark a notification as read with optional user ownership validation.
    """
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return False

    query: Dict[str, Any] = {"_id": oid}
    if user_id:
        query["user_id"] = user_id

    result = await db[COLLECTION].update_one(
        query,
        {"$set": {"read": True}},
    )
    return result.modified_count > 0

