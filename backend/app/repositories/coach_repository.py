"""
Coach Repository — direct MongoDB access for the 'career_coach' and 'linkedin_data' collections.

Collection: career_coach (docs/architecture-plan.md Section 2):
- user_id: string
- conversation_id: string ("conv_<unix_ts>")
- messages: list[dict]
  - prompt: str
  - response: str (HTML)
  - raw_response: str (Markdown)
  - time: datetime / ISO string
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION_COACH = "career_coach"
COLLECTION_LINKEDIN = "linkedin_data"


async def get_conversation(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve the full conversation document for a user."""
    return await db[COLLECTION_COACH].find_one({"user_id": user_id})


async def append_message_to_conversation(
    db: AsyncIOMotorDatabase,
    user_id: str,
    message: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Append a new message to the user's conversation document.
    Creates a new conversation document if one does not exist.
    Returns the complete list of messages.
    """
    existing = await db[COLLECTION_COACH].find_one({"user_id": user_id})

    if not existing:
        conv_id = f"conv_{int(time.time())}"
        doc = {
            "user_id": user_id,
            "conversation_id": conv_id,
            "messages": [message],
        }
        await db[COLLECTION_COACH].insert_one(doc)
        return [message]

    await db[COLLECTION_COACH].update_one(
        {"user_id": user_id},
        {"$push": {"messages": message}},
    )
    updated = await db[COLLECTION_COACH].find_one({"user_id": user_id})
    return updated.get("messages", []) if updated else []


async def clear_conversation(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> None:
    """Delete the user's coaching conversation document (clean slate)."""
    await db[COLLECTION_COACH].delete_one({"user_id": user_id})


async def get_linkedin_profile_data(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve rich scraped LinkedIn data if available."""
    return await db[COLLECTION_LINKEDIN].find_one({"user_id": user_id})
