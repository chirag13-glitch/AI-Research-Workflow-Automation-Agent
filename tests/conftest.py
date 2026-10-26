"""Shared pytest fixtures for async API testing and database setup."""
import os
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

# Force test environment variables before importing app
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ADMIN_API_KEY"] = "admin-secret-key-vault-03"
os.environ["DEFAULT_TEST_USER_KEY"] = "user-secret-key-vault-03"

from backend.config import get_settings
# Clear cache to pick up test settings
get_settings.cache_clear()

from backend.main import app
from backend.db.session import init_db, engine, Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create in-memory SQLite tables and seed test accounts."""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP test client bound to FastAPI application."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def user_headers():
    """Valid test user API key authorization header."""
    return {"Authorization": f"Bearer {os.environ['DEFAULT_TEST_USER_KEY']}"}


@pytest.fixture
def admin_headers():
    """Valid test admin API key authorization header."""
    return {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"}


@pytest.fixture
def invalid_headers():
    """Invalid API key authorization header."""
    return {"Authorization": "Bearer invalid-tampered-key-999"}
