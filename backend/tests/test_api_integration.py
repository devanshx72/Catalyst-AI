"""
Integration & security tests verifying authentication gates on all domain endpoints.
Ensures resume, goal, and roadmap endpoints properly enforce session validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

from unittest.mock import MagicMock
from app.core.dependencies import get_db

# Override get_db to return mock database so tests run hermetically without external MongoDB server
app.dependency_overrides[get_db] = lambda: MagicMock()

client = TestClient(app)


def test_roadmap_requires_auth():
    """Verify unauthenticated GET /api/v1/roadmap returns 401 Unauthorized."""
    response = client.get("/api/v1/roadmap")
    assert response.status_code == 401


def test_resume_upload_requires_auth():
    """Verify unauthenticated resume upload returns 401 Unauthorized."""
    files = {"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    response = client.post("/api/v1/resumes/upload", files=files)
    assert response.status_code == 401


def test_goals_active_requires_auth():
    """Verify unauthenticated goals fetch returns 401 Unauthorized."""
    response = client.get("/api/v1/goals/active")
    assert response.status_code == 401


def test_roadmap_generate_requires_auth():
    """Verify unauthenticated roadmap generation returns 401 Unauthorized."""
    response = client.post("/api/v1/roadmap/generate", json={})
    assert response.status_code == 401
