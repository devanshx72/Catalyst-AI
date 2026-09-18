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


async def add_notification(
    db: AsyncIOMotorDatabase,
    notification_data: Dict[str, Any],
) -> str:
    """
    Insert a new notification document.
    Ported from legacy db_utils.py:111-113 (currently uncalled).
    """
    doc = dict(notification_data)
    if "created_at" not in doc:
        doc["created_at"] = datetime.now(tz=timezone.utc)
    if "read" not in doc:
        doc["read"] = False

    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def mark_notification_read(
    db: AsyncIOMotorDatabase,
    notification_id: str,
) -> bool:
    """
    Mark a notification as read.
    Ported from legacy db_utils.py:123-128 (currently uncalled).
    """
    try:
        oid = ObjectId(notification_id)
    except Exception:
        return False

    result = await db[COLLECTION].update_one(
        {"_id": oid},
        {"$set": {"read": True}},
    )
    return result.modified_count > 0
