
"""
Production RAG Service - FastAPI application.

Features:
- Document upload, listing and deletion
- Document-grounded question answering
- HTML/CSS/JavaScript frontend
- Application health endpoint
- HTTP request performance monitoring
- Monitoring metrics endpoint
"""

import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import HealthResponse
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.core.logger import AppLogger
from app.core.monitoring import monitoring_service


logger = AppLogger.get_logger(__name__)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production RAG Service - English and Roman Urdu",
)


FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent / "frontend"
)


@app.middleware("http")
async def monitor_http_requests(
    request: Request,
    call_next,
):
    """
    Measure HTTP request duration and status.

    Does not record request bodies, document contents,
    user questions or API credentials.
    """
    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    finally:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        monitoring_service.record_request(
            status_code=status_code,
            duration_ms=duration_ms,
        )

        logger.info(
            "HTTP request | method=%s | path=%s | "
            "status=%d | duration_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )


app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the browser-based RAG dashboard."""
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


app.include_router(documents_router)
app.include_router(questions_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check application health",
)
async def health_check() -> HealthResponse:
    """Return application health information."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="View application performance metrics",
)
async def get_metrics() -> dict:
    """
    Return in-memory monitoring statistics.

    Includes:
    - Application uptime
    - Total HTTP requests
    - Successful and failed requests
    - HTTP status code counts
    - Average HTTP response duration
    - Average RAG retrieval duration
    - Average LLM generation duration

    Metrics reset when the application restarts.

    This endpoint is intended for development and demo
    environments. Protect it with authentication or
    network restrictions before public deployment.
    """
    return monitoring_service.get_metrics()
