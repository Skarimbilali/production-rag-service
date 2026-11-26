
"""
JWT-protected document-grounded question answering API.

Features:
- JWT authentication
- User-specific document retrieval
- Input guardrails
- Semantic + hybrid retrieval
- Groq answer generation
- Citation and output validation
- English and Roman Urdu refusals
- Retrieval and generation performance monitoring
"""

import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from groq import APIConnectionError, APIStatusError

from app.auth.router import get_current_user
from app.core.logger import AppLogger
from app.core.monitoring import monitoring_service
from app.schemas import QuestionRequest, QuestionResponse
from app.retrieval.retriever import RetrievalService
from app.generation.generator import GenerationService
from app.generation.llm_client import GroqLLMClient
from app.vector_store.store import VectorStoreService
from app.guardrails.guardrails import GuardrailService


logger = AppLogger.get_logger(__name__)


router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
)


vector_store = VectorStoreService()
retrieval_service = RetrievalService(vector_store)


@router.post(
    "/ask",
    response_model=QuestionResponse,
    responses={
        401: {
            "description": "Authentication required",
        },
        400: {
            "description": (
                "Question rejected by security guardrails"
            ),
        },
        422: {
            "description": (
                "Invalid request or answer processing error"
            ),
        },
        503: {
            "description": (
                "LLM provider temporarily unavailable"
            ),
        },
    },
)
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user),
) -> QuestionResponse:
    """
    Answer questions using only the authenticated
    user's indexed documents.

    User identity comes from the verified JWT.
    The client cannot select another user's identity.
    """

    user_id = current_user["id"]

    logger.info(
        "Authenticated question request received"
    )

    try:
        validated_question = (
            GuardrailService.validate_question(
                request.question
            )
        )

    except ValueError as exc:
        logger.warning(
            "Question rejected by input guardrails"
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    try:
        # Step 1: User-specific document retrieval.
        retrieval_started = time.perf_counter()

        try:
            chunks = retrieval_service.retrieve(
                question=validated_question,
                top_k=request.top_k,
                threshold=request.threshold,
                user_id=user_id,
            )

        finally:
            retrieval_ms = (
                time.perf_counter()
                - retrieval_started
            ) * 1000

            monitoring_service.record_retrieval(
                retrieval_ms
            )

            logger.info(
                "RAG retrieval duration | "
                "duration_ms=%.2f",
                retrieval_ms,
            )

        # Avoid calling Groq when the user's
        # documents contain no matching evidence.
        if not chunks:
            refusal = (
                GenerationService.get_refusal_message(
                    validated_question
                )
            )

            return QuestionResponse(
                answer=refusal,
                citations=[],
                retrieved_count=0,
                retrieved_chunks=[],
            )

        # Step 2: Initialize the LLM client.
        llm_client = GroqLLMClient()

        try:
            generation_service = (
                GenerationService(
                    llm_client.generate
                )
            )

            # Step 3: Measure generation duration.
            generation_started = (
                time.perf_counter()
            )

            try:
                result = (
                    await generation_service.generate_answer(
                        question=validated_question,
                        chunks=chunks,
                    )
                )

            finally:
                generation_ms = (
                    time.perf_counter()
                    - generation_started
                ) * 1000

                monitoring_service.record_generation(
                    generation_ms
                )

                logger.info(
                    "RAG generation duration | "
                    "duration_ms=%.2f",
                    generation_ms,
                )

        finally:
            # Release Groq HTTP connections.
            await llm_client.close()

        # Step 4: Return answer and source evidence.
        return QuestionResponse(
            answer=result["answer"],
            citations=result["citations"],
            retrieved_count=result["retrieved_count"],
            retrieved_chunks=chunks,
        )

    except APIConnectionError:
        logger.exception(
            "LLM connection failed"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "LLM service temporarily unavailable."
            ),
        )

    except APIStatusError as exc:
        logger.error(
            "LLM API failed | status=%s",
            exc.status_code,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "LLM service temporarily unavailable."
            ),
        )

    except ValueError:
        logger.exception(
            "Invalid question processing result"
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Unable to process question."
            ),
        )
