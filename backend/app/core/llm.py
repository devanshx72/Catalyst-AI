"""
Centralized LLM Client Factory & Provider.
Single source of truth for LLM instantiations (Groq, Mistral), model definitions,
and provider error handling across Catalyst AI.
"""
from __future__ import annotations

import logging
from typing import Optional
from groq import Groq
from mistralai import Mistral

from app.core.config import settings

logger = logging.getLogger(__name__)

_groq_client: Optional[Groq] = None
_mistral_client: Optional[Mistral] = None


def get_groq_client() -> Optional[Groq]:
    """
    Retrieve or initialize the singleton Groq client.
    Returns None if GROQ_API_KEY is not configured or fails initialization.
    """
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    if not settings.GROQ_API_KEY:
        logger.info("GROQ_API_KEY not configured — Groq operations will use structured fallbacks.")
        return None

    try:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return _groq_client
    except Exception as e:
        logger.warning("Failed to initialize Groq client: %s", e)
        return None


def get_mistral_client() -> Optional[Mistral]:
    """
    Retrieve or initialize the singleton Mistral AI client.
    Returns None if MISTRAL_API_KEY is not configured or fails initialization.
    """
    global _mistral_client
    if _mistral_client is not None:
        return _mistral_client

    if not settings.MISTRAL_API_KEY:
        logger.info("MISTRAL_API_KEY not configured — Mistral operations will use structured fallbacks.")
        return None

    try:
        _mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
        return _mistral_client
    except Exception as e:
        logger.warning("Failed to initialize Mistral client: %s", e)
        return None


def get_groq_model() -> str:
    """Return default Groq model identifier."""
    return settings.GROQ_MODEL


def get_mistral_model() -> str:
    """Return default Mistral model identifier."""
    return settings.MISTRAL_MODEL
