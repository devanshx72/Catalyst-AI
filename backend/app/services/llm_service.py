"""
LLM Service — Groq client integration for learning plan generation.

Corrected bug fix:
- Fallback learning plan builds 4 completely independent week dicts via list comprehension.
- Does NOT use the legacy buggy `[x] * 4` pattern that cloned identical dictionary references.
- Each week and daily task is uniquely instantiated with its own independent completion state.
"""
from __future__ import annotations

import copy
import json
import logging
from typing import Any, Dict, List, Optional
from groq import Groq

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_groq_client() -> Optional[Groq]:
    if not settings.GROQ_API_KEY:
        return None
    try:
        return Groq(api_key=settings.GROQ_API_KEY)
    except Exception as e:
        logger.warning("Failed to initialize Groq client: %s", e)
        return None


def get_fallback_learning_plan(phase_name: str) -> Dict[str, Any]:
    """
    Generate a deterministic, structured 4-week learning plan fallback.
    
    IMPORTANT: Creates 4 independent week dictionaries (no shared references).
    Each daily task includes `completed: False`.
    """
    fallback_weeks = [
        (
            "Foundations & Setup",
            "Read overview and setup environment",
            "Follow introductory tutorial",
            "Complete environment checklist",
        ),
        (
            "Core Mechanics & Concepts",
            "Study key components and patterns",
            "Implement initial exercises",
            "Complete practice milestone",
        ),
        (
            "Intermediate Application & Projects",
            "Build functional project module",
            "Test, debug, and troubleshoot",
            "Complete functional module",
        ),
        (
            "Review & Capstone Consolidation",
            "Refactor and consolidate project",
            "Review key takeaways and document",
            "Final assessment and code review",
        ),
    ]

    return {
        "weekly_schedule": [
            {
                "week": i + 1,
                "learning_objectives": [f"Master {phase_name} - Week {i+1}: {title}"],
                "daily_tasks": [
                    {
                        "day": 1,
                        "tasks": [task1],
                        "resources": ["YouTube", "Official docs"],
                        "duration_hours": 2,
                        "completed": False,
                    },
                    {
                        "day": 2,
                        "tasks": [task2],
                        "resources": ["Tutorials", "Documentation"],
                        "duration_hours": 2,
                        "completed": False,
                    },
                ],
                "assessment": assess,
            }
            for i, (title, task1, task2, assess) in enumerate(fallback_weeks)
        ]
    }


def generate_learning_plan(phase_name: str, skills: List[str]) -> Dict[str, Any]:
    """
    Generate a detailed 4-week learning plan using Groq LLM.
    Returns valid JSON dictionary with 'weekly_schedule'.
    Falls back to a structured 4-week template if Groq is unavailable or errors.
    """
    client = _get_groq_client()
    if not client:
        logger.info("GROQ_API_KEY not configured — using structured fallback learning plan.")
        return get_fallback_learning_plan(phase_name)

    skills_str = ", ".join(skills) if skills else "core concepts"

    prompt = f"""Generate a detailed 4-week learning plan for the phase "{phase_name}" 
focusing on skills: {skills_str}.

Return ONLY valid JSON in this EXACT format:
{{
    "weekly_schedule": [
        {{
            "week": 1,
            "learning_objectives": ["Objective 1", "Objective 2"],
            "daily_tasks": [
                {{
                    "day": 1,
                    "tasks": ["Task 1", "Task 2"],
                    "resources": ["Resource 1"],
                    "duration_hours": 2
                }}
            ],
            "assessment": "Short quiz or project"
        }}
    ]
}}

Include exactly 4 weeks. Return ONLY JSON. No markdown. No explanations."""

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON expert. Return ONLY valid JSON. No code blocks.",
                },
                {"role": "user", "content": prompt},
            ],
            model=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=1500,
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown code block delimiters if present
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        plan = json.loads(content)

        if "weekly_schedule" not in plan or not isinstance(plan["weekly_schedule"], list):
            raise ValueError("Missing weekly_schedule list in LLM response")

        weeks = plan["weekly_schedule"][:4]
        if len(weeks) == 0:
            raise ValueError("Empty weekly_schedule in LLM response")

        # Sanitize and ensure each week has required structure
        for i, week in enumerate(weeks):
            week.setdefault("week", i + 1)
            week.setdefault(
                "learning_objectives",
                [f"Learn core concepts of week {i+1} for {phase_name}"],
            )
            week.setdefault("assessment", "Complete weekly exercises")

            daily = week.get("daily_tasks", [])
            if not isinstance(daily, list) or len(daily) == 0:
                daily = [
                    {
                        "day": 1,
                        "tasks": [f"Study {phase_name} fundamentals"],
                        "resources": ["Online tutorial"],
                        "duration_hours": 2,
                    }
                ]
            for task in daily:
                task.setdefault("completed", False)
            week["daily_tasks"] = daily[:5]

        # Pad to 4 weeks if fewer were generated
        while len(weeks) < 4:
            last = weeks[-1]
            weeks.append(
                {
                    "week": len(weeks) + 1,
                    "learning_objectives": list(last.get("learning_objectives", [])),
                    "daily_tasks": copy.deepcopy(last.get("daily_tasks", [])),
                    "assessment": last.get("assessment", "Complete weekly tasks"),
                }
            )

        return {"weekly_schedule": weeks}

    except Exception as e:
        logger.warning("Groq learning plan generation failed (%s) — falling back to template.", e)
        return get_fallback_learning_plan(phase_name)


def get_groq_tutor_stream(
    message: str,
    topic: str,
    objectives: List[str],
    skills: List[str],
    resources: Dict[str, Any],
    conversation_context: Optional[List[Dict[str, str]]] = None,
):
    """
    Streaming AI Tutor response via Groq.
    Yields individual token chunks incrementally.
    Mirrors legacy get_groq_response_stream (legacy/app/utils/llm_utils.py:501-535).
    """
    client = _get_groq_client()
    if not client:
        logger.info("GROQ_API_KEY not configured — streaming simulated tutor response.")
        fallback_msg = (
            f"Hello! I am your AI Tutor for {topic}. "
            f"Regarding your question about '{message}': "
            f"Let's focus on mastering {', '.join(skills) if skills else 'the core objectives'}. "
            f"Break this down into small practice steps and test each concept."
        )
        for word in fallback_msg.split(" "):
            yield word + " "
        return

    # Build resource context string safely
    res_lines = []
    for k, v in (resources or {}).items():
        if isinstance(v, list):
            res_lines.append(f"{k}: {', '.join(str(item) for item in v)}")
        else:
            res_lines.append(f"{k}: {v}")
    resources_str = "\n".join(res_lines)

    system_prompt = f"""You are an AI tutor for {topic}.
Objectives: {', '.join(objectives)}
Skills: {', '.join(skills)}
Resources:
{resources_str}
Be concise and educational."""

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_context:
        messages.extend(conversation_context)
    messages.append({"role": "user", "content": message})

    try:
        stream = client.chat.completions.create(
            messages=messages,
            model=settings.GROQ_MODEL,
            temperature=0.5,
            max_tokens=1000,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("Groq stream error: %s", e)
        yield f"Error in stream: {e}"
