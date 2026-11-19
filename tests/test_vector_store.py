
from uuid import uuid4

import pytest

from app.vector_store.store import VectorStoreService


@pytest.fixture
def vector_store(tmp_path):
    """
    Create an isolated database for each test.

    Production ChromaDB data is not modified.
    """
    return VectorStoreService(
        db_path=str(tmp_path / "test_chroma")
    )


def test_add_and_count_chunks(vector_store):
    """Verify document chunks are stored successfully."""
    document_id = str(uuid4())

    chunks = [{
        "id": f"{document_id}-0",
        "text": "Employees receive 20 annual leave days.",
        "metadata": {
            "document_id": document_id,
            "filename": "policy.pdf",
            "page": 1,
            "chunk_position": 0
        }
    }]

    stored = vector_store.add_chunks(chunks)

    assert stored == 1
    assert vector_store.count_chunks() == 1


def test_search_english_and_roman_urdu(vector_store):
    """Verify both languages can retrieve a document chunk."""
    document_id = str(uuid4())

    vector_store.add_chunks([{
        "id": f"{document_id}-0",
        "text": "Employees receive 20 annual leave days.",
        "metadata": {
            "document_id": document_id,
            "filename": "policy.pdf",
            "page": 1,
            "chunk_position": 0
        }
    }])

    english_results = vector_store.search_chunks(
        "How many annual leave days do employees receive?"
    )

    roman_urdu_results = vector_store.search_chunks(
        "Employees ko kitni annual leaves milti hain?"
    )

    assert english_results
    assert roman_urdu_results

    assert english_results[0]["metadata"]["document_id"] == document_id
    assert roman_urdu_results[0]["metadata"]["document_id"] == document_id

    assert isinstance(
        roman_urdu_results[0]["similarity_score"], float
    )


def test_delete_document(vector_store):
    """Verify deleted document vectors are removed."""
    document_id = str(uuid4())

    vector_store.add_chunks([{
        "id": f"{document_id}-0",
        "text": "Employees receive 20 annual leave days.",
        "metadata": {
            "document_id": document_id,
            "filename": "policy.pdf",
            "page": 1,
            "chunk_position": 0
        }
    }])

    deleted = vector_store.delete_document(document_id)

    assert deleted == 1
    assert vector_store.count_chunks() == 0
    assert vector_store.search_chunks("Annual leave policy") == []
