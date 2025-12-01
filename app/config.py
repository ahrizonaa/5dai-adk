"""Application configuration."""

import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class Settings:
    """Application settings from environment variables."""

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    PORT: int = int(os.getenv("PORT", "7020"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_TRACING: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"

    @property
    def is_configured(self) -> bool:
        return bool(self.GOOGLE_API_KEY)

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
setup_logging(settings.LOG_LEVEL)
