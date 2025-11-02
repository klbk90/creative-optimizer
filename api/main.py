"""
FastAPI main application for TG Reposter SaaS.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from database.base import init_db
from cache import get_redis
from queue import get_queue
from utils.logger import setup_logger

# Import routers
from api.routers import auth, utm, analytics, landing
# from api.routers import channels, posts, billing

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Runs on startup and shutdown.
    """
    # Startup
    logger.info("🚀 Starting TG Reposter API...")

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Check Redis connection
    redis = get_redis()
    if redis.client:
        logger.info("✅ Redis connected")
    else:
        logger.warning("⚠️ Redis connection failed - continuing without cache")

    # Check Queue connection
    queue = get_queue()
    if queue.client:
        logger.info("✅ Task queue connected")
    else:
        logger.warning("⚠️ Task queue connection failed")

    logger.info("✅ API started successfully")

    yield

    # Shutdown
    logger.info("👋 Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="TG Reposter API",
    description="SaaS API for managing Telegram channel reposter",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Log
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"time={process_time:.3f}s"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    redis = get_redis()
    queue = get_queue()

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "database": "up",  # If we got here, DB is up
            "redis": "up" if redis.client else "down",
            "queue": "up" if queue.client else "down",
        },
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        API info
    """
    return {
        "name": "TG Reposter API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(utm.router, prefix="/api/v1/utm", tags=["UTM Tracking"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(landing.router, prefix="/api/v1/landing", tags=["Landing Pages"])
# app.include_router(channels.router, prefix="/api/v1/channels", tags=["Channels"])
# app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
# app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development mode
        log_level="info",
    )
