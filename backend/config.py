"""Application configuration using Pydantic Settings."""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for the Research Agent."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "SLURBUILDS Research Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # Offline Demo Mode: operates without paid LLM/Search/LangSmith keys
    DEMO_MODE: bool = True

    # Database connection string (defaults to async SQLite for local/offline)
    DATABASE_URL: str = "sqlite+aiosqlite:///./research_agent.db"

    # Security & API Keys
    SECRET_KEY: str = "insecure-default-change-me-in-production-vault-secret"
    ADMIN_API_KEY: str = "admin-secret-key-vault-03"
    DEFAULT_TEST_USER_KEY: str = "user-secret-key-vault-03"

    # Provider-neutral OpenAI-compatible LLM
    OPENAI_API_KEY: Optional[str] = "sk-placeholder"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # Search Provider (tavily, duckduckgo, mock)
    SEARCH_PROVIDER: str = "mock"
    TAVILY_API_KEY: Optional[str] = None

    # LangSmith Observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "slurbuilds-research-agent"

    # Execution Budgets & Safety Controls
    MAX_TOOL_CALLS_PER_TASK: int = 15
    MAX_SEARCH_RESULTS: int = 5
    FETCH_TIMEOUT_SECONDS: int = 8
    MAX_RETRIES_PER_STAGE: int = 2
    MAX_CONCURRENT_TOOL_CALLS: int = 3
    # Online Sampled Evaluation (Off by default)
    ONLINE_EVAL_ENABLED: bool = False
    ONLINE_EVAL_SAMPLE_RATE: float = 0.05  # 5% of production tasks sampled
    ONLINE_EVAL_COST_CAP_USD: float = 5.0  # Max USD spend limit on online evals
    EVAL_MAX_RUN_CASES: int = 40           # Bound evaluation batch size


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
