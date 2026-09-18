"""
Session management using a signed, HTTP-only cookie.

Design decisions (migration-rules.md):
- No JWT. No localStorage. HTTP-only cookie only.
- The cookie value is an HMAC-SHA256 signed payload: base64(json) + "." + hmac
- Payload contains: user_id, name, expires_at (ISO-8601 UTC)
- Signature prevents tampering without knowing SECRET_KEY.
- Secure and SameSite flags are set from config, defaulting to secure=True.

This is intentionally simple: no server-side session store, no Redis.
The signed cookie IS the session. Logout clears it.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Cookie, HTTPException, Response, status

from app.core.config import settings


# ── Cookie name ──────────────────────────────────────────────────────────────
COOKIE_NAME = "catalyst_session"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sign(payload_b64: str) -> str:
    """Return HMAC-SHA256 hex digest of the base64-encoded payload."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()


def _encode_session(user_id: str, name: str) -> str:
    """Encode and sign session data into a cookie value string."""
    expires_at = (
        datetime.now(tz=timezone.utc) + timedelta(seconds=settings.SESSION_MAX_AGE)
    ).isoformat()

    payload = json.dumps(
        {"user_id": user_id, "name": name, "expires_at": expires_at},
        separators=(",", ":"),
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = _sign(payload_b64)
    return f"{payload_b64}.{sig}"


def _decode_session(token: str) -> dict:
    """
    Decode and verify a cookie value.

    Raises HTTPException 401 if:
    - the token is malformed
    - the signature is invalid
    - the session has expired
    """
    try:
        payload_b64, sig = token.rsplit(".", 1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    expected_sig = _sign(payload_b64)
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session signature invalid")

    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed session payload")

    expires_at = datetime.fromisoformat(payload["expires_at"])
    if datetime.now(tz=timezone.utc) > expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return payload


# ── Public API ────────────────────────────────────────────────────────────────

def set_session_cookie(response: Response, user_id: str, name: str) -> None:
    """Write a signed, HTTP-only session cookie to the response."""
    token = _encode_session(user_id, name)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Delete the session cookie by setting max_age=0."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


def get_current_session(
    catalyst_session: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
) -> dict:
    """
    FastAPI dependency.  Returns the decoded session dict.

    Usage:
        @router.get("/protected")
        async def protected(session: dict = Depends(get_current_session)):
            return {"user_id": session["user_id"]}
    """
    if catalyst_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return _decode_session(catalyst_session)
