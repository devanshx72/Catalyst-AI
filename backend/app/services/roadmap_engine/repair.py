"""
Roadmap Repair Loop — Targeted corrective action when validation or evaluation flags issues.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Tuple
from app.schemas.roadmap import RoadmapValidationReport
from app.services.roadmap_engine.validator import validate_roadmap_deterministic

logger = logging.getLogger(__name__)


def repair_roadmap_draft(
    draft_data: Dict[str, Any],
    validation: RoadmapValidationReport,
    career_goal: str,
    target_duration_months: int,
    weekly_hours: int,
    missing_skills: List[str],
) -> Tuple[Dict[str, Any], RoadmapValidationReport]:
    """
    Perform targeted repairs on the roadmap draft:
    1. Fix missing phases / ensure exactly 4 phases.
    2. Fill any empty skill or description fields.
    3. Reorder prerequisite violations (e.g. Next.js before React, or Kubernetes before Docker).
    4. Re-run deterministic validation.
    """
    repaired = copy.deepcopy(draft_data)
    phases = repaired.get("phases", [])

    if not isinstance(phases, list):
        phases = []

    # Ensure 4 phases exist
    phase_titles = [
        "Phase 1: Foundations & Architecture Setup",
        "Phase 2: Core Engineering & Frameworks",
        "Phase 3: Advanced Systems & Distributed Architecture",
        "Phase 4: Capstone Project & Interview Readiness",
    ]
    per_phase_duration = f"{max(1, target_duration_months // 4)} months"

    while len(phases) < 4:
        idx = len(phases)
        phases.append({
            "name": phase_titles[idx],
            "duration": per_phase_duration,
            "description": f"Master key milestones for {career_goal}.",
            "skills": [missing_skills[idx % len(missing_skills)]] if missing_skills else ["Software Engineering"],
            "resources": {
                "Courses": [f"{career_goal} Specialization"],
                "Books": ["Designing Data-Intensive Applications"],
                "Projects": [f"Practical {career_goal} Implementation"],
            }
        })

    if len(phases) > 4:
        phases = phases[:4]

    # Ensure non-empty fields in every phase
    for idx, p in enumerate(phases):
        if not p.get("name"):
            p["name"] = phase_titles[idx]
        if not p.get("duration"):
            p["duration"] = per_phase_duration
        if not p.get("description"):
            p["description"] = f"Milestone curriculum targeting {career_goal} skills."
        if not p.get("skills"):
            p["skills"] = [missing_skills[idx % len(missing_skills)]] if missing_skills else ["Core Technologies"]

    # Prerequisite DAG repair:
    # If React is in Phase 2 and Next.js in Phase 1, swap them
    p1_skills_lower = [s.lower() for s in phases[0].get("skills", [])]
    p2_skills_lower = [s.lower() for s in phases[1].get("skills", [])]

    if "next.js" in p1_skills_lower and "react" in p2_skills_lower:
        # Move React to Phase 1, Next.js to Phase 2
        phases[0]["skills"] = [s for s in phases[0]["skills"] if s.lower() != "next.js"] + ["React"]
        phases[1]["skills"] = [s for s in phases[1]["skills"] if s.lower() != "react"] + ["Next.js"]

    if "kubernetes" in p1_skills_lower and "docker" in p2_skills_lower:
        phases[0]["skills"] = [s for s in phases[0]["skills"] if s.lower() != "kubernetes"] + ["Docker"]
        phases[1]["skills"] = [s for s in phases[1]["skills"] if s.lower() != "docker"] + ["Kubernetes"]

    repaired["phases"] = phases

    new_validation = validate_roadmap_deterministic(
        roadmap_data=repaired,
        target_duration_months=target_duration_months,
        weekly_hours=weekly_hours,
    )

    return repaired, new_validation
