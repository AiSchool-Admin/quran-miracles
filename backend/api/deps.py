"""Shared dependencies for API routes."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Look for .env in both backend/ and project root
_ENV_FILES = [
    Path(__file__).resolve().parent.parent / ".env",        # backend/.env
    Path(__file__).resolve().parent.parent.parent / ".env",  # project root .env
]
_ENV_FILE = next((f for f in _ENV_FILES if f.exists()), ".env")


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/quran_miracles"
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    model_config = {"env_file": str(_ENV_FILE)}


@lru_cache
def get_settings() -> Settings:
    return Settings()
