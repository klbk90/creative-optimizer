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


@router.post("/funnel/paid")
def track_paid_conversion(
    creative_id: str,
    device_id: str,
    amount: int = Field(..., description="Amount in cents"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    💰 Track paid conversion event."""

    tracker = FunnelTracker(db)
    result = tracker.track_paid_conversion(creative_id, device_id, amount)

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
