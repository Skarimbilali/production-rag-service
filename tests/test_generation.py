
import json

import pytest

from app.generation.generator import GenerationService


class FakeLLM:
    """Mock LLM for repeatable tests without Groq API calls."""

    def __init__(self, response: str):
        self.response = response
        self.call_count = 0
        self.last_messages = None

    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        self.call_count += 1
        self.last_messages = messages
        return self.response


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Provide document evidence with valid source metadata."""
    return [
        {
            "id": "document-123-0",
            "text": "Employees receive 20 annual leave days.",
            "metadata": {
                "document_id": "document-123",
                "filename": "policy.pdf",
                "page": 1,
                "chunk_position": 0,
            },
            "similarity_score": 0.92,
        }
    ]


class TestLanguageDetection:
    """Check language selection without calling an LLM."""

    @pytest.mark.parametrize(
        "question",
        [
            "What is the annual leave policy?",
            "How many days of leave are allowed?",
            "What is the company resignation policy?",
        ],
    )
    def test_english_detection(self, question):
        assert (
            GenerationService.detect_question_language(question)
            == "english"
        )

    @pytest.mark.parametrize(
        "question",
        [
            "Employees ko kitni leaves milti hain?",
            "Mujhe policy batao.",
            "Resignation ka notice kitna hoga?",
            "Kya maternity leave allowed hai?",
        ],
    )
    def test_roman_urdu_detection(self, question):
        assert (
            GenerationService.detect_question_language(question)
            == "roman_urdu"
        )


class TestMultilingualAnswers:
    """Verify language instructions and grounded answers."""

    @pytest.mark.asyncio
    async def test_valid_english_answer(self, sample_chunks):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "Employees receive 20 annual leave days.",
                "citations": ["S1"],
            })
        )

        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "How many annual leave days are allowed?",
            sample_chunks,
        )

        assert result["answer"] == (
            "Employees receive 20 annual leave days."
        )
        assert result["retrieved_count"] == 1
        assert len(result["citations"]) == 1
        assert result["citations"][0]["source_id"] == "S1"
        assert result["citations"][0]["chunk_id"] == (
            "document-123-0"
        )
        assert fake_llm.call_count == 1

        user_prompt = fake_llm.last_messages[1]["content"]
        assert "Respond in English" in user_prompt

    @pytest.mark.asyncio
    async def test_roman_urdu_answer(self, sample_chunks):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": (
                    "Employees ko 20 annual leave days milte hain."
                ),
                "citations": ["S1"],
            })
        )

        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "Employees ko kitni annual leaves milti hain?",
            sample_chunks,
        )

        assert "20 annual leave days" in result["answer"]
        assert result["citations"][0]["source_id"] == "S1"
        assert result["retrieved_count"] == 1

        user_prompt = fake_llm.last_messages[1]["content"]
        assert "Respond in natural Roman Urdu" in user_prompt

    @pytest.mark.asyncio
    async def test_source_context_preserved(self, sample_chunks):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "20 working days.",
                "citations": ["S1"],
            })
        )

        service = GenerationService(fake_llm.generate)

        await service.generate_answer(
            "What is the leave entitlement?",
            sample_chunks,
        )

        user_prompt = fake_llm.last_messages[1]["content"]

        assert "<untrusted_document_context>" in user_prompt
        assert "policy.pdf" in user_prompt
        assert "Employees receive 20 annual leave days." in (
            user_prompt
        )


class TestMultilingualRefusals:
    """Verify refusals use the user's detected language."""

    @pytest.mark.asyncio
    async def test_empty_context_english_refusal(self):
        fake_llm = FakeLLM("{}")
        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "What is the company policy?",
            [],
        )

        assert result["answer"] == (
            GenerationService.REFUSAL_MESSAGE
        )
        assert result["citations"] == []
        assert result["retrieved_count"] == 0
        assert fake_llm.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_context_roman_urdu_refusal(self):
        fake_llm = FakeLLM("{}")
        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "Company ki policy kya hai?",
            [],
        )

        assert result["answer"] == (
            GenerationService.ROMAN_URDU_REFUSAL_MESSAGE
        )
        assert result["citations"] == []
        assert result["retrieved_count"] == 0
        assert fake_llm.call_count == 0

    @pytest.mark.asyncio
    async def test_llm_english_insufficient_context(
        self,
        sample_chunks,
    ):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "INSUFFICIENT_CONTEXT",
                "citations": [],
            })
        )

        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "What is the CEO's personal phone number?",
            sample_chunks,
        )

        assert result["answer"] == (
            GenerationService.REFUSAL_MESSAGE
        )
        assert result["citations"] == []
        assert result["retrieved_count"] == 1

    @pytest.mark.asyncio
    async def test_llm_roman_urdu_insufficient_context(
        self,
        sample_chunks,
    ):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "INSUFFICIENT_CONTEXT",
                "citations": [],
            })
        )

        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "CEO ka personal number kya hai?",
            sample_chunks,
        )

        assert result["answer"] == (
            GenerationService.ROMAN_URDU_REFUSAL_MESSAGE
        )
        assert result["citations"] == []
        assert result["retrieved_count"] == 1


class TestGenerationValidation:
    """Preserve existing citation and response validation."""

    @pytest.mark.asyncio
    async def test_fake_citation_rejected(self, sample_chunks):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "Employees receive 20 leave days.",
                "citations": ["S999"],
            })
        )

        service = GenerationService(fake_llm.generate)

        with pytest.raises(ValueError, match="invalid citation"):
            await service.generate_answer(
                "What is the annual leave policy?",
                sample_chunks,
            )

    @pytest.mark.asyncio
    async def test_duplicate_citation_removed(self, sample_chunks):
        fake_llm = FakeLLM(
            json.dumps({
                "answer": "20 annual leave days.",
                "citations": ["S1", "S1"],
            })
        )

        service = GenerationService(fake_llm.generate)

        result = await service.generate_answer(
            "What is the annual leave policy?",
            sample_chunks,
        )

        assert len(result["citations"]) == 1
        assert result["citations"][0]["source_id"] == "S1"

    @pytest.mark.asyncio
    async def test_invalid_llm_json_rejected(self, sample_chunks):
        fake_llm = FakeLLM("This is not valid JSON")
        service = GenerationService(fake_llm.generate)

        with pytest.raises(ValueError, match="invalid JSON"):
            await service.generate_answer(
                "What is the leave policy?",
                sample_chunks,
            )

    @pytest.mark.asyncio
    async def test_empty_question_rejected(self, sample_chunks):
        fake_llm = FakeLLM("{}")
        service = GenerationService(fake_llm.generate)

        with pytest.raises(
            ValueError,
            match="Question cannot be empty",
        ):
            await service.generate_answer("   ", sample_chunks)

        assert fake_llm.call_count == 0
