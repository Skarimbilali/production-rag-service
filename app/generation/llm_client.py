
from typing import Any

from groq import AsyncGroq, APIConnectionError, APIStatusError

from app.config import settings
from app.core.logger import AppLogger


logger = AppLogger.get_logger(__name__)


class GroqLLMClient:
    """
    Reusable asynchronous LLM client for the RAG service.

    Responsibilities:
        1. Connect to the Groq API securely.
        2. Send system and user messages.
        3. Request JSON-formatted responses.
        4. Apply timeout and retry settings.
        5. Log successful calls and failures.

    The API key is loaded from environment variables.
    """

    def __init__(self) -> None:
        """Initialize the Groq client using application settings."""

        if not settings.GROQ_API_KEY.strip():
            raise ValueError(
                "GROQ_API_KEY is missing. Configure it in .env."
            )

        self.client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            timeout=settings.GROQ_TIMEOUT,
            max_retries=settings.GROQ_MAX_RETRIES,
        )

        self.model = settings.GROQ_MODEL

        logger.info(
            "Groq LLM client configured | model=%s",
            self.model
        )

    async def generate(
        self,
        messages: list[dict[str, str]]
    ) -> str:
        """
        Generate an answer from the Groq LLM.

        Args:
            messages: System and user messages prepared
                      by GenerationService.

        Returns:
            JSON response text produced by the LLM.

        Raises:
            Connection and API errors for upstream handling.
        """
        if not messages:
            raise ValueError("LLM messages cannot be empty.")

        try:
            logger.info("Groq LLM request started")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1024,
            )

            if not response.choices:
                raise ValueError("LLM returned no choices.")

            content = response.choices[0].message.content

            if not content:
                raise ValueError("LLM returned empty content.")

            logger.info(
                "Groq LLM request completed successfully"
            )

            return content

        except APIConnectionError:
            logger.exception("Groq connection or timeout error")
            raise

        except APIStatusError as exc:
            logger.error(
                "Groq API request failed | status=%s",
                exc.status_code
            )
            raise

        except Exception:
            logger.exception("Unexpected LLM generation failure")
            raise

    async def close(self) -> None:
        """Close the underlying asynchronous HTTP client."""
        await self.client.close()
