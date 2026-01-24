"""
RocketReach API Integration for Email Enrichment.

Пробивает email инфлюенсеров по их имени и профилю в соцсетях.

Usage:
    enricher = RocketReachEnricher(api_key="your_key")
    email = await enricher.find_email(name="John Doe", social_url="https://tiktok.com/@johndoe")
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
from sqlalchemy.orm import Session
import uuid

from utils.logger import setup_logger

logger = setup_logger(__name__)

ROCKETREACH_API_URL = "https://api.rocketreach.co/v2"


@dataclass
class EmailResult:
    """Результат поиска email."""
    email: str
    confidence: int  # 0-100
    source: str  # rocketreach, bio, manual
    verified: bool


class RocketReachEnricher:
    """
    Интеграция с RocketReach для поиска email инфлюенсеров.

    RocketReach использует профили LinkedIn, соцсети и публичные данные
    для поиска контактной информации.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ROCKETREACH_API_KEY")
        if not self.api_key:
            logger.warning("ROCKETREACH_API_KEY not set. Email enrichment disabled.")

        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Закрыть HTTP клиент."""
        await self.client.aclose()

    async def find_email(
        self,
        name: str,
        social_url: Optional[str] = None,
        platform: str = "tiktok",
        handle: Optional[str] = None
    ) -> Optional[EmailResult]:
        """
        Поиск email по имени и соцсетям.

        Args:
            name: Имя инфлюенсера
            social_url: URL профиля в соцсети
            platform: Платформа (tiktok, instagram, youtube)
            handle: Username без @

        Returns:
            EmailResult или None
        """
        if not self.api_key:
            logger.debug("RocketReach API key not set, skipping")
            return None

        try:
            # Формируем URL соцсети если не передан
            if not social_url and handle:
                social_url = self._build_social_url(platform, handle)

            # Поиск персоны
            headers = {
                "Api-Key": self.api_key,
                "Content-Type": "application/json"
            }

            # RocketReach Person Search
            search_payload = {
                "name": name,
            }

            # Добавляем соцсеть если есть
            if social_url:
                if "tiktok" in social_url:
                    search_payload["tiktok_url"] = social_url
                elif "instagram" in social_url:
                    search_payload["instagram_url"] = social_url
                elif "youtube" in social_url:
                    search_payload["youtube_url"] = social_url

            response = await self.client.post(
                f"{ROCKETREACH_API_URL}/api/v2/person/lookup",
                headers=headers,
                json=search_payload
            )

            if response.status_code == 200:
                data = response.json()

                # Извлекаем email
                emails = data.get("emails", [])
                if emails:
                    # Берем первый email с наивысшим confidence
                    best_email = max(emails, key=lambda x: x.get("confidence", 0))
                    return EmailResult(
                        email=best_email.get("email", ""),
                        confidence=best_email.get("confidence", 0),
                        source="rocketreach",
                        verified=best_email.get("verified", False)
                    )

                # Пробуем teaser email если есть
                teaser = data.get("teaser", {}).get("emails", [])
                if teaser:
                    return EmailResult(
                        email=teaser[0],
                        confidence=50,
                        source="rocketreach_teaser",
                        verified=False
                    )

            elif response.status_code == 404:
                logger.debug(f"No results found for {name}")
            else:
                logger.warning(f"RocketReach API error: {response.status_code}")

        except Exception as e:
            logger.error(f"RocketReach error: {e}")

        return None

    async def bulk_enrich(
        self,
        influencers: List[Dict[str, Any]],
        db: Session,
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> Dict[str, int]:
        """
        Массовое обогащение email для списка инфлюенсеров.

        Args:
            influencers: Список словарей с id, name, handle, platform
            db: SQLAlchemy сессия
            batch_size: Размер батча
            delay_between_batches: Задержка между батчами (rate limiting)

        Returns:
            {"found": N, "not_found": N, "errors": N}
        """
        from database.models import Influencer

        stats = {"found": 0, "not_found": 0, "errors": 0, "skipped": 0}

        for i in range(0, len(influencers), batch_size):
            batch = influencers[i:i + batch_size]

            for inf_data in batch:
                try:
                    inf_id = inf_data.get("id")
                    name = inf_data.get("name") or inf_data.get("handle", "")
                    handle = inf_data.get("handle", "")
                    platform = inf_data.get("platform", "tiktok")

                    if not name and not handle:
                        stats["skipped"] += 1
                        continue

                    # Поиск email
                    result = await self.find_email(
                        name=name,
                        handle=handle,
                        platform=platform
                    )

                    if result and result.email:
                        # Обновляем в БД
                        influencer = db.query(Influencer).filter(
                            Influencer.id == uuid.UUID(inf_id)
                        ).first()

                        if influencer:
                            influencer.email = result.email
                            influencer.email_source = result.source
                            influencer.email_verified = result.verified
                            influencer.status = "email_found"
                            influencer.updated_at = datetime.utcnow()
                            stats["found"] += 1
                            logger.info(f"Found email for @{handle}: {result.email}")
                    else:
                        stats["not_found"] += 1

                except Exception as e:
                    logger.error(f"Error enriching {inf_data}: {e}")
                    stats["errors"] += 1

            # Коммит после каждого батча
            db.commit()

            # Rate limiting
            if i + batch_size < len(influencers):
                await asyncio.sleep(delay_between_batches)

        logger.info(f"Bulk enrichment complete: {stats}")
        return stats

    def _build_social_url(self, platform: str, handle: str) -> str:
        """Построить URL профиля по platform и handle."""
        handle = handle.lstrip("@")

        urls = {
            "tiktok": f"https://www.tiktok.com/@{handle}",
            "instagram": f"https://www.instagram.com/{handle}",
            "youtube": f"https://www.youtube.com/@{handle}",
        }
        return urls.get(platform, "")


# ========== API ROUTER ENDPOINT ==========

async def enrich_influencer_emails(
    influencer_ids: Optional[List[str]],
    user_id: uuid.UUID,
    db: Session,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Обогатить email для инфлюенсеров.

    Если influencer_ids не указан - обрабатывает всех без email.

    Args:
        influencer_ids: Список ID или None для всех без email
        user_id: ID пользователя
        db: SQLAlchemy сессия
        limit: Максимум для обработки

    Returns:
        Статистика обогащения
    """
    from database.models import Influencer

    query = db.query(Influencer).filter(Influencer.user_id == user_id)

    if influencer_ids:
        query = query.filter(Influencer.id.in_([uuid.UUID(i) for i in influencer_ids]))
    else:
        # Только без email
        query = query.filter(Influencer.email.is_(None))

    influencers = query.limit(limit).all()

    if not influencers:
        return {
            "success": True,
            "message": "No influencers to enrich",
            "stats": {"found": 0, "not_found": 0, "errors": 0}
        }

    # Конвертируем в список словарей
    inf_list = [
        {
            "id": str(inf.id),
            "name": inf.name,
            "handle": inf.handle,
            "platform": inf.platform
        }
        for inf in influencers
    ]

    # Обогащаем
    enricher = RocketReachEnricher()
    try:
        stats = await enricher.bulk_enrich(inf_list, db)
        return {
            "success": True,
            "processed": len(inf_list),
            "stats": stats,
            "message": f"Enriched {stats['found']} emails out of {len(inf_list)} influencers"
        }
    finally:
        await enricher.close()


# ========== EMAIL FROM BIO EXTRACTOR ==========

def extract_email_from_bio(bio: str) -> Optional[str]:
    """
    Извлечь email из био инфлюенсера.

    Многие инфлюенсеры указывают email в био для коллабораций.
    """
    import re

    if not bio:
        return None

    # Паттерн для email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    matches = re.findall(email_pattern, bio)
    if matches:
        # Берем первый найденный email
        return matches[0].lower()

    return None


async def extract_emails_from_bios(
    user_id: uuid.UUID,
    db: Session
) -> Dict[str, int]:
    """
    Извлечь email из био для всех инфлюенсеров без email.

    Бесплатный метод - не требует API.
    """
    from database.models import Influencer

    influencers = db.query(Influencer).filter(
        Influencer.user_id == user_id,
        Influencer.email.is_(None),
        Influencer.bio.isnot(None)
    ).all()

    stats = {"found": 0, "total": len(influencers)}

    for inf in influencers:
        email = extract_email_from_bio(inf.bio)
        if email:
            inf.email = email
            inf.email_source = "bio"
            inf.email_verified = False
            inf.status = "email_found"
            inf.updated_at = datetime.utcnow()
            stats["found"] += 1
            logger.info(f"Extracted email from bio for @{inf.handle}: {email}")

    db.commit()
    logger.info(f"Bio email extraction: {stats}")
    return stats
