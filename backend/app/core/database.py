from __future__ import annotations
"""
MongoDB connection lifecycle.

Motor (async pymongo) is used instead of pymongo directly so that all DB
operations are non-blocking in the FastAPI async context.

Connection is opened once at startup and closed at shutdown via the lifespan
context manager in main.py.  All route code obtains the db via get_db().
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: Optional[AsyncIOMotorClient] = None


async def connect_db() -> None:
    """Open the Motor connection pool.  Call from app lifespan startup."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    # Cheap ping to validate credentials / reachability at startup.
    await _client.admin.command("ping")


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
