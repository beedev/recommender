"""
SQLAlchemy database configuration for authentication system.

Provides SQLAlchemy async session management for user authentication
and profile management functionality.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class SQLAlchemyManager:
    """SQLAlchemy database session manager."""
    
    def __init__(self):
        """Initialize SQLAlchemy manager."""
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    def init_db(self):
        """Initialize SQLAlchemy engine and session factory."""
        if self._initialized:
            return
        
        # Create async database URL
        database_url = (
            f"postgresql+asyncpg://{self.settings.POSTGRES_USER}:"
            f"{self.settings.POSTGRES_PASSWORD}@{self.settings.POSTGRES_HOST}:"
            f"{self.settings.POSTGRES_PORT}/{self.settings.POSTGRES_DB}"
        )
        
        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=self.settings.DEBUG,
            poolclass=NullPool,  # Use NullPool to avoid connection pool conflicts
            future=True
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        self._initialized = True
        logger.info("SQLAlchemy database engine initialized")
    
    async def close(self):
        """Close SQLAlchemy engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("SQLAlchemy engine disposed")

# Global SQLAlchemy manager instance
sqlalchemy_manager = SQLAlchemyManager()

def init_sqlalchemy():
    """Initialize SQLAlchemy database engine."""
    sqlalchemy_manager.init_db()

async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting PostgreSQL session.
    
    Yields:
        SQLAlchemy async session
    """
    if not sqlalchemy_manager._initialized:
        sqlalchemy_manager.init_db()
    
    async with sqlalchemy_manager.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_sqlalchemy():
    """Close SQLAlchemy connections."""
    await sqlalchemy_manager.close()