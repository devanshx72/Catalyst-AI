"""
Company repository — read queries for the 'companies' collection.

Collection: companies (docs/architecture-plan.md Section 2):
Read-only collection used on the home page dashboard to display visiting companies.
"""
from __future__ import annotations

from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "companies"


async def get_companies(
    db: AsyncIOMotorDatabase,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch upcoming/visiting companies sorted by visit_date ascending.
    Mirrors legacy main.py:30.
    """
    cursor = db[COLLECTION].find().sort("visit_date", 1).limit(limit)
    companies = await cursor.to_list(length=limit)
    for c in companies:
        if "_id" in c:
            c["_id"] = str(c["_id"])
    return companies
