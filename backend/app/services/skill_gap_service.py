"""
Skill-Gap Analysis Service — Canonical skill normalization and role matrix matching.
Identifies missing, weak, and acquired skills and computes prerequisite learning orders.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.llm import get_groq_client, get_groq_model
from app.schemas.goals import SkillGapItem, SkillGapResponse

logger = logging.getLogger(__name__)

# Canonical synonym dictionary
CANONICAL_SYNONYMS: Dict[str, str] = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ecmascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "golang": "Go",
    "go": "Go",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express",
    "expressjs": "Express",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "tailwind": "TailwindCSS",
    "tailwindcss": "TailwindCSS",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "graphql": "GraphQL",
    "git": "Git",
}

# Role requirement standards & prerequisites
ROLE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "full stack": {
        "critical": ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "REST APIs", "Git"],
        "recommended": ["Next.js", "Docker", "TailwindCSS", "Redis", "CI/CD"],
        "optional": ["GraphQL", "AWS", "Kubernetes"],
        "prerequisites": {
            "TypeScript": ["JavaScript"],
            "React": ["JavaScript", "HTML", "CSS"],
            "Next.js": ["React"],
            "PostgreSQL": ["SQL"],
            "Redis": ["PostgreSQL"],
            "Docker": ["Linux"],
            "Kubernetes": ["Docker"],
        }
    },
    "frontend": {
        "critical": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Git"],
        "recommended": ["Next.js", "TailwindCSS", "REST APIs", "Redux"],
        "optional": ["GraphQL", "Webpack", "Vue.js"],
        "prerequisites": {
            "TypeScript": ["JavaScript"],
            "React": ["JavaScript"],
            "Next.js": ["React"],
        }
    },
    "backend": {
        "critical": ["Python", "FastAPI", "PostgreSQL", "REST APIs", "Docker", "Git"],
        "recommended": ["Redis", "Microservices", "CI/CD", "Linux", "SQLAlchemy"],
        "optional": ["Kubernetes", "AWS", "GraphQL", "gRPC"],
        "prerequisites": {
            "FastAPI": ["Python"],
            "Redis": ["PostgreSQL"],
            "Kubernetes": ["Docker"],
        }
    },
    "ai engineer": {
        "critical": ["Python", "PyTorch", "NumPy", "Pandas", "LLMs", "Git"],
        "recommended": ["FastAPI", "Docker", "LangChain", "Transformers", "Scikit-Learn"],
        "optional": ["Kubernetes", "AWS", "MLOps"],
        "prerequisites": {
            "PyTorch": ["Python", "NumPy"],
            "LangChain": ["Python", "LLMs"],
            "Transformers": ["PyTorch"],
        }
    },
    "devops": {
        "critical": ["Linux", "Docker", "Kubernetes", "CI/CD", "Git", "Bash"],
        "recommended": ["AWS", "Terraform", "Python", "Nginx"],
        "optional": ["Go", "Ansible", "Prometheus"],
        "prerequisites": {
            "Kubernetes": ["Docker"],
            "CI/CD": ["Git"],
        }
    }
}


def normalize_skill(skill: str) -> str:
    """Normalize any skill spelling or variant into its canonical name."""
    clean = skill.strip().lower()
    return CANONICAL_SYNONYMS.get(clean, skill.strip())


def normalize_skill_list(skills: List[str]) -> List[str]:
    """Return unique list of canonical skills."""
    seen = set()
    result = []
    for s in skills:
        norm = normalize_skill(s)
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            result.append(norm)
    return result


def extract_dynamic_role_spec_with_llm(role_title: str) -> Optional[Dict[str, Any]]:
    """
    Query Groq LLM to dynamically generate required skills, priorities, and prerequisites
    for any custom or specialized career goal (e.g. 'iOS Engineer', 'Rust Systems', 'Blockchain').
    """
    client = get_groq_client()
    if not client:
        return None

    prompt = f"""You are a technical career curriculum architect.
Given the target tech career role: "{role_title}", identify the standard industry skills requirements.

Return ONLY a JSON object with this exact structure:
{{
  "critical": ["5 to 7 essential core technologies/languages/frameworks"],
  "recommended": ["4 to 6 high-value modern tools/libraries"],
  "optional": ["3 to 4 useful complementary skills"],
  "prerequisites": {{
    "AdvancedSkill": ["PrerequisiteSkill1"]
  }}
}}

Return ONLY valid JSON. No markdown fences. No explanations."""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a technical role analyzer. Return ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            model=get_groq_model(),
            temperature=0.1,
            max_tokens=600,
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
        if "critical" in data and isinstance(data["critical"], list) and len(data["critical"]) > 0:
            return data
    except Exception as e:
        logger.warning("Dynamic LLM role requirements extraction failed (%s) — using fallback matrix.", e)

    return None


def find_matching_role_spec(role_title: str) -> Dict[str, Any]:
    """
    Match role title to curated standards or dynamically query LLM for custom roles.
    Ensures any custom career goal entered by the user receives tailored skill requirements.
    """
    title_lower = role_title.lower()
    for key, spec in ROLE_REQUIREMENTS.items():
        if key in title_lower:
            return spec

    # Attempt dynamic LLM extraction for specialized/custom roles
    dynamic_spec = extract_dynamic_role_spec_with_llm(role_title)
    if dynamic_spec:
        return dynamic_spec

    # Default fallback to full stack if unknown and LLM offline
    return ROLE_REQUIREMENTS["full stack"]


def analyze_skill_gaps(
    user_skills: List[str],
    career_goal_title: str,
    current_level: str = "beginner",
) -> SkillGapResponse:
    """
    Perform deterministic skill-gap calculation:
    Existing Skills vs. Target Role Requirements = Skill Gap.
    """
    normalized_user_skills = normalize_skill_list(user_skills)
    user_skill_set = set(s.lower() for s in normalized_user_skills)

    role_spec = find_matching_role_spec(career_goal_title)
    critical_skills = [normalize_skill(s) for s in role_spec.get("critical", [])]
    recommended_skills = [normalize_skill(s) for s in role_spec.get("recommended", [])]
    optional_skills = [normalize_skill(s) for s in role_spec.get("optional", [])]
    prereqs = role_spec.get("prerequisites", {})

    gaps: List[SkillGapItem] = []
    missing_skills: List[str] = []
    acquired_skills: List[str] = []

    # Check critical skills
    for skill in critical_skills:
        req_prereqs = [normalize_skill(p) for p in prereqs.get(skill, [])]
        if skill.lower() in user_skill_set:
            acquired_skills.append(skill)
            gaps.append(SkillGapItem(
                skill=skill,
                category="technical",
                status="acquired",
                importance="critical",
                prerequisites=req_prereqs,
                rationale=f"Core prerequisite mastered for {career_goal_title}"
            ))
        else:
            missing_skills.append(skill)
            gaps.append(SkillGapItem(
                skill=skill,
                category="technical",
                status="missing",
                importance="critical",
                prerequisites=req_prereqs,
                rationale=f"Essential foundation for {career_goal_title}"
            ))

    # Check recommended skills
    for skill in recommended_skills:
        req_prereqs = [normalize_skill(p) for p in prereqs.get(skill, [])]
        if skill.lower() in user_skill_set:
            acquired_skills.append(skill)
            gaps.append(SkillGapItem(
                skill=skill,
                category="technical",
                status="acquired",
                importance="recommended",
                prerequisites=req_prereqs,
                rationale=f"Valuable asset already acquired for {career_goal_title}"
            ))
        else:
            missing_skills.append(skill)
            gaps.append(SkillGapItem(
                skill=skill,
                category="technical",
                status="missing",
                importance="recommended",
                prerequisites=req_prereqs,
                rationale=f"Strongly boosts job readiness for {career_goal_title}"
            ))

    # Compute topological-like learning order
    # Prerequisites first, then critical skills, then recommended
    learning_order: List[str] = []
    for s in missing_skills:
        # Add unmet prereqs first
        for p in prereqs.get(s, []):
            p_norm = normalize_skill(p)
            if p_norm.lower() not in user_skill_set and p_norm not in learning_order:
                learning_order.append(p_norm)
        if s not in learning_order:
            learning_order.append(s)

    return SkillGapResponse(
        goal_title=career_goal_title,
        current_level=current_level,
        acquired_skills=acquired_skills,
        gaps=gaps,
        missing_skills=missing_skills,
        recommended_learning_order=learning_order,
    )
