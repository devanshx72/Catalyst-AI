"""
Unit tests for skill normalization and skill-gap calculation.
"""
import pytest
from app.services.skill_gap_service import (
    analyze_skill_gaps,
    normalize_skill,
    normalize_skill_list,
)


def test_skill_normalization():
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("JS") == "JavaScript"
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("react.js") == "React"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("golang") == "Go"


def test_skill_list_deduplication():
    input_skills = ["js", "JavaScript", "React", "react.js", "docker", "Docker"]
    normalized = normalize_skill_list(input_skills)
    assert normalized == ["JavaScript", "React", "Docker"]


def test_skill_gap_analysis():
    user_skills = ["Python", "Git", "SQL"]
    response = analyze_skill_gaps(
        user_skills=user_skills,
        career_goal_title="Backend Developer",
        current_level="beginner"
    )

    assert "Python" in response.acquired_skills
    assert "Git" in response.acquired_skills
    assert "FastAPI" in response.missing_skills
    assert "Docker" in response.missing_skills
    # Check recommended learning order has prerequisites first
    assert len(response.recommended_learning_order) > 0


def test_custom_role_handling():
    """Verify that a specialized or custom role title is handled gracefully."""
    user_skills = ["Rust", "Linux", "Git"]
    response = analyze_skill_gaps(
        user_skills=user_skills,
        career_goal_title="Embedded Systems & Kernel Engineer",
        current_level="intermediate"
    )
    assert response.goal_title == "Embedded Systems & Kernel Engineer"
    assert len(response.gaps) > 0
    assert len(response.missing_skills) > 0
