
"""
User-specific retrieval service for RAG questions.

Features:
- English and Roman Urdu retrieval
- Input validation
- ChromaDB-level user isolation
- Hybrid semantic and keyword search
- Similarity threshold filtering
"""

from typing import Any

from app.core.logger import AppLogger
from app.vector_store.store import VectorStoreService


logger = AppLogger.get_logger(__name__)


class RetrievalService:
    DEFAULT_TOP_K = 5
    DEFAULT_THRESHOLD = 0.30

    def __init__(
        self,
        vector_store: VectorStoreService,
    ) -> None:
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD,
        user_id: str = "",
    ) -> list[dict[str, Any]]:
        """
        Retrieve only documents belonging to the
        authenticated user.

        The user_id must come from JWT authentication,
        never from the request body.
        """

        if (
            not isinstance(user_id, str)
            or not user_id.strip()
        ):
            raise ValueError(
                "A valid user_id is required"
            )

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            logger.warning(
                "Empty retrieval question rejected"
            )
            raise ValueError(
                "Question cannot be empty"
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k < 1
        ):
            raise ValueError(
                "top_k must be a positive integer"
            )

        if (
            not isinstance(threshold, (int, float))
            or isinstance(threshold, bool)
            or not 0.0 <= threshold <= 1.0
        ):
            raise ValueError(
                "Similarity threshold must be between 0 and 1"
            )

        try:
            logger.info(
                "Retrieval started | "
                "top_k=%d | threshold=%.2f",
                top_k,
                threshold,
            )

            retrieved_chunks = (
                self.vector_store.search_chunks(
                    question=question,
                    top_k=top_k,
                    user_id=user_id,
                )
            )

            relevant_chunks = [
                chunk
                for chunk in retrieved_chunks
                if (
                    chunk["similarity_score"]
                    >= threshold
                )
            ]

            logger.info(
                "Retrieval completed | "
                "fetched=%d | relevant=%d",
                len(retrieved_chunks),
                len(relevant_chunks),
            )

            return relevant_chunks

        except Exception:
            logger.exception(
                "Document retrieval failed"
            )
            raise
