
"""
Security guardrails for the Production RAG Service.

Responsibilities:
- Validate user questions.
- Detect common prompt-injection and jailbreak attempts.
- Validate LLM-generated answers.
- Detect common API key leakage patterns.
- Validate extracted PDF/DOCX document text.
- Reduce false positives for educational content.

Pattern matching provides baseline protection only.
It does not guarantee detection of every attack.
"""

import re
import unicodedata

from app.core.logger import AppLogger


logger = AppLogger.get_logger(__name__)


class GuardrailService:
    """Centralized input, output and document security checks."""

    MAX_QUESTION_LENGTH = 2000

    BLOCKED_PATTERNS = [
        r"\bignore\s+(?:all\s+|your\s+|the\s+)?"
        r"(?:previous|prior|above)\s+instructions\b",

        r"\b(?:reveal|display|print|expose)\s+"
        r"(?:your\s+|the\s+)?"
        r"(?:system\s+prompt|hidden\s+instructions|"
        r"developer\s+instructions)\b",

        r"\bshow\s+(?:me\s+)?(?:your\s+|the\s+)?"
        r"(?:api\s+key|secret\s+key|private\s+key)\b",

        r"\b(?:bypass|disable|turn\s+off)\s+"
        r"(?:your\s+|the\s+)?"
        r"(?:safety|security|guardrails|"
        r"safety\s+rules|security\s+rules)\b",

        r"\b(?:enable|activate|enter|switch\s+to)\s+"
        r"developer\s+mode\b",

        r"\b(?:perform|execute|attempt|start)\s+"
        r"(?:a\s+)?jailbreak\b",

        r"\bjailbreak\s+attempt\b",

        r"\bforget\s+(?:all\s+|your\s+|the\s+)?"
        r"(?:instructions|rules)\b",

        r"\b(?:you\s+are\s+now|act\s+as)\s+"
        r"(?:an?\s+)?(?:unrestricted|uncensored)\s+"
        r"(?:assistant|ai|model)\b",
    ]

    BLOCKED_OUTPUT_PATTERNS = [
        r"\bsecurity\s+guardrails\s+are\s+disabled\b",

        r"\bignore\s+all\s+previous\s+instructions\b",

        r"\bimportant\s+system\s+override\b",

        r"\bsk-proj-[A-Za-z0-9_-]{10,}\b",

        r"\bgsk_[A-Za-z0-9_-]{10,}\b",
    ]

    # Additional instructions specifically targeting an
    # assistant while it reads an uploaded document.
    DOCUMENT_INJECTION_PATTERNS = [
        r"\b(?:system|developer)\s+override\s*:",

        r"\b(?:assistant|model|chatbot)\s*[:,]\s*"
        r"(?:ignore|reveal|bypass|forget|disable)\b",

        r"\b(?:when\s+answering|before\s+answering)\s+"
        r"(?:the\s+)?(?:user|question)\s*[:,]?\s*"
        r"(?:ignore|forget|reveal|disclose|bypass)\b",

        r"\b(?:disclose|leak|exfiltrate)\s+"
        r"(?:your\s+|the\s+)?"
        r"(?:api\s+key|secret\s+key|private\s+key)\b",

        r"\b(?:execute|run)\s+"
        r"(?:this\s+)?(?:shell\s+)?command\s*:",
    ]

    _INPUT_REGEX = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in BLOCKED_PATTERNS
    ]

    _OUTPUT_REGEX = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in BLOCKED_OUTPUT_PATTERNS
    ]

    _DOCUMENT_REGEX = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            BLOCKED_PATTERNS + DOCUMENT_INJECTION_PATTERNS
        )
    ]

    @staticmethod
    def _normalize_for_detection(value: str) -> str:
        """
        Normalize text for security detection.

        The original text is not replaced in stored
        documents or returned answers.
        """
        value = unicodedata.normalize("NFKC", value)

        # Remove invisible characters that can split
        # otherwise recognizable malicious instructions.
        value = re.sub(
            r"[\u200b-\u200d\u2060\ufeff]",
            "",
            value,
        )

        # Normalize newlines, tabs and repeated spaces.
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    @classmethod
    def validate_question(cls, question: str) -> str:
        """
        Validate user input before document retrieval.

        Returns:
            Trimmed question.

        Raises:
            ValueError for invalid or blocked input.
        """
        if not isinstance(question, str):
            logger.warning("Non-string question rejected")
            raise ValueError("Question must be a string.")

        question = question.strip()

        if not question:
            logger.warning("Empty question rejected")
            raise ValueError("Question cannot be empty.")

        if len(question) > cls.MAX_QUESTION_LENGTH:
            logger.warning("Overly long question rejected")
            raise ValueError("Question exceeds maximum length.")

        normalized = cls._normalize_for_detection(question)

        if not normalized:
            logger.warning("Invisible-only question rejected")
            raise ValueError("Question cannot be empty.")

        for pattern in cls._INPUT_REGEX:
            if pattern.search(normalized):
                logger.warning(
                    "Potential prompt injection detected"
                )
                raise ValueError(
                    "Question violates security rules."
                )

        logger.info("Question passed input guardrails")

        return question

    @classmethod
    def validate_answer(cls, answer: str) -> str:
        """
        Validate generated LLM output before returning it.

        Returns:
            Trimmed answer.

        Raises:
            ValueError for invalid or blocked output.
        """
        if not isinstance(answer, str):
            logger.warning("Non-string LLM answer rejected")
            raise ValueError("LLM answer cannot be empty.")

        answer = answer.strip()

        if not answer:
            logger.warning("Empty LLM answer rejected")
            raise ValueError("LLM answer cannot be empty.")

        normalized = cls._normalize_for_detection(answer)

        if not normalized:
            logger.warning("Invisible-only LLM answer rejected")
            raise ValueError("LLM answer cannot be empty.")

        for pattern in cls._OUTPUT_REGEX:
            if pattern.search(normalized):
                logger.warning("Unsafe LLM output detected")
                raise ValueError(
                    "LLM output violates security rules."
                )

        return answer

    @classmethod
    def validate_document_text(cls, document_text: str) -> str:
        """
        Check extracted PDF/DOCX text for common
        document-based prompt-injection instructions.

        Call this after text extraction and before
        chunking, embedding or vector storage.

        Returns:
            Trimmed original document text.

        Raises:
            ValueError when text is invalid, empty
            or contains a known malicious pattern.
        """
        if not isinstance(document_text, str):
            logger.warning(
                "Non-string document text rejected"
            )
            raise ValueError(
                "Document text must be a string."
            )

        document_text = document_text.strip()

        if not document_text:
            logger.warning("Empty document text rejected")
            raise ValueError(
                "Document text cannot be empty."
            )

        normalized = cls._normalize_for_detection(
            document_text
        )

        if not normalized:
            logger.warning(
                "Invisible-only document text rejected"
            )
            raise ValueError(
                "Document text cannot be empty."
            )

        for pattern in cls._DOCUMENT_REGEX:
            if pattern.search(normalized):
                logger.warning(
                    "Potential document prompt injection detected"
                )
                raise ValueError(
                    "Document violates security rules."
                )

        logger.info(
            "Document text passed security validation"
        )

        return document_text
