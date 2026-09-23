"""
Pydantic schemas for Resumes and Resume Intelligence.
Covers file metadata, structured entities, parsing statuses, and user review updates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResumeMetadata(BaseModel):
    file_name: str
    file_size: int
    content_type: str
    storage_path: Optional[str] = None


class ParsedExperience(BaseModel):
    company: str = ""
    role: str = ""
    duration: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class ParsedEducation(BaseModel):
    institution: str = ""
    degree: str = ""
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None


class ParsedProject(BaseModel):
    name: str = ""
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class ParsedResumeData(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience: List[ParsedExperience] = Field(default_factory=list)
    education: List[ParsedEducation] = Field(default_factory=list)
    projects: List[ParsedProject] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_metadata: ResumeMetadata
    parsed_data: ParsedResumeData
    parsing_status: str  # "pending" | "processing" | "completed" | "failed"
    error_message: Optional[str] = None
    created_at: str
    is_active: bool = True


class ResumeUpdateRequest(BaseModel):
    """Allows user to inspect and correct extracted resume data."""
    skills: Optional[List[str]] = None
    experience: Optional[List[ParsedExperience]] = None
    education: Optional[List[ParsedEducation]] = None
    projects: Optional[List[ParsedProject]] = None
    certifications: Optional[List[str]] = None
    summary: Optional[str] = None
