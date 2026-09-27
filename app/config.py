from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PageWise"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    max_upload_mb: int = 10
    max_pages: int = 200
    max_question_chars: int = 2000
    chunk_size: int = 1200
    chunk_overlap: int = 200
    top_k: int = 5
    min_similarity: float = 0.15
    session_ttl_minutes: int = 60
    allowed_origins: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def static_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()
