"""
Influencer Scraper Router - Apify integration for TikTok influencer discovery.

Endpoints:
- POST /scrape - Запуск скрапинга по хэштегам
- GET /list - Список инфлюенсеров с фильтрами
- PUT /{id}/status - Обновление статуса
- POST /enrich-emails - Обогащение email через RocketReach
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from database.base import get_db
from database.models import Influencer, User
from api.dependencies import get_current_user
from utils.apify_scraper import ApifyTikTokScraper, scrape_influencers_by_niche
from utils.rocketreach import enrich_influencer_emails, extract_emails_from_bios
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/influencers", tags=["Influencer Scraper"])


# ========== SCHEMAS ==========

class ScrapeRequest(BaseModel):
    """Запрос на скрапинг инфлюенсеров."""
    niche: str  # fitness, edtech, finance, etc.
    hashtags: List[str]  # ["fitness", "workout", "gym"]
    limit_per_hashtag: int = 30
    min_followers: int = 10000
    max_followers: int = 500000


class ScrapeResponse(BaseModel):
    """Результат скрапинга."""
    success: bool
    niche: str
    hashtags: List[str]
    total_found: int
    inserted: int
    updated: int
    errors: int
    message: str


class InfluencerResponse(BaseModel):
    """Инфлюенсер в ответе API."""
    id: str
    handle: str
    name: Optional[str]
    bio: Optional[str]
    platform: str
    niche: str
    followers: int
    engagement_rate: Optional[float]  # В процентах (3.5)
    email: Optional[str]
    email_verified: bool
    status: str
    source_keyword: Optional[str]
    scraped_at: datetime
    contacted_at: Optional[datetime]


class UpdateStatusRequest(BaseModel):
    """Запрос на обновление статуса."""
    status: str  # new, email_found, contacted, responded, agreed, posted, rejected
    notes: Optional[str] = None


class BulkStatusUpdate(BaseModel):
    """Массовое обновление статуса."""
    influencer_ids: List[str]
    status: str
    notes: Optional[str] = None


class EnrichEmailsRequest(BaseModel):
    """Запрос на обогащение email."""
    influencer_ids: Optional[List[str]] = None  # None = все без email
    limit: int = 50


# ========== HELPERS ==========

def influencer_to_response(inf: Influencer) -> InfluencerResponse:
    """Convert DB model to response."""
    return InfluencerResponse(
        id=str(inf.id),
        handle=inf.handle,
        name=inf.name,
        bio=inf.bio[:200] + "..." if inf.bio and len(inf.bio) > 200 else inf.bio,
        platform=inf.platform,
        niche=inf.niche,
        followers=inf.followers,
        engagement_rate=inf.engagement_rate / 10000 if inf.engagement_rate else None,
        email=inf.email,
        email_verified=inf.email_verified or False,
        status=inf.status,
        source_keyword=inf.source_keyword,
        scraped_at=inf.scraped_at,
        contacted_at=inf.contacted_at,
    )


# ========== ENDPOINTS ==========

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_influencers(
    request: ScrapeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔍 Запуск скрапинга инфлюенсеров по хэштегам.

    Использует Apify TikTok Scraper для поиска креаторов.
    Результаты сохраняются в БД со статусом 'new'.

    Example:
    ```json
    {
      "niche": "fitness",
      "hashtags": ["fitness", "workout", "gymlife", "fitnessmotivation"],
      "limit_per_hashtag": 30,
      "min_followers": 10000,
      "max_followers": 200000
    }
    ```
    """
    logger.info(f"Starting scrape for niche={request.niche}, hashtags={request.hashtags}")

    result = await scrape_influencers_by_niche(
        niche=request.niche,
        hashtags=request.hashtags,
        user_id=current_user.id,
        db=db,
        limit_per_hashtag=request.limit_per_hashtag,
        min_followers=request.min_followers,
        max_followers=request.max_followers
    )

    stats = result.get("stats", {})

    return ScrapeResponse(
        success=result.get("success", False),
        niche=request.niche,
        hashtags=request.hashtags,
        total_found=result.get("total_found", 0),
        inserted=stats.get("inserted", 0),
        updated=stats.get("updated", 0),
        errors=stats.get("errors", 0),
        message=f"Scraped {result.get('total_found', 0)} influencers. "
                f"New: {stats.get('inserted', 0)}, Updated: {stats.get('updated', 0)}"
    )


@router.get("/list", response_model=List[InfluencerResponse])
async def list_influencers(
    niche: Optional[str] = None,
    status: Optional[str] = None,
    platform: str = "tiktok",
    min_followers: int = 0,
    max_followers: int = 10000000,
    has_email: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "followers",  # followers, engagement_rate, scraped_at
    sort_order: str = "desc",
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📋 Список инфлюенсеров с фильтрами.

    Параметры:
    - niche: Фильтр по нише (fitness, edtech, etc.)
    - status: Фильтр по статусу (new, email_found, contacted, etc.)
    - platform: Платформа (tiktok, instagram)
    - min_followers, max_followers: Диапазон подписчиков
    - has_email: True = только с email, False = только без
    - search: Поиск по handle/name
    - sort_by: Сортировка (followers, engagement_rate, scraped_at)
    """
    query = db.query(Influencer).filter(Influencer.user_id == current_user.id)

    # Filters
    if niche:
        query = query.filter(Influencer.niche == niche)
    if status:
        query = query.filter(Influencer.status == status)
    if platform:
        query = query.filter(Influencer.platform == platform)
    if min_followers > 0:
        query = query.filter(Influencer.followers >= min_followers)
    if max_followers < 10000000:
        query = query.filter(Influencer.followers <= max_followers)
    if has_email is True:
        query = query.filter(Influencer.email.isnot(None))
    elif has_email is False:
        query = query.filter(Influencer.email.is_(None))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Influencer.handle.ilike(search_pattern)) |
            (Influencer.name.ilike(search_pattern))
        )

    # Sorting
    sort_column = {
        "followers": Influencer.followers,
        "engagement_rate": Influencer.engagement_rate,
        "scraped_at": Influencer.scraped_at,
        "created_at": Influencer.created_at,
    }.get(sort_by, Influencer.followers)

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    influencers = query.offset(offset).limit(limit).all()

    return [influencer_to_response(inf) for inf in influencers]


@router.get("/stats")
async def get_influencer_stats(
    niche: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Статистика по инфлюенсерам.

    Возвращает количество по статусам и нишам.
    """
    base_query = db.query(Influencer).filter(Influencer.user_id == current_user.id)

    if niche:
        base_query = base_query.filter(Influencer.niche == niche)

    # По статусам
    status_counts = db.query(
        Influencer.status,
        func.count(Influencer.id)
    ).filter(
        Influencer.user_id == current_user.id
    ).group_by(Influencer.status).all()

    # По нишам
    niche_counts = db.query(
        Influencer.niche,
        func.count(Influencer.id)
    ).filter(
        Influencer.user_id == current_user.id
    ).group_by(Influencer.niche).all()

    # С email / без email
    with_email = base_query.filter(Influencer.email.isnot(None)).count()
    without_email = base_query.filter(Influencer.email.is_(None)).count()

    total = base_query.count()

    return {
        "total": total,
        "by_status": {status: count for status, count in status_counts},
        "by_niche": {niche: count for niche, count in niche_counts},
        "with_email": with_email,
        "without_email": without_email,
    }


@router.put("/{influencer_id}/status")
async def update_influencer_status(
    influencer_id: str,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ Обновить статус инфлюенсера.

    Статусы:
    - new: Только найден
    - email_found: Email получен
    - contacted: Письмо отправлено
    - responded: Ответил
    - agreed: Согласился
    - posted: Опубликовал
    - rejected: Отказался
    """
    influencer = db.query(Influencer).filter(
        Influencer.id == uuid.UUID(influencer_id),
        Influencer.user_id == current_user.id
    ).first()

    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    valid_statuses = ["new", "email_found", "contacted", "responded", "agreed", "posted", "rejected"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    # Update status and timestamps
    old_status = influencer.status
    influencer.status = request.status
    influencer.updated_at = datetime.utcnow()

    if request.notes:
        influencer.notes = request.notes

    # Set timestamps based on status
    if request.status == "contacted" and not influencer.contacted_at:
        influencer.contacted_at = datetime.utcnow()
    elif request.status == "responded" and not influencer.responded_at:
        influencer.responded_at = datetime.utcnow()
    elif request.status == "agreed" and not influencer.agreed_at:
        influencer.agreed_at = datetime.utcnow()
    elif request.status == "posted" and not influencer.posted_at:
        influencer.posted_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "influencer_id": influencer_id,
        "old_status": old_status,
        "new_status": request.status,
        "message": f"Status updated: {old_status} → {request.status}"
    }


@router.post("/bulk-status")
async def bulk_update_status(
    request: BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ Массовое обновление статуса.

    Обновляет статус для списка инфлюенсеров.
    """
    valid_statuses = ["new", "email_found", "contacted", "responded", "agreed", "posted", "rejected"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    updated = 0
    for inf_id in request.influencer_ids:
        try:
            influencer = db.query(Influencer).filter(
                Influencer.id == uuid.UUID(inf_id),
                Influencer.user_id == current_user.id
            ).first()

            if influencer:
                influencer.status = request.status
                influencer.updated_at = datetime.utcnow()
                if request.notes:
                    influencer.notes = request.notes
                updated += 1
        except Exception as e:
            logger.error(f"Error updating influencer {inf_id}: {e}")

    db.commit()

    return {
        "success": True,
        "updated": updated,
        "total_requested": len(request.influencer_ids),
        "message": f"Updated {updated} influencers to status '{request.status}'"
    }


@router.delete("/{influencer_id}")
async def delete_influencer(
    influencer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🗑️ Удалить инфлюенсера.
    """
    influencer = db.query(Influencer).filter(
        Influencer.id == uuid.UUID(influencer_id),
        Influencer.user_id == current_user.id
    ).first()

    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    db.delete(influencer)
    db.commit()

    return {
        "success": True,
        "message": f"Deleted influencer @{influencer.handle}"
    }


@router.get("/niches")
async def get_available_niches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📂 Список доступных ниш.

    Возвращает уникальные ниши из БД пользователя.
    """
    niches = db.query(Influencer.niche).filter(
        Influencer.user_id == current_user.id
    ).distinct().all()

    return {
        "niches": [n[0] for n in niches],
        "suggested": ["fitness", "edtech", "finance", "beauty", "tech", "gaming", "food", "travel"]
    }


# ========== EMAIL ENRICHMENT ==========

@router.post("/enrich-emails")
async def enrich_emails_endpoint(
    request: EnrichEmailsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📧 Обогащение email через RocketReach API.

    Если influencer_ids не указан - обрабатывает всех без email.

    Example:
    ```json
    {
      "influencer_ids": ["uuid1", "uuid2"],  // или null для всех без email
      "limit": 50
    }
    ```

    Note: Требует ROCKETREACH_API_KEY в .env
    """
    result = await enrich_influencer_emails(
        influencer_ids=request.influencer_ids,
        user_id=current_user.id,
        db=db,
        limit=request.limit
    )
    return result


@router.post("/extract-emails-from-bio")
async def extract_emails_from_bio_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📧 Извлечь email из био инфлюенсеров.

    Бесплатный метод - парсит email из bio (многие указывают для коллабов).
    Не требует API ключей.
    """
    stats = await extract_emails_from_bios(
        user_id=current_user.id,
        db=db
    )
    return {
        "success": True,
        "stats": stats,
        "message": f"Extracted {stats['found']} emails from {stats['total']} bios"
    }
