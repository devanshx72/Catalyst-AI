"""
Roadmap Evaluator — Structured quality assessment assessing alignment, coverage, and feasibility.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.llm import get_groq_client, get_groq_model
from app.schemas.roadmap import RoadmapEvaluationScore

logger = logging.getLogger(__name__)


def evaluate_roadmap_heuristics(
    roadmap_data: Dict[str, Any],
    career_goal: str,
    missing_skills: List[str],
    duration_months: int,
) -> RoadmapEvaluationScore:
    """Deterministic heuristic evaluation when LLM is offline or in test environments."""
    phases = roadmap_data.get("phases", [])
    all_skills_in_roadmap = set()
    for p in phases:
        for s in p.get("skills", []):
            all_skills_in_roadmap.add(s.lower())

    # Skill coverage calculation
    if missing_skills:
        covered = sum(1 for m in missing_skills if m.lower() in all_skills_in_roadmap)
        coverage_score = round(min(1.0, (covered / len(missing_skills)) + 0.1), 2)
    else:
        coverage_score = 0.95

    # Goal alignment: check if phase names/descriptions reference target domain
    goal_words = set(w.lower() for w in career_goal.split() if len(w) > 3)
    matched_words = 0
    full_text = " ".join([p.get("name", "") + " " + p.get("description", "") for p in phases]).lower()
    for w in goal_words:
        if w in full_text:
            matched_words += 1
    alignment_score = 0.90 if matched_words > 0 else 0.75

    # Feasibility: phases distributed evenly
    feasibility_score = 0.92 if duration_months in [3, 6, 9, 12] else 0.85

    overall = round((alignment_score * 0.35 + coverage_score * 0.45 + feasibility_score * 0.20), 2)
    recommendation = "accept" if overall >= 0.70 else "repair"

    return RoadmapEvaluationScore(
        overall_score=overall,
        goal_alignment=alignment_score,
        skill_coverage=coverage_score,
        timeline_feasibility=feasibility_score,
        recommendation=recommendation,
        notes=f"Evaluation completed for {career_goal} over {duration_months} months."
    )


def evaluate_roadmap_quality(
    roadmap_data: Dict[str, Any],
    career_goal: str,
    missing_skills: List[str],
    duration_months: int,
) -> RoadmapEvaluationScore:
    """Quality evaluator with Groq LLM integration and heuristic fallback."""
    client = get_groq_client()
    if not client:
        return evaluate_roadmap_heuristics(roadmap_data, career_goal, missing_skills, duration_months)

    try:
        skills_str = ", ".join(missing_skills) if missing_skills else "Industry standard skills"
        prompt = f"""Evaluate this 4-phase learning roadmap for an aspiring {career_goal}.
Target duration: {duration_months} months.
Required missing skills to cover: {skills_str}.

Roadmap JSON:
{json.dumps(roadmap_data, indent=2)}

Score on a scale from 0.0 to 1.0 for:
1. goal_alignment
2. skill_coverage
3. timeline_feasibility
4. overall_score
5. recommendation ("accept" if overall_score >= 0.75 else "repair")

Return ONLY valid JSON matching this schema:
{{
  "overall_score": 0.88,
  "goal_alignment": 0.90,
  "skill_coverage": 0.85,
  "timeline_feasibility": 0.89,
  "recommendation": "accept",
  "notes": "Good progression from fundamentals to interview prep."
}}"""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior technical curriculum auditor. Return ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            model=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=500,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        data = json.loads(content)
        return RoadmapEvaluationScore(**data)

    except Exception as e:
        logger.warning("LLM evaluation failed (%s) — falling back to heuristic evaluation.", e)
        return evaluate_roadmap_heuristics(roadmap_data, career_goal, missing_skills, duration_months)
