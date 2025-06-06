"""
GreenLightPA - Realtime Prior Authorization Navigator
Main FastAPI application entry point
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import get_database
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting GreenLightPA application...")
    yield
    logger.info("Shutting down GreenLightPA application...")

# Create FastAPI app
app = FastAPI(
    title="GreenLightPA API",
    description="Realtime Prior Authorization Navigator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GreenLightPA - Realtime Prior Authorization Navigator",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(db = Depends(get_database)):
    """Health check endpoint"""
    try:
        # Test database connection
        await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        } 