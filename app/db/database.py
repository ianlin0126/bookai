from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
import urllib.parse
import ssl

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Ensure we see the logs

# Get database URL and environment from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bookai")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Debug log to see what URL we're getting (mask sensitive parts)
debug_url = DATABASE_URL
if debug_url:
    # Parse the URL to mask sensitive parts but show host/port
    try:
        parsed = urllib.parse.urlparse(debug_url)
        masked_url = f"{parsed.scheme}://****:****@{parsed.hostname}:{parsed.port}{parsed.path}"
        logger.info(f"Initial Database URL (masked): {masked_url}")
    except Exception as e:
        logger.error(f"Error parsing DATABASE_URL: {str(e)}")

# Convert URL format if needed (for Railway)
if DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
    # Extract all parts of the URL
    parsed = urllib.parse.urlparse(DATABASE_URL)
    if parsed.scheme in ["postgres", "postgresql"]:
        # Reconstruct the URL with asyncpg driver
        DATABASE_URL = (
            f"postgresql+asyncpg://{parsed.username}:{parsed.password}@"
            f"{parsed.hostname}:{parsed.port}{parsed.path}"
        )
        try:
            masked_url = f"postgresql+asyncpg://****:****@{parsed.hostname}:{parsed.port}{parsed.path}"
            logger.info(f"Converted Database URL (masked): {masked_url}")
        except Exception as e:
            logger.error(f"Error parsing converted DATABASE_URL: {str(e)}")

# Ensure we're using the asyncpg driver
if "sqlite" in DATABASE_URL:
    raise ValueError(f"SQLite is not supported. Please use PostgreSQL with asyncpg driver. Current URL type: {DATABASE_URL.split('://')[0]}")

if "postgresql+asyncpg" not in DATABASE_URL:
    raise ValueError(f"Only PostgreSQL with asyncpg is supported. Please check your DATABASE_URL. Current URL type: {DATABASE_URL.split('://')[0]}")

logger.info(f"Using database URL: {masked_url}")

# Configure SSL context based on environment
engine_kwargs = {
    "echo": True,
    "pool_size": 20,
    "max_overflow": 10,
    "connect_args": {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
}

# Only use SSL in production
if ENVIRONMENT == "production":
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    engine_kwargs["connect_args"]["ssl"] = ssl_context
else:
    # Disable SSL for local development
    engine_kwargs["connect_args"]["ssl"] = False

try:
    engine = create_async_engine(DATABASE_URL, **engine_kwargs)
    logger.info(f"Successfully created database engine (Environment: {ENVIRONMENT})")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

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
