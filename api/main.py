"""
FastAPI main application for TG Reposter SaaS.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time

from database.base import init_db
from cache import get_redis
from task_queue import get_queue
from utils.logger import setup_logger

# Import routers
from api.routers import auth, utm, analytics, landing, creative_ml, rudderstack, edtech_landing, landing_pro, pattern_optimization, influencer_search, creative_admin, market_intelligence
# New clean ML router: creative_ml (working!)
# RudderStack integration: rudderstack (Bayesian update!)
# EdTech landing: edtech_landing (NEW - for micro-influencer testing!)
# Premium landing: landing_pro (STYLISH - modern design!)
# Pattern optimization: pattern_optimization (Gap Finder, Uniqueness, Trends!)
# Disabled old buggy routers: creative_mvp, creative_analysis, landing_builder

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

        # Seed benchmark data (only runs if DB is empty)
        try:
            from scripts.seed_benchmarks import seed_benchmarks
            seed_benchmarks()
        except Exception as seed_error:
            logger.warning(f"⚠️ Benchmark seeding skipped: {seed_error}")

        # Seed benchmark videos (FB Ad Library examples)
        try:
            from scripts.seed_benchmark_videos import seed_benchmark_videos
            seed_benchmark_videos()
        except Exception as seed_error:
            logger.warning(f"⚠️ Benchmark videos seeding skipped: {seed_error}")

        # Trigger analysis for benchmark videos (is_benchmark=True)
        try:
            from database.base import SessionLocal
            from database.models import Creative
            from utils.analysis_orchestrator import check_analysis_trigger

            db_session = SessionLocal()
            benchmarks = db_session.query(Creative).filter(
                Creative.is_benchmark == True,
                Creative.analysis_status == 'pending'
            ).all()

            for benchmark in benchmarks:
                logger.info(f"🎯 Triggering analysis for benchmark: {benchmark.name}")
                check_analysis_trigger(benchmark.id, db_session)

            db_session.close()
            logger.info(f"✅ Triggered analysis for {len(benchmarks)} benchmark videos")
        except Exception as analysis_error:
            logger.warning(f"⚠️ Benchmark analysis trigger failed: {analysis_error}")

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
from utils.security import get_cors_origins, get_security_headers

allowed_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and add security headers."""
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

    # Add security headers
    security_headers = get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value

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


# Mount static files (for landing pages)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(utm.router, prefix="/api/v1/utm", tags=["UTM Tracking"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(landing.router, prefix="/api/v1/landing", tags=["Landing Pages"])
app.include_router(landing_pro.router, prefix="/api/v1")  # Premium stylish landing (NO NPM!)
app.include_router(edtech_landing.router, prefix="/api/v1")  # EdTech landing pages
app.include_router(creative_ml.router)  # Clean ML router with Markov Chain + Thompson Sampling
app.include_router(rudderstack.router)  # RudderStack webhook with Bayesian CVR update

# Webhook routes (альтернативный путь для совместимости)
app.include_router(rudderstack.router, prefix="/webhooks", include_in_schema=False)  # /webhooks/rudderstack/track
app.include_router(pattern_optimization.router)  # Pattern optimization (Gap Finder, Uniqueness, Trends)
app.include_router(influencer_search.router)  # Influencer search with Modash + AI scoring
app.include_router(creative_admin.router)  # Creative admin (force analyze, video access with JWT)
app.include_router(market_intelligence.router)  # Market Intelligence (Facebook Ads Library import)
# app.include_router(channels.router, prefix="/api/v1/channels", tags=["Channels"])
# app.include_router(posts.router, prefix="/api/v1/posts", tags=["Posts"])
# app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])


# ==================== PROMETHEUS METRICS ENDPOINT ====================

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Metrics include:
    - utm_clicks_total - Total clicks
    - utm_conversions_total - Total conversions
    - utm_revenue_cents - Revenue in cents
    - creative_cvr - Creative CVR
    - api_request_duration_seconds - API latency
    - cluster_avg_cvr - Cluster performance

    **Usage:**
    Configure Prometheus to scrape this endpoint:
    ```yaml
    scrape_configs:
      - job_name: 'utm-tracking'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
    ```
    """
    from utils.metrics import get_metrics
    from prometheus_client import CONTENT_TYPE_LATEST

    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development mode
        log_level="info",
    )
