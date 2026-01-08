from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Application
    APP_NAME: str = "AI Travel Copilot"
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database - PostgreSQL
    DATABASE_URL: str
    
    # Database - MongoDB
    MONGODB_URL: str
    
    # Vector Database - Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str
    
    # AI - Google Gemini
    GEMINI_API_KEY: str

    SERPAPI_KEY: str 
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
