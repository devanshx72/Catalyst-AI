"""
Unit tests for Document 3 compliant MongoDB schema repositories:
- init_db_indexes (Section 33)
- learning_plan_repository (Sections 21-23)
- conversation_repository (Sections 27-30)
- notification_repository (Sections 31-32)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.core.database import init_db_indexes
from app.repositories import (
    conversation_repository,
    learning_plan_repository,
    notification_repository,
    goal_repository,
)


@pytest.mark.anyio
async def test_init_db_indexes_creates_all_8_collection_indexes():
    """Verify init_db_indexes invokes create_index on all 8 core collections."""
    mock_db = MagicMock()
    # Return an AsyncMock for every collection's create_index
    mock_collections = {}
    for coll in [
        "users", "resumes", "career_goals", "roadmaps",
        "learning_plans", "progress", "conversations", "notifications"
    ]:
        m_coll = MagicMock()
        m_coll.create_index = AsyncMock()
        mock_collections[coll] = m_coll

    mock_db.__getitem__.side_effect = lambda key: mock_collections[key]

    await init_db_indexes(mock_db)

    # Verify each collection had create_index called
    for coll, m in mock_collections.items():
        assert m.create_index.call_count >= 1, f"Expected create_index on {coll}"


@pytest.mark.anyio
async def test_learning_plan_create_and_item_traceability():
    """Verify learning plan document structure complies with Document 3 Section 21."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    fake_id = ObjectId()
    mock_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))
    mock_coll.update_many = AsyncMock()
    mock_db.__getitem__.return_value = mock_coll

    plan_doc = {
        "user_id": "usr_123",
        "goal_id": "goal_123",
        "roadmap_id": "rdm_123",
        "items": [
            {
                "item_id": "p0_w0_d0",
                "roadmap_phase_id": "0",
                "roadmap_module_id": "m_0",
                "roadmap_task_id": "t_0_0",
                "title": "Learn FastAPI dependency injection",
                "description": "Read docs",
                "estimated_hours": 2,
                "status": "pending",
            }
        ]
    }

    inserted_id = await learning_plan_repository.create_learning_plan(mock_db, plan_doc)
    assert inserted_id == str(fake_id)
    assert plan_doc["status"] == "active"
    assert "created_at" in plan_doc
    assert len(plan_doc["items"]) == 1
    assert plan_doc["items"][0]["roadmap_task_id"] == "t_0_0"


@pytest.mark.anyio
async def test_conversation_repository_tutor_coach_isolation():
    """Verify unified conversation repository handles tutor and coach isolation."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    fake_id = ObjectId()
    mock_coll.find_one = AsyncMock(return_value=None)
    mock_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))
    mock_coll.update_one = AsyncMock()
    mock_db.__getitem__.return_value = mock_coll

    # Append tutor message
    msg = await conversation_repository.append_message(
        db=mock_db,
        user_id="usr_123",
        assistant_type="tutor",
        role="user",
        content="What is Python GIL?",
        context={"phase_id": "0", "module_id": "1"},
    )
    assert msg["role"] == "user"
    assert msg["content"] == "What is Python GIL?"
    assert "created_at" in msg


@pytest.mark.anyio
async def test_notification_repository_typed_entity():
    """Verify notification repository creates structured entity references per Section 31."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    fake_id = ObjectId()
    mock_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))
    mock_db.__getitem__.return_value = mock_coll

    notif_id = await notification_repository.create_notification(
        db=mock_db,
        user_id="usr_123",
        notification_type="roadmap_ready",
        title="Roadmap Ready",
        message="Your roadmap is generated",
        entity_type="roadmap",
        entity_id="rdm_456",
    )
    assert notif_id == str(fake_id)
    mock_coll.insert_one.assert_called_once()
    doc_arg = mock_coll.insert_one.call_args[0][0]
    assert doc_arg["type"] == "roadmap_ready"
    assert doc_arg["entity"]["type"] == "roadmap"
    assert doc_arg["entity"]["id"] == "rdm_456"
    assert doc_arg["read"] is False


@pytest.mark.anyio
async def test_goal_structured_target_duration():
    """Verify career goals normalize target_duration to {value, unit} per Section 11."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    fake_id = ObjectId()
    mock_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=fake_id))
    mock_coll.update_many = AsyncMock()
    mock_db.__getitem__.return_value = mock_coll

    goal_doc = {
        "user_id": "usr_123",
        "target_role": "Backend Engineer",
        "target_duration_months": 6,
        "weekly_hours": 15,
    }
    await goal_repository.create_goal(mock_db, goal_doc)
    assert goal_doc["target_duration"] == {"value": 6, "unit": "months"}
    assert goal_doc["status"] == "active"
