
"""
Tests for JWT user-scoped RAG retrieval.

Features:
- English retrieval
- Roman Urdu retrieval
- User ID forwarding
- Similarity threshold filtering
- Invalid input rejection
- Empty retrieval results

Uses mocks to avoid changing production ChromaDB data.
"""

from unittest.mock import Mock

import pytest

from app.retrieval.retriever import RetrievalService


USER_A = "user-a"
USER_B = "user-b"


@pytest.fixture
def retrieval_service():
    """Create retrieval service with mocked vector store."""
    vector_store = Mock()

    vector_store.search_chunks.return_value = [
        {
            "id": "chunk-1",
            "text": "Employees receive 20 annual leave days.",
            "metadata": {
                "document_id": "document-1",
                "filename": "policy.pdf",
                "user_id": USER_A,
            },
            "similarity_score": 0.90,
        }
    ]

    return RetrievalService(vector_store)


def test_english_retrieval(retrieval_service):
    """English questions retrieve user-scoped chunks."""
    question = "How many annual leave days?"

    results = retrieval_service.retrieve(
        question=question,
        top_k=5,
        threshold=0.30,
        user_id=USER_A,
    )

    assert len(results) == 1
    assert results[0]["similarity_score"] == 0.90

    retrieval_service.vector_store.search_chunks.assert_called_once_with(
        question=question,
        top_k=5,
        user_id=USER_A,
    )


def test_roman_urdu_retrieval(retrieval_service):
    """Roman Urdu questions use the same secure retrieval."""
    question = "Employees ko kitni annual leaves milti hain?"

    results = retrieval_service.retrieve(
        question=question,
        top_k=5,
        threshold=0.30,
        user_id=USER_A,
    )

    assert results
    assert "similarity_score" in results[0]

    retrieval_service.vector_store.search_chunks.assert_called_once_with(
        question=question,
        top_k=5,
        user_id=USER_A,
    )


def test_similarity_threshold(retrieval_service):
    """Chunks below the requested threshold are excluded."""
    results = retrieval_service.retrieve(
        question="annual leave",
        threshold=0.95,
        user_id=USER_A,
    )

    assert results == []


def test_user_identity_forwarded(retrieval_service):
    """Retrieval passes the requested identity to the vector store."""
    retrieval_service.retrieve(
        question="annual leave",
        user_id=USER_B,
    )

    retrieval_service.vector_store.search_chunks.assert_called_once_with(
        question="annual leave",
        top_k=5,
        user_id=USER_B,
    )


def test_missing_user_id_rejected(retrieval_service):
    """Search without a user ID must fail."""
    with pytest.raises(ValueError, match="user_id"):
        retrieval_service.retrieve(
            question="annual leave",
        )

    retrieval_service.vector_store.search_chunks.assert_not_called()


def test_invalid_top_k_rejected(retrieval_service):
    """Reject invalid retrieval counts."""
    with pytest.raises(ValueError, match="top_k"):
        retrieval_service.retrieve(
            question="annual leave",
            top_k=0,
            user_id=USER_A,
        )


def test_invalid_threshold_rejected(retrieval_service):
    """Reject similarity thresholds outside 0 to 1."""
    with pytest.raises(ValueError, match="threshold"):
        retrieval_service.retrieve(
            question="annual leave",
            threshold=1.5,
            user_id=USER_A,
        )


def test_empty_results(retrieval_service):
    """Return an empty list when no user documents match."""
    retrieval_service.vector_store.search_chunks.return_value = []

    results = retrieval_service.retrieve(
        question="unknown topic",
        user_id=USER_A,
    )

    assert results == []
