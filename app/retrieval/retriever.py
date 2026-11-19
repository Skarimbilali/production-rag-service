
from typing import Any

from app.core.logger import AppLogger
from app.vector_store.store import VectorStoreService


# Reuse centralized application logger.
logger = AppLogger.get_logger(__name__)


class RetrievalService:
    """
    Retrieve relevant document chunks for RAG questions.

    Responsibilities:
        1. Validate the user question.
        2. Perform multilingual semantic search.
        3. Apply a similarity threshold.
        4. Return source metadata and similarity scores.
        5. Log retrieval operations and failures.

    Business logic remains separate from API routes.
    """

    DEFAULT_TOP_K = 5
    DEFAULT_THRESHOLD = 0.30

    def __init__(
        self,
        vector_store: VectorStoreService
    ) -> None:
        """
        Initialize retrieval with an existing vector store.

        Args:
            vector_store: Shared ChromaDB service instance.
        """
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        threshold: float = DEFAULT_THRESHOLD
    ) -> list[dict[str, Any]]:
        """
        Find relevant chunks using semantic similarity.

        Args:
            question: English or Roman Urdu question.
            top_k: Maximum number of chunks to retrieve.
            threshold: Minimum cosine similarity score.

        Returns:
            List of matching chunks, including metadata,
            text and similarity scores.

        Raises:
            ValueError: Invalid question or search settings.
        """

        # Validate before accessing the database.
        if not isinstance(question, str) or not question.strip():
            logger.warning("Empty retrieval question rejected")
            raise ValueError("Question cannot be empty")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "Similarity threshold must be between 0 and 1"
            )

        try:
            logger.info(
                "Retrieval started | top_k=%d | threshold=%.2f",
                top_k,
                threshold
            )

            # VectorStoreService handles embedding and DB search.
            # Do not generate query embeddings twice.
            retrieved_chunks = self.vector_store.search_chunks(
                question=question,
                top_k=top_k
            )

            # Filter out chunks below our baseline threshold.
            relevant_chunks = [
                chunk
                for chunk in retrieved_chunks
                if chunk["similarity_score"] >= threshold
            ]

            logger.info(
                "Retrieval completed | fetched=%d | relevant=%d",
                len(retrieved_chunks),
                len(relevant_chunks)
            )

            return relevant_chunks

        except Exception:
            logger.exception("Document retrieval failed")
            raise
