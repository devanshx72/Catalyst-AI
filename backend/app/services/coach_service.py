"""
Career Coach (Leo) Service — AI career coaching using Mistral.

PII REDACTION FIX (migration-rules.md & Section 3 LLM Call 1):
Legacy career_coach.py transmitted unredacted real names, exact past employer names,
exact educational institutions, and personal statements directly to Mistral.
This service builds a privacy-preserving prompt:
- Direct PII (real name, contact info, emails, usernames) is completely excluded.
- Past employer names are generalized/redacted to organizational tiers (e.g., 'Enterprise Company').
- Educational institution names are generalized (e.g., 'Accredited Institution').
- Dream company targets are framed generically to protect confidential job hunt preferences.
- Full personal greeting is retained only client-side in the rendered application.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import markdown2
from mistralai import Mistral

from app.core.config import settings
from app.repositories import coach_repository, user_repository
from app.schemas.coach import (
    CoachChatResponse,
    CoachClearHistoryResponse,
    CoachMessage,
    CoachMessagesResponse,
)
from app.services.github_service import fetch_github_projects

logger = logging.getLogger(__name__)

MISTRAL_FALLBACK_TEXT = (
    "Hi there! With your skills, next: build a small project this week. I’ll help you plan it!"
)


def _get_mistral_client() -> Optional[Mistral]:
    if not settings.MISTRAL_API_KEY:
        return None
    try:
        return Mistral(api_key=settings.MISTRAL_API_KEY)
    except Exception as e:
        logger.warning("Failed to initialize Mistral client: %s", e)
        return None


def sanitize_text(text: Optional[str]) -> str:
    """Strip emails, phone numbers, and URLs from freeform text."""
    if not text:
        return ""
    # Strip emails
    cleaned = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[redacted-email]", text)
    # Strip phone numbers
    cleaned = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[redacted-phone]", cleaned)
    # Strip external URLs
    cleaned = re.sub(r"https?://\S+", "[redacted-link]", cleaned)
    return cleaned.strip()


def build_privacy_conscious_prompt(
    rich_user_data: Dict[str, Any],
    user_query: str,
    chat_history: List[Dict[str, Any]],
    github_projects: Optional[List[Dict[str, Any]]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a privacy-conscious coaching prompt for Mistral with all PII scrubbed.
    
    Redactions applied:
    - Real name omitted (framed as 'Candidate').
    - Past employer names scrubbed from experience entries.
    - Specific schools/institutions scrubbed from education entries.
    - Personal statements sanitized for contact information.
    """
    profile = user_profile or {}

    # Role & Summary (No PII)
    headline = sanitize_text(rich_user_data.get("position") or profile.get("career_goal") or "Software Engineering Student")
    about_raw = rich_user_data.get("about") or profile.get("personal_statement") or ""
    about_summary = sanitize_text(about_raw)[:300] if about_raw else "Motivated learner pursuing career growth."

    # Career Aspirations (Generalised)
    career_goal = sanitize_text(profile.get("career_goal") or "Software Developer")
    company_preference = sanitize_text(profile.get("company_preference") or "Technology & Innovation")
    dream_company = sanitize_text(profile.get("dream_company") or "")
    dream_company_framed = f"High-growth technology company (focus: {company_preference})" if dream_company else "Industry-leading organization"

    industries = profile.get("interested_industries") or profile.get("key_interests") or []
    if isinstance(industries, list):
        industries_str = ", ".join([str(i) for i in industries[:5]])
    else:
        industries_str = sanitize_text(str(industries))

    # Skills
    skills = rich_user_data.get("interests") or rich_user_data.get("skills") or profile.get("key_interests") or []
    skills_str = ", ".join([str(s) for s in skills[:15]]) if skills else "Core technical problem solving"

    # Redacted Experiences: Strip exact company/employer names
    experiences = rich_user_data.get("experiences", [])
    experience_list: List[str] = []
    for exp in experiences[:3]:
        title = sanitize_text(exp.get("title", "Technical Role"))
        duration = sanitize_text(exp.get("duration", ""))
        dur_str = f" ({duration})" if duration else ""
        experience_list.append(f"- Role: {title}{dur_str} at an Industry Organization")

    exp_str = "\n".join(experience_list) if experience_list else "Project-based experience and self-directed coursework."

    # Redacted Education: Strip exact universities/colleges
    educations = rich_user_data.get("education", [])
    education_list: List[str] = []
    for edu in educations[:2]:
        degree = sanitize_text(edu.get("degree", "Degree"))
        major = sanitize_text(edu.get("description", "Computer Science / STEM"))
        education_list.append(f"- {degree} in {major} from an Accredited Institution")

    edu_str = "\n".join(education_list) if education_list else "Higher Education / Degree in progress."

    # GitHub Projects (Technical attributes only, no personal usernames)
    if github_projects and isinstance(github_projects, list) and len(github_projects) > 0:
        project_lines: List[str] = []
        for repo in github_projects[:5]:
            title = sanitize_text(repo.get("title", "Project"))
            desc = sanitize_text(repo.get("description", "Technical implementation"))[:80]
            lang = sanitize_text(repo.get("language", "Code"))
            stars = repo.get("stars", 0)
            project_lines.append(f"- {title} ({lang}, {stars}★): {desc}")
        github_str = "\n".join(project_lines)
    else:
        github_str = "Portfolio projects in active development."

    # Last 3 interactions for conversational continuity (Section 3 LLM Call 1)
    recent_history = chat_history[-3:] if chat_history else []
    history_lines: List[str] = []
    for msg in recent_history:
        if isinstance(msg, dict):
            prompt_snip = sanitize_text(msg.get("prompt", ""))
            resp_snip = sanitize_text(msg.get("raw_response", ""))
            history_lines.append(f"User: {prompt_snip}\nLeo: {resp_snip}")

    history_str = "\n".join(history_lines) if history_lines else "First coaching session."

    return f"""You are Leo, a professional and encouraging Career Coach AI.

=== CANDIDATE PROFILE (PRIVACY-PRESERVED) ===
Professional Focus: {headline}
Summary: {about_summary}

=== CAREER ASPIRATIONS ===
Career Goal: {career_goal}
Target Sector: {dream_company_framed}
Industry Focus: {industries_str or 'Technology'}

TOP SKILLS:
{skills_str}

EXPERIENCE (ANONYMIZED):
{exp_str}

EDUCATION (ANONYMIZED):
{edu_str}

PROJECT PORTFOLIO:
{github_str}

=== RECENT CONVERSATION (Memory) ===
{history_str}

=== USER QUESTION ===
"{sanitize_text(user_query)}"

=== INSTRUCTIONS ===
1. Greet the candidate warmly (e.g., "Hi there!").
2. Answer the question using their skill profile, project experience, and career goal ({career_goal}).
3. When discussing projects or technical depth, reference their technical stack and portfolio projects.
4. If asked about career growth, provide 1 actionable and practical next step.
5. Maintain conversational context from recent conversation.
6. Keep response concise (maximum 2-3 short paragraphs).
7. Maintain an inspiring, actionable, and professional tone.
""".strip()


def call_mistral(prompt: str) -> str:
    """Execute Mistral chat completion with fallback on failure."""
    client = _get_mistral_client()
    if not client:
        logger.info("MISTRAL_API_KEY not configured — using fallback coaching response.")
        return MISTRAL_FALLBACK_TEXT

    try:
        response = client.chat.complete(
            model=settings.MISTRAL_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are Leo, a friendly career coach. Be concise, warm, and give 1 actionable tip.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        return MISTRAL_FALLBACK_TEXT
    except Exception as e:
        logger.error("Mistral API error: %s — using fallback.", e)
        return MISTRAL_FALLBACK_TEXT


async def get_coach_messages(
    db: Any,
    user_id: str,
) -> CoachMessagesResponse:
    """Retrieve full conversation history for Leo career coach."""
    doc = await coach_repository.get_conversation(db, user_id)
    if not doc:
        return CoachMessagesResponse(messages=[], conversation_id=None)

    raw_msgs = doc.get("messages", [])
    formatted: List[CoachMessage] = []
    for m in raw_msgs:
        formatted.append(
            CoachMessage(
                prompt=m.get("prompt", ""),
                response=m.get("response", ""),
                raw_response=m.get("raw_response", ""),
                time=str(m.get("time", "")) if m.get("time") else None,
            )
        )

    return CoachMessagesResponse(
        messages=formatted,
        conversation_id=doc.get("conversation_id"),
    )


async def chat_with_coach(
    db: Any,
    user_id: str,
    user_query: str,
) -> CoachChatResponse:
    """
    Handle a user message to Leo:
    1. Loads profile and LinkedIn data (gracefully handling empty fields).
    2. Fetches GitHub projects.
    3. Builds privacy-redacted prompt and calls Mistral.
    4. Converts response to HTML and persists turn to MongoDB.
    """
    user_record = await user_repository.find_by_user_id(db, user_id) or {}

    # 1. Fetch LinkedIn data from db if present (gracefully handling empty fields)
    rich_data = await coach_repository.get_linkedin_profile_data(db, user_id) or {}
    if not rich_data:
        rich_data = dict(user_record)
        rich_data.setdefault("experiences", [])
        rich_data.setdefault("education", [])
        rich_data.setdefault("interests", user_record.get("key_interests", []))

    # 2. Fetch GitHub projects
    github_url = user_record.get("github_profile") or user_record.get("githubProfile")
    github_projects = None
    if github_url:
        result = fetch_github_projects(github_url)
        if isinstance(result, list):
            github_projects = result
        else:
            logger.info("GitHub fetch note: %s", result)

    # 3. Retrieve conversation history for context (last 3 interactions)
    conv = await coach_repository.get_conversation(db, user_id)
    chat_history = conv.get("messages", []) if conv else []

    # 4. Generate redacted prompt & invoke Mistral
    try:
        prompt = build_privacy_conscious_prompt(
            rich_user_data=rich_data,
            user_query=user_query,
            chat_history=chat_history,
            github_projects=github_projects,
            user_profile=user_record,
        )
        raw_resp = call_mistral(prompt)
        html_resp = markdown2.markdown(raw_resp)
    except Exception as e:
        logger.error("Error generating coaching response: %s", e)
        user_name = (user_record.get("name") or "there").split()[0]
        raw_resp = f"I'm sorry {user_name}, I'm having trouble thinking right now. Could you ask that again?"
        html_resp = markdown2.markdown(raw_resp)

    # 5. Persist message turn in MongoDB
    new_msg = {
        "prompt": user_query,
        "response": html_resp,
        "raw_response": raw_resp,
        "time": datetime.now(tz=timezone.utc).isoformat(),
    }
    all_messages = await coach_repository.append_message_to_conversation(
        db, user_id, new_msg
    )

    formatted_msgs = [
        CoachMessage(
            prompt=m.get("prompt", ""),
            response=m.get("response", ""),
            raw_response=m.get("raw_response", ""),
            time=str(m.get("time", "")) if m.get("time") else None,
        )
        for m in all_messages
    ]

    return CoachChatResponse(
        prompt=user_query,
        response=html_resp,
        raw_response=raw_resp,
        messages=formatted_msgs,
    )


async def clear_coach_history(
    db: Any,
    user_id: str,
) -> CoachClearHistoryResponse:
    """Clear conversation history with Leo."""
    await coach_repository.clear_conversation(db, user_id)
    return CoachClearHistoryResponse()
