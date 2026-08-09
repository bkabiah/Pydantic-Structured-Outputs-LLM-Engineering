"""Zentrale, typsichere Konfiguration via pydantic-settings.

Werte werden aus Umgebungsvariablen bzw. einer `.env`-Datei geladen.
Siehe `.env.example` für alle verfügbaren Optionen.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Pydantic AI Extraction Service"
    llm_provider: LLMProvider = LLMProvider.MOCK
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-5"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached Settings-Instanz (wird als FastAPI-Dependency genutzt)."""
    return Settings()
