
from fastapi import FastAPI

from app.config import settings
from app.schemas import HealthResponse
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Initialize FastAPI application.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production RAG Service - English and Roman Urdu"
)
# Frontend directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Serve frontend CSS and JavaScript
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
# Register document management routes.
app.include_router(documents_router)

# Register document-based question answering routes.
app.include_router(questions_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check application health"
)
async def health_check() -> HealthResponse:
    """Return basic application health information."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION
    )
