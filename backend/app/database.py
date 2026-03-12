from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# Use NullPool in test to avoid "attached to a different loop" when TestClient
# and pytest-asyncio tests share the process (different event loops).
_engine_kw: dict = {
    "echo": settings.log_level == "DEBUG",
    "connect_args": {"timeout": settings.db_connect_timeout},
}
if settings.environment == "test":
    _engine_kw["poolclass"] = NullPool
else:
    _engine_kw["pool_size"] = 20
    _engine_kw["max_overflow"] = 10
    _engine_kw["pool_timeout"] = settings.db_pool_timeout

engine = create_async_engine(settings.database_url, **_engine_kw)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
