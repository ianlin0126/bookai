from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bookai")

# Debug log to see what URL we're getting (mask sensitive parts)
debug_url = DATABASE_URL
if debug_url:
    # Mask username/password if present
    parts = debug_url.split("@")
    if len(parts) > 1:
        masked_credentials = "****:****"
        debug_url = f"{masked_credentials}@{parts[1]}"
logger.error(f"Database URL (masked): {debug_url}")  # Using error level for visibility in Railway logs

# Convert URL format if needed (for Railway)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    logger.error(f"Converted Database URL (masked): {debug_url}")

# Ensure we're using the asyncpg driver
if "sqlite" in DATABASE_URL:
    raise ValueError(f"SQLite is not supported. Please use PostgreSQL with asyncpg driver. Current URL type: {DATABASE_URL.split('://')[0]}")

if "postgresql" not in DATABASE_URL:
    raise ValueError(f"Only PostgreSQL is supported. Please check your DATABASE_URL. Current URL type: {DATABASE_URL.split('://')[0]}")

logger.info(f"Using database URL: {debug_url}")

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
