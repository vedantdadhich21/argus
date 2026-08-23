"""
config.py — Application settings loaded from .env via pydantic-settings.
All environment variables defined in Reference §5.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


import os
from pathlib import Path

_SERVER_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _SERVER_ROOT / ".env"


class Settings(BaseSettings):
    # Server
    port: int = 8000
    database_url: str = "sqlite:///./sentinel.db"
    storage_dir: str = "./storage"
    max_upload_mb: int = 100
    scan_timeout_seconds: int = 300  # 5 minutes for deep analysis & complex APKs

    # CORS — comma-separated origins in .env, parsed as list
    cors_origins: str = "*"

    # Decompiler
    jadx_path: str = "jadx"

    # LLM (any OpenAI-compatible)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 60  # 60s for LLM JSON response

    llm_max_methods: int = 10
    llm_max_chars_per_method: int = 3000

    # Concurrent scan cap
    max_concurrent_scans: int = 2

    class Config:
        env_file = str(_ENV_PATH)
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS_ORIGINS into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
