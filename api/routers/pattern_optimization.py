"""
Pattern Optimization API endpoints - New features for white themes.

Includes:
- Pattern Gap Finder
- Uniqueness Score
- Trend vs Stable Classifier
- Funnel Tracking
- LTV Prediction
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.base import get_db
from database.models import Creative
from utils.pattern_gap_finder import PatternGapFinder, find_all_gaps
from utils.uniqueness_score import UniquenessScorer, quick_uniqueness_check
from utils.trend_classifier import TrendClassifier, quick_trend_check
from utils.funnel_tracker import FunnelTracker, calculate_funnel_health
from utils.ltv_predictor import LTVPredictor
from utils.retention_cohorts import RetentionCohorts, calculate_retention_quality
from utils.ab_testing import ABTest
from utils.public_data_bootstrap import PublicDataBootstrap
from api.dependencies import get_current_user


router = APIRouter(prefix="/api/v1/optimize", tags=["Pattern Optimization"])


# ==================== SCHEMAS ====================

class PublicPattern(BaseModel):
    """Public pattern from TikTok Creative Center."""
    hook_type: str
    emotion: str
    pacing: str
    cta_type: Optional[str] = None
    frequency: float = Field(..., description="Frequency in public data (0-1)")
    avg_engagement: float = Field(default=0.0)


class FunnelEventRequest(BaseModel):
    """Funnel event tracking."""
    creative_id: str
    device_id: str
    platform: Optional[str] = "ios"


class LTVPredictionRequest(BaseModel):
    """LTV prediction request."""
    day_7_sessions: int = Field(..., description="Number of sessions in first 7 days")
    day_7_time_in_app: float = Field(..., description="Minutes in app in first 7 days")
    features_used: int = Field(..., description="Number of features user tried")
    category: str = Field(default="language_learning")


# ==================== PATTERN GAP ENDPOINTS ====================

@router.get("/gaps/find")
def find_pattern_gaps(
    product_category: str,
    min_gap_score: float = 0.7,
    top_n: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Find untested pattern combinations (competitive advantages).

    Returns patterns that should work but haven't been tested yet.

    **Example:**
    ```
    GET /api/v1/optimize/gaps/find?product_category=language_learning&min_gap_score=0.7
    ```

    **Response:**
    ```json
    {
      "pattern_gaps": [
        {
          "hook_type": "before_after",
          "emotion": "curiosity",
          "gap_score": 0.92,
          "expected_performance": "high",
          "reasoning": "Proven hook + uncommon emotion = fresh angle"
        }
      ]
    }
    ```
    """

    user_id = current_user["user_id"]

    finder = PatternGapFinder(db, user_id, product_category)
    gaps = finder.find_gaps(min_gap_score=min_gap_score, top_n=top_n)

    return {
        "product_category": product_category,
        "gaps_found": len(gaps),
        "pattern_gaps": gaps,
        "recommendation": (
            f"Test top {min(3, len(gaps))} gaps first - highest probability of success"
            if gaps else "No gaps found - expand testing to new patterns"
        )
    }


@router.post("/gaps/competitor")
def find_competitor_gaps(
    product_category: str,
    public_patterns: List[PublicPattern],
    top_n: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Find patterns popular with competitors but not tested by you.

    **Use case:** After scraping TikTok Creative Center, find what's missing.

    **Example request:**
    ```json
    {
      "product_category": "language_learning",
      "public_patterns": [
        {
          "hook_type": "before_after",
          "emotion": "achievement",
          "pacing": "fast",
          "frequency": 0.35,
          "avg_engagement": 0.045
        }
      ]
    }
    ```
    """

    user_id = current_user["user_id"]

    finder = PatternGapFinder(db, user_id, product_category)
    gaps = finder.find_competitor_gaps(
        [p.dict() for p in public_patterns],
        top_n=top_n
    )

    return {
        "product_category": product_category,
        "competitor_gaps": gaps,
        "total_gaps": len(gaps)
    }


# ==================== UNIQUENESS ENDPOINTS ====================

@router.post("/uniqueness/check")
def check_uniqueness(
    hook_type: str,
    emotion: str,
    pacing: str,
    product_category: str,
    caption: Optional[str] = None,
    cta_type: Optional[str] = None,
    public_patterns: Optional[List[PublicPattern]] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Check if creative is unique (not a copy).

    **Returns:**
    - Uniqueness score (0-100)
    - Is unique? (score >= 60)
    - Is copy? (score < 30)
    - Recommendations

    **Example:**
    ```
    POST /api/v1/optimize/uniqueness/check
    {
      "hook_type": "before_after",
      "emotion": "achievement",
      "pacing": "fast",
      "product_category": "language_learning",
      "caption": "I learned Spanish in 3 months"
    }
    ```

    **Response:**
    ```json
    {
      "uniqueness_score": 45,
      "verdict": "⚠️ Moderately unique - consider variations",
      "is_unique": false,
      "is_copy": false,
      "proceed_with_test": false,
      "recommendations": ["Pattern is popular - try different emotion"]
    }
    ```
    """

    user_id = current_user["user_id"]

    scorer = UniquenessScorer(db, user_id, product_category)

    result = scorer.calculate_uniqueness(
        hook_type,
        emotion,
        pacing,
        caption,
        cta_type,
        [p.dict() for p in public_patterns] if public_patterns else None
    )

    return result


@router.post("/uniqueness/suggest")
def suggest_unique_variations(
    hook_type: str,
    emotion: str,
    pacing: str,
    product_category: str,
    public_patterns: Optional[List[PublicPattern]] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    💡 Suggest more unique variations of a pattern.

    **Use case:** Pattern is too saturated → Get fresh alternatives.

    **Response:**
    ```json
    {
      "suggestions": [
        {
          "type": "emotion_swap",
          "original": "before_after + achievement",
          "suggested": "before_after + curiosity",
          "uniqueness_gain": 78,
          "reasoning": "Same hook, but curiosity is underused → more unique"
        }
      ]
    }
    ```
    """

    user_id = current_user["user_id"]

    scorer = UniquenessScorer(db, user_id, product_category)

    suggestions = scorer.suggest_unique_variations(
        hook_type,
        emotion,
        pacing,
        [p.dict() for p in public_patterns] if public_patterns else None
    )

    return {
        "original_pattern": f"{hook_type} + {emotion} + {pacing}",
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }


# ==================== TREND CLASSIFIER ENDPOINTS ====================

@router.get("/trends/classify")
def classify_pattern_trend(
    hook_type: str,
    emotion: str,
    pacing: str,
    product_category: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Classify pattern as STABLE or TREND.

    **STABLE** = Safe to invest (works long-term)
    **TREND** = Risky (temporary, will die soon)

    **Example:**
    ```
    GET /api/v1/optimize/trends/classify?hook_type=before_after&emotion=achievement&pacing=fast&product_category=language_learning
    ```

    **Response:**
    ```json
    {
      "pattern": "before_after + achievement + fast",
      "classification": "stable",
      "confidence": 0.85,
      "stability_score": 82,
      "verdict": "✅ STABLE - Safe to invest",
      "recommendations": [
        "✅ Safe to invest - Pattern has proven longevity",
        "Create your unique version (don't copy exactly)"
      ]
    }
    ```
    """

    user_id = current_user["user_id"]

    classifier = TrendClassifier(db, user_id, product_category)
    result = classifier.classify_pattern(hook_type, emotion, pacing)

    return result


@router.get("/trends/all")
def classify_all_patterns(
    product_category: str,
    min_sample_size: int = 3,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Classify all patterns you've tested (sorted by stability).

    **Returns patterns ranked by stability score.**

    **Use case:** See which patterns are stable winners vs temporary trends.
    """

    user_id = current_user["user_id"]

    classifier = TrendClassifier(db, user_id, product_category)
    results = classifier.classify_all_patterns(min_sample_size=min_sample_size)

    return {
        "product_category": product_category,
        "patterns": results,
        "total_patterns": len(results),
        "stable_patterns": [p for p in results if p["classification"] == "stable"],
        "trend_patterns": [p for p in results if p["classification"] == "trend"]
    }


# ==================== FUNNEL TRACKING ENDPOINTS ====================

@router.post("/funnel/install")
def track_install(
    request: FunnelEventRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📱 Track app install event.

    **Example:**
    ```json
    {
      "creative_id": "uuid",
      "device_id": "device-123",
      "platform": "ios"
    }
    ```
    """

    tracker = FunnelTracker(db)
    result = tracker.track_install(
        request.creative_id,
        request.device_id,
        request.platform
    )

    return result


@router.post("/funnel/trial")
def track_trial_start(
    request: FunnelEventRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Track trial activation event."""

    tracker = FunnelTracker(db)
    result = tracker.track_trial_start(request.creative_id, request.device_id)

    return result


class PaidConversionRequest(BaseModel):
    """Paid conversion tracking request."""
    creative_id: str
    device_id: str
    amount: int = Field(..., description="Amount in cents")


@router.post("/funnel/paid")
def track_paid_conversion(
    request: PaidConversionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    💰 Track paid conversion event."""

    tracker = FunnelTracker(db)
    result = tracker.track_paid_conversion(request.creative_id, request.device_id, request.amount)

    return result


@router.get("/funnel/metrics/{creative_id}")
def get_funnel_metrics(
    creative_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Get complete funnel metrics for creative.

    **Response:**
    ```json
    {
      "creative_id": "uuid",
      "funnel": {
        "clicks": 1000,
        "installs": 250,
        "trial_starts": 100,
        "paid_conversions": 15
      },
      "rates": {
        "install_rate": 25.0,
        "trial_activation_rate": 40.0,
        "trial_to_paid_rate": 15.0
      },
      "revenue": 750.00,
      "cpa": 50.00
    }
    ```
    """

    tracker = FunnelTracker(db)
    metrics = tracker.get_funnel_metrics(creative_id)

    return metrics


# ==================== LTV PREDICTION ENDPOINTS ====================

@router.post("/ltv/predict")
def predict_ltv(
    request: LTVPredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    💰 Predict user lifetime value from early signals.

    **Example request:**
    ```json
    {
      "day_7_sessions": 8,
      "day_7_time_in_app": 65.5,
      "features_used": 12,
      "category": "language_learning"
    }
    ```

    **Response:**
    ```json
    {
      "predicted_ltv_d30": 45.00,
      "predicted_ltv_d90": 105.00,
      "predicted_ltv_d180": 150.00,
      "estimated_retention": {
        "day_30": 0.35,
        "day_90": 0.22,
        "day_180": 0.15
      },
      "confidence": 0.8,
      "user_segment": "active_user"
    }
    ```
    """

    predictor = LTVPredictor(db)

    result = predictor.predict_ltv(
        request.day_7_sessions,
        request.day_7_time_in_app,
        request.features_used,
        request.category
    )

    return result


@router.get("/ltv/creative/{creative_id}")
def predict_creative_ltv(
    creative_id: str,
    avg_sessions_d7: int,
    avg_time_d7: float,
    avg_features_d7: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    💰 Predict LTV for creative based on user cohort.

    **Query params:**
    - avg_sessions_d7: Average sessions in first 7 days
    - avg_time_d7: Average time in app (minutes)
    - avg_features_d7: Average features used

    **Returns LTV + ROAS projection.**
    """

    predictor = LTVPredictor(db)

    result = predictor.predict_creative_ltv(
        creative_id,
        {
            "avg_sessions_d7": avg_sessions_d7,
            "avg_time_in_app_d7": avg_time_d7,
            "avg_features_used_d7": avg_features_d7
        }
    )

    return result


# ==================== RETENTION COHORTS ====================

@router.get("/retention/{creative_id}")
def get_retention_cohorts(
    creative_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Get retention cohorts for creative (Day 1, 7, 30).

    **Example response:**
    ```json
    {
      "creative_id": "uuid-123",
      "cohort_size": 1000,
      "day_1_retention": 0.75,
      "day_7_retention": 0.35,
      "day_30_retention": 0.12,
      "quality": "good"
    }
    ```
    """
    user_id = current_user.get("sub")

    cohorts = RetentionCohorts(db, user_id)
    retention = cohorts.calculate_retention(creative_id)

    # Add quality classification
    retention["quality"] = calculate_retention_quality(retention)

    return retention


@router.post("/retention/compare")
def compare_retention(
    creative_ids: List[str],
    metric: str = "day_7_retention",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Compare retention across multiple creatives.

    **Example request:**
    ```json
    {
      "creative_ids": ["uuid-1", "uuid-2", "uuid-3"],
      "metric": "day_7_retention"
    }
    ```
    """
    user_id = current_user.get("sub")

    cohorts = RetentionCohorts(db, user_id)
    comparison = cohorts.compare_creatives(creative_ids, metric)

    return {
        "metric": metric,
        "creatives": comparison,
        "winner": comparison[0] if comparison else None
    }


# ==================== A/B TESTING ====================

@router.post("/ab-test/analyze")
def analyze_ab_test(
    creative_a_id: str,
    creative_b_id: str,
    metric: str = "cvr",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🧪 Statistical A/B test analysis.

    **Example request:**
    ```
    POST /api/v1/optimize/ab-test/analyze?creative_a_id=uuid-1&creative_b_id=uuid-2&metric=cvr
    ```

    **Returns:**
    - Statistical significance (p-value)
    - Winner with confidence
    - Lift percentage
    - Recommendation
    """
    user_id = current_user.get("sub")

    ab_test = ABTest(db, user_id)
    result = ab_test.analyze_test(creative_a_id, creative_b_id, metric)

    return result


@router.get("/ab-test/sample-size")
def calculate_ab_sample_size(
    baseline_cvr: float,
    minimum_detectable_effect: float = 0.20,
    alpha: float = 0.05,
    power: float = 0.80,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🧮 Calculate required sample size for A/B test.

    **Example:**
    ```
    GET /api/v1/optimize/ab-test/sample-size?baseline_cvr=0.05&minimum_detectable_effect=0.20
    ```

    **Returns:**
    ```json
    {
      "baseline_cvr": 0.05,
      "target_cvr": 0.06,
      "minimum_detectable_effect": 0.20,
      "required_sample_size": 15000,
      "estimated_cost": "$750 per variant at $0.05 CPC"
    }
    ```
    """
    user_id = current_user.get("sub")

    ab_test = ABTest(db, user_id)
    sample_size = ab_test.calculate_sample_size(
        baseline_cvr,
        minimum_detectable_effect,
        alpha,
        power
    )

    # Estimate cost (assuming $0.05 CPC average)
    estimated_cost = sample_size * 0.05

    return {
        "baseline_cvr": baseline_cvr,
        "target_cvr": baseline_cvr * (1 + minimum_detectable_effect),
        "minimum_detectable_effect": minimum_detectable_effect,
        "alpha": alpha,
        "power": power,
        "required_sample_size": sample_size,
        "estimated_cost_per_variant": f"${estimated_cost:.2f}",
        "note": "Based on $0.05 CPC average"
    }


# ==================== PUBLIC DATA BOOTSTRAP ====================

@router.get("/bootstrap/stable-patterns")
def get_stable_patterns(
    product_category: str,
    min_lifespan_days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    🔍 Get STABLE patterns from public data (not trends!).

    **Example:**
    ```
    GET /api/v1/optimize/bootstrap/stable-patterns?product_category=language_learning
    ```

    **Returns:**
    - Stable hooks (last 30+ days)
    - Stable emotions
    - Stable pacing
    - Filters out temporary trends
    """

    bootstrap = PublicDataBootstrap(product_category)
    bootstrap.load_public_data()
    stable_patterns = bootstrap.extract_stable_patterns(min_lifespan_days)

    return {
        "product_category": product_category,
        "min_lifespan_days": min_lifespan_days,
        "stable_patterns": {
            "hooks": [
                {
                    "pattern": p.pattern_value,
                    "frequency": f"{p.frequency * 100:.1f}%",
                    "avg_lifespan": f"{p.avg_lifespan_days} days",
                    "trend_status": p.trend_status
                }
                for p in stable_patterns.get("hooks", [])
            ],
            "emotions": [
                {
                    "pattern": p.pattern_value,
                    "frequency": f"{p.frequency * 100:.1f}%",
                    "avg_lifespan": f"{p.avg_lifespan_days} days",
                    "trend_status": p.trend_status
                }
                for p in stable_patterns.get("emotions", [])
            ],
            "pacing": [
                {
                    "pattern": p.pattern_value,
                    "frequency": f"{p.frequency * 100:.1f}%",
                    "avg_lifespan": f"{p.avg_lifespan_days} days",
                    "trend_status": p.trend_status
                }
                for p in stable_patterns.get("pacing", [])
            ]
        }
    }


@router.get("/bootstrap/untested-gaps")
def get_untested_gaps(
    product_category: str,
    top_n: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    💎 Find UNTESTED pattern combinations (GOLD!).

    Public data shows: "before_after" + "achievement" → 500 creatives (saturated)
    Gap: "before_after" + "curiosity" → 0 creatives (OPPORTUNITY!)

    **Example:**
    ```
    GET /api/v1/optimize/bootstrap/untested-gaps?product_category=language_learning&top_n=10
    ```

    **Returns:**
    - Top 10 untested combinations
    - Gap score (how promising)
    - Reasoning
    """

    bootstrap = PublicDataBootstrap(product_category)
    bootstrap.load_public_data()
    bootstrap.extract_stable_patterns()

    gaps = bootstrap.find_untested_gaps()

    return {
        "product_category": product_category,
        "gaps_found": len(gaps),
        "top_gaps": gaps[:top_n],
        "recommendation": "Test these untested combinations - proven patterns in fresh angles"
    }


@router.get("/bootstrap/benchmarks")
def get_industry_benchmarks(
    product_category: str,
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Get industry benchmarks for product category.

    **Example:**
    ```
    GET /api/v1/optimize/bootstrap/benchmarks?product_category=language_learning
    ```

    **Returns:**
    ```json
    {
      "category": "language_learning",
      "avg_ctr": 0.025,
      "avg_cvr": 0.08,
      "top_10_percent_cvr": 0.15,
      "avg_install_rate": 0.18,
      "avg_trial_conversion": 0.45,
      "avg_trial_to_paid": 0.12
    }
    ```
    """

    bootstrap = PublicDataBootstrap(product_category)
    benchmarks = bootstrap.get_industry_benchmarks()

    return {
        "category": product_category,
        **benchmarks
    }


@router.post("/bootstrap/compare-to-benchmark")
def compare_to_benchmark(
    product_category: str,
    your_cvr: float,
    your_install_rate: float,
    current_user: dict = Depends(get_current_user)
):
    """
    🎯 Compare YOUR results to industry benchmarks.

    **Example:**
    ```json
    {
      "product_category": "language_learning",
      "your_cvr": 0.105,
      "your_install_rate": 0.22
    }
    ```

    **Returns:**
    ```json
    {
      "cvr_percentile": 75,
      "cvr_vs_average": "+31%",
      "verdict": "Good (above average)"
    }
    ```
    """

    bootstrap = PublicDataBootstrap(product_category)
    comparison = bootstrap.compare_to_benchmark(your_cvr, your_install_rate)

    return comparison
