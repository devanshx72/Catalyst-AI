"""
Auth router — POST /api/v1/auth/register, login, logout.

Route handlers are intentionally thin:
  request body validation (Pydantic) → service call → set/clear cookie → response.
No business logic in this file.
"""
from fastapi import APIRouter, Depends, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db
from app.core.security import (
    clear_session_cookie,
    get_current_session,
    set_session_cookie,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RegisterResponse:
    """
    Create a new user account.

    - Validates password match and uniqueness of email + username.
    - Stores bcrypt-hashed password; never stores plaintext.
    - Does NOT auto-login — client must call /login after registering
      (mirrors legacy behaviour: auth.py:66-67 redirects to sign_in).
    """
    await register_user(db, payload)
    return RegisterResponse()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive a session cookie",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate with email-or-username + password.

    On success, sets an HTTP-only, Secure, SameSite session cookie.
    The cookie is signed (HMAC-SHA256) and carries user_id + name + expiry.
    No token is returned in the response body.
    """
    user = await login_user(db, payload)
    set_session_cookie(response, user_id=user["user_id"], name=user["name"])
    return LoginResponse(
        message=f"Welcome back, {user['name']}!",
        user_id=user["user_id"],
        name=user["name"],
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out and clear the session cookie",
)
async def logout(
    response: Response,
    # Require a valid session to log out (prevents spurious cookie clears).
    _session: dict = Depends(get_current_session),
) -> LogoutResponse:
    """
    Clear the session cookie.  Requires an active session (returns 401 if not logged in).
    """
    clear_session_cookie(response)
    return LogoutResponse()
