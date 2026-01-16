"""
MVP Creative Analysis Router - Simplified version
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from database.base import get_db
from database.models import Creative
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/creative", tags=["Creative MVP"])


@router.get("/ping")
async def ping():
    """Simple ping endpoint to test if router is working."""
    return {"status": "ok", "message": "creative_mvp router is working!"}


@router.get("/test-storage")
async def test_storage():
    """Debug endpoint to test storage configuration."""
    try:
        from utils.storage import get_storage
        import os

        storage = get_storage()

        return {
            "storage_type": storage.storage_type,
            "r2_endpoint": os.getenv("R2_ENDPOINT_URL", "NOT SET"),
            "r2_access_key": "SET" if os.getenv("R2_ACCESS_KEY_ID") else "NOT SET",
            "r2_secret": "SET" if os.getenv("R2_SECRET_ACCESS_KEY") else "NOT SET",
            "client_bucket": os.getenv("R2_CLIENT_ASSETS_BUCKET", "NOT SET"),
            "market_bucket": os.getenv("R2_MARKET_BENCHMARKS_BUCKET", "NOT SET"),
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }


class CreativeResponse(BaseModel):
    id: str
    name: str
    creative_type: str
    product_category: str
    predicted_cvr: Optional[float] = None
    conversion_rate: Optional[float] = None
    impressions: Optional[int] = 0
    conversions: Optional[int] = 0
    test_completed: bool = False

    class Config:
        from_attributes = True


@router.post("/upload")
async def upload_creative(
    video: UploadFile = File(...),
    creative_name: str = Form(...),
    product_category: str = Form(default="language_learning"),
    creative_type: str = Form(default="ugc"),
    campaign_tag: str = Form(None),  # Упрощенная метка вместо UTM
    db: Session = Depends(get_db)
):
    """
    Упрощенная загрузка креатива для MVP

    - Загружает видео в Cloudflare R2
    - Создает запись в БД
    - Возвращает ID для отслеживания
    """
    from utils.storage import get_storage
    from utils.logger import setup_logger

    logger = setup_logger(__name__)

    try:
        # Get storage instance
        storage = get_storage()

        # Generate a unique user_id for MVP (anonymous upload)
        # In production, this would come from authentication
        anonymous_user_id = str(uuid.uuid4())

        # Read video content
        video_content = await video.read()

        # Upload to R2
        internal_key = storage.upload_client_video(
            file_content=video_content,
            filename=video.filename,
            user_id=anonymous_user_id
        )

        # Create database record
        creative = Creative(
            id=uuid.uuid4(),
            user_id=uuid.UUID(anonymous_user_id),
            name=creative_name,
            creative_type=creative_type,
            product_category=product_category,
            video_url=internal_key,  # r2://client-assets/...
            hook_type="unknown",  # Заполнится при анализе
            emotion="unknown",
            pacing="medium",
            predicted_cvr=0.05,  # Дефолтное значение
            campaign_tag=campaign_tag,
            is_public=False  # MVP videos are private
        )

        db.add(creative)
        db.commit()
        db.refresh(creative)

        logger.info(f"✅ Creative uploaded: {creative.id} → {internal_key}")

        return {
            "id": str(creative.id),
            "name": creative.name,
            "message": "Креатив загружен в Cloudflare R2. Используйте campaign_tag для отслеживания результатов.",
            "campaign_tag": campaign_tag,
            "video_url": internal_key
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Upload failed: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/creatives")
async def list_creatives(
    limit: int = 100,
    campaign_tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Список всех креативов с фильтрацией по метке
    """
    query = db.query(Creative)

    if campaign_tag:
        query = query.filter(Creative.campaign_tag == campaign_tag)

    creatives = query.order_by(Creative.created_at.desc()).limit(limit).all()

    return [{
        "id": str(c.id),
        "name": c.name,
        "creative_type": c.creative_type,
        "product_category": c.product_category,
        "campaign_tag": c.campaign_tag,
        "hook_type": c.hook_type,
        "emotion": c.emotion,
        "predicted_cvr": (c.predicted_cvr or 0) / 10000,  # Convert from int to decimal
        "conversion_rate": (c.cvr or 0) / 10000,  # Convert from int to decimal
        "impressions": c.impressions or 0,
        "conversions": c.conversions or 0,
        "test_completed": c.test_completed,
        "created_at": c.created_at.isoformat() if c.created_at else None
    } for c in creatives]


@router.put("/creatives/{creative_id}/metrics")
async def update_metrics(
    creative_id: str,
    impressions: int = Form(...),
    clicks: int = Form(...),
    conversions: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Обновить метрики креатива вручную
    """
    creative = db.query(Creative).filter(Creative.id == uuid.UUID(creative_id)).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    creative.impressions = impressions
    creative.clicks = clicks
    creative.conversions = conversions
    creative.conversion_rate = conversions / impressions if impressions > 0 else 0
    creative.updated_at = datetime.utcnow()

    db.commit()

    return {
        "id": str(creative.id),
        "name": creative.name,
        "impressions": creative.impressions,
        "conversions": creative.conversions,
        "conversion_rate": creative.conversion_rate
    }
