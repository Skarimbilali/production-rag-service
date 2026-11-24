
from fastapi import APIRouter, HTTPException, status
from groq import APIConnectionError, APIStatusError

from app.core.logger import AppLogger
from app.schemas import QuestionRequest, QuestionResponse
from app.retrieval.retriever import RetrievalService
from app.generation.generator import GenerationService
from app.generation.llm_client import GroqLLMClient
from app.vector_store.store import VectorStoreService
from app.guardrails.guardrails import GuardrailService


logger = AppLogger.get_logger(__name__)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)

# Reuse the vector database and retrieval service.
vector_store = VectorStoreService()
retrieval_service = RetrievalService(vector_store)



@router.post(
    "/ask",
    response_model=QuestionResponse,
    responses={
        400: {
            "description": "Question rejected by security guardrails",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Question violates security rules."
                    }
                }
            }
        },
        422: {
            "description": "Invalid request or answer processing error"
        },
        503: {
            "description": "LLM provider temporarily unavailable"
        }
    }
)

async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Answer an English or Roman Urdu question using RAG.

    Workflow:
        1. Retrieve relevant document chunks.
        2. Generate a grounded answer using Groq.
        3. Validate citations against retrieved sources.
        4. Return answer, citations and similarity scores.

    External API failures return HTTP 503.
    """
    logger.info("Question answering request received")
        # Validate question before retrieval and LLM processing.
    try:
        validated_question = GuardrailService.validate_question(
            request.question
        )
    except ValueError as exc:
        logger.warning("Question rejected by input guardrails")
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    try:
        # Step 1: Retrieve relevant context.
        chunks = retrieval_service.retrieve(
            question=validated_question,
            top_k=request.top_k,
            threshold=request.threshold
        )

        # No LLM request is needed when retrieval finds nothing.
        if not chunks:
            return QuestionResponse(
                answer=GenerationService.REFUSAL_MESSAGE,
                citations=[],
                retrieved_count=0,
                retrieved_chunks=[]
            )

        # Step 2: Create an asynchronous LLM client.
        llm_client = GroqLLMClient()

        try:
            generation_service = GenerationService(
                llm_client.generate
            )

            # Step 3: Generate answer and validate citations.
            result = await generation_service.generate_answer(
                question=request.question,
                chunks=chunks
            )

        finally:
            # Ensure HTTP connections are released.
            await llm_client.close()

        # Step 4: Return the evidence with the answer.
        return QuestionResponse(
            answer=result["answer"],
            citations=result["citations"],
            retrieved_count=result["retrieved_count"],
            retrieved_chunks=chunks
        )

    except APIConnectionError:
        logger.exception("LLM connection failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service temporarily unavailable."
        )

    except APIStatusError as exc:
        logger.error(
            "LLM API failed | status=%s",
            exc.status_code
        )
        raise HTTPException(
            status_code=503,
            detail="LLM service temporarily unavailable."
        )

    except ValueError:
        logger.exception("Invalid question processing result")
        raise HTTPException(
            status_code=422,
            detail="Unable to process question."
        )
