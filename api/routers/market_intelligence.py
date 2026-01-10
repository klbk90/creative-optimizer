"""
Market Intelligence Router - импорт данных из Facebook Ads Library.

Endpoints для загрузки РЕАЛЬНЫХ market benchmarks из:
- Facebook Ads Library
- TikTok Ads (будущее)
- YouTube Ads (будущее)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os

from database.base import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/market", tags=["Market Intelligence"])


# ========== SCHEMAS ==========

class FacebookImportRequest(BaseModel):
    """Request to import from Facebook Ads Library."""
    search_terms: str
    ad_reached_countries: str = "US"
    limit: int = 10
    analyze_with_claude: bool = False  # Use Claude Vision to analyze videos


class ImportStatusResponse(BaseModel):
    """Import status response."""
    job_id: str
    status: str  # pending, running, completed, failed
    message: str
    total_found: Optional[int] = None
    successfully_ingested: Optional[int] = None
    failed: Optional[int] = None


# ========== ENDPOINTS ==========

@router.post("/import/facebook-ads", response_model=ImportStatusResponse)
async def import_from_facebook_ads(
    request: FacebookImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    🔥 Import REAL market benchmarks from Facebook Ads Library.

    This endpoint:
    1. Searches Facebook Ads Library for successful ads
    2. Estimates CVR from ad longevity and spend
    3. Downloads videos (optional)
    4. Analyzes with Claude Vision (optional)
    5. Ingests into database with Bayesian Priors

    **Requirements:**
    - FACEBOOK_ACCESS_TOKEN environment variable
    - FACEBOOK_APP_ID environment variable

    **Get Facebook Token:**
    1. Go to https://developers.facebook.com/tools/accesstoken/
    2. Create a Facebook App
    3. Get User Access Token
    4. Add to environment: FACEBOOK_ACCESS_TOKEN=your_token

    Example:
    ```json
    {
      "search_terms": "language learning app",
      "ad_reached_countries": "US",
      "limit": 10,
      "analyze_with_claude": false
    }
    ```

    Returns:
    ```json
    {
      "job_id": "uuid-123",
      "status": "running",
      "message": "Importing Facebook ads in background..."
    }
    ```
    """

    # Check if Facebook token is set
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    if not fb_token:
        logger.warning("⚠️ FACEBOOK_ACCESS_TOKEN not set. Using MOCK data for demo.")

    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())

    # Run import in background
    from scripts.facebook_ads_parser import parse_and_ingest_facebook_ads

    def run_import():
        try:
            logger.info(f"🚀 Starting Facebook import job {job_id}")
            result = parse_and_ingest_facebook_ads(
                search_terms=request.search_terms,
                ad_reached_countries=request.ad_reached_countries,
                limit=request.limit,
                analyze_with_claude=request.analyze_with_claude
            )
            logger.info(f"✅ Job {job_id} completed: {result}")
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")

    background_tasks.add_task(run_import)

    return ImportStatusResponse(
        job_id=job_id,
        status="running",
        message=f"✅ Importing Facebook ads for '{request.search_terms}' in background. Check logs for progress."
    )


@router.post("/import/facebook-ads/sync", response_model=ImportStatusResponse)
async def import_from_facebook_ads_sync(
    request: FacebookImportRequest,
    db: Session = Depends(get_db)
):
    """
    🔥 Import from Facebook Ads Library (SYNCHRONOUS).

    Same as /import/facebook-ads but waits for completion.
    Use this for testing or small imports (<5 ads).

    Example:
    ```json
    {
      "search_terms": "EdTech learning",
      "limit": 3
    }
    ```
    """
    import uuid
    job_id = str(uuid.uuid4())

    try:
        from scripts.facebook_ads_parser import parse_and_ingest_facebook_ads

        logger.info(f"🚀 Starting sync Facebook import {job_id}")

        result = parse_and_ingest_facebook_ads(
            search_terms=request.search_terms,
            ad_reached_countries=request.ad_reached_countries,
            limit=request.limit,
            analyze_with_claude=request.analyze_with_claude
        )

        return ImportStatusResponse(
            job_id=job_id,
            status="completed",
            message=result.get("message", "Completed"),
            total_found=result.get("total_found"),
            successfully_ingested=result.get("successfully_ingested"),
            failed=result.get("failed")
        )

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_market_intelligence_status(db: Session = Depends(get_db)):
    """
    📊 Get Market Intelligence status.

    Returns:
    - Total benchmarks in database
    - Sources (Facebook, TikTok, etc.)
    - Last import date
    - Facebook API status
    """
    from database.models import Creative, PatternPerformance

    # Count benchmarks
    total_benchmarks = db.query(Creative).filter(
        Creative.is_benchmark == True
    ).count()

    total_patterns = db.query(PatternPerformance).filter(
        PatternPerformance.source == 'benchmark'
    ).count()

    # Check Facebook API
    fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    fb_api_status = "configured" if fb_token else "not_configured"

    return {
        "total_benchmarks": total_benchmarks,
        "total_patterns": total_patterns,
        "sources": {
            "facebook_ads_library": {
                "status": fb_api_status,
                "note": "Set FACEBOOK_ACCESS_TOKEN to enable real imports"
            },
            "tiktok_ads": {
                "status": "not_implemented",
                "note": "Coming soon"
            }
        },
        "mock_mode": not fb_token,
        "message": "✅ Market Intelligence module ready" if fb_token else "⚠️ Using MOCK data (set FACEBOOK_ACCESS_TOKEN for real data)"
    }


@router.delete("/clear-seed-data")
async def clear_seed_data(db: Session = Depends(get_db)):
    """
    🗑️ Clear SEED benchmark data from database.

    This removes all fake/demo patterns created by seed_benchmarks.py.
    Use this before importing REAL Facebook data.

    Returns count of deleted records.
    """
    from database.models import PatternPerformance, Creative
    import uuid

    # System user ID (used for seed data)
    SYSTEM_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')

    try:
        # Delete patterns
        deleted_patterns = db.query(PatternPerformance).filter(
            PatternPerformance.user_id == SYSTEM_USER_ID,
            PatternPerformance.source == 'client'  # Seed data has source='client'
        ).delete()

        # Delete creatives (keep benchmarks from real imports)
        deleted_creatives = db.query(Creative).filter(
            Creative.user_id == SYSTEM_USER_ID,
            Creative.is_benchmark == False  # Only delete non-benchmark test data
        ).delete()

        db.commit()

        logger.info(f"🗑️ Deleted {deleted_patterns} seed patterns and {deleted_creatives} test creatives")

        return {
            "success": True,
            "deleted_patterns": deleted_patterns,
            "deleted_creatives": deleted_creatives,
            "message": f"✅ Cleared seed data. Database ready for real Facebook imports."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to clear seed data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
