from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List,Optional


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
    QDRANT_COLLECTION_NAME: str = "travel_guides"
    QDRANT_POLICIES_COLLECTION: str = "travel_policies"

    # AI - Google Gemini
    GEMINI_API_KEY: str

    SERPAPI_KEY: str 

    # Email settings
    RESEND_API_KEY: str
    FROM_EMAIL: str = "onboarding@resend.dev"  # Resend's test email

    AVIATIONSTACK_API_KEY: str  
    TOMORROW_IO_API_KEY: str    

    # Foursquare API
    FOURSQUARE_API_KEY: str

    # Caching (NEW)
    CACHE_TTL_DAYS: int = 30
    CACHE_CHECK_INTERVAL_HOURS: int = 24
    MAX_CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    POLICY_CACHE_TTL_DAYS: int = 90  # Policies expire after 90 days
    POLICY_CHUNK_SIZE: int = 600  # Larger chunks for legal text
    POLICY_CHUNK_OVERLAP: int = 100
    
    # Web Search (NEW)
    WEB_SEARCH_PROVIDER: str = "serpapi"
    MAX_SEARCH_RESULTS: int = 7
    MAX_POLICY_SEARCH_RESULTS: int = 5

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
