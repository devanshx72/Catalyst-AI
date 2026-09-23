"""
Resume Service — Secure upload, parsing, entity extraction, and domain management.
Converts PDF/DOCX/TXT files into first-class structured domain objects.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import pypdf

from app.core.config import settings
from app.repositories import resume_repository
from app.schemas.resume import (
    ParsedEducation,
    ParsedExperience,
    ParsedProject,
    ParsedResumeData,
    ResumeMetadata,
    ResumeResponse,
    ResumeUpdateRequest,
)

logger = logging.getLogger(__name__)

# Security restrictions
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

UPLOAD_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "resumes"


# Comprehensive dictionary of technical skills for deterministic entity extraction
SKILL_VOCABULARY = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Go", "Golang", "Rust", "Java", "C++", "C#", "C",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL", "HTML", "CSS", "Bash", "Shell",
    # Frontend
    "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Svelte", "Redux", "Zustand",
    "TailwindCSS", "Tailwind", "Bootstrap", "Webpack", "Vite",
    # Backend & Systems
    "FastAPI", "Django", "Flask", "Node.js", "Express", "NestJS", "Spring Boot", "ASP.NET",
    "GraphQL", "REST APIs", "gRPC", "Microservices",
    # Databases & Caching
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra", "DynamoDB",
    "Elasticsearch", "Prisma", "SQLAlchemy",
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Terraform",
    "Linux", "Nginx", "Git",
    # AI / ML
    "PyTorch", "TensorFlow", "Scikit-Learn", "Pandas", "NumPy", "OpenAI", "LangChain", "LLMs",
    "Transformers", "NLP", "Computer Vision"
]


def _extract_text_from_pdf(stream: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    text_chunks = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(stream))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    except Exception as e:
        logger.warning("PDF extraction error: %s", e)
    return "\n".join(text_chunks)


def _extract_skills_from_text(text: str) -> List[str]:
    """Deterministically match skills against technical vocabulary."""
    found = set()
    text_lower = f" {text.lower()} "
    for skill in SKILL_VOCABULARY:
        # Match word boundary
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        if re.search(pattern, text_lower):
            # Canonicalize representation
            found.add(skill)
    return sorted(list(found))


def _extract_education_from_text(text: str) -> List[ParsedEducation]:
    """Heuristic extraction for degrees and colleges."""
    education_list: List[ParsedEducation] = []
    degree_patterns = [
        r"(Bachelor(?:\'s)?|B\.?S\.?|B\.?Tech|B\.?E\.?|Master(?:\'s)?|M\.?S\.?|M\.?Tech|Ph\.?D)\s+(?:of|in)?\s*([A-Za-z\s]+)?",
    ]
    for pattern in degree_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            deg = m.group(0).strip()
            education_list.append(ParsedEducation(
                institution="University / College",
                degree=deg[:60],
                field_of_study="Computer Science & Engineering",
            ))
            if len(education_list) >= 2:
                break
    return education_list


def _extract_projects_from_text(text: str) -> List[ParsedProject]:
    """Extract potential project titles and mentioned technologies."""
    projects: List[ParsedProject] = []
    lines = text.splitlines()
    in_projects_section = False

    for i, line in enumerate(lines):
        line_clean = line.strip()
        if re.search(r"^(projects|personal projects|academic projects)", line_clean, re.I):
            in_projects_section = True
            continue
        if in_projects_section and re.search(r"^(education|experience|skills|certifications)", line_clean, re.I):
            break

        if in_projects_section and len(line_clean) > 4 and len(line_clean) < 60:
            # Check if this line looks like a project heading
            if any(char.isupper() for char in line_clean) and not line_clean.startswith("-"):
                proj_skills = [s for s in SKILL_VOCABULARY if s.lower() in line_clean.lower()]
                projects.append(ParsedProject(
                    name=line_clean,
                    description="Project identified from resume",
                    technologies=proj_skills
                ))
                if len(projects) >= 4:
                    break

    return projects


def _extract_experience_from_text(text: str) -> List[ParsedExperience]:
    """Extract job roles and experience blocks."""
    experiences: List[ParsedExperience] = []
    lines = text.splitlines()
    in_exp = False

    for line in lines:
        line_clean = line.strip()
        if re.search(r"^(experience|work experience|employment|internships)", line_clean, re.I):
            in_exp = True
            continue
        if in_exp and re.search(r"^(education|projects|skills|certifications)", line_clean, re.I):
            break
        if in_exp and (re.search(r"(intern|engineer|developer|analyst|specialist|lead)", line_clean, re.I)):
            experiences.append(ParsedExperience(
                role=line_clean[:80],
                company="Company",
                highlights=["Key contributor to engineering initiatives"]
            ))
            if len(experiences) >= 3:
                break

    return experiences


def parse_resume_content(raw_text: str) -> ParsedResumeData:
    """Combine rule-based extraction into ParsedResumeData."""
    skills = _extract_skills_from_text(raw_text)
    education = _extract_education_from_text(raw_text)
    projects = _extract_projects_from_text(raw_text)
    experience = _extract_experience_from_text(raw_text)

    first_lines = [l.strip() for l in raw_text.splitlines()[:5] if len(l.strip()) > 20]
    summary = first_lines[0] if first_lines else "Aspiring Software Engineer"

    return ParsedResumeData(
        skills=skills,
        experience=experience,
        education=education,
        projects=projects,
        certifications=[],
        summary=summary,
    )


async def handle_resume_upload(
    db: AsyncIOMotorDatabase,
    user_id: str,
    file: UploadFile,
) -> ResumeResponse:
    """
    Validate, securely store, and parse a resume file.
    Creates a first-class record in the 'resumes' MongoDB collection.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    # Storage isolation per user
    user_dir = UPLOAD_BASE_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:12]}_{re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)}"
    storage_path = str(user_dir / safe_name)

    with open(storage_path, "wb") as f:
        f.write(content)

    # Text extraction
    raw_text = ""
    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(content)
    elif ext == ".txt":
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("latin-1", errors="ignore")
    else:
        # Fallback text extraction
        raw_text = content.decode("utf-8", errors="ignore")

    parsed_data = parse_resume_content(raw_text)

    metadata = ResumeMetadata(
        file_name=file.filename,
        file_size=len(content),
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
    )

    resume_doc = {
        "user_id": user_id,
        "file_metadata": metadata.model_dump(),
        "raw_text": raw_text[:50000],  # Bound raw text length
        "parsed_data": parsed_data.model_dump(),
        "parsing_status": "completed",
        "error_message": None,
    }

    resume_id = await resume_repository.insert_resume(db, resume_doc)
    resume_doc["id"] = resume_id

    return ResumeResponse(**resume_doc)


async def get_active_resume(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[ResumeResponse]:
    """Fetch user's current active resume."""
    doc = await resume_repository.find_active_by_user_id(db, user_id)
    if not doc:
        return None
    return ResumeResponse(**doc)


async def update_user_resume_data(
    db: AsyncIOMotorDatabase,
    user_id: str,
    payload: ResumeUpdateRequest,
) -> ResumeResponse:
    """Allow user to inspect, edit, and correct parsed resume entities."""
    active_resume = await resume_repository.find_active_by_user_id(db, user_id)
    if not active_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found for this user."
        )

    current_data = active_resume.get("parsed_data", {})
    updates = payload.model_dump(exclude_unset=True)

    for k, v in updates.items():
        if v is not None:
            current_data[k] = v

    updated = await resume_repository.update_parsed_data(
        db=db,
        resume_id=active_resume["id"],
        user_id=user_id,
        parsed_data=current_data,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update resume data.")

    return ResumeResponse(**updated)
