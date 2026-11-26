
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    All secrets are loaded from environment variables.
    Never hardcode API keys or JWT secrets.
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

    # JWT authentication settings
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 15
    JWT_REFRESH_TOKEN_DAYS: int = 7

    # SQLite authentication storage
    AUTH_DATABASE_PATH: str = "data/auth.db"

    # Session cookie configuration
    AUTH_COOKIE_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
