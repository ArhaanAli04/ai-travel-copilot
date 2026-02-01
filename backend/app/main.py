from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
# Configure logging FIRST, before any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Disable SQLAlchemy verbose logging IMMEDIATELY
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

# Keep your app logs at INFO level
logging.getLogger("app").setLevel(logging.INFO)

from app.core.config import settings
from app.core.postgres import test_connection as test_postgres
from app.core.mongo import connect_to_mongo, close_mongo_connection
from app.core.qdrant import connect_to_qdrant
from app.api import planner,flights,guides,disruptions,admin,local_discovery,chat


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered travel planning copilot with planner, disruption handling, local discovery, and safety features",
    version="0.1.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(planner.router, prefix="/api")
app.include_router(flights.router, prefix="/api")
app.include_router(guides.router, prefix="/api")
app.include_router(disruptions.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(local_discovery.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENV,
        "version": "0.1.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"📝 Environment: {settings.ENV}")
    
    # Test PostgreSQL
    test_postgres()
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Connect to Qdrant
    connect_to_qdrant()
    
    logger.info(f"📚 API Docs: http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")
    await close_mongo_connection()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False
    )
