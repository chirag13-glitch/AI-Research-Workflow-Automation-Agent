"""Async database connection and session management."""
import hashlib
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.config import get_settings
from backend.models.orm import Base, User, ApiKey

settings = get_settings()

# Engine creation with connection pooling args appropriate for db driver
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def hash_key(raw_key: str) -> str:
    """Deterministic SHA-256 hash of API key for storage."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def init_db() -> None:
    """Initialize database tables and seed default users if not present."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default user and admin
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        admin_key_hash = hash_key(settings.ADMIN_API_KEY)
        user_key_hash = hash_key(settings.DEFAULT_TEST_USER_KEY)

        admin = await session.get(User, "usr-admin-01")
        if not admin:
            admin = User(
                id="usr-admin-01",
                username="admin",
                email="admin@slurbuilds.ai",
                is_admin=True,
                is_active=True,
            )
            session.add(admin)
            admin_key = ApiKey(
                id="key-admin-01",
                key_hash=admin_key_hash,
                prefix=settings.ADMIN_API_KEY[:8],
                user_id="usr-admin-01",
                name="System Admin Key",
                is_active=True,
            )
            session.add(admin_key)

        test_user = await session.get(User, "usr-demo-01")
        if not test_user:
            test_user = User(
                id="usr-demo-01",
                username="demouser",
                email="demo@slurbuilds.ai",
                is_admin=False,
                is_active=True,
            )
            session.add(test_user)
            test_user_key = ApiKey(
                id="key-demo-01",
                key_hash=user_key_hash,
                prefix=settings.DEFAULT_TEST_USER_KEY[:8],
                user_id="usr-demo-01",
                name="Default User Key",
                is_active=True,
            )
            session.add(test_user_key)

        await session.commit()
