"""
GitHub service — unauthenticated GitHub REST API repository fetching for user portfolios.

Ported from legacy/app/utils/llm_utils.py:109-172 (Section 4, API 3).
Preserves error handling contract: returns list of dicts on success, or string error on failure.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
import requests

logger = logging.getLogger(__name__)


def extract_github_username(github_input: Optional[str]) -> Optional[str]:
    """
    Extract GitHub username from a profile URL or return as-is if already a username.
    
    Handles:
    - https://github.com/username
    - http://github.com/username
    - github.com/username
    - username
    """
    if not github_input:
        return None

    cleaned = github_input.strip().rstrip("/")
    if "github.com/" in cleaned:
        parts = cleaned.split("github.com/")
        if len(parts) > 1:
            username = parts[1].split("/")[0].strip()
            return username if username else None
    return cleaned if cleaned else None


def fetch_github_projects(github_input: Optional[str]) -> Union[List[Dict[str, Any]], str]:
    """
    Fetch public repositories for a given GitHub username or profile URL.

    Returns:
        List[Dict[str, Any]] containing 'title', 'description', 'language', 'stars'
        OR string error message if fetch fails.
    """
    username = extract_github_username(github_input)
    if not username:
        return "No valid GitHub username provided"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "CatalystAI-CareerCoach"},
            timeout=8,
        )
        if response.status_code == 404:
            return f"GitHub user '{username}' not found"
        response.raise_for_status()
        repos = response.json()

        if not isinstance(repos, list):
            return "Unexpected response format from GitHub"

        return [
            {
                "title": r.get("name", "Project"),
                "description": r.get("description") or "No description",
                "language": r.get("language") or "Not specified",
                "stars": r.get("stargazers_count", 0),
            }
            for r in repos
            if isinstance(r, dict)
        ]
    except Exception as e:
        logger.warning("GitHub fetch failed for '%s': %s", username, e)
        return f"GitHub fetch failed: {e}"
