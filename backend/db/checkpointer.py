"""LangGraph checkpointer factory supporting PostgreSQL and in-memory/SQLite."""
from typing import Any
from langgraph.checkpoint.memory import MemorySaver
from backend.config import get_settings

settings = get_settings()

_memory_saver = MemorySaver()


def get_checkpointer():
    """
    Return appropriate checkpointer for LangGraph state persistence.
    Uses AsyncPostgresSaver when connected to PostgreSQL in production,
    or MemorySaver in SQLite/Demo mode.
    """
    if not settings.DEMO_MODE and "postgresql" in settings.DATABASE_URL:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg_pool import AsyncConnectionPool

            # Normalize asyncpg URL to standard postgresql URI for psycopg
            pg_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            pool = AsyncConnectionPool(conninfo=pg_url, max_size=10)
            return AsyncPostgresSaver(pool)
        except Exception:
            # Fallback to MemorySaver if connection pool fails to initialize
            return _memory_saver

    return _memory_saver
