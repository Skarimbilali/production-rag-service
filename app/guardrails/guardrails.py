
import re

from app.core.logger import AppLogger


logger = AppLogger.get_logger(__name__)


class GuardrailService:
    """
    Centralized security checks for RAG questions.

    Responsibilities:
        1. Reject empty questions.
        2. Reject overly long questions.
        3. Detect common prompt-injection patterns.
        4. Detect common jailbreak attempts.

    Pattern-based detection is a baseline defense.
    It cannot detect every malicious question.
    """

    MAX_QUESTION_LENGTH = 2000

    BLOCKED_PATTERNS = [
        r"ignore (all |your )?(previous|prior) instructions",
        r"reveal (your |the )?(system prompt|hidden instructions)",
        r"show (me )?(your |the )?(api key|secret key)",
        r"bypass (your |the )?(safety|security|guardrails)",
        r"developer mode",
        r"jailbreak",
        r"forget (all |your )?(instructions|rules)",
    ]

    @classmethod
    def validate_question(cls, question: str) -> str:
        """
        Validate question content before retrieval.

        Returns:
            Normalized question.

        Raises:
            ValueError: Empty, overly long or blocked question.
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

        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, question, re.IGNORECASE):
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
        Apply basic security checks to an LLM-generated answer.

        This is a defense-in-depth check, not a complete
        secret detection or prompt-injection solution.
        """
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("LLM answer cannot be empty.")

        answer = answer.strip()

        blocked_output_patterns = [
            r"security guardrails are disabled",
            r"ignore all previous instructions",
            r"important system override",
            r"sk-proj-[A-Za-z0-9_-]{10,}",
            r"gsk_[A-Za-z0-9]{10,}",
        ]

        for pattern in blocked_output_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                logger.warning("Unsafe LLM output detected")
                raise ValueError("LLM output violates security rules.")

        return answer
