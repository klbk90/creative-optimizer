"""
TikTok Creative Center scraper.

Extracts top-performing ads from TikTok Creative Center:
https://ads.tiktok.com/business/creativecenter/

Free public data with metrics:
- Views, Likes, Shares
- Upload date, Last active date (→ lifespan!)
- Geography, Platform
- Creative patterns (hook, emotion visible in video)

NO API KEY NEEDED - all data is public!
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


class TikTokCreativeCenterScraper:
    """
    Scrape TikTok Creative Center for public ad performance data.
    """

    BASE_URL = "https://ads.tiktok.com/business/creativecenter/api/v1"

    # Industry categories
    CATEGORIES = {
        "fitness": "Health & Fitness",
        "language_learning": "Education",
        "finance": "Finance",
        "gaming": "Gaming",
        "ecommerce": "E-commerce"
    }

    def __init__(self, region: str = "US"):
        """
        Args:
            region: Country code (US, UK, JP, etc)
        """
        self.region = region
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })

    def scrape_top_ads(
        self,
        category: str,
        limit: int = 100,
        time_range_days: int = 30
    ) -> List[Dict]:
        """
        Scrape top-performing ads from TikTok Creative Center.

        Args:
            category: Category (fitness, finance, etc)
            limit: Max number of ads to return
            time_range_days: Look back period (7, 30, 90 days)

        Returns:
            [
                {
                    "video_id": "7123456789",
                    "video_url": "https://...",
                    "views": 500000,
                    "likes": 25000,
                    "shares": 5000,
                    "comments": 2000,
                    "first_seen": "2025-01-15",
                    "last_seen": "2025-02-08",
                    "lifespan_days": 24,
                    "engagement_rate": 0.064,  # (likes+shares+comments)/views
                    "region": "US",
                    "industry": "fitness"
                },
                ...
            ]
        """

        logger.info(
            f"Scraping TikTok Creative Center: category={category}, "
            f"region={self.region}, limit={limit}"
        )

        # TODO: Implement actual scraping
        # For now, return simulated data based on category

        # In production, you would:
        # 1. Navigate to Creative Center
        # 2. Filter by category, region, time range
        # 3. Extract video IDs and metrics
        # 4. Parse lifespan from "Active since" date

        logger.warning(
            "⚠️  TikTok Creative Center scraping not yet implemented. "
            "Returning simulated data for development."
        )

        return self._get_simulated_data(category, limit, time_range_days)

    def _get_simulated_data(
        self,
        category: str,
        limit: int,
        time_range_days: int
    ) -> List[Dict]:
        """
        Simulated data for development/testing.

        In production, replace this with actual scraping.
        """

        base_date = datetime.utcnow() - timedelta(days=time_range_days)

        if category == "fitness":
            return self._simulate_fitness_ads(base_date, limit)
        elif category == "finance":
            return self._simulate_finance_ads(base_date, limit)
        else:
            return self._simulate_generic_ads(base_date, limit)

    def _simulate_fitness_ads(self, base_date: datetime, limit: int) -> List[Dict]:
        """Simulated fitness ads data."""

        ads = []

        # Pattern 1: Transformation videos (STABLE - 60+ days)
        for i in range(min(30, limit)):
            first_seen = base_date + timedelta(days=i * 2)
            last_seen = first_seen + timedelta(days=60 + i)  # Long lifespan

            ads.append({
                "video_id": f"fit_transform_{i}",
                "video_url": f"https://tiktok.com/@fitness/video/{1000+i}",
                "views": 400000 + i * 10000,
                "likes": 20000 + i * 500,
                "shares": 4000 + i * 100,
                "comments": 1500 + i * 50,
                "first_seen": first_seen.strftime("%Y-%m-%d"),
                "last_seen": last_seen.strftime("%Y-%m-%d"),
                "lifespan_days": (last_seen - first_seen).days,
                "engagement_rate": round((20000 + 4000 + 1500) / 400000, 4),
                "region": self.region,
                "industry": "fitness",
                "pattern_hint": "transformation"
            })

        # Pattern 2: Challenge videos (TREND - 7-14 days)
        for i in range(min(20, limit - 30)):
            first_seen = base_date + timedelta(days=20 + i)
            last_seen = first_seen + timedelta(days=10)  # Short lifespan (TREND!)

            ads.append({
                "video_id": f"fit_challenge_{i}",
                "video_url": f"https://tiktok.com/@fitness/video/{2000+i}",
                "views": 800000,  # High views but short-lived
                "likes": 50000,
                "shares": 15000,
                "comments": 3000,
                "first_seen": first_seen.strftime("%Y-%m-%d"),
                "last_seen": last_seen.strftime("%Y-%m-%d"),
                "lifespan_days": (last_seen - first_seen).days,
                "engagement_rate": round((50000 + 15000 + 3000) / 800000, 4),
                "region": self.region,
                "industry": "fitness",
                "pattern_hint": "challenge_trend"
            })

        return ads[:limit]

    def _simulate_finance_ads(self, base_date: datetime, limit: int) -> List[Dict]:
        """Simulated finance ads data."""

        ads = []

        for i in range(limit):
            first_seen = base_date + timedelta(days=i * 3)
            last_seen = first_seen + timedelta(days=45 + i % 30)

            ads.append({
                "video_id": f"fin_{i}",
                "video_url": f"https://tiktok.com/@finance/video/{3000+i}",
                "views": 300000 + i * 5000,
                "likes": 15000 + i * 300,
                "shares": 2500 + i * 50,
                "comments": 1000 + i * 20,
                "first_seen": first_seen.strftime("%Y-%m-%d"),
                "last_seen": last_seen.strftime("%Y-%m-%d"),
                "lifespan_days": (last_seen - first_seen).days,
                "engagement_rate": round((15000 + 2500 + 1000) / 300000, 4),
                "region": self.region,
                "industry": "finance",
                "pattern_hint": "wealth_building"
            })

        return ads

    def _simulate_generic_ads(self, base_date: datetime, limit: int) -> List[Dict]:
        """Generic simulated data."""

        return [{
            "video_id": f"generic_{i}",
            "video_url": f"https://tiktok.com/video/{4000+i}",
            "views": 250000,
            "likes": 12000,
            "shares": 2000,
            "comments": 800,
            "first_seen": (base_date + timedelta(days=i*2)).strftime("%Y-%m-%d"),
            "last_seen": (base_date + timedelta(days=i*2 + 30)).strftime("%Y-%m-%d"),
            "lifespan_days": 30,
            "engagement_rate": 0.059,
            "region": self.region,
            "industry": "generic",
            "pattern_hint": "unknown"
        } for i in range(limit)]

    def calculate_stability_score(self, ad: Dict) -> float:
        """
        Calculate stability score (0-1) based on lifespan and engagement.

        Stable ad characteristics:
        - Lifespan > 30 days
        - Consistent engagement (not spike)
        - Moderate views (not viral spike)

        Returns:
            0-1 score (1 = very stable)
        """

        lifespan_days = ad["lifespan_days"]
        views = ad["views"]
        engagement_rate = ad["engagement_rate"]

        # Lifespan score (0-0.6)
        if lifespan_days >= 60:
            lifespan_score = 0.6
        elif lifespan_days >= 30:
            lifespan_score = 0.4
        elif lifespan_days >= 14:
            lifespan_score = 0.2
        else:
            lifespan_score = 0.0  # Trend

        # Engagement consistency score (0-0.2)
        # Too high engagement = viral spike (unstable)
        # Moderate engagement = stable
        if 0.03 <= engagement_rate <= 0.08:
            engagement_score = 0.2  # Sweet spot
        elif 0.02 <= engagement_rate <= 0.10:
            engagement_score = 0.1
        else:
            engagement_score = 0.0

        # Views score (0-0.2)
        # Moderate views = stable
        # Very high views = viral (unstable)
        if 200000 <= views <= 600000:
            views_score = 0.2  # Stable range
        elif 100000 <= views <= 1000000:
            views_score = 0.1
        else:
            views_score = 0.0

        stability = lifespan_score + engagement_score + views_score

        return round(stability, 3)


def scrape_tiktok_top_ads(category: str, limit: int = 100) -> List[Dict]:
    """
    Quick helper function to scrape TikTok Creative Center.

    Usage:
    ```python
    from utils.scrapers.tiktok_creative_center import scrape_tiktok_top_ads

    ads = scrape_tiktok_top_ads(category="fitness", limit=50)

    for ad in ads:
        print(f"{ad['video_id']}: {ad['lifespan_days']} days, stability={ad['stability_score']}")
    ```
    """

    scraper = TikTokCreativeCenterScraper(region="US")
    ads = scraper.scrape_top_ads(category=category, limit=limit)

    # Add stability scores
    for ad in ads:
        ad["stability_score"] = scraper.calculate_stability_score(ad)

    return ads
