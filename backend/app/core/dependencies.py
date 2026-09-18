"""
FastAPI dependencies shared across route modules.

get_db        — yields the Motor database for the current request.
get_current_session  — re-exported from security for ergonomic imports.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.core.database import get_database
from app.core.security import get_current_session  # noqa: F401 — re-export


def get_db() -> AsyncIOMotorDatabase:
    """Dependency that returns the live Motor database handle."""
    return get_database()
