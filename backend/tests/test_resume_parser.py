"""
Unit tests for resume text parsing and entity extraction.
"""
import pytest
from app.services.resume_service import parse_resume_content


def test_resume_parser_entities():
    sample_text = """
    Jane Doe
    jane@example.com
    
    Education:
    Bachelor of Science in Computer Science - State University (2024)
    
    Skills:
    Python, FastAPI, Docker, PostgreSQL, React, Git, Redis, AWS
    
    Experience:
    Software Engineering Intern at CloudTech
    - Built RESTful microservices using FastAPI and Docker
    
    Projects:
    E-Commerce Microservices
    - Distributed payment service using Go and PostgreSQL
    """

    parsed = parse_resume_content(sample_text)

    # Check extracted skills
    assert "Python" in parsed.skills
    assert "FastAPI" in parsed.skills
    assert "Docker" in parsed.skills
    assert "PostgreSQL" in parsed.skills
    assert "React" in parsed.skills

    # Check education
    assert len(parsed.education) > 0
    assert "Bachelor" in parsed.education[0].degree
