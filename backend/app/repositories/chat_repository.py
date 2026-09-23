"""
Chat Repository — direct MongoDB access for the 'user_chat_histories' collection.

Schema (docs/architecture-plan.md Section 2):
- user_id: string
- modules: dict[string, list[dict]]
  key format: "<phase_id>_<module_id>" (e.g., "0_1")
  item format: {"role": "user"|"assistant", "content": str, "timestamp": datetime}
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import conversation_repository

COLLECTION = "user_chat_histories"


def _make_module_key(phase_id: int, module_id: int) -> str:
    return f"{phase_id}_{module_id}"


async def get_module_chat_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
) -> List[Dict[str, Any]]:
    """
    Retrieve all messages for a specific module.
    Queries the authoritative 'conversations' collection first, falling back to legacy collection.
    """
    context = {"phase_id": str(phase_id), "module_id": str(module_id)}
    conv_messages = await conversation_repository.get_messages(
        db, user_id=user_id, assistant_type="tutor", context=context
    )
    if conv_messages:
        # Normalize to the legacy item format: role, content, timestamp
        return [
            {
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
                "timestamp": m.get("created_at", m.get("timestamp")),
            }
            for m in conv_messages
        ]

    # Legacy fallback
    doc = await db[COLLECTION].find_one({"user_id": user_id})
    if not doc or "modules" not in doc:
        return []
    module_key = _make_module_key(phase_id, module_id)
    return doc.get("modules", {}).get(module_key, [])


async def append_module_messages(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
    messages: List[Dict[str, Any]],
) -> None:
    """
    Append new messages to both the authoritative 'conversations' collection
    and the legacy 'user_chat_histories' collection.
    """
    context = {"phase_id": str(phase_id), "module_id": str(module_id)}
    
    # 1. Authoritative conversations collection
    for msg in messages:
        await conversation_repository.append_message(
            db=db,
            user_id=user_id,
            assistant_type="tutor",
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            context=context,
        )

    # 2. Dual-write to legacy user_chat_histories for zero-downtime safety
    module_key = _make_module_key(phase_id, module_id)
    for msg in messages:
        if "timestamp" not in msg:
            msg["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

    await db[COLLECTION].update_one(
        {"user_id": user_id},
        {"$push": {f"modules.{module_key}": {"$each": messages}}},
        upsert=True,
    )


async def clear_module_chat_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
) -> None:
    """Clear chat history for a specific module across both collections."""
    context = {"phase_id": str(phase_id), "module_id": str(module_id)}
    await conversation_repository.clear_messages(
        db=db, user_id=user_id, assistant_type="tutor", context=context
    )

    module_key = _make_module_key(phase_id, module_id)
    await db[COLLECTION].update_one(
        {"user_id": user_id},
        {"$set": {f"modules.{module_key}": []}},
        upsert=True,
    )

