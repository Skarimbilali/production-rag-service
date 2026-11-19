
from fastapi import FastAPI

from app.config import settings
from app.schemas import HealthResponse
from app.api.documents import router as documents_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production RAG Service - English and Roman Urdu"
)

# Register document upload, listing and deletion routes.
app.include_router(documents_router)


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
