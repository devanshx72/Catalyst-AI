
"""
FastAPI application factory and lifespan manager.
Startup: open Motor connection, ping MongoDB.
Shutdown: gracefully close the connection pool.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close_db, connect_db
from app.routers import auth as auth_router
from app.routers import coach as coach_router
from app.routers import goals as goals_router
from app.routers import home as home_router
from app.routers import profile as profile_router
from app.routers import resume as resume_router
from app.routers import roadmap as roadmap_router
from app.routers import tutor as tutor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    await connect_db()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Catalyst AI API",
        description="FastAPI backend for Catalyst AI — migrated from Flask.",
        version="0.1.0",
        lifespan=lifespan,
        # Disable default /docs redirect in production if desired; keep for now.
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Allow the Next.js dev server (port 3000) during development.
    # Tighten to the production domain before go-live.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,   # required for cookies to be sent cross-origin
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router)
    app.include_router(profile_router.router)
    app.include_router(resume_router.router)
    app.include_router(goals_router.router)
    app.include_router(roadmap_router.router)
    app.include_router(tutor_router.router)
    app.include_router(coach_router.router)
    app.include_router(home_router.router)

    return app


app = create_app()
