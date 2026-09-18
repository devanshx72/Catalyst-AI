"""
Resource service — search integration for YouTube, Google Scholar (RapidAPI), and Google Custom Search.

Ported from legacy/app/utils/resource_utils.py.

FLAG / CAUTION:
- GOOGLE_CUSTOM_SEARCH_CX uses a hardcoded placeholder engine ID ('017576662512468239146:omuauf_lfve')
  inherited from legacy. A valid Google CSE ID must be configured in production via GOOGLE_CUSTOM_SEARCH_CX.
- GOOGLE_SCHOLOR_API_KEY intentionally preserves the legacy typo in the environment variable name.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)


def fetch_youtube_videos(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch educational videos from YouTube Data API v3."""
    if not settings.YOUTUBE_API_KEY:
        logger.info("YOUTUBE_API_KEY not set — skipping YouTube search.")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        search_response = (
            youtube.search()
            .list(
                q=query,
                part="snippet",
                maxResults=max_results,
                type="video",
                relevanceLanguage="en",
                safeSearch="moderate",
            )
            .execute()
        )

        videos = []
        for item in search_response.get("items", []):
            video_id = item["id"].get("videoId")
            if video_id:
                videos.append(
                    {
                        "id": video_id,
                        "title": item["snippet"].get("title", ""),
                        "description": item["snippet"].get("description", ""),
                        "thumbnail": item["snippet"]
                        .get("thumbnails", {})
                        .get("medium", {})
                        .get("url", ""),
                        "publishedAt": item["snippet"].get("publishedAt", ""),
                        "channelTitle": item["snippet"].get("channelTitle", ""),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                )
        return videos
    except HttpError as e:
        logger.warning("YouTube API HttpError: %s", e)
        return []
    except Exception as e:
        logger.warning("Error fetching YouTube videos: %s", e)
        return []


def fetch_google_scholar_papers(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch academic papers from Google Scholar via RapidAPI."""
    if not settings.GOOGLE_SCHOLOR_API_KEY:
        logger.info("GOOGLE_SCHOLOR_API_KEY not set — skipping Scholar search.")
        return []

    url = "https://google-scholar1.p.rapidapi.com/search_pubs"
    params = {
        "query": query,
        "max_results": str(max_results),
        "patents": "true",
        "citations": "true",
        "sort_by": "relevance",
        "include_last_year": "abstracts",
        "start_index": "0",
    }
    headers = {
        "x-rapidapi-key": settings.GOOGLE_SCHOLOR_API_KEY,
        "x-rapidapi-host": "google-scholar1.p.rapidapi.com",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning("Google Scholar API error: %s - %s", response.status_code, response.text)
            return []

        data = response.json()
        papers = []
        if "result" in data and isinstance(data["result"], list):
            for item in data["result"][:max_results]:
                bib = item.get("bib", {})
                authors = bib.get("author", []) if isinstance(bib.get("author"), list) else []
                papers.append(
                    {
                        "title": bib.get("title", "Untitled"),
                        "authors": authors,
                        "abstract": bib.get("abstract", "No abstract available"),
                        "year": bib.get("pub_year", "Unknown year"),
                        "citations": item.get("num_citations", 0),
                        "url": item.get("pub_url", ""),
                    }
                )
        return papers
    except Exception as e:
        logger.warning("Error fetching Google Scholar papers: %s", e)
        return []


def fetch_google_search_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch general web search results from Google Custom Search API.
    
    WARNING: GOOGLE_CUSTOM_SEARCH_CX defaults to the legacy hardcoded placeholder ID
    '017576662512468239146:omuauf_lfve'. Ensure a real Custom Search Engine ID is configured.
    """
    if not settings.GOOGLE_CUSTOM_SEARCH_API_KEY:
        logger.info("GOOGLE_CUSTOM_SEARCH_API_KEY not set — skipping Custom Search.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.GOOGLE_CUSTOM_SEARCH_API_KEY,
        "cx": settings.GOOGLE_CUSTOM_SEARCH_CX,
        "q": query,
        "num": max_results,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            logger.warning("Google Search API error: %s - %s", response.status_code, response.text)
            return []

        data = response.json()
        results = []
        for item in data.get("items", []):
            results.append(
                {
                    "title": item.get("title", "Untitled"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet", "No description available"),
                    "displayLink": item.get("displayLink"),
                    "formattedUrl": item.get("formattedUrl"),
                }
            )
        return results
    except Exception as e:
        logger.warning("Error fetching Google search results: %s", e)
        return []


def get_topic_resources(topic: str, resource_type: str = "all") -> Dict[str, Any]:
    """Aggregate search results across supported providers."""
    results: Dict[str, Any] = {}
    r_type = resource_type.lower()

    if r_type in ["all", "youtube"]:
        results["youtube"] = fetch_youtube_videos(topic, max_results=5)
    if r_type in ["all", "papers"]:
        results["papers"] = fetch_google_scholar_papers(topic, max_results=5)
    if r_type in ["all", "web"]:
        results["web"] = fetch_google_search_results(topic, max_results=5)

    return results
