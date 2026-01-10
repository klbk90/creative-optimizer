"""
Seed benchmark videos from Facebook Ad Library.

Эти видео анализируются СРАЗУ (is_benchmark=True).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import SessionLocal
from database.models import Creative
from datetime import datetime
import uuid

# Test user ID
TEST_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


# FB Ad Library winning videos (публичные примеры)
BENCHMARK_VIDEOS = [
    {
        "name": "Duolingo - 'Too Busy to Learn?' Winner",
        "video_url": "https://example.com/duolingo-winner.mp4",  # Замените на реальный URL
        "product_category": "language_learning",
        "creative_type": "ugc",
        "estimated_cvr": 0.145,  # 14.5% CVR
        "estimated_conversions": 87,
        "estimated_impressions": 60000,
        "reasoning": "FB Ad Library top performer - Problem agitation hook"
    },
    {
        "name": "Peloton - Before/After Transformation",
        "video_url": "https://example.com/peloton-winner.mp4",
        "product_category": "fitness",
        "creative_type": "ugc",
        "estimated_cvr": 0.132,
        "estimated_conversions": 124,
        "estimated_impressions": 94000,
        "reasoning": "FB Ad Library winner - Transformation + social proof"
    },
    {
        "name": "Codecademy - 'Are You Missing Out?' FOMO",
        "video_url": "https://example.com/codecademy-winner.mp4",
        "product_category": "programming",
        "creative_type": "ugc",
        "estimated_cvr": 0.118,
        "estimated_conversions": 65,
        "estimated_impressions": 55000,
        "reasoning": "FB Ad Library winner - Question + FOMO hook"
    },
    {
        "name": "Babbel - Social Proof Testimonial",
        "video_url": "https://example.com/babbel-winner.mp4",
        "product_category": "language_learning",
        "creative_type": "ugc",
        "estimated_cvr": 0.095,
        "estimated_conversions": 43,
        "estimated_impressions": 45000,
        "reasoning": "FB Ad Library - Trust-building through real stories"
    },
    {
        "name": "Beachbody - Transformation Guarantee",
        "video_url": "https://example.com/beachbody-winner.mp4",
        "product_category": "fitness",
        "creative_type": "ugc",
        "estimated_cvr": 0.087,
        "estimated_conversions": 56,
        "estimated_impressions": 64000,
        "reasoning": "FB Ad Library - Long-form transformation with guarantee"
    },
]


def seed_benchmark_videos():
    """
    Загружает benchmark videos в базу с флагом is_benchmark=True.

    Эти видео будут проанализированы Claude Vision сразу.
    """
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(Creative).filter(
            Creative.is_benchmark == True
        ).count()

        if existing > 0:
            print(f"✅ Already seeded {existing} benchmark videos. Skipping.")
            return

        print("🌱 Seeding benchmark videos from Facebook Ad Library...")

        for video_data in BENCHMARK_VIDEOS:
            creative_id = uuid.uuid4()

            creative = Creative(
                id=creative_id,
                user_id=TEST_USER_ID,
                name=video_data["name"],
                video_url=video_data["video_url"],
                product_category=video_data["product_category"],
                creative_type=video_data["creative_type"],
                # Metrics from FB Ad Library
                impressions=video_data["estimated_impressions"],
                conversions=video_data["estimated_conversions"],
                cvr=int(video_data["estimated_cvr"] * 10000),
                # Benchmark flag
                is_benchmark=True,
                analysis_status='pending',  # Will be analyzed immediately on startup
                # AI tags - будут заполнены Claude Vision
                hook_type="unknown",
                emotion="unknown",
                pacing="medium",
                target_audience_pain="unknown",
                created_at=datetime.utcnow()
            )

            db.add(creative)
            print(f"  ✅ {video_data['name']} → {video_data['estimated_cvr']*100:.1f}% CVR")

        db.commit()

        print(f"\n✅ Seeded {len(BENCHMARK_VIDEOS)} benchmark videos!")
        print(f"\n🎯 These will be analyzed by Claude Vision on first startup!")
        print(f"🏆 After analysis, they'll populate the 'Market Trends' tab!")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_benchmark_videos()
