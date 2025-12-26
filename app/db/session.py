from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.setting import settings

_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """Lazily create and return the async engine, erroring clearly if DSN missing."""
    global _engine
    if _engine is None:
        if not settings.PG_DSN:
            raise RuntimeError("PG_DSN is not set. Set PG_DSN or create a .env before accessing the database.")
        _engine = create_async_engine(
            settings.PG_DSN,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
    return _engine


def create_async_session():
    return sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = create_async_session()
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
