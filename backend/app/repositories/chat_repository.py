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

COLLECTION = "user_chat_histories"


def _make_module_key(phase_id: int, module_id: int) -> str:
    return f"{phase_id}_{module_id}"


async def get_module_chat_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    phase_id: int,
    module_id: int,
) -> List[Dict[str, Any]]:
    """Retrieve all messages for a specific module."""
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
    Append new messages (user + assistant) to the module chat history.
    Creates the document/module list if it does not exist (upsert).
    """
    module_key = _make_module_key(phase_id, module_id)
    # Ensure all messages have timestamp
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
    """Clear chat history array for a specific module."""
    module_key = _make_module_key(phase_id, module_id)
    await db[COLLECTION].update_one(
        {"user_id": user_id},
        {"$set": {f"modules.{module_key}": []}},
        upsert=True,
    )
