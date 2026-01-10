"""
Influencer Search Router - Modash API integration with AI scoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import os
import requests

from database.base import get_db
from database.models import TrafficSource, Creative
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/influencers", tags=["Influencer Search"])

MODASH_API_KEY = os.getenv("MODASH_API_KEY", "")
MODASH_API_URL = "https://api.modash.io/v1"


# ========== SCHEMAS ==========

class InfluencerSearchRequest(BaseModel):
    """Modash search request."""
    niche: str
    min_followers: int = 10000
    max_followers: int = 100000
    min_engagement_rate: float = 2.0
    platform: str = "instagram"
    location: Optional[str] = None
    limit: int = 20


class InfluencerResult(BaseModel):
    """Influencer search result with AI score."""
    id: str
    handle: str
    name: str
    followers: int
    engagement_rate: float
    platform: str
    niche: List[str]
    ai_score: float  # Our custom score
    ai_reasoning: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class AddToTestRequest(BaseModel):
    """Add influencer to test campaign."""
    creative_id: str
    influencer_handle: str
    influencer_followers: int
    platform: str


# ========== HELPERS ==========

def calculate_ai_score(influencer_data: dict, creative_pain: str, creative_niche: str) -> tuple[float, str]:
    """
    Calculate AI Score based on influencer-creative match.

    Returns:
        (score, reasoning)
    """
    score = 50.0  # Base score
    reasoning_parts = []

    # Niche match (up to +30 points)
    influencer_niches = influencer_data.get("topics", [])
    if creative_niche.lower() in [n.lower() for n in influencer_niches]:
        score += 30
        reasoning_parts.append(f"✅ Exact niche match ({creative_niche})")
    elif any(creative_niche.lower() in n.lower() or n.lower() in creative_niche.lower() for n in influencer_niches):
        score += 15
        reasoning_parts.append(f"⚠️ Partial niche match")
    else:
        score -= 10
        reasoning_parts.append(f"❌ Niche mismatch")

    # Engagement rate (up to +20 points)
    engagement_rate = influencer_data.get("engagement_rate", 0)
    if engagement_rate > 5.0:
        score += 20
        reasoning_parts.append(f"✅ High engagement ({engagement_rate:.1f}%)")
    elif engagement_rate > 3.0:
        score += 10
        reasoning_parts.append(f"⚠️ Good engagement ({engagement_rate:.1f}%)")
    else:
        reasoning_parts.append(f"Low engagement ({engagement_rate:.1f}%)")

    # Follower size (micro-influencer bonus)
    followers = influencer_data.get("followers", 0)
    if 10000 <= followers <= 50000:
        score += 10
        reasoning_parts.append(f"✅ Micro-influencer sweet spot")
    elif followers > 100000:
        score -= 5
        reasoning_parts.append(f"⚠️ Too large for micro-testing")

    # Cap at 100
    score = min(100, max(0, score))

    reasoning = " | ".join(reasoning_parts)

    return score, reasoning


def search_modash(params: InfluencerSearchRequest) -> List[dict]:
    """
    Search Modash API for influencers.

    Returns:
        List of influencer data dicts
    """

    # MVP: Mock data if no API key
    if not MODASH_API_KEY:
        logger.warning("MODASH_API_KEY not set. Using mock data.")
        return [
            {
                "id": f"inf_{i}",
                "handle": f"@fitness_creator_{i}",
                "name": f"Fitness Creator {i}",
                "followers": 25000 + (i * 5000),
                "engagement_rate": 3.5 + (i * 0.3),
                "platform": "instagram",
                "topics": ["fitness", "health", "wellness"],
                "avatar_url": f"https://i.pravatar.cc/150?img={i}",
                "bio": f"Fitness enthusiast | Helping people transform their lives"
            }
            for i in range(1, min(params.limit + 1, 21))
        ]

    # Real Modash API call
    headers = {
        "Authorization": f"Bearer {MODASH_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "filter": {
            "audience": {
                "age": {"code": ["18-24", "25-34"]},
                "location": {"value": [params.location]} if params.location else None,
            },
            "profile": {
                "followers": {"min": params.min_followers, "max": params.max_followers},
                "engagementRate": {"min": params.min_engagement_rate},
                "topics": [params.niche],
            },
        },
        "sort": {"field": "engagementRate", "direction": "desc"},
        "page": {"size": params.limit}
    }

    try:
        response = requests.post(
            f"{MODASH_API_URL}/instagram/search",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        logger.error(f"Modash API error: {e}")
        raise HTTPException(status_code=500, detail=f"Modash API error: {str(e)}")


# ========== ENDPOINTS ==========

@router.post("/search", response_model=List[InfluencerResult])
async def search_influencers(
    request: InfluencerSearchRequest,
    creative_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    🔍 Search for influencers via Modash API with AI scoring.

    Example:
    ```json
    {
      "niche": "fitness",
      "min_followers": 10000,
      "max_followers": 50000,
      "min_engagement_rate": 2.5,
      "platform": "instagram",
      "limit": 20
    }
    ```

    Returns influencers with AI Score based on creative match.
    """

    # Get creative info for AI scoring
    creative_pain = "unknown"
    creative_niche = request.niche

    if creative_id:
        creative = db.query(Creative).filter(Creative.id == uuid.UUID(creative_id)).first()
        if creative:
            creative_pain = getattr(creative, 'target_audience_pain', 'unknown')
            creative_niche = creative.product_category or request.niche

    # Search Modash
    influencers_raw = search_modash(request)

    # Add AI scores
    results = []
    for inf in influencers_raw:
        ai_score, ai_reasoning = calculate_ai_score(inf, creative_pain, creative_niche)

        results.append(InfluencerResult(
            id=inf.get("id", str(uuid.uuid4())),
            handle=inf.get("handle", ""),
            name=inf.get("name", ""),
            followers=inf.get("followers", 0),
            engagement_rate=inf.get("engagement_rate", 0.0),
            platform=inf.get("platform", request.platform),
            niche=inf.get("topics", []),
            ai_score=ai_score,
            ai_reasoning=ai_reasoning,
            avatar_url=inf.get("avatar_url"),
            bio=inf.get("bio")
        ))

    # Sort by AI score
    results.sort(key=lambda x: x.ai_score, reverse=True)

    return results


@router.post("/add-to-test")
async def add_influencer_to_test(
    request: AddToTestRequest,
    db: Session = Depends(get_db)
):
    """
    ➕ Add influencer to test campaign.

    Creates TrafficSource with unique UTM link for this influencer.

    Example:
    ```json
    {
      "creative_id": "uuid-123",
      "influencer_handle": "@fitness_creator_5",
      "influencer_followers": 35000,
      "platform": "instagram"
    }
    ```
    """

    # Get creative
    creative = db.query(Creative).filter(Creative.id == uuid.UUID(request.creative_id)).first()

    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")

    # Generate UTM ID
    handle_clean = request.influencer_handle.replace("@", "").replace(".", "_")
    utm_id = f"inf_{handle_clean}_{str(uuid.uuid4())[:8]}"

    # Create TrafficSource
    test_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    traffic_source = TrafficSource(
        id=uuid.uuid4(),
        user_id=test_user_id,
        utm_source=request.platform,
        utm_medium="influencer",
        utm_campaign=f"creative_{str(creative.id)[:8]}",
        utm_content=request.influencer_handle,
        utm_id=utm_id,
        clicks=0,
        conversions=0,
        revenue=0,
        first_click=datetime.utcnow(),
        referrer=f"influencer_search|{request.influencer_handle}",
        # Store influencer metadata
        device_type=None,  # Will be tracked later
        external_id=request.influencer_handle
    )

    db.add(traffic_source)
    db.commit()
    db.refresh(traffic_source)

    # Generate landing URL
    landing_url = f"http://localhost:8000/api/v1/edtech/landing?utm_id={utm_id}"

    return {
        "success": True,
        "utm_id": utm_id,
        "landing_url": landing_url,
        "influencer_handle": request.influencer_handle,
        "creative_name": creative.name,
        "message": f"✅ Added {request.influencer_handle} to test campaign!",
        "instructions": f"Send this link to {request.influencer_handle}: {landing_url}"
    }
