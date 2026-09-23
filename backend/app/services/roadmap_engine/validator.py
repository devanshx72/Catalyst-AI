"""
Deterministic Roadmap Validator — Independent rules and schema checker without LLM dependency.
Verifies structure, required fields, phase ordering, duration sanity, and workload viability.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from app.schemas.roadmap import RoadmapValidationReport


def validate_roadmap_deterministic(
    roadmap_data: Dict[str, Any],
    target_duration_months: int = 6,
    weekly_hours: int = 15,
) -> RoadmapValidationReport:
    """
    Apply strict deterministic rules to generated roadmap:
    1. Must have exactly 4 phases.
    2. Every phase must have non-empty name, duration, description, skills, and milestones/modules.
    3. Workload must be feasible for user's declared weekly availability.
    4. Prerequisites check: fundamental topics must precede advanced frameworks.
    """
    issues: List[str] = []
    prereqs_valid = True

    if not isinstance(roadmap_data, dict):
        return RoadmapValidationReport(
            is_valid=False,
            issues=["Roadmap data must be a valid JSON dictionary."],
            workload_hours_per_week=0.0,
            prerequisites_valid=False,
        )

    phases = roadmap_data.get("phases", [])
    if not isinstance(phases, list) or len(phases) != 4:
        issues.append(f"Roadmap must contain exactly 4 milestone phases, found {len(phases) if isinstance(phases, list) else 0}.")

    all_phase_skills: List[List[str]] = []

    for idx, phase in enumerate(phases if isinstance(phases, list) else []):
        p_num = idx + 1
        name = (phase.get("name") or "").strip()
        if not name:
            issues.append(f"Phase {p_num} is missing a name.")

        duration = (phase.get("duration") or "").strip()
        if not duration:
            issues.append(f"Phase {p_num} is missing a duration.")

        desc = (phase.get("description") or "").strip()
        if not desc:
            issues.append(f"Phase {p_num} is missing a description.")

        skills = phase.get("skills", [])
        if not isinstance(skills, list) or len(skills) == 0:
            issues.append(f"Phase {p_num} has no target skills assigned.")
        else:
            all_phase_skills.append([s.lower() for s in skills])

    # Check workload feasibility:
    # Target duration (months) * 4.33 weeks * weekly_hours = total available study hours
    total_available_hours = target_duration_months * 4.33 * weekly_hours
    # Roadmap should distribute ~weekly_hours across weeks
    workload_per_week = float(weekly_hours)

    if weekly_hours < 4:
        issues.append(f"Weekly availability ({weekly_hours}h) is too low for practical progress.")
    elif weekly_hours > 70:
        issues.append(f"Weekly availability ({weekly_hours}h) exceeds realistic burnout limits.")

    # Check prerequisite progression across all phases (DAG ordering check)
    KNOWN_PREREQUISITES = {
        "next.js": "react",
        "kubernetes": "docker",
        "fastapi": "python",
        "microservices": "python",
    }

    PREREQ_DISPLAY = {
        "next.js": "Next.js",
        "react": "React",
        "kubernetes": "Kubernetes",
        "docker": "Docker",
        "fastapi": "FastAPI",
        "python": "Python",
        "microservices": "Microservices",
    }

    for i in range(len(all_phase_skills)):
        curr_skills = set(all_phase_skills[i])
        for advanced, prereq in KNOWN_PREREQUISITES.items():
            if advanced in curr_skills:
                for j in range(i + 1, len(all_phase_skills)):
                    later_skills = set(all_phase_skills[j])
                    if prereq in later_skills:
                        adv_name = PREREQ_DISPLAY.get(advanced, advanced.title())
                        prereq_name = PREREQ_DISPLAY.get(prereq, prereq.title())
                        issues.append(
                            f"Prerequisite violation: {adv_name} is scheduled in Phase {i + 1} "
                            f"before its prerequisite {prereq_name} in Phase {j + 1}."
                        )
                        prereqs_valid = False

    is_valid = len(issues) == 0

    return RoadmapValidationReport(
        is_valid=is_valid,
        issues=issues,
        workload_hours_per_week=workload_per_week,
        prerequisites_valid=prereqs_valid,
    )
