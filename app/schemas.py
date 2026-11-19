from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question about uploaded documents"
    )


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str