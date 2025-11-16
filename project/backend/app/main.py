"""
Main FastAPI application for Contract Refund Eligibility System.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_database, check_database_health
from app.schemas.responses import HealthResponse
from app.middleware.error_handling import error_handling_middleware
from app.middleware.logging import request_logging_middleware
from app.api.v1 import contracts, extractions, audit, chat
from app.utils.cache import get_cache_stats, close_redis, get_redis

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")

    # Verify database connectivity (optional - log warning if fails)
    db_healthy = await check_database_health()
    if db_healthy:
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection not available (may not be configured yet)")

    # TODO: Initialize Redis connection
    # TODO: Verify external service connectivity (optional)

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_database()
    logger.info("Database connections closed")
    await close_redis()
    logger.info("Redis connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered contract extraction and review system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(request_logging_middleware)
app.middleware("http")(error_handling_middleware)


# Health check endpoint
@app.get("/health", tags=["Health"], response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancer / monitoring.
    Returns 200 OK if service is running.
    Checks database and Redis connectivity.
    """
    # Check database connection
    db_status = "connected" if await check_database_health() else "disconnected"

    # Check Redis connection
    redis = await get_redis()
    if redis:
        try:
            await redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
    else:
        redis_status = "not_configured"

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        environment=settings.app_env,
        database=db_status,
        redis=redis_status,
    )


# Readiness check endpoint
@app.get("/ready", tags=["Health"], response_model=HealthResponse)
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 OK if service is ready to accept requests (database connected).
    Returns 503 if database is not available.
    """
    # Check database connection
    db_healthy = await check_database_health()
    db_status = "connected" if db_healthy else "disconnected"

    # Check Redis connection
    redis = await get_redis()
    if redis:
        try:
            await redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
    else:
        redis_status = "not_configured"

    # Service is only ready if database is connected
    if not db_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": settings.app_name,
                "environment": settings.app_env,
                "database": db_status,
                "redis": redis_status,
                "message": "Database connection not available",
            },
        )

    return HealthResponse(
        status="ready",
        service=settings.app_name,
        environment=settings.app_env,
        database=db_status,
        redis=redis_status,
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - provides API information.
    """
    return {
        "message": "Contract Refund Eligibility System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "cache_stats": "/cache/stats",
    }


# Cache statistics endpoint
@app.get("/cache/stats", tags=["Cache"])
async def cache_statistics():
    """
    Get cache statistics including hit rate.
    """
    stats = get_cache_stats()
    return {"cache_stats": stats, "message": "Cache statistics (hits, misses, errors, hit_rate)"}


# Include API routers
app.include_router(contracts.router, prefix=settings.api_v1_prefix, tags=["Contracts"])
app.include_router(extractions.router, prefix=settings.api_v1_prefix, tags=["Extractions"])
app.include_router(audit.router, prefix=settings.api_v1_prefix, tags=["Audit"])
app.include_router(chat.router, prefix=settings.api_v1_prefix, tags=["Chat"])

# TODO: Include remaining routers (Day 11+)
# from app.api.v1 import admin
# app.include_router(admin.router, prefix=settings.api_v1_prefix, tags=["Admin"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development(),
        log_level=settings.log_level.lower(),
    )
