import os
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse

# Load .env file FIRST before any other imports that might use env vars
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker


def build_test_database_url() -> str:
    """Build test database URL from environment variables.
    
    Priority:
    1. TEST_PG_DSN - full test database DSN
    2. PG_DSN with database name replaced to test database
    3. Individual TEST_PG_* or PG_* environment variables
    4. Default localhost connection
    """
    # Option 1: Direct test DSN
    if dsn := os.getenv("TEST_PG_DSN"):
        return dsn
    
    # Option 2: Use main PG_DSN and replace database name
    if main_dsn := os.getenv("PG_DSN"):
        parsed = urlparse(main_dsn)
        test_db = os.getenv("TEST_PG_DB", "shorakka_test")
        # Replace the database name in the path
        test_dsn = urlunparse(parsed._replace(path=f"/{test_db}"))
        return test_dsn
    
    # Option 3: Build from individual components
    user = os.getenv("TEST_PG_USER", os.getenv("PG_USER", "postgres"))
    password = os.getenv("TEST_PG_PASSWORD", os.getenv("PG_PASSWORD", "postgres"))
    host = os.getenv("TEST_PG_HOST", os.getenv("PG_HOST", "localhost"))
    port = os.getenv("TEST_PG_PORT", os.getenv("PG_PORT", "5432"))
    db = os.getenv("TEST_PG_DB", "shorakka_test")
    
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


TEST_DATABASE_URL = build_test_database_url()
os.environ.setdefault("PG_DSN", TEST_DATABASE_URL)

from app.main import app
from app.db.session import get_session
from app.db.models import URL, URLVisit, URLDailyStat


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test DB engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=None,
    )
    
    async with engine.begin() as conn:
        from app.db.models import SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        from app.db.models import SQLModel
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Get a test DB session."""
    async_session_maker = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        await cleanup_tables(session)
        
        yield session
        
        await cleanup_tables(session)
        await session.close()


async def cleanup_tables(session: AsyncSession) -> None:
    """Clear all tables."""
    await session.exec(text("TRUNCATE url_visits CASCADE"))
    await session.exec(text("TRUNCATE url_daily_stats CASCADE"))
    await session.exec(text("TRUNCATE urls CASCADE"))
    await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with test session override."""
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()
