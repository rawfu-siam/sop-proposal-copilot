"""Validated runtime settings for the SOP & Proposal Knowledge Copilot."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Centralized configuration loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    openai_api_key: str = Field(..., min_length=1, alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", min_length=1, alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        min_length=1,
        alias="OPENAI_EMBEDDING_MODEL",
    )

    chroma_persist_dir: Path = Field(default=Path("./chroma_db"), alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="sop_proposal_knowledge",
        min_length=1,
        alias="CHROMA_COLLECTION_NAME",
    )

    slack_webhook_url: HttpUrl | None = Field(default=None, alias="SLACK_WEBHOOK_URL")
    n8n_webhook_url: HttpUrl | None = Field(default=None, alias="N8N_WEBHOOK_URL")
    webhook_timeout_seconds: float = Field(
        default=10.0,
        gt=0.0,
        le=120.0,
        alias="WEBHOOK_TIMEOUT_SECONDS",
    )
    webhook_max_retries: int = Field(default=3, ge=0, le=10, alias="WEBHOOK_MAX_RETRIES")

    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )
    log_dir: Path = Field(default=Path("./logs"), alias="LOG_DIR")
    log_file_name: str = Field(default="copilot.log", min_length=1, alias="LOG_FILE_NAME")
    log_max_bytes: int = Field(default=5_242_880, ge=1024, alias="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=5, ge=1, le=50, alias="LOG_BACKUP_COUNT")

    retrieval_top_k: int = Field(default=4, ge=1, le=20, alias="RETRIEVAL_TOP_K")
    confidence_threshold: float = Field(default=0.65, ge=0.0, le=1.0, alias="CONFIDENCE_THRESHOLD")

    @field_validator("openai_api_key")
    @classmethod
    def validate_non_blank_api_key(cls, value: str) -> str:
        """Reject whitespace-only or placeholder-style blank API keys."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("OPENAI_API_KEY must not be blank or whitespace.")
        return stripped

    @field_validator("slack_webhook_url", "n8n_webhook_url", mode="before")
    @classmethod
    def normalize_empty_webhook_url(cls, value: object) -> object:
        """Treat empty strings as unset so optional webhook URLs fail cleanly only if malformed."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def log_file_path(self) -> Path:
        """Return full filesystem path to the active rotating log file."""
        return self.log_dir / self.log_file_name


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached `AppSettings` instance validated against current environment."""
    return AppSettings()
