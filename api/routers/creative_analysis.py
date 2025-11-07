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


# ==================== CLUSTERING ENDPOINTS ====================

@router.post("/cluster/visual")
def cluster_creatives_visual(
    n_clusters: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Кластеризация креативов по визуальному сходству (CLIP embeddings).

    **Use case:**
    - Группировать похожие креативы
    - Найти выстреливающие кластеры
    - Понять какой визуальный стиль работает

    **Example response:**
    ```json
    {
      "clusters": [
        {
          "cluster_id": 0,
          "size": 15,
          "avg_cvr": 0.125,
          "avg_roas": 3.5,
          "top_creative_ids": [...],
          "common_patterns": {
            "hook_type": "wait",
            "emotion": "excitement"
          }
        }
      ],
      "silhouette_score": 0.65
    }
    ```
    """

    from utils.creative_clustering import CreativeClustering

    user_id = current_user["user_id"]

    clustering = CreativeClustering(db, user_id)
    result = clustering.cluster_by_visual_similarity(n_clusters=n_clusters)

    return result


@router.post("/cluster/patterns")
def cluster_creatives_patterns(
    n_clusters: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Кластеризация креативов по паттернам (hook, emotion, pacing).

    **Быстрее чем visual clustering, не требует CLIP embeddings.**
    """

    from utils.creative_clustering import CreativeClustering

    user_id = current_user["user_id"]

    clustering = CreativeClustering(db, user_id)
    result = clustering.cluster_by_patterns(n_clusters=n_clusters)

    return result


@router.get("/cluster/winning")
def get_winning_cluster(
    min_cvr: float = 0.10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Найти выстреливающий кластер (CVR > threshold).

    **Use case:**
    - Определить лучший кластер для масштабирования
    - Понять какие паттерны работают

    **Example:**
    ```
    GET /api/v1/creative/cluster/winning?min_cvr=0.10

    Returns cluster with AVG CVR > 10%
    ```
    """

    from utils.creative_clustering import CreativeClustering

    user_id = current_user["user_id"]

    clustering = CreativeClustering(db, user_id)
    winning = clustering.find_winning_cluster(min_cvr=min_cvr)

    if not winning:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cluster found with CVR > {min_cvr*100}%"
        )

    return winning


@router.post("/recommend/scaling")
def recommend_scaling_creatives(
    budget: int = Field(..., description="Budget in cents (e.g., $50 = 5000)"),
    min_cvr: float = Field(default=0.10, description="Minimum CVR threshold"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🚀 ГЛАВНАЯ ФИЧА: Рекомендовать креативы для масштабирования.

    **Workflow:**
    1. Микро-тесты на 20 креативов (по $50)
    2. Анализ результатов + кластеризация
    3. Вызов этого endpoint: `/recommend/scaling`
    4. Получить топ креативы для масштабирования
    5. Залить на них $5k-50k

    **Example request:**
    ```json
    {
      "budget": 500000,  // $5,000
      "min_cvr": 0.10    // Минимум 10% CVR
    }
    ```

    **Example response:**
    ```json
    {
      "recommended_creatives": [
        {
          "id": "uuid",
          "name": "Video 1",
          "cvr": 0.15,
          "roas": 4.2,
          "recommended_budget": 100000,  // $1,000
          "expected_conversions": 150
        }
      ],
      "cluster_info": {
        "cluster_id": 0,
        "avg_cvr": 0.145,
        "avg_roas": 3.8
      },
      "total_budget": 500000,
      "expected_revenue": 2100000,  // $21,000
      "expected_roi": 4.2,
      "confidence": 0.85
    }
    ```
    """

    from utils.creative_clustering import CreativeClustering

    user_id = current_user["user_id"]

    clustering = CreativeClustering(db, user_id)
    recommendations = clustering.recommend_scaling_creatives(
        budget=budget,
        min_cvr=min_cvr
    )

    if "error" in recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=recommendations["error"]
        )

    return recommendations


@router.post("/update-from-utm")
def update_creative_performance_from_utm(
    creative_id: str = Field(..., description="Creative UUID"),
    utm_campaign: str = Field(..., description="UTM campaign name to fetch data from"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🔗 Автоматически обновить метрики креатива из UTM данных.

    **Workflow:**
    1. Создали креатив
    2. Создали UTM ссылку (utm_content = creative_id)
    3. Запустили микро-тест
    4. Вызываем этот endpoint → автоматически подтягивает метрики

    **Example:**
    ```json
    {
      "creative_id": "uuid-123",
      "utm_campaign": "test_video_1"
    }
    ```

    **Система:**
    - Найдет все traffic_sources с utm_campaign = "test_video_1"
    - Суммирует clicks, conversions, revenue
    - Обновит креатив
    - Пересчитает CVR, ROAS
    """

    user_id = current_user["user_id"]

    # Найти креатив
    creative = db.query(Creative).filter(
        Creative.id == creative_id,
        Creative.user_id == user_id
    ).first()

    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )

    # Найти все UTM записи для этой кампании
    traffic_sources = db.query(TrafficSource).filter(
        TrafficSource.user_id == user_id,
        TrafficSource.utm_campaign == utm_campaign
    ).all()

    if not traffic_sources:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No UTM data found for campaign: {utm_campaign}"
        )

    # Суммировать метрики
    total_impressions = len(traffic_sources)  # Каждый клик = просмотр landing page
    total_clicks = sum(ts.clicks for ts in traffic_sources)
    total_conversions = sum(ts.conversions for ts in traffic_sources)
    total_revenue = sum(ts.revenue for ts in traffic_sources)

    # Обновить креатив
    creative.impressions = total_impressions
    creative.clicks = total_clicks
    creative.conversions = total_conversions
    creative.revenue = total_revenue

    # Рассчитать метрики
    if total_impressions > 0:
        creative.ctr = int((total_clicks / total_impressions) * 10000)  # CTR * 10000

    if total_clicks > 0:
        creative.cvr = int((total_conversions / total_clicks) * 10000)  # CVR * 10000

    if creative.media_spend and creative.media_spend > 0:
        creative.roas = int((total_revenue / creative.media_spend) * 100)  # ROAS * 100
        creative.cpa = creative.media_spend // total_conversions if total_conversions > 0 else 0

    # Обновить статус
    if creative.status == "draft":
        creative.status = "testing"

    creative.tested_at = datetime.utcnow()
    creative.last_stats_update = datetime.utcnow()

    db.commit()
    db.refresh(creative)

    return {
        "message": "Creative performance updated from UTM data",
        "creative_id": str(creative.id),
        "utm_campaign": utm_campaign,
        "metrics": {
            "impressions": creative.impressions,
            "clicks": creative.clicks,
            "conversions": creative.conversions,
            "revenue": creative.revenue / 100,  # В долларах
            "ctr": creative.ctr / 10000,
            "cvr": creative.cvr / 10000,
            "roas": creative.roas / 100 if creative.roas else None
        }
    }


@router.post("/bulk-update-from-utm")
def bulk_update_creatives_from_utm(
    utm_campaigns: list[str] = Field(..., description="List of UTM campaigns"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🔗 Массово обновить все креативы из UTM данных.

    **Use case:**
    После завершения всех микро-тестов (20 креативов):

    ```json
    {
      "utm_campaigns": [
        "test_video_1",
        "test_video_2",
        "test_video_3",
        ...
        "test_video_20"
      ]
    }
    ```

    Система обновит все 20 креативов одним запросом.
    """

    user_id = current_user["user_id"]
    results = []
    errors = []

    for utm_campaign in utm_campaigns:
        try:
            # Найти креатив по utm_campaign
            # Предполагается что utm_campaign уникален для креатива
            traffic_sources = db.query(TrafficSource).filter(
                TrafficSource.user_id == user_id,
                TrafficSource.utm_campaign == utm_campaign
            ).all()

            if not traffic_sources:
                errors.append({
                    "utm_campaign": utm_campaign,
                    "error": "No UTM data found"
                })
                continue

            # Попробовать найти creative_id из utm_content
            # (если вы указали creative_id в utm_content при создании UTM)
            utm_content = traffic_sources[0].utm_content

            creative = db.query(Creative).filter(
                Creative.user_id == user_id,
                Creative.id == utm_content  # utm_content содержит creative_id
            ).first()

            if not creative:
                # Альтернативно: найти по названию кампании
                creative = db.query(Creative).filter(
                    Creative.user_id == user_id,
                    Creative.name.contains(utm_campaign)
                ).first()

            if not creative:
                errors.append({
                    "utm_campaign": utm_campaign,
                    "error": "Creative not found"
                })
                continue

            # Обновить метрики (аналогично update-from-utm)
            total_impressions = len(traffic_sources)
            total_clicks = sum(ts.clicks for ts in traffic_sources)
            total_conversions = sum(ts.conversions for ts in traffic_sources)
            total_revenue = sum(ts.revenue for ts in traffic_sources)

            creative.impressions = total_impressions
            creative.clicks = total_clicks
            creative.conversions = total_conversions
            creative.revenue = total_revenue

            if total_impressions > 0:
                creative.ctr = int((total_clicks / total_impressions) * 10000)

            if total_clicks > 0:
                creative.cvr = int((total_conversions / total_clicks) * 10000)

            if creative.media_spend and creative.media_spend > 0:
                creative.roas = int((total_revenue / creative.media_spend) * 100)

            creative.status = "testing"
            creative.tested_at = datetime.utcnow()
            creative.last_stats_update = datetime.utcnow()

            results.append({
                "creative_id": str(creative.id),
                "utm_campaign": utm_campaign,
                "cvr": creative.cvr / 10000,
                "conversions": creative.conversions
            })

        except Exception as e:
            errors.append({
                "utm_campaign": utm_campaign,
                "error": str(e)
            })

    db.commit()

    return {
        "message": f"Updated {len(results)} creatives",
        "results": results,
        "errors": errors if errors else None
    }


@router.post("/train-markov-chain")
def train_markov_chain_model(
    product_category: str = Field(..., description="Product category to train on"),
    min_sample_size: int = Field(default=5, description="Minimum creatives required"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🧠 Обучить Markov Chain модель на собранных данных.

    **Когда использовать:**
    После завершения цикла микро-тестов:
    1. Загрузили 20 креативов
    2. Запустили микро-тесты
    3. Обновили все метрики через `/bulk-update-from-utm`
    4. Вызываем этот endpoint → обучение модели

    **Что делает:**
    - Агрегирует performance по паттернам
    - Обновляет таблицу pattern_performance
    - Рассчитывает transition probabilities
    - Модель готова для предсказаний!

    **Example:**
    ```json
    {
      "product_category": "lootbox",
      "min_sample_size": 5
    }
    ```
    """

    user_id = current_user["user_id"]

    # Получить все креативы с метриками
    creatives = db.query(Creative).filter(
        Creative.user_id == user_id,
        Creative.product_category == product_category,
        Creative.status.in_(["testing", "active"]),
        Creative.conversions > 0  # Только с данными
    ).all()

    if len(creatives) < min_sample_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough data. Need at least {min_sample_size} creatives with conversions. Found: {len(creatives)}"
        )

    # Группировать по паттернам
    from collections import defaultdict

    pattern_stats = defaultdict(lambda: {
        "sample_size": 0,
        "total_impressions": 0,
        "total_clicks": 0,
        "total_conversions": 0,
        "total_revenue": 0
    })

    for creative in creatives:
        # Создать ключ паттерна
        pattern_key = (
            creative.hook_type or "unknown",
            creative.emotion or "unknown",
            creative.pacing or "unknown",
            creative.cta_type or "unknown"
        )

        stats = pattern_stats[pattern_key]
        stats["sample_size"] += 1
        stats["total_impressions"] += creative.impressions or 0
        stats["total_clicks"] += creative.clicks or 0
        stats["total_conversions"] += creative.conversions or 0
        stats["total_revenue"] += creative.revenue or 0

    # Обновить/создать PatternPerformance записи
    updated_patterns = []

    for pattern_key, stats in pattern_stats.items():
        hook_type, emotion, pacing, cta_type = pattern_key

        # Найти или создать
        pattern_perf = db.query(PatternPerformance).filter(
            PatternPerformance.user_id == user_id,
            PatternPerformance.product_category == product_category,
            PatternPerformance.hook_type == hook_type,
            PatternPerformance.emotion == emotion,
            PatternPerformance.pacing == pacing,
            PatternPerformance.cta_type == cta_type
        ).first()

        if not pattern_perf:
            pattern_perf = PatternPerformance(
                user_id=user_id,
                product_category=product_category,
                hook_type=hook_type,
                emotion=emotion,
                pacing=pacing,
                cta_type=cta_type
            )
            db.add(pattern_perf)

        # Обновить метрики
        pattern_perf.sample_size = stats["sample_size"]
        pattern_perf.total_impressions = stats["total_impressions"]
        pattern_perf.total_clicks = stats["total_clicks"]
        pattern_perf.total_conversions = stats["total_conversions"]
        pattern_perf.total_revenue = stats["total_revenue"]

        # Рассчитать средние
        if stats["total_clicks"] > 0:
            avg_ctr = stats["total_clicks"] / stats["total_impressions"] if stats["total_impressions"] > 0 else 0
            pattern_perf.avg_ctr = int(avg_ctr * 10000)

            avg_cvr = stats["total_conversions"] / stats["total_clicks"]
            pattern_perf.avg_cvr = int(avg_cvr * 10000)

        # Transition probability (вероятность конверсии при данном паттерне)
        if stats["total_clicks"] > 0:
            transition_prob = stats["total_conversions"] / stats["total_clicks"]
            pattern_perf.transition_probability = int(transition_prob * 10000)

        pattern_perf.updated_at = datetime.utcnow()

        updated_patterns.append({
            "pattern": f"{hook_type}_{emotion}_{pacing}",
            "sample_size": stats["sample_size"],
            "avg_cvr": pattern_perf.avg_cvr / 10000 if pattern_perf.avg_cvr else 0
        })

    db.commit()

    return {
        "message": "Markov Chain model trained successfully",
        "product_category": product_category,
        "total_creatives": len(creatives),
        "patterns_learned": len(updated_patterns),
        "patterns": updated_patterns,
        "model_ready": True,
        "next_step": "Use POST /api/v1/creative/analyze to predict new creatives"
    }
