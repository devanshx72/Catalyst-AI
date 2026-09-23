"""
Roadmap Planner — Orchestrated workflow coordinating generation, validation, evaluation, and repair.
Produces high-quality, verified 4-phase milestone roadmaps tailored to user career goals and availability.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from groq import Groq

from app.core.config import settings
from app.schemas.roadmap import RoadmapEvaluationScore, RoadmapValidationReport
from app.services.roadmap_engine.evaluator import evaluate_roadmap_quality
from app.services.roadmap_engine.repair import repair_roadmap_draft
from app.services.roadmap_engine.validator import validate_roadmap_deterministic

logger = logging.getLogger(__name__)


def build_deterministic_roadmap_draft(
    career_goal: str,
    target_duration_months: int,
    weekly_hours: int,
    current_level: str,
    acquired_skills: List[str],
    missing_skills: List[str],
    learning_order: List[str],
) -> Dict[str, Any]:
    """Build a structured 4-phase milestone roadmap based on topological skill gap ordering."""
    months_per_phase = max(1, round(target_duration_months / 4))
    duration_str = f"{months_per_phase} Month{'s' if months_per_phase > 1 else ''}"

    # Partition skills across 4 phases based on recommended learning order
    order = learning_order if learning_order else missing_skills
    chunk_size = max(1, len(order) // 4) if order else 1

    p1_skills = order[:chunk_size] if order else ["Computer Science Foundations", "Git"]
    p2_skills = order[chunk_size:chunk_size*2] if len(order) > chunk_size else ["Core Frameworks", "APIs"]
    p3_skills = order[chunk_size*2:chunk_size*3] if len(order) > chunk_size*2 else ["System Design", "Cloud Infrastructure"]
    p4_skills = order[chunk_size*3:] if len(order) > chunk_size*3 else ["Full Stack Capstone", "Interview Prep"]

    # Fallbacks if any phase slice is empty
    if not p1_skills: p1_skills = ["Development Environment Setup", "Core Syntax"]
    if not p2_skills: p2_skills = ["Application Architecture", "Database Integrations"]
    if not p3_skills: p3_skills = ["Performance Optimization", "Testing & CI/CD"]
    if not p4_skills: p4_skills = ["Production Deployment", "Technical Interview Prep"]

    phases = [
        {
            "name": "Phase 1: Foundations & Architecture Setup",
            "duration": duration_str,
            "description": f"Master core foundations, toolchains, and essential building blocks for {career_goal}.",
            "skills": p1_skills,
            "resources": {
                "Courses": [f"Modern {p1_skills[0]} Masterclass", "Developer Environment Foundations"],
                "Books": ["The Pragmatic Programmer"],
                "Projects": [f"Command-line utility and project starter using {p1_skills[0]}"],
            },
        },
        {
            "name": "Phase 2: Core Engineering & Applied Frameworks",
            "duration": duration_str,
            "description": f"Develop production-grade competencies in primary frameworks and persistence layers.",
            "skills": p2_skills,
            "resources": {
                "Courses": [f"Building Scalable Applications with {p2_skills[0]}"],
                "Books": ["Clean Code: A Handbook of Agile Software Craftsmanship"],
                "Projects": [f"Full feature service integrating {', '.join(p2_skills[:2])}"],
            },
        },
        {
            "name": "Phase 3: Advanced Systems & Distributed Architecture",
            "duration": duration_str,
            "description": f"Scale system capabilities with robust data pipelines, caching, and cloud deployments.",
            "skills": p3_skills,
            "resources": {
                "Courses": ["System Design & Distributed Systems Engineering"],
                "Books": ["Designing Data-Intensive Applications by Martin Kleppmann"],
                "Projects": [f"High-throughput resilient backend with automated CI/CD"],
            },
        },
        {
            "name": "Phase 4: Capstone Project & Industry Interview Readiness",
            "duration": duration_str,
            "description": f"Consolidate engineering skills into a flagship portfolio capstone and ace technical interviews.",
            "skills": p4_skills,
            "resources": {
                "Courses": [f"Cracking the {career_goal} Technical & Behavioral Interview"],
                "Books": ["Cracking the Coding Interview by Gayle Laakmann McDowell"],
                "Projects": [f"Flagship End-to-End {career_goal} Production Capstone"],
            },
        },
    ]

    return {
        "title": f"Career Roadmap for {career_goal}",
        "target_duration_months": target_duration_months,
        "weekly_hours": weekly_hours,
        "current_level": current_level,
        "phases": phases,
    }


def plan_and_orchestrate_roadmap(
    career_goal: str,
    target_duration_months: int,
    weekly_hours: int,
    current_level: str,
    acquired_skills: List[str],
    missing_skills: List[str],
    learning_order: List[str],
) -> Tuple[Dict[str, Any], RoadmapValidationReport, RoadmapEvaluationScore]:
    """
    Complete Roadmap Orchestration Pipeline:
    1. Generate Draft (Template / LLM)
    2. Deterministic Validation
    3. AI Quality Evaluation
    4. Controlled Repair Loop (if needed, max 2 passes)
    """
    # Step 1: Generate initial draft
    draft = build_deterministic_roadmap_draft(
        career_goal=career_goal,
        target_duration_months=target_duration_months,
        weekly_hours=weekly_hours,
        current_level=current_level,
        acquired_skills=acquired_skills,
        missing_skills=missing_skills,
        learning_order=learning_order,
    )

    # Step 2: Validate
    validation = validate_roadmap_deterministic(
        roadmap_data=draft,
        target_duration_months=target_duration_months,
        weekly_hours=weekly_hours,
    )

    # Step 3: Evaluate
    evaluation = evaluate_roadmap_quality(
        roadmap_data=draft,
        career_goal=career_goal,
        missing_skills=missing_skills,
        duration_months=target_duration_months,
    )

    # Step 4: Repair loop if required
    retries = 0
    max_retries = 2
    while (not validation.is_valid or evaluation.recommendation == "repair") and retries < max_retries:
        logger.info("Roadmap issues detected (pass %d). Triggering targeted repair.", retries + 1)
        draft, validation = repair_roadmap_draft(
            draft_data=draft,
            validation=validation,
            career_goal=career_goal,
            target_duration_months=target_duration_months,
            weekly_hours=weekly_hours,
            missing_skills=missing_skills,
        )
        evaluation = evaluate_roadmap_quality(
            roadmap_data=draft,
            career_goal=career_goal,
            missing_skills=missing_skills,
            duration_months=target_duration_months,
        )
        retries += 1

    return draft, validation, evaluation
