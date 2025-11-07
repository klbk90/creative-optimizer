"""
Creative analysis API endpoints.

Provides endpoints for:
1. Analyzing new creatives (predict performance before launch)
2. Saving creative data with patterns
3. Getting top performing patterns
4. Finding similar creatives (CLIP similarity)
5. Updating pattern performance (Markov Chain training)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from database.base import get_db
from database.models import Creative, CreativePattern, PatternPerformance, TrafficSource
from utils.markov_chain import MarkovChainPredictor
from utils.creative_analyzer import CreativeAnalyzer, analyze_creative_quick
from api.dependencies import get_current_user


router = APIRouter(prefix="/api/v1/creative", tags=["Creative Analysis"])


# ==================== SCHEMAS ====================

class CreativeAnalysisRequest(BaseModel):
    """Request to analyze a creative (before launch)."""

    # Option 1: Provide video
    video_url: Optional[str] = None
    video_path: Optional[str] = None

    # Option 2: Provide patterns manually
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None

    # Option 3: Provide patterns directly (from manual input or previous analysis)
    hook_type: Optional[str] = None
    emotion: Optional[str] = None
    pacing: Optional[str] = None
    cta_type: Optional[str] = None

    # Required: Product category for accurate prediction
    product_category: str = Field(..., description="Product category (e.g., lootbox, sports_betting)")


class CreativeAnalysisResponse(BaseModel):
    """Response from creative analysis."""

    # Extracted patterns
    hook_type: str
    emotion: str
    pacing: str
    cta_type: Optional[str]

    # Additional features
    has_text_overlay: bool = False
    has_voiceover: bool = False
    features: dict = {}

    # Predictions (from Markov Chain)
    predicted_cvr: float
    predicted_cvr_percent: float
    confidence_score: float
    sample_size: int
    confidence_interval: tuple
    confidence_interval_percent: tuple
    prediction_method: str

    # Analysis metadata
    analysis_confidence: float
    reasoning: str


class CreativeCreateRequest(BaseModel):
    """Request to save a creative."""

    name: str
    creative_type: str = Field(..., description="ugc, micro_influencer, studio, spark_ad")
    product_category: str
    source_platform: Optional[str] = "tiktok"

    # Video info
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None

    # Cost tracking
    production_cost: Optional[int] = 0  # in cents
    media_spend: Optional[int] = 0

    # Patterns (from analysis)
    hook_type: Optional[str] = None
    emotion: Optional[str] = None
    pacing: Optional[str] = None
    cta_type: Optional[str] = None
    has_text_overlay: Optional[bool] = False
    has_voiceover: Optional[bool] = False
    features: Optional[dict] = {}

    # Predictions (from Markov Chain)
    predicted_cvr: Optional[int] = None  # * 10000
    predicted_roas: Optional[int] = None  # * 100
    confidence_score: Optional[int] = None  # * 100

    # Testing info
    test_phase: Optional[str] = "micro_test"
    traffic_source_id: Optional[str] = None


class CreativeUpdateRequest(BaseModel):
    """Request to update creative performance."""

    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    revenue: Optional[int] = None  # in cents

    status: Optional[str] = None  # draft, testing, active, paused, archived
    is_winner: Optional[bool] = None


class PatternPerformanceResponse(BaseModel):
    """Top performing patterns."""

    hook_type: Optional[str]
    emotion: Optional[str]
    pacing: Optional[str]
    cta_type: Optional[str]

    avg_cvr: float
    avg_ctr: float
    avg_roas: float

    sample_size: int
    total_conversions: int
    confidence_interval: tuple


# ==================== ENDPOINTS ====================

@router.post("/analyze", response_model=CreativeAnalysisResponse)
def analyze_creative(
    request: CreativeAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a creative and predict performance BEFORE spending money.

    **Use Cases:**
    1. Upload UGC video → Get predicted CVR
    2. Provide caption → Get pattern analysis + prediction
    3. Manually enter patterns → Get prediction from Markov Chain

    **Example:**
    ```json
    {
      "caption": "Wait until the end! 🔥 You won't believe this lootbox opening",
      "hashtags": ["fyp", "gaming", "lootbox"],
      "product_category": "lootbox"
    }
    ```

    **Returns:**
    - Extracted patterns (hook, emotion, pacing, CTA)
    - Predicted CVR with confidence interval
    - Sample size (how many similar creatives tested)
    - Prediction method (exact_match, partial_match, bayesian_estimate)
    """

    user_id = current_user["user_id"]

    # Step 1: Extract patterns
    if request.hook_type and request.emotion and request.pacing:
        # Patterns provided manually
        patterns = {
            "hook_type": request.hook_type,
            "emotion": request.emotion,
            "pacing": request.pacing,
            "cta_type": request.cta_type or "none",
            "has_text_overlay": False,
            "has_voiceover": False,
            "features": {},
            "confidence": 1.0,
            "reasoning": "Patterns provided manually"
        }
    else:
        # Analyze automatically
        try:
            patterns = analyze_creative_quick(
                video_url=request.video_url,
                video_path=request.video_path,
                caption=request.caption,
                hashtags=request.hashtags
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to analyze creative: {str(e)}"
            )

    # Step 2: Predict performance using Markov Chain
    predictor = MarkovChainPredictor(
        db=db,
        user_id=user_id,
        product_category=request.product_category
    )

    prediction = predictor.predict_cvr(
        hook_type=patterns["hook_type"],
        emotion=patterns["emotion"],
        pacing=patterns["pacing"],
        cta_type=patterns.get("cta_type")
    )

    # Step 3: Combine analysis + prediction
    return CreativeAnalysisResponse(
        hook_type=patterns["hook_type"],
        emotion=patterns["emotion"],
        pacing=patterns["pacing"],
        cta_type=patterns.get("cta_type"),
        has_text_overlay=patterns.get("has_text_overlay", False),
        has_voiceover=patterns.get("has_voiceover", False),
        features=patterns.get("features", {}),
        predicted_cvr=prediction["predicted_cvr"],
        predicted_cvr_percent=prediction["predicted_cvr_percent"],
        confidence_score=prediction["confidence_score"],
        sample_size=prediction["sample_size"],
        confidence_interval=prediction["confidence_interval"],
        confidence_interval_percent=prediction["confidence_interval_percent"],
        prediction_method=prediction["prediction_method"],
        analysis_confidence=patterns.get("confidence", 0.0),
        reasoning=patterns.get("reasoning", "")
    )


@router.post("/creatives", status_code=status.HTTP_201_CREATED)
def create_creative(
    request: CreativeCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Save a creative to database.

    **When to use:**
    - After analyzing a creative (save predictions)
    - When starting a test (mark creative as "testing")
    - When uploading UGC videos from Fiverr

    **Example:**
    ```json
    {
      "name": "UGC Lootbox Opening v1",
      "creative_type": "ugc",
      "product_category": "lootbox",
      "video_url": "https://...",
      "production_cost": 5000,
      "hook_type": "wait",
      "emotion": "excitement",
      "pacing": "fast",
      "predicted_cvr": 1200,
      "test_phase": "ugc_test"
    }
    ```
    """

    user_id = current_user["user_id"]

    # Create creative
    creative = Creative(
        user_id=user_id,
        name=request.name,
        creative_type=request.creative_type,
        product_category=request.product_category,
        source_platform=request.source_platform,
        video_url=request.video_url,
        thumbnail_url=request.thumbnail_url,
        duration_seconds=request.duration_seconds,
        production_cost=request.production_cost,
        media_spend=request.media_spend,
        hook_type=request.hook_type,
        emotion=request.emotion,
        pacing=request.pacing,
        cta_type=request.cta_type,
        has_text_overlay=request.has_text_overlay,
        has_voiceover=request.has_voiceover,
        features=request.features or {},
        predicted_cvr=request.predicted_cvr,
        predicted_roas=request.predicted_roas,
        confidence_score=request.confidence_score,
        test_phase=request.test_phase,
        traffic_source_id=request.traffic_source_id,
        status="draft"
    )

    db.add(creative)
    db.commit()
    db.refresh(creative)

    return {
        "creative_id": str(creative.id),
        "message": "Creative saved successfully"
    }


@router.put("/creatives/{creative_id}")
def update_creative_performance(
    creative_id: str,
    request: CreativeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update creative performance metrics.

    **When to use:**
    - After running a test (update clicks, conversions)
    - When marking a creative as winner
    - When pausing/activating a creative

    **Example:**
    ```json
    {
      "impressions": 10000,
      "clicks": 500,
      "conversions": 75,
      "revenue": 375000,
      "status": "active",
      "is_winner": true
    }
    ```
    """

    user_id = current_user["user_id"]

    creative = db.query(Creative).filter(
        Creative.id == creative_id,
        Creative.user_id == user_id
    ).first()

    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )

    # Update fields
    if request.impressions is not None:
        creative.impressions = request.impressions
    if request.clicks is not None:
        creative.clicks = request.clicks
    if request.conversions is not None:
        creative.conversions = request.conversions
    if request.revenue is not None:
        creative.revenue = request.revenue
    if request.status is not None:
        creative.status = request.status
    if request.is_winner is not None:
        creative.is_winner = request.is_winner

    # Calculate metrics
    if creative.clicks and creative.impressions:
        creative.ctr = int((creative.clicks / creative.impressions) * 10000)
    if creative.conversions and creative.clicks:
        creative.cvr = int((creative.conversions / creative.clicks) * 10000)
    if creative.revenue and (creative.production_cost + creative.media_spend):
        creative.roas = int((creative.revenue / (creative.production_cost + creative.media_spend)) * 100)
    if creative.conversions and (creative.production_cost + creative.media_spend):
        creative.cpa = int((creative.production_cost + creative.media_spend) / creative.conversions)

    creative.last_stats_update = datetime.utcnow()

    db.commit()

    return {
        "message": "Creative updated successfully",
        "metrics": {
            "ctr": creative.ctr / 10000,
            "cvr": creative.cvr / 10000,
            "roas": creative.roas / 100,
            "cpa": creative.cpa / 100
        }
    }


@router.get("/creatives")
def list_creatives(
    product_category: Optional[str] = None,
    creative_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all creatives with optional filters.

    **Filters:**
    - product_category: Filter by product (lootbox, sports_betting, etc.)
    - creative_type: Filter by type (ugc, micro_influencer, studio, spark_ad)
    - status: Filter by status (draft, testing, active, paused)
    """

    user_id = current_user["user_id"]

    query = db.query(Creative).filter(Creative.user_id == user_id)

    if product_category:
        query = query.filter(Creative.product_category == product_category)
    if creative_type:
        query = query.filter(Creative.creative_type == creative_type)
    if status:
        query = query.filter(Creative.status == status)

    creatives = query.order_by(Creative.created_at.desc()).limit(limit).all()

    return {
        "creatives": [
            {
                "id": str(c.id),
                "name": c.name,
                "creative_type": c.creative_type,
                "product_category": c.product_category,
                "hook_type": c.hook_type,
                "emotion": c.emotion,
                "pacing": c.pacing,
                "predicted_cvr": c.predicted_cvr / 10000 if c.predicted_cvr else None,
                "actual_cvr": c.cvr / 10000 if c.cvr else None,
                "conversions": c.conversions,
                "revenue": c.revenue / 100 if c.revenue else 0,
                "status": c.status,
                "is_winner": c.is_winner,
                "created_at": c.created_at.isoformat()
            }
            for c in creatives
        ]
    }


@router.get("/patterns/top", response_model=List[PatternPerformanceResponse])
def get_top_patterns(
    product_category: str,
    metric: str = "cvr",  # cvr, ctr, roas
    top_n: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get top performing pattern combinations.

    **Use Cases:**
    1. See which hooks work best for your product
    2. Find winning pattern combinations
    3. Guide UGC brief creation

    **Example response:**
    ```json
    [
      {
        "hook_type": "wait",
        "emotion": "excitement",
        "pacing": "fast",
        "cta_type": "urgency",
        "avg_cvr": 0.15,
        "sample_size": 25,
        "total_conversions": 375
      }
    ]
    ```
    """

    user_id = current_user["user_id"]

    predictor = MarkovChainPredictor(
        db=db,
        user_id=user_id,
        product_category=product_category
    )

    patterns = predictor.get_best_patterns(metric=metric, top_n=top_n)

    return patterns


@router.post("/patterns/update")
def update_pattern_performance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Recalculate pattern performance from all creatives.

    **When to run:**
    - After uploading new creative performance data
    - Daily (automated job)
    - Before analyzing new creatives (to get latest predictions)

    This updates the Markov Chain model with latest data.
    """

    user_id = current_user["user_id"]

    # Get all product categories for this user
    product_categories = db.query(Creative.product_category).filter(
        Creative.user_id == user_id
    ).distinct().all()

    results = []

    for (product_category,) in product_categories:
        predictor = MarkovChainPredictor(
            db=db,
            user_id=user_id,
            product_category=product_category
        )

        result = predictor.update_pattern_performance()
        results.append({
            "product_category": product_category,
            **result
        })

    return {
        "message": "Pattern performance updated successfully",
        "results": results
    }


@router.get("/creatives/{creative_id}/similar")
def find_similar_creatives(
    creative_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Find similar creatives using CLIP embeddings.

    **Use Cases:**
    1. Find creatives with similar visual style
    2. Identify pattern variations that work
    3. Avoid testing duplicate creatives

    **Note:** Requires CLIP embeddings to be computed for creatives.
    If embeddings are not available, falls back to pattern matching.
    """

    user_id = current_user["user_id"]

    creative = db.query(Creative).filter(
        Creative.id == creative_id,
        Creative.user_id == user_id
    ).first()

    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )

    # If CLIP embeddings available, use them
    if creative.clip_embedding:
        # TODO: Implement CLIP similarity search
        # For now, fall back to pattern matching
        pass

    # Fall back: Pattern matching
    similar = db.query(Creative).filter(
        Creative.user_id == user_id,
        Creative.product_category == creative.product_category,
        Creative.id != creative.id
    ).filter(
        (Creative.hook_type == creative.hook_type) |
        (Creative.emotion == creative.emotion) |
        (Creative.pacing == creative.pacing)
    ).order_by(Creative.cvr.desc()).limit(limit).all()

    return {
        "similar_creatives": [
            {
                "id": str(c.id),
                "name": c.name,
                "hook_type": c.hook_type,
                "emotion": c.emotion,
                "pacing": c.pacing,
                "cvr": c.cvr / 10000 if c.cvr else None,
                "conversions": c.conversions,
                "similarity_score": 0.85  # Placeholder
            }
            for c in similar
        ]
    }
