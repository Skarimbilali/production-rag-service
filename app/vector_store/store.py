
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import chromadb

from app.core.logger import AppLogger
from app.ingestion.embeddings import EmbeddingService


logger = AppLogger.get_logger(__name__)


class VectorStoreService:
    """
    Store document vectors and perform generic hybrid retrieval.

    Hybrid retrieval combines:
        1. Semantic similarity from ChromaDB.
        2. Keyword relevance from retrieved candidate chunks.

    No document names, subjects or answers are hardcoded.
    """

    COLLECTION_NAME = "rag_documents"

    # Retrieve a wider candidate pool before reranking.
    CANDIDATE_POOL_SIZE = 80

    # Generic query stopwords, not document-specific keywords.
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "can", "could", "do", "does", "for", "from",
        "has", "have", "how", "i", "in", "is", "it",
        "of", "on", "or", "our", "should", "the",
        "their", "there", "this", "to", "was", "were",
        "what", "when", "where", "which", "who",
        "will", "with", "would", "you", "your",

        # Common Roman Urdu question words.
        "aur", "hai", "hain", "ho", "hoga", "hogi",
        "ka", "ke", "ki", "ko", "kya", "kitna",
        "kitni", "mein", "me", "mujhe", "ne",
        "nahi", "par", "pe", "se", "to", "wala",
        "wale", "wali", "ye", "wo"
    }

    def __init__(self, db_path: str = "data/chroma_db"):
        """
        Initialize persistent ChromaDB with cosine distance.
        """
        try:
            Path(db_path).mkdir(
                parents=True,
                exist_ok=True
            )

            self.client = chromadb.PersistentClient(
                path=db_path
            )

            self.collection = (
                self.client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    configuration={
                        "hnsw": {"space": "cosine"}
                    }
                )
            )

            logger.info(
                "ChromaDB initialized successfully"
            )

        except Exception:
            logger.exception(
                "ChromaDB initialization failed"
            )
            raise

    def add_chunks(
        self,
        chunks: list[dict[str, Any]]
    ) -> int:
        """
        Store chunks, embeddings and metadata.
        """
        if not chunks:
            logger.warning(
                "Empty chunk list received"
            )
            return 0

        try:
            ids = [
                chunk["id"]
                for chunk in chunks
            ]

            texts = [
                chunk["text"]
                for chunk in chunks
            ]

            metadatas = [
                {
                    key: value
                    for key, value in chunk["metadata"].items()
                    if value is not None
                }
                for chunk in chunks
            ]

            embeddings = (
                EmbeddingService.embed_documents(texts)
            )

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(
                "Stored %d chunks successfully",
                len(chunks)
            )

            return len(chunks)

        except Exception:
            logger.exception(
                "Failed to store document chunks"
            )
            raise

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """
        Extract searchable English/Roman Urdu terms.

        Keeps letters and numbers from Unicode text.
        Removes only common question/filler words.
        """
        words = re.findall(
            r"[^\W_]+",
            text.lower(),
            flags=re.UNICODE
        )

        return [
            word
            for word in words
            if len(word) > 1
            and word not in cls.STOPWORDS
        ]

    @classmethod
    def _keyword_scores(
        cls,
        question: str,
        chunks: list[dict[str, Any]]
    ) -> list[float]:
        """
        Calculate keyword relevance within the candidate pool.

        Rare matching terms receive higher weight.
        Query terms are not tied to any particular topic.

        Returns scores between 0 and 1.
        """
        question_terms = set(
            cls._tokenize(question)
        )

        if not question_terms:
            return [0.0] * len(chunks)

        document_terms = []

        for chunk in chunks:
            metadata = chunk.get("metadata") or {}

            searchable_text = " ".join([
                str(chunk.get("text") or ""),
                str(metadata.get("section") or "")
            ])

            document_terms.append(
                set(cls._tokenize(searchable_text))
            )

        total_documents = len(document_terms)

        # Number of candidate chunks containing each term.
        document_frequency = Counter()

        for terms in document_terms:
            document_frequency.update(
                terms.intersection(question_terms)
            )

        # IDF gives rarer matching terms more weight.
        term_weights = {
            term: math.log(
                1.0
                + (
                    total_documents
                    - document_frequency[term]
                    + 0.5
                ) / (
                    document_frequency[term]
                    + 0.5
                )
            )
            for term in question_terms
        }

        total_weight = sum(
            term_weights.values()
        )

        if total_weight <= 0:
            return [0.0] * len(chunks)

        scores = []

        for terms in document_terms:
            matched_terms = (
                question_terms.intersection(terms)
            )

            matching_weight = sum(
                term_weights[term]
                for term in matched_terms
            )

            score = matching_weight / total_weight

            scores.append(
                max(0.0, min(1.0, score))
            )

        return scores

    @classmethod
    def _rerank(
        cls,
        question: str,
        chunks: list[dict[str, Any]],
        top_k: int
    ) -> list[dict[str, Any]]:
        """
        Rerank semantic candidates using keyword coverage.

        Semantic similarity remains unchanged in the
        public response.

        The combined score is used only for ranking.
        """
        if not chunks:
            return []

        keyword_scores = cls._keyword_scores(
            question,
            chunks
        )

        ranked_chunks = []

        for chunk, keyword_score in zip(
            chunks,
            keyword_scores
        ):
            semantic_score = max(
                0.0,
                min(
                    1.0,
                    float(
                        chunk["similarity_score"]
                    )
                )
            )

            # Give keyword evidence meaningful influence
            # while preserving semantic search.
            combined_score = (
                0.50 * semantic_score
                + 0.50 * keyword_score
            )

            ranked_chunks.append(
                (combined_score, chunk)
            )

        ranked_chunks.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return [
            chunk
            for _, chunk in ranked_chunks[:top_k]
        ]

    def search_chunks(
        self,
        question: str,
        top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Search all uploaded documents automatically.

        Workflow:
            1. Embed question.
            2. Retrieve wider semantic candidate pool.
            3. Calculate generic keyword relevance.
            4. Rerank candidates.
            5. Return the best top_k chunks.

        The original cosine similarity remains available
        for threshold filtering and frontend display.
        """
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "Question cannot be empty"
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k < 1
        ):
            raise ValueError(
                "top_k must be greater than zero"
            )

        try:
            total = self.collection.count()

            if total == 0:
                logger.info(
                    "No document chunks available"
                )
                return []

            query_embedding = (
                EmbeddingService.embed_query(question)
            )

            candidate_count = min(
                total,
                max(
                    top_k,
                    self.CANDIDATE_POOL_SIZE
                )
            )

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_count,
                include=[
                    "documents",
                    "metadatas",
                    "distances"
                ]
            )

            candidate_chunks = []

            for (
                chunk_id,
                text,
                metadata,
                distance
            ) in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                similarity = (
                    1.0 - float(distance)
                )

                candidate_chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "metadata": metadata or {},
                    "similarity_score": similarity
                })

            relevant_chunks = self._rerank(
                question=question,
                chunks=candidate_chunks,
                top_k=top_k
            )

            logger.info(
                "Hybrid retrieval completed | "
                "candidates=%d | returned=%d",
                len(candidate_chunks),
                len(relevant_chunks)
            )

            return relevant_chunks

        except Exception:
            logger.exception(
                "Vector search failed"
            )
            raise

    def delete_document(
        self,
        document_id: str
    ) -> int:
        """
        Delete all chunks belonging to a document.
        """
        if not document_id.strip():
            raise ValueError(
                "Document ID cannot be empty"
            )

        try:
            matches = self.collection.get(
                where={
                    "document_id": document_id
                }
            )

            ids = matches["ids"]

            if ids:
                self.collection.delete(
                    ids=ids
                )

            logger.info(
                "Deleted %d document chunks",
                len(ids)
            )

            return len(ids)

        except Exception:
            logger.exception(
                "Document deletion failed"
            )
            raise

    def count_chunks(self) -> int:
        """
        Return total stored chunk count.
        """
        return self.collection.count()
