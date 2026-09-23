"""
Conversation Repository — Direct MongoDB access for the unified 'conversations' collection.
Conforms to Catalyst AI Doc 3 (Sections 27-30).
Unifies Tutor and Coach conversations while isolating context by assistant_type and context entity.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "conversations"


async def get_or_create_conversation(
    db: AsyncIOMotorDatabase,
    user_id: str,
    assistant_type: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Find the active conversation for a user by assistant_type (and optional module/phase context).
    Creates one if it does not yet exist.
    """
    query: Dict[str, Any] = {
        "user_id": user_id,
        "assistant_type": assistant_type,
    }
    if context:
        for k, v in context.items():
            if v is not None:
                query[f"context.{k}"] = v

    doc = await db[COLLECTION].find_one(query, sort=[("updated_at", -1)])
    if not doc:
        now = datetime.now(timezone.utc).isoformat()
        new_conv = {
            "user_id": user_id,
            "assistant_type": assistant_type,
            "context": context or {},
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        res = await db[COLLECTION].insert_one(new_conv)
        new_conv["_id"] = res.inserted_id
        new_conv["id"] = str(res.inserted_id)
        return new_conv

    doc["id"] = str(doc["_id"])
    return doc


async def append_message(
    db: AsyncIOMotorDatabase,
    user_id: str,
    assistant_type: str,
    role: str,
    content: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Append a single message {role, content, created_at} to the active conversation.
    Returns the message object appended.
    """
    conv = await get_or_create_conversation(db, user_id, assistant_type, context)
    now = datetime.now(timezone.utc).isoformat()
    msg = {
        "role": role,
        "content": content,
        "created_at": now,
    }

    oid = conv["_id"] if isinstance(conv["_id"], ObjectId) else ObjectId(conv["id"])
    await db[COLLECTION].update_one(
        {"_id": oid},
        {
            "$push": {"messages": msg},
            "$set": {"updated_at": now},
        },
    )
    return msg


async def get_messages(
    db: AsyncIOMotorDatabase,
    user_id: str,
    assistant_type: str,
    context: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve messages for a given assistant and context."""
    conv = await get_or_create_conversation(db, user_id, assistant_type, context)
    messages = conv.get("messages", [])
    if limit and len(messages) > limit:
        return messages[-limit:]
    return messages


async def clear_messages(
    db: AsyncIOMotorDatabase,
    user_id: str,
    assistant_type: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Clear message history for a specific assistant conversation."""
    query: Dict[str, Any] = {
        "user_id": user_id,
        "assistant_type": assistant_type,
    }
    if context:
        for k, v in context.items():
            if v is not None:
                query[f"context.{k}"] = v

    now = datetime.now(timezone.utc).isoformat()
    await db[COLLECTION].update_many(
        query,
        {"$set": {"messages": [], "updated_at": now}},
    )
