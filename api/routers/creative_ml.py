"""
Creative ML Router - Clean implementation with ML features

MVP Features:
- Upload video/patterns
- Markov Chain CVR prediction
- Thompson Sampling recommendations
- Metrics tracking
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

from database.base import get_db
from database.models import Creative, PatternPerformance, TrafficSource

router = APIRouter(prefix="/api/v1/creative", tags=["Creative ML"])


# ========== SCHEMAS ==========

class CreativeListResponse(BaseModel):
    id: str
    name: str
    creative_type: str
    product_category: str
    campaign_tag: Optional[str]
    hook_type: Optional[str]
    emotion: Optional[str]
    predicted_cvr: Optional[float]
    cvr: Optional[float]  # Will be converted from int
    impressions: int
    conversions: int
    created_at: str


class PatternRecommendation(BaseModel):
    hook_type: str
    emotion: str
    pacing: str
    expected_cvr: float
    confidence: float
    sample_size: int
    priority: float
    reasoning: str


# ========== ENDPOINTS ==========

@router.post("/get-upload-url")
async def get_upload_url(
    filename: str,
    content_type: str = "video/mp4"
):
    """
    Get presigned URL for direct upload to Cloudflare R2.

    Frontend uploads directly to R2, bypassing backend.

    Example:
    ```
    POST /api/v1/creative/get-upload-url
    {
      "filename": "my-video.mp4",
      "content_type": "video/mp4"
    }
    ```

    Returns presigned URL + metadata.
    """
    from utils.storage import get_storage

    storage = get_storage()

    try:
        presigned_data = storage.generate_presigned_upload_url(filename)

        return {
            "success": True,
            **presigned_data,
            "instructions": (
                "Upload file using multipart/form-data to upload_url with fields. "
                "After upload, call /api/v1/creative/confirm-upload with file_key."
            )
        }
    except ValueError as e:
        # R2 not configured, use regular upload
        return {
            "success": False,
            "error": str(e),
            "fallback": "Use POST /api/v1/creative/upload instead"
        }


@router.post("/upload")
async def upload_creative(
    video: UploadFile = File(...),
    creative_name: str = Form(...),
    product_category: str = Form(default="language_learning"),
    creative_type: str = Form(default="ugc"),
    campaign_tag: Optional[str] = Form(None),
    hook_type: Optional[str] = Form("unknown"),
    emotion: Optional[str] = Form("unknown"),
    pacing: Optional[str] = Form("medium"),
    target_audience_pain: Optional[str] = Form("unknown"),  # EdTech: боль ЦА
    db: Session = Depends(get_db)
):
    """
    Upload creative (MVP без auth)

    Returns:
        - id: creative ID
        - predicted_cvr: Markov Chain prediction
        - campaign_tag: for tracking
    """

    # Save video
    upload_dir = "/tmp/utm-videos"
    os.makedirs(upload_dir, exist_ok=True)

    video_filename = f"{uuid.uuid4()}_{video.filename}"
    video_path = f"{upload_dir}/{video_filename}"

    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    # Simple Markov Chain prediction (simplified for MVP)
    # TODO: Use real MarkovChainPredictor from utils
    pattern_key = f"{hook_type}_{emotion}"

    # Query existing performance for this pattern
    pattern_perf = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == product_category,
        PatternPerformance.hook_type == hook_type,
        PatternPerformance.emotion == emotion
    ).first()

    if pattern_perf and pattern_perf.sample_size > 0:
        predicted_cvr = pattern_perf.avg_cvr
        confidence = min(pattern_perf.sample_size / 20, 1.0)  # Max confidence at 20 samples
    else:
        # Default prediction for new patterns
        predicted_cvr = 0.05  # 5% default
        confidence = 0.1

    # Create creative record (with test user for MVP)
    creative_id = uuid.uuid4()
    test_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')  # Test user ID
    creative = Creative(
        id=creative_id,
        user_id=test_user_id,  # Use test user
        name=creative_name,
        creative_type=creative_type,
        product_category=product_category,
        video_url=video_path,
        hook_type=hook_type,
        emotion=emotion,
        pacing=pacing,
        target_audience_pain=target_audience_pain,  # EdTech: на какую боль давит
        predicted_cvr=predicted_cvr,
        campaign_tag=campaign_tag,
        impressions=0,
        clicks=0,
        conversions=0,
        cvr=0,  # cvr stored as integer (cvr * 10000)
        created_at=datetime.utcnow()
    )

    db.add(creative)
    db.flush()  # Get creative.id before creating traffic source

    # 🔥 AUTO-CREATE UTM LINK for this creative
    import hashlib

    # Generate UTM ID: {source}_{creative_short_id}
    creative_short = str(creative.id)[:8]
    utm_id = f"creative_{creative_short}"

    # Create TrafficSource linked to this creative
    traffic_source = TrafficSource(
        id=uuid.uuid4(),
        user_id=test_user_id,
        utm_source=creative_type,  # e.g., "ugc"
        utm_medium="social",
        utm_campaign=campaign_tag or f"creative_{creative_short}",
        utm_content=creative_name,
        utm_id=utm_id,
        clicks=0,
        conversions=0,
        revenue=0,
        first_click=datetime.utcnow(),
        referrer=f"auto_created_for_creative"
    )

    db.add(traffic_source)
    db.flush()

    # Link creative to traffic source
    creative.traffic_source_id = traffic_source.id

    db.commit()
    db.refresh(creative)
    db.refresh(traffic_source)

    # Generate landing URL
    landing_url = f"http://localhost:8000/api/v1/landing/l/{utm_id}"

    return {
        "id": str(creative.id),
        "name": creative.name,
        "predicted_cvr": predicted_cvr,
        "confidence": confidence,
        "campaign_tag": campaign_tag,
        "utm_id": utm_id,
        "utm_link": landing_url,
        "message": f"✅ Creative uploaded! Predicted CVR: {predicted_cvr*100:.1f}%\n🔗 Use this link in TikTok bio: {landing_url}"
    }


@router.get("/creatives", response_model=List[CreativeListResponse])
@router.get("/list", response_model=List[CreativeListResponse])  # Alias for frontend
async def list_creatives(
    limit: int = 100,
    campaign_tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all creatives"""

    query = db.query(Creative)

    if campaign_tag:
        query = query.filter(Creative.campaign_tag == campaign_tag)

    creatives = query.order_by(Creative.created_at.desc()).limit(limit).all()

    return [
        CreativeListResponse(
            id=str(c.id),
            name=c.name,
            creative_type=c.creative_type,
            product_category=c.product_category,
            campaign_tag=c.campaign_tag,
            hook_type=c.hook_type,
            emotion=c.emotion,
            predicted_cvr=(c.predicted_cvr or 0) / 10000,  # Convert from int to float (500 -> 0.05)
            cvr=(c.cvr or 0) / 10000,  # Convert from int to float
            impressions=c.impressions or 0,
            conversions=c.conversions or 0,
            created_at=c.created_at.isoformat() if c.created_at else datetime.utcnow().isoformat()
        )
        for c in creatives
    ]


@router.get("/{creative_id}", response_model=CreativeListResponse)
async def get_creative(
    creative_id: str,
    db: Session = Depends(get_db)
):
    """Get a single creative by ID"""

    creative = db.query(Creative).filter(Creative.id == uuid.UUID(creative_id)).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    return CreativeListResponse(
        id=str(creative.id),
        name=creative.name,
        creative_type=creative.creative_type,
        product_category=creative.product_category,
        campaign_tag=creative.campaign_tag,
        hook_type=creative.hook_type,
        emotion=creative.emotion,
        predicted_cvr=creative.predicted_cvr,
        cvr=(creative.cvr or 0) / 10000,
        impressions=creative.impressions or 0,
        conversions=creative.conversions or 0,
        created_at=creative.created_at.isoformat() if creative.created_at else datetime.utcnow().isoformat()
    )


@router.put("/creatives/{creative_id}/metrics")
async def update_metrics(
    creative_id: str,
    impressions: int = Form(...),
    clicks: int = Form(...),
    conversions: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Update creative metrics and retrain Markov Chain
    """

    creative = db.query(Creative).filter(Creative.id == uuid.UUID(creative_id)).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Update creative metrics
    creative.impressions = impressions
    creative.clicks = clicks
    creative.conversions = conversions
    cvr_value = conversions / impressions if impressions > 0 else 0.0
    creative.cvr = int(cvr_value * 10000)  # Store as integer (* 10000)
    creative.last_stats_update = datetime.utcnow()

    # 🔥 AUTO-SYNC with linked TrafficSource
    if creative.traffic_source_id:
        traffic_source = db.query(TrafficSource).filter(
            TrafficSource.id == creative.traffic_source_id
        ).first()

        if traffic_source:
            # Sync clicks & conversions from creative to UTM tracking
            traffic_source.clicks = clicks
            traffic_source.conversions = conversions
            # Revenue можно добавить если есть
            # traffic_source.revenue = ...

    # Update Markov Chain pattern performance
    pattern_perf = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == creative.product_category,
        PatternPerformance.hook_type == creative.hook_type,
        PatternPerformance.emotion == creative.emotion
    ).first()

    if pattern_perf:
        # Update existing pattern
        old_total = pattern_perf.avg_cvr * pattern_perf.sample_size
        new_total = old_total + cvr_value
        pattern_perf.sample_size += 1
        pattern_perf.avg_cvr = new_total / pattern_perf.sample_size
        pattern_perf.total_conversions = (pattern_perf.total_conversions or 0) + conversions
        pattern_perf.updated_at = datetime.utcnow()
    else:
        # Create new pattern
        pattern_perf = PatternPerformance(
            id=uuid.uuid4(),
            user_id=creative.user_id,
            product_category=creative.product_category,
            hook_type=creative.hook_type,
            emotion=creative.emotion,
            pacing=creative.pacing,
            avg_cvr=cvr_value,
            sample_size=1,
            total_conversions=conversions,
            created_at=datetime.utcnow()
        )
        db.add(pattern_perf)

    db.commit()

    return {
        "id": str(creative.id),
        "name": creative.name,
        "impressions": creative.impressions,
        "conversions": creative.conversions,
        "cvr": cvr_value,
        "pattern_updated": True
    }


@router.get("/patterns/recommend", response_model=List[PatternRecommendation])
async def recommend_patterns(
    product_category: str = "language_learning",
    n_patterns: int = 5,
    db: Session = Depends(get_db)
):
    """
    Thompson Sampling: recommend best patterns to test next

    Balances:
    - Exploitation: test proven winners (high CVR, many samples)
    - Exploration: try new patterns (low samples)
    """

    # Get all patterns for this category
    patterns = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == product_category,
        PatternPerformance.sample_size > 0
    ).all()

    if not patterns:
        return []

    # Simple Thompson Sampling (simplified)
    recommendations = []

    for pattern in patterns[:n_patterns * 2]:  # Get more than needed
        # Priority = CVR * confidence_factor
        # Confidence increases with sample size, maxes at 20 samples
        confidence = min(pattern.sample_size / 20, 1.0)

        # Exploration bonus for low sample patterns
        exploration_bonus = (1 - confidence) * 0.02  # Up to +2% for new patterns

        priority = (pattern.avg_cvr + exploration_bonus) * (0.5 + 0.5 * confidence)

        reasoning = ""
        if pattern.sample_size >= 10:
            reasoning = f"Proven winner with {pattern.sample_size} tests"
        elif pattern.sample_size >= 5:
            reasoning = f"Promising pattern, needs more data"
        else:
            reasoning = f"New pattern, high exploration value"

        recommendations.append(PatternRecommendation(
            hook_type=pattern.hook_type,
            emotion=pattern.emotion,
            pacing=pattern.pacing or "medium",
            expected_cvr=pattern.avg_cvr,
            confidence=confidence,
            sample_size=pattern.sample_size,
            priority=priority,
            reasoning=reasoning
        ))

    # Sort by priority and return top N
    recommendations.sort(key=lambda x: x.priority, reverse=True)
    return recommendations[:n_patterns]


@router.get("/{creative_id}/analysis-status")
async def get_analysis_status(
    creative_id: str,
    db: Session = Depends(get_db)
):
    """
    Get analysis status for creative (for UI feedback).

    Returns UI-friendly status with labels, colors, icons.

    Example response:
    ```json
    {
      "status": "completed",
      "label": "Winner Patterns Identified",
      "color": "green",
      "icon": "check-circle",
      "deeply_analyzed": true,
      "ai_patterns": {
        "hook_type": "problem_agitation",
        "emotion": "frustration",
        "pacing": "fast",
        "target_audience_pain": "no_time"
      },
      "ai_reasoning": "...",
      "conversions": 7,
      "threshold": 5,
      "cost_cents": 15
    }
    ```
    """
    creative = db.query(Creative).filter(Creative.id == uuid.UUID(creative_id)).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    from utils.analysis_orchestrator import get_analysis_status_label

    status_info = get_analysis_status_label(creative.analysis_status or 'pending')

    return {
        "status": creative.analysis_status or 'pending',
        **status_info,
        "deeply_analyzed": creative.deeply_analyzed or False,
        "ai_patterns": {
            "hook_type": creative.hook_type,
            "emotion": creative.emotion,
            "pacing": creative.pacing,
            "target_audience_pain": creative.target_audience_pain
        } if creative.deeply_analyzed else None,
        "ai_reasoning": creative.ai_reasoning,
        "conversions": creative.conversions or 0,
        "threshold": 5,  # DEEP_ANALYSIS_THRESHOLD
        "cost_cents": creative.analysis_cost_cents or 0,
        "analyzed_at": creative.analyzed_at.isoformat() if creative.analyzed_at else None
    }


@router.get("/patterns/top")
async def get_top_patterns(
    product_category: str = "language_learning",
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top performing patterns"""

    patterns = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == product_category,
        PatternPerformance.sample_size > 0
    ).order_by(PatternPerformance.avg_cvr.desc()).limit(limit).all()

    return [
        {
            "hook_type": p.hook_type,
            "emotion": p.emotion,
            "pacing": p.pacing,
            "avg_cvr": p.avg_cvr,
            "sample_size": p.sample_size,
            "total_conversions": p.total_conversions or 0
        }
        for p in patterns
    ]
