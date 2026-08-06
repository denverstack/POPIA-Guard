"""FastAPI application entrypoint.

Phase 1 exposes only a health check — the scanner, auth, and report
endpoints are implemented in Phase 2 once the engine itself exists.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.project_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Liveness check used by Docker Compose and, later, CI."""
    return {"status": "ok", "environment": settings.environment}
