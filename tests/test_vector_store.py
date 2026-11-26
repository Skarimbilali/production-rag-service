
"""
Tests for secure user-specific ChromaDB storage.
"""

from uuid import uuid4

import pytest

from app.vector_store.store import VectorStoreService


USER_A = "user-a"
USER_B = "user-b"


@pytest.fixture
def vector_store(tmp_path):
    """Use isolated test database."""
    return VectorStoreService(
        db_path=str(
            tmp_path / "test_chroma"
        )
    )


def sample_chunk(
    text="Employees receive 20 annual leave days.",
):
    document_id = str(uuid4())

    return {
        "id": f"{document_id}-0",
        "text": text,
        "metadata": {
            "document_id": document_id,
            "filename": "policy.pdf",
            "page": 1,
            "chunk_position": 0,
        },
    }


def test_add_and_count_chunks(vector_store):
    chunk = sample_chunk()

    stored = vector_store.add_chunks(
        [chunk],
        user_id=USER_A,
    )

    assert stored == 1

    assert vector_store.count_chunks(
        user_id=USER_A
    ) == 1

    assert vector_store.count_chunks(
        user_id=USER_B
    ) == 0


def test_search_english_and_roman_urdu(
    vector_store,
):
    chunk = sample_chunk()

    vector_store.add_chunks(
        [chunk],
        user_id=USER_A,
    )

    english_results = (
        vector_store.search_chunks(
            question=(
                "How many annual leave days "
                "do employees receive?"
            ),
            user_id=USER_A,
        )
    )

    roman_urdu_results = (
        vector_store.search_chunks(
            question=(
                "Employees ko kitni annual "
                "leaves milti hain?"
            ),
            user_id=USER_A,
        )
    )

    assert english_results
    assert roman_urdu_results

    document_id = (
        chunk["metadata"]["document_id"]
    )

    assert (
        english_results[0]["metadata"]["document_id"]
        == document_id
    )

    assert (
        roman_urdu_results[0]["metadata"]["document_id"]
        == document_id
    )

    assert isinstance(
        roman_urdu_results[0]["similarity_score"],
        float,
    )


def test_cross_user_search_and_delete_denied(
    vector_store,
):
    chunk = sample_chunk(
        "Highly confidential annual leave policy."
    )

    vector_store.add_chunks(
        [chunk],
        user_id=USER_A,
    )

    results = vector_store.search_chunks(
        "annual leave",
        user_id=USER_B,
    )

    assert results == []

    document_id = (
        chunk["metadata"]["document_id"]
    )

    deleted_by_b = (
        vector_store.delete_document(
            document_id,
            user_id=USER_B,
        )
    )

    assert deleted_by_b == 0

    assert vector_store.count_chunks(
        user_id=USER_A
    ) == 1

    deleted_by_a = (
        vector_store.delete_document(
            document_id,
            user_id=USER_A,
        )
    )

    assert deleted_by_a == 1

    assert vector_store.count_chunks(
        user_id=USER_A
    ) == 0


def test_supplied_metadata_cannot_spoof_owner(
    vector_store,
):
    chunk = sample_chunk()

    # Attempt to supply another user's identity.
    chunk["metadata"]["user_id"] = USER_B

    vector_store.add_chunks(
        [chunk],
        user_id=USER_A,
    )

    assert vector_store.count_chunks(
        user_id=USER_A
    ) == 1

    assert vector_store.count_chunks(
        user_id=USER_B
    ) == 0


def test_legacy_unowned_chunks_are_invisible(
    vector_store,
):
    chunk = sample_chunk()

    # Simulate a document indexed before JWT support.
    vector_store.collection.add(
        ids=[
            chunk["id"]
        ],
        documents=[
            chunk["text"]
        ],
        embeddings=[
            [0.1] * 384
        ],
        metadatas=[
            chunk["metadata"]
        ],
    )

    assert vector_store.count_chunks(
        user_id=USER_A
    ) == 0

    assert vector_store.search_chunks(
        "annual leave",
        user_id=USER_A,
    ) == []

    assert vector_store.delete_document(
        chunk["metadata"]["document_id"],
        user_id=USER_A,
    ) == 0


def test_owner_required(vector_store):
    chunk = sample_chunk()

    with pytest.raises(
        ValueError,
        match="user_id",
    ):
        vector_store.add_chunks(
            [chunk],
            user_id="",
        )

    with pytest.raises(
        ValueError,
        match="user_id",
    ):
        vector_store.search_chunks(
            "annual leave"
        )

    with pytest.raises(
        ValueError,
        match="user_id",
    ):
        vector_store.delete_document(
            chunk["metadata"]["document_id"],
            "",
        )

    with pytest.raises(
        ValueError,
        match="user_id",
    ):
        vector_store.count_chunks(
            ""
        )
