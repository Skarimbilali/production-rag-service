
import json

import pytest

from app.generation.generator import GenerationService


class FakeLLM:
    """
    Mock LLM used for testing without calling Groq.

    This avoids API cost and makes tests reproducible.
    """

    def __init__(self, response: str):
        self.response = response
        self.call_count = 0

    async def generate(self, messages: list[dict[str, str]]) -> str:
        """Return a predefined response instead of calling an API."""
        self.call_count += 1
        return self.response


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Provide a retrieved chunk with valid source metadata."""
    return [
        {
            "id": "document-123-0",
            "text": "Employees receive 20 annual leave days.",
            "metadata": {
                "document_id": "document-123",
                "filename": "policy.pdf",
                "page": 1,
                "chunk_position": 0
            },
            "similarity_score": 0.92
        }
    ]


@pytest.mark.asyncio
async def test_valid_answer_with_citation(sample_chunks):
    """A valid source ID must map to the retrieved chunk."""
    fake_llm = FakeLLM(
        json.dumps({
            "answer": "Employees receive 20 annual leave days.",
            "citations": ["S1"]
        })
    )

    service = GenerationService(fake_llm.generate)

    result = await service.generate_answer(
        "How many annual leave days do employees receive?",
        sample_chunks
    )

    assert result["answer"] == "Employees receive 20 annual leave days."
    assert result["retrieved_count"] == 1
    assert len(result["citations"]) == 1
    assert result["citations"][0]["source_id"] == "S1"
    assert result["citations"][0]["chunk_id"] == "document-123-0"


@pytest.mark.asyncio
async def test_roman_urdu_answer(sample_chunks):
    """Verify a Roman Urdu response can be returned with citations."""
    fake_llm = FakeLLM(
        json.dumps({
            "answer": "Employees ko 20 annual leave days milte hain.",
            "citations": ["S1"]
        })
    )

    service = GenerationService(fake_llm.generate)

    result = await service.generate_answer(
        "Employees ko kitni annual leaves milti hain?",
        sample_chunks
    )

    assert "20 annual leave days" in result["answer"]
    assert result["citations"][0]["source_id"] == "S1"


@pytest.mark.asyncio
async def test_empty_context_refusal():
    """The service must refuse without calling the LLM."""
    fake_llm = FakeLLM("{}")
    service = GenerationService(fake_llm.generate)

    result = await service.generate_answer(
        "What is the company policy?",
        []
    )

    assert result["citations"] == []
    assert result["retrieved_count"] == 0
    assert result["answer"] == GenerationService.REFUSAL_MESSAGE
    assert fake_llm.call_count == 0


@pytest.mark.asyncio
async def test_unanswerable_question(sample_chunks):
    """The LLM can explicitly report insufficient context."""
    fake_llm = FakeLLM(
        json.dumps({
            "answer": "INSUFFICIENT_CONTEXT",
            "citations": []
        })
    )

    service = GenerationService(fake_llm.generate)

    result = await service.generate_answer(
        "What is the CEO's personal phone number?",
        sample_chunks
    )

    assert result["answer"] == GenerationService.REFUSAL_MESSAGE
    assert result["citations"] == []


@pytest.mark.asyncio
async def test_fake_citation_rejected(sample_chunks):
    """An invented source ID must never be accepted."""
    fake_llm = FakeLLM(
        json.dumps({
            "answer": "Employees receive 20 leave days.",
            "citations": ["S999"]
        })
    )

    service = GenerationService(fake_llm.generate)

    with pytest.raises(ValueError, match="invalid citation"):
        await service.generate_answer(
            "What is the annual leave policy?",
            sample_chunks
        )


@pytest.mark.asyncio
async def test_invalid_llm_json_rejected(sample_chunks):
    """Invalid JSON responses must raise a controlled error."""
    fake_llm = FakeLLM("This is not valid JSON")

    service = GenerationService(fake_llm.generate)

    with pytest.raises(ValueError, match="invalid JSON"):
        await service.generate_answer(
            "What is the leave policy?",
            sample_chunks
        )


@pytest.mark.asyncio
async def test_empty_question_rejected(sample_chunks):
    """Empty questions must fail validation."""
    fake_llm = FakeLLM("{}")
    service = GenerationService(fake_llm.generate)

    with pytest.raises(ValueError, match="Question cannot be empty"):
        await service.generate_answer("   ", sample_chunks)

    assert fake_llm.call_count == 0
