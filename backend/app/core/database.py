"""
Database configuration and session management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    poolclass=NullPool,
)


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """
    Get database session directly (for Celery tasks)
    """
    async with AsyncSessionLocal() as session:
        return session
