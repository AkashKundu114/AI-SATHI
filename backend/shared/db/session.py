from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from shared.config.settings import get_settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        s = get_settings()
        if s.database_url.startswith("sqlite"):
            _engine = create_async_engine(s.database_url)
        else:
            _engine = create_async_engine(
                s.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300,
            )
    return _engine


@asynccontextmanager
async def get_db_session():
    async with AsyncSession(get_engine()) as session:
        yield session
