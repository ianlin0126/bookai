from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "BookDigest.ai"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings with default for local development
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bookai"
    
    # Optional settings with defaults
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    AMAZON_AFFILIATE_ID: Optional[str] = None
    ADMIN_TOKEN: Optional[str] = None
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
