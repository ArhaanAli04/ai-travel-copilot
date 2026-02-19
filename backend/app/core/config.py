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

    # Background Job Scheduling (Day 28)
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"
    
    # OSM Ingestion Schedule (monthly on 1st at 2 AM)
    OSM_INGESTION_CRON_DAY: int = 1
    OSM_INGESTION_CRON_HOUR: int = 2
    OSM_INGESTION_CRON_MINUTE: int = 0
    OSM_INGESTION_CITIES: str = "mumbai,goa,delhi"
    
    # RSS/Blog Ingestion Schedule (weekly on Sunday at 3 AM)
    RSS_INGESTION_CRON_DAY_OF_WEEK: str = "sun"
    RSS_INGESTION_CRON_HOUR: int = 3
    RSS_INGESTION_CRON_MINUTE: int = 0
    RSS_INGESTION_CITIES: str = "mumbai,goa,delhi"
    RSS_INGESTION_DAYS_BACK: int = 7

    # Storage Thresholds
    STORAGE_ALERT_THRESHOLD_MB: float = 850.0  # Alert at 850 MB (85% of 1GB)
    STORAGE_CRITICAL_THRESHOLD_MB: float = 950.0  # Critical at 950 MB (95%)
    
    # Alert Recipients (comma-separated emails)
    ALERT_EMAIL_RECIPIENTS: str = ""  # e.g., "admin@example.com,dev@example.com"
    
    # Webhook for alerts (optional)
    ALERT_WEBHOOK_URL: Optional[str] = None
    
    # Enable/disable alerts
    ALERTS_ENABLED: bool = True

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
    
    @property
    def osm_cities_list(self) -> List[str]:
        """Parse OSM_INGESTION_CITIES into a list"""
        return [city.strip() for city in self.OSM_INGESTION_CITIES.split(",")]
    
    @property
    def rss_cities_list(self) -> List[str]:
        """Parse RSS_INGESTION_CITIES into a list"""
        return [city.strip() for city in self.RSS_INGESTION_CITIES.split(",")]
    
    @property
    def alert_recipients_list(self) -> List[str]:
        """Parse alert email recipients into a list"""
        if not self.ALERT_EMAIL_RECIPIENTS:
            return []
        return [email.strip() for email in self.ALERT_EMAIL_RECIPIENTS.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
