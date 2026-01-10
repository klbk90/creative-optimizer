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

    - Загружает видео (сохраняет локально)
    - Создает запись в БД
    - Возвращает ID для отслеживания
    """

    # Сохранить файл локально
    import os
    upload_dir = "/tmp/utm-videos"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = f"{upload_dir}/{uuid.uuid4()}_{video.filename}"
    with open(file_path, "wb") as f:
        content = await video.read()
        f.write(content)

    # Создать запись
    creative = Creative(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # TODO: from auth
        name=creative_name,
        creative_type=creative_type,
        product_category=product_category,
        video_url=file_path,
        hook_type="unknown",  # Заполнится при анализе
        emotion="unknown",
        pacing="medium",
        predicted_cvr=0.05,  # Дефолтное значение
        campaign_tag=campaign_tag
    )

    db.add(creative)
    db.commit()
    db.refresh(creative)

    return {
        "id": str(creative.id),
        "name": creative.name,
        "message": "Креатив загружен. Используйте campaign_tag для отслеживания результатов.",
        "campaign_tag": campaign_tag
    }


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
