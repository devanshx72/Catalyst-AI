"""
Unit tests for deterministic roadmap validator and repair engine.
"""
import pytest
from app.services.roadmap_engine.validator import validate_roadmap_deterministic
from app.services.roadmap_engine.repair import repair_roadmap_draft


def test_valid_roadmap():
    sample_roadmap = {
        "phases": [
            {
                "name": "Phase 1: Foundations",
                "duration": "1.5 Months",
                "description": "Basics and setup",
                "skills": ["JavaScript", "HTML", "CSS"],
            },
            {
                "name": "Phase 2: Frameworks",
                "duration": "1.5 Months",
                "description": "Frontend frameworks",
                "skills": ["React"],
            },
            {
                "name": "Phase 3: Advanced Systems",
                "duration": "1.5 Months",
                "description": "Backend integration",
                "skills": ["Node.js", "PostgreSQL"],
            },
            {
                "name": "Phase 4: Capstone",
                "duration": "1.5 Months",
                "description": "Full stack project",
                "skills": ["Next.js", "Docker"],
            },
        ]
    }
    report = validate_roadmap_deterministic(sample_roadmap, target_duration_months=6, weekly_hours=15)
    assert report.is_valid is True
    assert len(report.issues) == 0
    assert report.prerequisites_valid is True
    assert report.workload_hours_per_week == 15.0


def test_prerequisite_violation():
    """Detects when an advanced framework is scheduled before its core prerequisite."""
    invalid_roadmap = {
        "phases": [
            {
                "name": "Phase 1: Advanced Frameworks",
                "duration": "1.5 Months",
                "description": "Frameworks first",
                "skills": ["Next.js"],  # Next.js before React
            },
            {
                "name": "Phase 2: Foundations",
                "duration": "1.5 Months",
                "description": "React basics",
                "skills": ["React"],
            },
            {
                "name": "Phase 3: Cloud",
                "duration": "1.5 Months",
                "description": "Cloud deployment",
                "skills": ["Kubernetes"],  # Kubernetes before Docker
            },
            {
                "name": "Phase 4: Containers",
                "duration": "1.5 Months",
                "description": "Container basics",
                "skills": ["Docker"],
            },
        ]
    }
    report = validate_roadmap_deterministic(invalid_roadmap, target_duration_months=6, weekly_hours=15)
    assert report.is_valid is False
    assert report.prerequisites_valid is False
    assert any("Next.js" in issue for issue in report.issues)
    assert any("Kubernetes" in issue for issue in report.issues)


def test_repair_loop():
    """Verifies that the repair loop fixes prerequisite violations and missing phases."""
    broken_roadmap = {
        "phases": [
            {
                "name": "Phase 1: Advanced Next.js",
                "duration": "2 Months",
                "description": "Next.js",
                "skills": ["Next.js"],
            },
            {
                "name": "Phase 2: React Basics",
                "duration": "2 Months",
                "description": "React",
                "skills": ["React"],
            }
            # Only 2 phases
        ]
    }
    initial_report = validate_roadmap_deterministic(broken_roadmap, target_duration_months=6, weekly_hours=15)
    assert initial_report.is_valid is False

    repaired_draft, repaired_report = repair_roadmap_draft(
        draft_data=broken_roadmap,
        validation=initial_report,
        career_goal="Full Stack Developer",
        target_duration_months=6,
        weekly_hours=15,
        missing_skills=["JavaScript", "React", "Next.js", "Docker"],
    )

    assert len(repaired_draft["phases"]) == 4
    assert repaired_report.is_valid is True
    assert repaired_report.prerequisites_valid is True
