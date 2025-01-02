from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "BookDigest.ai"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str
    REDIS_URL: str
    
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    
    AMAZON_AFFILIATE_ID: str
    
    # Add optional settings
    DEBUG: Optional[bool] = False
    LOG_LEVEL: Optional[str] = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
