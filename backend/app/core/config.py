"""
Application configuration.

All values are loaded from environment variables (same .env as legacy/).
No defaults for secrets — the app will fail fast if they are missing.
"""
from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── MongoDB ─────────────────────────────────────────────────────────────
    # Same env-var names as legacy/app/__init__.py so a single .env works.
    MONGO_URI: str
    DB_NAME: str = "catalyst_ai_db"

    # ── Session / Cookie ─────────────────────────────────────────────────────
    # Used to sign the session token stored in the HTTP-only cookie.
    SECRET_KEY: str
    # Lifetime in seconds (7 days — mirrors legacy PERMANENT_SESSION_LIFETIME)
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7

    # ── Cookie flags ─────────────────────────────────────────────────────────
    # Set COOKIE_SECURE=false only in local dev without HTTPS.
    # In production this MUST be True (migration-rules.md requirement).
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"    # "lax" | "strict" | "none"
    COOKIE_HTTPONLY: bool = True     # never false — no JWT in localStorage

    # ── LLM / Groq & Mistral ──────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "open-mistral-nemo"

    # ── External Search & Resource APIs ──────────────────────────────────────
    YOUTUBE_API_KEY: Optional[str] = None
    # NOTE: Preserving legacy typo in env var name (GOOGLE_SCHOLOR_API_KEY)
    GOOGLE_SCHOLOR_API_KEY: Optional[str] = None
    GOOGLE_CUSTOM_SEARCH_API_KEY: Optional[str] = None
    # Google Custom Search Engine ID (placeholder from legacy/app/utils/resource_utils.py:153)
    GOOGLE_CUSTOM_SEARCH_CX: str = "017576662512468239146:omuauf_lfve"
    MEDIUM_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # silently ignore unknown env vars from legacy
    )


# Module-level singleton — import this everywhere.
settings = Settings()
