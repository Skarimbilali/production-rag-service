from fastapi import FastAPI

from app.config import settings
from app.schemas import HealthResponse


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Retrieval-Augmented Generation API"
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check application health"
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION
    )