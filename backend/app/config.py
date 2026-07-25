from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "SkinSpect"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Default to False for production
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()