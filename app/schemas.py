
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for application health checks."""

    status: str
    service: str
    version: str


class QuestionRequest(BaseModel):
    """Validate an English or Roman Urdu question."""

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Question about uploaded documents",
        examples=["RAG project kaise kaam karta hai?"]
    )

    top_k: int = Field(default=5, ge=1, le=20)

    threshold: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0
    )


class CitationResponse(BaseModel):
    """Reference to a retrieved document chunk."""

    source_id: str
    chunk_id: str
    metadata: dict[str, Any]


class RetrievedChunkResponse(BaseModel):
    """Retrieved chunk and its cosine similarity score."""

    id: str
    text: str
    metadata: dict[str, Any]
    similarity_score: float


class QuestionResponse(BaseModel):
    """Grounded answer including citations and retrieved evidence."""

    answer: str
    citations: list[CitationResponse]
    retrieved_count: int
    retrieved_chunks: list[RetrievedChunkResponse]
