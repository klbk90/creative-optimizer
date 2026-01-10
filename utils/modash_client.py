"""
Modash API Client - Micro-influencer discovery and analytics.

Modash API documentation: https://docs.modash.io/

Features:
- Search influencers by niche, followers, engagement, geo
- Get influencer analytics (audience demographics, engagement rate)
- Export influencer lists for outreach campaigns
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime


class ModashClient:
    """
    Client for Modash influencer marketing API.

    Supports MOCK MODE when MODASH_API_KEY is not set - returns realistic fake data
    for frontend testing without requiring a real API key.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize Modash client.

        Args:
            api_key: Modash API key (or set MODASH_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("MODASH_API_KEY")
        self.mock_mode = not self.api_key  # Enable mock mode if no API key

        if self.mock_mode:
            # Mock mode - для тестирования фронтенда без реального API ключа
            self.base_url = None
            self.headers = None
        else:
            self.base_url = "https://api.modash.io/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

    def search_influencers(
        self,
        platform: str = "instagram",
        keywords: List[str] = None,
        categories: List[str] = None,
        min_followers: int = 5000,
        max_followers: int = 50000,
        min_engagement_rate: float = 0.03,
        audience_geo: List[str] = None,
        audience_languages: List[str] = None,
        has_contact_email: bool = True,
        is_verified: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Search for influencers based on filters.

        Args:
            platform: "instagram", "tiktok", "youtube"
            keywords: Keywords in bio/content (e.g., ["programming", "python", "coding"])
            categories: Content categories (e.g., ["Education", "Technology"])
            min_followers: Minimum follower count
            max_followers: Maximum follower count
            min_engagement_rate: Minimum engagement rate (e.g., 0.03 = 3%)
            audience_geo: ISO country codes (e.g., ["US", "GB", "CA"])
            audience_languages: Language codes (e.g., ["en", "ru"])
            has_contact_email: Filter by presence of contact email
            is_verified: Filter by verified accounts
            limit: Number of results per page
            offset: Pagination offset

        Returns:
            {
                "data": [
                    {
                        "username": "tech_creator",
                        "fullname": "Tech Creator",
                        "follower_count": 25000,
                        "engagement_rate": 0.045,  # 4.5%
                        "contact_email": "creator@email.com",
                        "audience": {
                            "geolocations": [{"code": "US", "weight": 0.65}],
                            "languages": [{"code": "en", "weight": 0.85}]
                        },
                        ...
                    }
                ],
                "total": 150,
                "page": 1
            }
        """
        # MOCK MODE - возвращаем заглушку для тестирования фронтенда
        if self.mock_mode:
            return self._get_mock_influencers(
                platform=platform,
                min_followers=min_followers,
                max_followers=max_followers,
                limit=limit
            )

        # Build filter payload
        filters = {
            "follower_count": {
                "from": min_followers,
                "to": max_followers
            },
            "engagement_rate": {
                "from": min_engagement_rate
            },
            "is_verified": is_verified,
            "has_contact_email": has_contact_email
        }

        # Add optional filters
        if keywords:
            filters["keywords"] = keywords

        if categories:
            filters["categories"] = categories

        if audience_geo:
            filters["audience_geolocations"] = audience_geo

        if audience_languages:
            filters["audience_languages"] = audience_languages

        # Request payload
        payload = {
            "filters": filters,
            "sort": {"field": "engagement_rate", "direction": "desc"},
            "limit": limit,
            "offset": offset
        }

        # Make request
        endpoint = f"{self.base_url}/search/{platform}"

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                return {
                    "data": data.get("data", []),
                    "total": data.get("total", 0),
                    "page": offset // limit + 1,
                    "limit": limit
                }
            else:
                error_msg = f"Modash API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {"error": error_msg, "data": [], "total": 0}

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg, "data": [], "total": 0}

    def _get_mock_influencers(
        self,
        platform: str = "instagram",
        min_followers: int = 5000,
        max_followers: int = 50000,
        limit: int = 10
    ) -> Dict:
        """
        Generate MOCK influencer data for testing without API key.

        Returns realistic fake data that matches Modash API format.
        """
        mock_influencers = [
            {
                "username": f"edtech_creator_{i}",
                "fullname": f"Education Creator {i}",
                "platform": platform,
                "follower_count": min_followers + (i * 2000),
                "engagement_rate": 0.035 + (i * 0.005),  # 3.5% - 8%
                "avg_likes": 250 + (i * 50),
                "avg_comments": 15 + (i * 3),
                "contact_email": f"creator{i}@email.com" if i % 2 == 0 else None,
                "bio": f"🎓 Helping students learn faster | EdTech enthusiast | DM for collabs",
                "is_verified": i < 2,  # Only first 2 are verified
                "audience": {
                    "geolocations": [
                        {"code": "US", "weight": 0.65},
                        {"code": "GB", "weight": 0.15},
                        {"code": "CA", "weight": 0.10}
                    ],
                    "languages": [
                        {"code": "en", "weight": 0.95}
                    ],
                    "ages": [
                        {"code": "18-24", "weight": 0.45},
                        {"code": "25-34", "weight": 0.35}
                    ],
                    "genders": [
                        {"code": "MALE", "weight": 0.52},
                        {"code": "FEMALE", "weight": 0.48}
                    ]
                },
                "profile_pic_url": f"https://via.placeholder.com/150?text=Creator{i}",
                "profile_url": f"https://{platform}.com/{platform=='tiktok' and '@' or ''}edtech_creator_{i}",
            }
            for i in range(1, min(limit + 1, 11))
        ]

        return {
            "data": mock_influencers,
            "total": 47,  # Fake total
            "page": 1,
            "limit": limit,
            "mock_mode": True  # Indicate this is fake data
        }

    def get_influencer_profile(
        self,
        username: str,
        platform: str = "instagram"
    ) -> Optional[Dict]:
        """
        Get detailed profile for a specific influencer.

        Args:
            username: Influencer username (without @)
            platform: "instagram", "tiktok", "youtube"

        Returns:
            Detailed profile or None if not found
        """

        endpoint = f"{self.base_url}/{platform}/{username}"

        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"⚠️ Influencer not found: @{username}")
                return None
            else:
                print(f"❌ API error: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None

    def search_edtech_influencers(
        self,
        niche: str = "programming",
        geo: List[str] = ["US", "GB", "CA"],
        language: str = "en",
        min_followers: int = 5000,
        max_followers: int = 50000,
        min_engagement: float = 0.03,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for EdTech micro-influencers.

        Pre-configured for EdTech niches:
        - programming, design, english, career, business

        Args:
            niche: EdTech niche
            geo: Target countries
            language: Content language
            min_followers: Min follower count
            max_followers: Max follower count
            min_engagement: Min engagement rate
            limit: Number of results

        Returns:
            List of influencers
        """

        # EdTech niche keywords
        niche_keywords_map = {
            "programming": ["programming", "coding", "developer", "python", "javascript", "web development"],
            "design": ["design", "figma", "ui", "ux", "web design", "graphic design"],
            "english": ["english", "language learning", "grammar", "vocabulary", "speaking"],
            "career": ["career", "resume", "job search", "interview", "remote work"],
            "business": ["business", "entrepreneurship", "startup", "marketing", "sales"],
            "general": ["education", "learning", "courses", "skills", "online learning"]
        }

        keywords = niche_keywords_map.get(niche, niche_keywords_map["general"])

        result = self.search_influencers(
            platform="instagram",
            keywords=keywords,
            categories=["Education", "Technology", "Business"],
            min_followers=min_followers,
            max_followers=max_followers,
            min_engagement_rate=min_engagement,
            audience_geo=geo,
            audience_languages=[language],
            has_contact_email=True,
            is_verified=False,  # Micro-influencers typically not verified
            limit=limit
        )

        return result.get("data", [])

    def export_influencer_list(
        self,
        influencers: List[Dict],
        output_format: str = "csv"
    ) -> str:
        """
        Export influencer list to CSV or JSON.

        Args:
            influencers: List of influencer data
            output_format: "csv" or "json"

        Returns:
            Formatted output string
        """

        if output_format == "csv":
            # CSV headers
            csv_lines = [
                "username,fullname,followers,engagement_rate,email,platform,url"
            ]

            for inf in influencers:
                username = inf.get("username", "")
                fullname = inf.get("fullname", "")
                followers = inf.get("follower_count", 0)
                er = inf.get("engagement_rate", 0)
                email = inf.get("contact_email", "")
                platform = "instagram"
                url = f"https://instagram.com/{username}"

                csv_lines.append(
                    f"{username},{fullname},{followers},{er:.4f},{email},{platform},{url}"
                )

            return "\n".join(csv_lines)

        elif output_format == "json":
            import json
            return json.dumps(influencers, indent=2)

        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def get_audience_insights(
        self,
        username: str,
        platform: str = "instagram"
    ) -> Optional[Dict]:
        """
        Get audience demographics for an influencer.

        Returns:
            {
                "geolocations": [{"code": "US", "weight": 0.65}, ...],
                "languages": [{"code": "en", "weight": 0.85}, ...],
                "age_groups": [{"code": "18-24", "weight": 0.35}, ...],
                "gender": {"male": 0.45, "female": 0.55}
            }
        """

        profile = self.get_influencer_profile(username, platform)

        if not profile:
            return None

        return profile.get("audience", {})


# ========== HELPER FUNCTIONS ==========

def find_micro_influencers_for_creative(
    creative_id: str,
    product_category: str,
    target_niche: str,
    target_geo: List[str] = ["US", "GB", "CA"],
    n_influencers: int = 20
) -> List[Dict]:
    """
    Find micro-influencers for testing a creative.

    Usage:
    ```python
    from utils.modash_client import find_micro_influencers_for_creative

    influencers = find_micro_influencers_for_creative(
        creative_id="123e4567-e89b-12d3-a456-426614174000",
        product_category="language_learning",
        target_niche="english",
        target_geo=["US", "GB"],
        n_influencers=20
    )

    print(f"Found {len(influencers)} influencers")
    ```
    """

    try:
        client = ModashClient()

        influencers = client.search_edtech_influencers(
            niche=target_niche,
            geo=target_geo,
            limit=n_influencers
        )

        print(f"✅ Found {len(influencers)} micro-influencers in '{target_niche}' niche")

        return influencers

    except Exception as e:
        print(f"❌ Error finding influencers: {e}")
        return []


if __name__ == "__main__":
    # Test example
    print("🔍 Modash Client - EdTech Edition")
    print("\nUsage:")
    print("  export MODASH_API_KEY=your_api_key")
    print("\nExample:")
    print("  from utils.modash_client import ModashClient")
    print("  client = ModashClient()")
    print("  influencers = client.search_edtech_influencers(niche='programming', limit=10)")
    print("\nSupported niches:")
    print("  - programming, design, english, career, business, general")
