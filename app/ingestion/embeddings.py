
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.logger import AppLogger


logger = AppLogger.get_logger(__name__)


class EmbeddingService:
    """
    Generate multilingual embeddings for the RAG pipeline.

    Model:
        intfloat/multilingual-e5-small

    Responsibilities:
        1. Load and cache the embedding model.
        2. Convert document chunks into vectors.
        3. Convert user questions into vectors.
        4. Validate inputs.
        5. Log processing events and errors.

    Notes:
        The E5 model uses different prefixes:
        - passage: for document content
        - query: for user questions

        English and Roman Urdu retrieval quality must
        be measured separately during evaluation.
    """

    MODEL_NAME = "intfloat/multilingual-e5-small"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_model() -> SentenceTransformer:
        """
        Load the embedding model once per Python process.

        Returns:
            Cached SentenceTransformer instance.
        """
        try:
            logger.info(
                "Loading embedding model: %s",
                EmbeddingService.MODEL_NAME
            )

            model = SentenceTransformer(
                EmbeddingService.MODEL_NAME
            )

            logger.info(
                "Embedding model loaded successfully"
            )

            return model

        except Exception:
            logger.exception(
                "Failed to load embedding model"
            )
            raise

    @classmethod
    def embed_documents(
        cls,
        texts: list[str]
    ) -> list[list[float]]:
        """
        Generate embeddings for document chunks.

        Args:
            texts: List of extracted document chunks.

        Returns:
            List of normalized embedding vectors.
        """
        if not texts:
            logger.warning(
                "Embedding requested with empty document list"
            )
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "All document chunks must be non-empty strings."
            )

        try:
            logger.info(
                "Generating embeddings for %d chunks",
                len(texts)
            )

            # E5 requires the passage prefix.
            passages = [
                f"passage: {text.strip()}"
                for text in texts
            ]

            model = cls.get_model()

            vectors = model.encode(
                passages,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            logger.info(
                "Successfully embedded %d chunks",
                len(vectors)
            )

            return vectors.tolist()

        except Exception:
            logger.exception(
                "Document embedding failed"
            )
            raise

    @classmethod
    def embed_query(
        cls,
        question: str
    ) -> list[float]:
        """
        Convert an English or Roman Urdu question
        into a normalized embedding vector.

        Args:
            question: User's question.

        Returns:
            Single embedding vector.
        """
        if not isinstance(question, str) or not question.strip():
            logger.warning(
                "Empty or invalid embedding query rejected"
            )
            raise ValueError(
                "Question cannot be empty."
            )

        try:
            logger.info(
                "Generating query embedding"
            )

            # The query prefix is required by E5.
            query = f"query: {question.strip()}"

            model = cls.get_model()

            vector = model.encode(
                query,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            logger.info(
                "Query embedding generated successfully"
            )

            return vector.tolist()

        except Exception:
            logger.exception(
                "Query embedding failed"
            )
            raise
