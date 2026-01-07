from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG   # Log SQL queries in debug mode
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Dependency that provides a database session.
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Test database connection
def test_connection():
    """
    Test PostgreSQL connection
    """
    try:
        with engine.connect() as conn:
            logger.info("✅ PostgreSQL connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False
