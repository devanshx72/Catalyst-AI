"""
User repository — all direct MongoDB reads/writes for the users collection.

Rules (migration-rules.md):
- No business logic here. Pure data access only.
- Schema matches architecture-plan.md Section 2 (users collection).
- Password hashing happens in the service layer, not here.
"""
from typing import Optional

import bcrypt
from motor.motor_asyncio import AsyncIOMotorDatabase


COLLECTION = "users"


# ── Reads ─────────────────────────────────────────────────────────────────────

async def find_by_email_or_user_id(
    db: AsyncIOMotorDatabase,
    identifier: str,
) -> Optional[dict]:
    """
    Find a user by email OR user_id.
    Mirrors legacy db_utils.find_user_by_credentials (db_utils.py:36-37).
    """
    return await db[COLLECTION].find_one(
        {"$or": [{"email": identifier}, {"user_id": identifier}]}
    )


async def find_duplicate(
    db: AsyncIOMotorDatabase,
    email: str,
    username: str,
) -> Optional[dict]:
    """
    Return an existing document if email or user_id is already taken.
    Mirrors legacy db_utils.check_existing_user (db_utils.py:28-29).
    """
    return await db[COLLECTION].find_one(
        {"$or": [{"email": email}, {"user_id": username}]}
    )


async def find_by_user_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[dict]:
    """Fetch a single user by their user_id primary key."""
    return await db[COLLECTION].find_one({"user_id": user_id})


# ── Writes ────────────────────────────────────────────────────────────────────

async def insert_user(
    db: AsyncIOMotorDatabase,
    user_doc: dict,
) -> str:
    """
    Insert a new user document.  Returns the inserted _id as a string.
    Mirrors legacy db_utils.insert_user (db_utils.py:32-33).
    """
    result = await db[COLLECTION].insert_one(user_doc)
    return str(result.inserted_id)


async def update_user_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
    updates: dict,
    unset_fields: Optional[list[str]] = None,
) -> Optional[dict]:
    """
    Update a user document by user_id with $set and optional $unset.
    Returns the updated document.
    """
    update_op: dict = {}
    if updates:
        update_op["$set"] = updates
    if unset_fields:
        update_op["$unset"] = {field: "" for field in unset_fields}

    if not update_op:
        return await find_by_user_id(db, user_id)

    await db[COLLECTION].update_one({"user_id": user_id}, update_op)
    return await find_by_user_id(db, user_id)


async def update_user_roadmap(
    db: AsyncIOMotorDatabase,
    user_id: str,
    roadmap_json: str,
) -> None:
    """
    Update the 'road_map' field on the user document.
    Mirrors legacy roadmap.py update_one $set road_map.
    """
    await db[COLLECTION].update_one(
        {"user_id": user_id},
        {"$set": {"road_map": roadmap_json}},
    )


# ── Password helpers ──────────────────────────────────────────────────────────
# Kept here so the service layer has a single import path.
# Algorithm matches legacy/app/utils/db_utils.py:40-45 (bcrypt).

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt. Returns a UTF-8 string."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
