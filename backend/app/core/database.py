from __future__ import annotations
"""
MongoDB connection lifecycle.

Motor (async pymongo) is used instead of pymongo directly so that all DB
operations are non-blocking in the FastAPI async context.

Connection is opened once at startup and closed at shutdown via the lifespan
context manager in main.py.  All route code obtains the db via get_db().
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None


async def init_db_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Initialize indexes for the 8 core collections as specified in
    Catalyst AI Doc 3 (Section 33: Index Strategy).
    Idempotent and resilient.
    """
    index_specs = [
        # 1. users
        ("users", [("email", ASCENDING)], {"unique": True, "sparse": True}),
        
        # 2. resumes
        ("resumes", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
        ("resumes", [("user_id", ASCENDING), ("status", ASCENDING)], {}),
        
        # 3. career_goals
        ("career_goals", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
        ("career_goals", [("user_id", ASCENDING), ("status", ASCENDING)], {}),
        
        # 4. roadmaps
        ("roadmaps", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
        ("roadmaps", [("goal_id", ASCENDING), ("version", DESCENDING)], {}),
        ("roadmaps", [("user_id", ASCENDING), ("status", ASCENDING)], {}),
        ("roadmaps", [("goal_id", ASCENDING), ("status", ASCENDING)], {}),
        
        # 5. learning_plans
        ("learning_plans", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
        ("learning_plans", [("roadmap_id", ASCENDING)], {}),
        ("learning_plans", [("user_id", ASCENDING), ("status", ASCENDING)], {}),
        
        # 6. progress
        ("progress", [("user_id", ASCENDING), ("roadmap_id", ASCENDING)], {}),
        ("progress", [("user_id", ASCENDING), ("status", ASCENDING)], {}),
        ("progress", [("roadmap_id", ASCENDING), ("roadmap_task_id", ASCENDING)], {}),
        
        # 7. conversations
        ("conversations", [("user_id", ASCENDING), ("updated_at", DESCENDING)], {}),
        ("conversations", [("user_id", ASCENDING), ("assistant_type", ASCENDING), ("updated_at", DESCENDING)], {}),
        
        # 8. notifications
        ("notifications", [("user_id", ASCENDING), ("read", ASCENDING), ("created_at", DESCENDING)], {}),
        ("notifications", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
    ]

    for coll_name, keys, opts in index_specs:
        try:
            await db[coll_name].create_index(keys, **opts)
        except Exception as e:
            logger.warning(f"Could not create index on {coll_name} for keys {keys}: {e}")


async def connect_db() -> None:
    """Open the Motor connection pool and ensure required indexes exist. Call from app lifespan startup."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    # Cheap ping to validate credentials / reachability at startup.
    await _client.admin.command("ping")
    await init_db_indexes(_client[settings.DB_NAME])


async def close_db() -> None:
    """Close the connection pool.  Call from app lifespan shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the application database.  Raises if connect_db() wasn't called."""
    if _client is None:
        raise RuntimeError("Database client not initialised — call connect_db() first.")
    return _client[settings.DB_NAME]

