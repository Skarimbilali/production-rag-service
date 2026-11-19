
from app.retrieval.retriever import RetrievalService
from app.vector_store.store import VectorStoreService


def test_english_retrieval():
    """Check English retrieval against uploaded documents."""
    service = RetrievalService(VectorStoreService())

    results = service.retrieve(
        "How does the RAG project work?",
        top_k=5,
        threshold=0.0
    )

    assert results, "No chunks retrieved for English query"
    assert all("similarity_score" in r for r in results)


def test_roman_urdu_retrieval():
    """Check Roman Urdu retrieval against uploaded documents."""
    service = RetrievalService(VectorStoreService())

    results = service.retrieve(
        "RAG project kaise kaam karta hai?",
        top_k=5,
        threshold=0.0
    )

    assert results, "No chunks retrieved for Roman Urdu query"
    assert all("similarity_score" in r for r in results)
