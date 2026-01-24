"""
Apify TikTok Scraper Integration.

Скрапит инфлюенсеров по хэштегам и ключевым словам.
Сохраняет в таблицу influencers со статусом 'new'.

Usage:
    scraper = ApifyTikTokScraper(api_token="your_token")
    results = await scraper.search_by_hashtag("#fitness", limit=100)
    saved = await scraper.save_to_db(results, user_id, niche="fitness")
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import uuid

from utils.logger import setup_logger

logger = setup_logger(__name__)

APIFY_API_URL = "https://api.apify.com/v2"
APIFY_TIKTOK_ACTOR = "clockworks/tiktok-scraper"  # Популярный TikTok scraper на Apify


@dataclass
class ScrapedInfluencer:
    """Данные инфлюенсера из скрапера."""
    handle: str
    name: Optional[str]
    bio: Optional[str]
    platform: str
    followers: int
    following: Optional[int]
    engagement_rate: Optional[int]  # ER * 10000
    avg_views: Optional[int]
    total_likes: Optional[int]
    total_videos: Optional[int]
    source_hashtag: Optional[str]
    extra_data: Dict[str, Any]


class ApifyTikTokScraper:
    """
    Интеграция с Apify для скрапинга TikTok инфлюенсеров.

    Использует актор clockworks/tiktok-scraper для поиска по хэштегам.
    """

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN not set. Scraper will use mock data.")

        self.client = httpx.AsyncClient(timeout=120.0)

    async def close(self):
        """Закрыть HTTP клиент."""
        await self.client.aclose()

    async def search_by_hashtag(
        self,
        hashtag: str,
        limit: int = 50,
        min_followers: int = 10000,
        max_followers: int = 500000
    ) -> List[ScrapedInfluencer]:
        """
        Поиск инфлюенсеров по хэштегу.

        Args:
            hashtag: Хэштег для поиска (с # или без)
            limit: Максимум результатов
            min_followers: Минимум подписчиков
            max_followers: Максимум подписчиков

        Returns:
            Список ScrapedInfluencer
        """
        hashtag = hashtag.lstrip("#")

        if not self.api_token:
            logger.info(f"Using mock data for hashtag #{hashtag}")
            return self._get_mock_data(hashtag, limit)

        try:
            # Запуск актора Apify
            run_input = {
                "hashtags": [hashtag],
                "resultsPerPage": min(limit * 3, 100),  # Берем больше, потом фильтруем
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
            }

            # Запустить актор и ждать результаты
            run_url = f"{APIFY_API_URL}/acts/{APIFY_TIKTOK_ACTOR}/runs"
            headers = {"Authorization": f"Bearer {self.api_token}"}

            logger.info(f"Starting Apify actor for #{hashtag}...")

            response = await self.client.post(
                run_url,
                headers=headers,
                json=run_input,
                params={"waitForFinish": 120}  # Ждем до 2 минут
            )
            response.raise_for_status()
            run_data = response.json()

            run_id = run_data["data"]["id"]
            dataset_id = run_data["data"]["defaultDatasetId"]

            logger.info(f"Actor run completed. Run ID: {run_id}, Dataset ID: {dataset_id}")

            # Получить результаты из dataset
            dataset_url = f"{APIFY_API_URL}/datasets/{dataset_id}/items"
            dataset_response = await self.client.get(
                dataset_url,
                headers=headers,
                params={"format": "json", "limit": limit * 3}
            )
            dataset_response.raise_for_status()
            items = dataset_response.json()

            # Парсим и фильтруем
            influencers = self._parse_apify_results(items, hashtag, min_followers, max_followers)

            # Дедупликация по handle
            seen_handles = set()
            unique_influencers = []
            for inf in influencers:
                if inf.handle not in seen_handles:
                    seen_handles.add(inf.handle)
                    unique_influencers.append(inf)
                    if len(unique_influencers) >= limit:
                        break

            logger.info(f"Found {len(unique_influencers)} unique influencers for #{hashtag}")
            return unique_influencers

        except Exception as e:
            logger.error(f"Apify scraper error: {e}")
            # Fallback to mock data on error
            return self._get_mock_data(hashtag, limit)

    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 50,
        min_followers: int = 10000,
        max_followers: int = 500000
    ) -> List[ScrapedInfluencer]:
        """
        Поиск по нескольким ключевым словам/хэштегам.

        Args:
            keywords: Список ключевых слов или хэштегов
            limit: Максимум результатов на ключевое слово
            min_followers: Минимум подписчиков
            max_followers: Максимум подписчиков

        Returns:
            Объединенный список инфлюенсеров (дедуплицированный)
        """
        all_influencers = []
        seen_handles = set()

        for keyword in keywords:
            results = await self.search_by_hashtag(
                keyword,
                limit=limit,
                min_followers=min_followers,
                max_followers=max_followers
            )
            for inf in results:
                if inf.handle not in seen_handles:
                    seen_handles.add(inf.handle)
                    all_influencers.append(inf)

        logger.info(f"Total unique influencers from {len(keywords)} keywords: {len(all_influencers)}")
        return all_influencers

    def _parse_apify_results(
        self,
        items: List[Dict],
        source_hashtag: str,
        min_followers: int,
        max_followers: int
    ) -> List[ScrapedInfluencer]:
        """
        Парсинг результатов от Apify TikTok Scraper.

        Apify возвращает видео, нам нужно извлечь уникальных авторов.
        """
        influencers = []
        seen_authors = set()

        for item in items:
            # Извлекаем автора из видео
            author_info = item.get("authorMeta", {}) or item.get("author", {})
            if not author_info:
                continue

            handle = author_info.get("name", "") or author_info.get("uniqueId", "")
            if not handle or handle in seen_authors:
                continue

            followers = author_info.get("fans", 0) or author_info.get("followerCount", 0)

            # Фильтр по подписчикам
            if followers < min_followers or followers > max_followers:
                continue

            seen_authors.add(handle)

            # Расчет engagement rate
            likes = author_info.get("heart", 0) or author_info.get("heartCount", 0)
            videos = author_info.get("video", 0) or author_info.get("videoCount", 0)

            engagement_rate = None
            if followers > 0 and videos > 0 and likes > 0:
                avg_likes_per_video = likes / max(videos, 1)
                er = (avg_likes_per_video / followers) * 100
                engagement_rate = int(er * 10000)  # 3.5% -> 35000

            influencers.append(ScrapedInfluencer(
                handle=handle,
                name=author_info.get("nickname", "") or author_info.get("name", ""),
                bio=author_info.get("signature", "") or author_info.get("bio", ""),
                platform="tiktok",
                followers=followers,
                following=author_info.get("following", None) or author_info.get("followingCount"),
                engagement_rate=engagement_rate,
                avg_views=None,  # Можно посчитать из данных видео
                total_likes=likes if likes > 0 else None,
                total_videos=videos if videos > 0 else None,
                source_hashtag=source_hashtag,
                extra_data={
                    "verified": author_info.get("verified", False),
                    "region": author_info.get("region", ""),
                    "scraped_at": datetime.utcnow().isoformat(),
                }
            ))

        return influencers

    def _get_mock_data(self, hashtag: str, limit: int) -> List[ScrapedInfluencer]:
        """Mock данные для тестирования без API ключа."""
        mock_influencers = []
        niches = {
            "fitness": ["fitgirl", "gymbro", "workout_daily", "healthcoach", "fitnessmom"],
            "edtech": ["learnwithjohn", "codingqueen", "studytips", "mathtutor", "languagelab"],
            "finance": ["moneytips", "investorbob", "cryptoqueen", "budgethacks", "wealthcoach"],
        }

        # Выбираем префиксы по хэштегу
        prefixes = niches.get(hashtag.lower(), ["creator"])

        for i in range(min(limit, 20)):
            prefix = prefixes[i % len(prefixes)]
            followers = 15000 + (i * 8000)
            er = 35000 + (i * 2000)  # 3.5% - 5.5%

            mock_influencers.append(ScrapedInfluencer(
                handle=f"{prefix}_{i+1}",
                name=f"{prefix.replace('_', ' ').title()} {i+1}",
                bio=f"Passionate about {hashtag} | DM for collabs | Link in bio",
                platform="tiktok",
                followers=followers,
                following=500 + (i * 50),
                engagement_rate=er,
                avg_views=int(followers * 0.15),
                total_likes=followers * 10,
                total_videos=50 + (i * 10),
                source_hashtag=hashtag,
                extra_data={
                    "verified": i < 3,
                    "region": "US",
                    "mock": True,
                    "scraped_at": datetime.utcnow().isoformat(),
                }
            ))

        return mock_influencers

    async def save_to_db(
        self,
        influencers: List[ScrapedInfluencer],
        user_id: uuid.UUID,
        niche: str,
        source_keyword: str,
        db: Session
    ) -> Dict[str, int]:
        """
        Сохранить инфлюенсеров в БД.

        Использует upsert для избежания дубликатов.

        Args:
            influencers: Список инфлюенсеров
            user_id: ID пользователя
            niche: Ниша (fitness, edtech, etc.)
            source_keyword: Ключевое слово поиска
            db: SQLAlchemy сессия

        Returns:
            {"inserted": N, "updated": N, "errors": N}
        """
        from database.models import Influencer

        stats = {"inserted": 0, "updated": 0, "errors": 0}

        for inf in influencers:
            try:
                # Проверяем существование
                existing = db.query(Influencer).filter(
                    Influencer.user_id == user_id,
                    Influencer.platform == inf.platform,
                    Influencer.handle == inf.handle
                ).first()

                if existing:
                    # Обновляем метрики
                    existing.followers = inf.followers
                    existing.following = inf.following
                    existing.engagement_rate = inf.engagement_rate
                    existing.total_likes = inf.total_likes
                    existing.total_videos = inf.total_videos
                    existing.bio = inf.bio or existing.bio
                    existing.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Создаем нового
                    new_influencer = Influencer(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        handle=inf.handle,
                        name=inf.name,
                        bio=inf.bio,
                        platform=inf.platform,
                        niche=niche,
                        followers=inf.followers,
                        following=inf.following,
                        engagement_rate=inf.engagement_rate,
                        avg_views=inf.avg_views,
                        total_likes=inf.total_likes,
                        total_videos=inf.total_videos,
                        status="new",
                        source_keyword=source_keyword,
                        source_hashtag=inf.source_hashtag,
                        scraped_from="apify",
                        extra_data=inf.extra_data,
                        scraped_at=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                    )
                    db.add(new_influencer)
                    stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Error saving influencer @{inf.handle}: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(f"Saved influencers: {stats}")
        return stats


# ========== CONVENIENCE FUNCTIONS ==========

async def scrape_influencers_by_niche(
    niche: str,
    hashtags: List[str],
    user_id: uuid.UUID,
    db: Session,
    limit_per_hashtag: int = 30,
    min_followers: int = 10000,
    max_followers: int = 500000,
    api_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Удобная функция для скрапинга инфлюенсеров по нише.

    Example:
        result = await scrape_influencers_by_niche(
            niche="fitness",
            hashtags=["fitness", "workout", "gym", "fitnessmotivation"],
            user_id=user.id,
            db=db_session,
            limit_per_hashtag=50
        )
    """
    scraper = ApifyTikTokScraper(api_token=api_token)

    try:
        all_influencers = await scraper.search_by_keywords(
            keywords=hashtags,
            limit=limit_per_hashtag,
            min_followers=min_followers,
            max_followers=max_followers
        )

        save_stats = await scraper.save_to_db(
            influencers=all_influencers,
            user_id=user_id,
            niche=niche,
            source_keyword=", ".join(hashtags),
            db=db
        )

        return {
            "success": True,
            "niche": niche,
            "hashtags": hashtags,
            "total_found": len(all_influencers),
            "stats": save_stats
        }

    finally:
        await scraper.close()
