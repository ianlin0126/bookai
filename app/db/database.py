from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bookai")

# Convert URL format if needed (for Railway)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Ensure we're using the asyncpg driver
if "sqlite" in DATABASE_URL:
    raise ValueError("SQLite is not supported. Please use PostgreSQL with asyncpg driver.")

if "postgresql" not in DATABASE_URL:
    raise ValueError("Only PostgreSQL is supported. Please check your DATABASE_URL.")

logger.info(f"Using database URL: {DATABASE_URL}")

# Create engine with appropriate settings
engine_kwargs = {
    "echo": True,
    "pool_size": 20,
    "max_overflow": 10
}

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
