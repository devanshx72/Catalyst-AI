"""
Roadmap Repository — Direct MongoDB access for the 'roadmaps' and 'progress' collections.
Replaces the anti-pattern of serialized JSON strings in the 'users' collection with
first-class versioned domain documents.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION_ROADMAPS = "roadmaps"
COLLECTION_PROGRESS = "progress"


async def get_next_version(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Calculate the next integer version number for a user's roadmap."""
    latest = await db[COLLECTION_ROADMAPS].find_one(
        {"user_id": user_id},
        sort=[("version", -1)],
        projection={"version": 1}
    )
    if latest and "version" in latest:
        return int(latest["version"]) + 1
    return 1


async def save_roadmap(db: AsyncIOMotorDatabase, roadmap_doc: Dict[str, Any]) -> str:
    """
    Persist a new versioned roadmap document and set it as active.
    Deactivates prior roadmaps for this user.
    """
    now = datetime.now(timezone.utc).isoformat()
    roadmap_doc.setdefault("created_at", now)
    roadmap_doc.setdefault("updated_at", now)
    roadmap_doc.setdefault("is_active", True)
    roadmap_doc.setdefault("status", "active")

    # Deactivate previous active roadmaps for this user
    await db[COLLECTION_ROADMAPS].update_many(
        {"user_id": roadmap_doc["user_id"], "is_active": True},
        {"$set": {"is_active": False, "status": "archived", "updated_at": now}}
    )

    result = await db[COLLECTION_ROADMAPS].insert_one(roadmap_doc)
    return str(result.inserted_id)


async def find_active_by_user_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve the current active roadmap document for a user."""
    doc = await db[COLLECTION_ROADMAPS].find_one(
        {"user_id": user_id, "is_active": True},
        sort=[("version", -1)]
    )
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def find_by_id(
    db: AsyncIOMotorDatabase,
    roadmap_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve a specific roadmap by ID and user_id."""
    try:
        oid = ObjectId(roadmap_id)
    except Exception:
        return None

    doc = await db[COLLECTION_ROADMAPS].find_one({"_id": oid, "user_id": user_id})
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


async def update_phase_plan(
    db: AsyncIOMotorDatabase,
    roadmap_id: str,
    phase_id: int,
    learning_plan: Dict[str, Any],
) -> None:
    """Store or update the generated learning plan for a specific phase."""
    try:
        oid = ObjectId(roadmap_id)
    except Exception:
        return

    now = datetime.now(timezone.utc).isoformat()
    await db[COLLECTION_ROADMAPS].update_one(
        {"_id": oid},
        {
            "$set": {
                f"phases.{phase_id}.learning_plan": learning_plan,
                "updated_at": now,
            }
        }
    )


async def record_task_status(
    db: AsyncIOMotorDatabase,
    user_id: str,
    roadmap_id: str,
    phase_id: int,
    week_index: int,
    day_index: int,
    completed: bool,
) -> None:
    """
    Record task status in both the roadmap document and the dedicated progress collection.
    Conforms to Document 3 Section 24 with item-level traceability.
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        oid = ObjectId(roadmap_id)
    except Exception:
        return

    # 1. Update task in embedded learning plan
    field_path = f"phases.{phase_id}.learning_plan.weekly_schedule.{week_index}.daily_tasks.{day_index}.completed"
    await db[COLLECTION_ROADMAPS].update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {field_path: completed, "updated_at": now}}
    )

    # 2. Upsert in progress tracking collection (Doc 3 Section 24)
    task_id_str = f"t_{week_index}_{day_index}"
    progress_status = "completed" if completed else "pending"
    progress_pct = 100 if completed else 0

    progress_filter = {
        "user_id": user_id,
        "roadmap_id": roadmap_id,
        "roadmap_task_id": task_id_str,
    }
    progress_doc = {
        "user_id": user_id,
        "roadmap_id": roadmap_id,
        "item_type": "task",
        "roadmap_phase_id": str(phase_id),
        "roadmap_module_id": f"m_{week_index}",
        "roadmap_task_id": task_id_str,
        # Legacy index fields for query backward-compatibility
        "phase_id": phase_id,
        "week_index": week_index,
        "day_index": day_index,
        "completed": completed,
        "status": progress_status,
        "progress_percentage": progress_pct,
        "updated_at": now,
    }
    if completed:
        progress_doc["completed_at"] = now
    else:
        progress_doc["completed_at"] = None

    await db[COLLECTION_PROGRESS].update_one(
        progress_filter,
        {"$set": progress_doc},
        upsert=True,
    )



async def compute_roadmap_progress(
    db: AsyncIOMotorDatabase,
    user_id: str,
    roadmap_id: str,
) -> Dict[str, Any]:
    """
    Calculate derived progress across tasks, modules, phases, and total roadmap.
    Returns:
    {
      "total_tasks": int,
      "completed_tasks": int,
      "progress_percent": int,
      "phases_progress": [ { "phase_id": 0, "total": 10, "completed": 5, "percent": 50 } ]
    }
    """
    roadmap = await find_by_id(db, roadmap_id, user_id)
    if not roadmap:
        return {"total_tasks": 0, "completed_tasks": 0, "progress_percent": 0, "phases_progress": []}

    phases = roadmap.get("phases", [])
    total_all = 0
    completed_all = 0
    phases_progress = []

    for idx, phase in enumerate(phases):
        p_total = 0
        p_completed = 0
        lp = phase.get("learning_plan") or {}
        for week in lp.get("weekly_schedule", []):
            for task in week.get("daily_tasks", []):
                p_total += 1
                if task.get("completed"):
                    p_completed += 1

        total_all += p_total
        completed_all += p_completed
        percent = int(round((p_completed / p_total) * 100)) if p_total > 0 else 0
        phases_progress.append({
            "phase_id": idx,
            "phase_name": phase.get("name", f"Phase {idx+1}"),
            "total_tasks": p_total,
            "completed_tasks": p_completed,
            "progress_percent": percent
        })

    overall_percent = int(round((completed_all / total_all) * 100)) if total_all > 0 else 0
    return {
        "total_tasks": total_all,
        "completed_tasks": completed_all,
        "progress_percent": overall_percent,
        "phases_progress": phases_progress
    }
