
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    All secrets are loaded from environment variables.
    Never hardcode API keys in Python files.
    """

    # FastAPI application settings
    APP_NAME: str = "Production RAG Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Groq LLM settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT: float = 30.0
    GROQ_MAX_RETRIES: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
