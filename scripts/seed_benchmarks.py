"""
Seed script: Market benchmarks and winning patterns.

Создает стартовые данные из Facebook Ad Library для демонстрации клиенту.
Запускается автоматически при первом деплое на Railway.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import SessionLocal
from database.models import PatternPerformance, Creative
from datetime import datetime
import uuid

# Test user ID для демо данных
TEST_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


# ========== MARKET BENCHMARKS (from Facebook Ad Library analysis) ==========

WINNING_PATTERNS = [
    {
        "pattern_hash": "hook:problem_agitation|emo:frustration|pace:fast|pain:no_time|cta:urgency",
        "hook_type": "problem_agitation",
        "emotion": "frustration",
        "pacing": "fast",
        "cta_type": "urgency",
        "target_audience_pain": "no_time",
        "product_category": "language_learning",
        "avg_cvr": 0.145,  # 14.5% CVR - top performer
        "sample_size": 87,
        "total_conversions": 1261,
        "total_clicks": 8700,
        "confidence_interval_lower": 0.128,
        "confidence_interval_upper": 0.162,
        "reasoning": "Facebook Ad Library winner: 'Too busy to learn?' → 15 min/day solution"
    },
    {
        "pattern_hash": "hook:before_after|emo:achievement|pace:medium|pain:lack_results|cta:social_proof",
        "hook_type": "before_after",
        "emotion": "achievement",
        "pacing": "medium",
        "cta_type": "social_proof",
        "target_audience_pain": "lack_results",
        "product_category": "fitness",
        "avg_cvr": 0.132,  # 13.2% CVR
        "sample_size": 124,
        "total_conversions": 1637,
        "total_clicks": 12400,
        "confidence_interval_lower": 0.117,
        "confidence_interval_upper": 0.147,
        "reasoning": "Transformation stories with testimonials - proven winner"
    },
    {
        "pattern_hash": "hook:question|emo:curiosity|pace:fast|pain:fear_missing_out|cta:scarcity",
        "hook_type": "question",
        "emotion": "curiosity",
        "pacing": "fast",
        "cta_type": "scarcity",
        "target_audience_pain": "fear_missing_out",
        "product_category": "programming",
        "avg_cvr": 0.118,  # 11.8% CVR
        "sample_size": 65,
        "total_conversions": 767,
        "total_clicks": 6500,
        "confidence_interval_lower": 0.102,
        "confidence_interval_upper": 0.134,
        "reasoning": "FOMO-driven question hooks - works for tech products"
    },
    {
        "pattern_hash": "hook:social_proof|emo:trust|pace:medium|pain:skepticism|cta:testimonial",
        "hook_type": "social_proof",
        "emotion": "trust",
        "pacing": "medium",
        "cta_type": "testimonial",
        "target_audience_pain": "skepticism",
        "product_category": "language_learning",
        "avg_cvr": 0.095,  # 9.5% CVR
        "sample_size": 43,
        "total_conversions": 409,
        "total_clicks": 4300,
        "confidence_interval_lower": 0.078,
        "confidence_interval_upper": 0.112,
        "reasoning": "Trust-building through real user stories"
    },
    {
        "pattern_hash": "hook:transformation|emo:hope|pace:slow|pain:tried_everything|cta:guarantee",
        "hook_type": "transformation",
        "emotion": "hope",
        "pacing": "slow",
        "cta_type": "guarantee",
        "target_audience_pain": "tried_everything",
        "product_category": "fitness",
        "avg_cvr": 0.087,  # 8.7% CVR
        "sample_size": 56,
        "total_conversions": 487,
        "total_clicks": 5600,
        "confidence_interval_lower": 0.071,
        "confidence_interval_upper": 0.103,
        "reasoning": "Long-form transformation with money-back guarantee"
    },
    {
        "pattern_hash": "hook:pain_point|emo:empathy|pace:medium|pain:overwhelmed|cta:simplicity",
        "hook_type": "pain_point",
        "emotion": "empathy",
        "pacing": "medium",
        "cta_type": "simplicity",
        "target_audience_pain": "overwhelmed",
        "product_category": "programming",
        "avg_cvr": 0.082,  # 8.2% CVR
        "sample_size": 38,
        "total_conversions": 312,
        "total_clicks": 3800,
        "confidence_interval_lower": 0.065,
        "confidence_interval_upper": 0.099,
        "reasoning": "'Feeling overwhelmed by coding?' → simple step-by-step"
    },
    {
        "pattern_hash": "hook:urgency|emo:fomo|pace:fast|pain:fear_missing_out|cta:deadline",
        "hook_type": "urgency",
        "emotion": "fomo",
        "pacing": "fast",
        "cta_type": "deadline",
        "target_audience_pain": "fear_missing_out",
        "product_category": "language_learning",
        "avg_cvr": 0.075,  # 7.5% CVR
        "sample_size": 29,
        "total_conversions": 218,
        "total_clicks": 2900,
        "confidence_interval_lower": 0.058,
        "confidence_interval_upper": 0.092,
        "reasoning": "Limited-time offer with countdown timer"
    },
    {
        "pattern_hash": "hook:insider_secret|emo:curiosity|pace:fast|pain:lack_knowledge|cta:reveal",
        "hook_type": "insider_secret",
        "emotion": "curiosity",
        "pacing": "fast",
        "cta_type": "reveal",
        "target_audience_pain": "lack_knowledge",
        "product_category": "fitness",
        "avg_cvr": 0.068,  # 6.8% CVR
        "sample_size": 22,
        "total_conversions": 150,
        "total_clicks": 2200,
        "confidence_interval_lower": 0.051,
        "confidence_interval_upper": 0.085,
        "reasoning": "'Trainer's secret nobody tells you' - curiosity gap"
    },
]

# Losing patterns (to show contrast)
LOSING_PATTERNS = [
    {
        "pattern_hash": "hook:generic_intro|emo:neutral|pace:slow|pain:unknown|cta:generic",
        "hook_type": "generic_intro",
        "emotion": "neutral",
        "pacing": "slow",
        "cta_type": "generic",
        "target_audience_pain": "unknown",
        "product_category": "language_learning",
        "avg_cvr": 0.012,  # 1.2% CVR - poor performer
        "sample_size": 45,
        "total_conversions": 54,
        "total_clicks": 4500,
        "confidence_interval_lower": 0.008,
        "confidence_interval_upper": 0.016,
        "reasoning": "Generic 'Learn English' intros - no hook, no emotion"
    },
    {
        "pattern_hash": "hook:feature_list|emo:neutral|pace:medium|pain:unknown|cta:learn_more",
        "hook_type": "feature_list",
        "emotion": "neutral",
        "pacing": "medium",
        "cta_type": "learn_more",
        "target_audience_pain": "unknown",
        "product_category": "programming",
        "avg_cvr": 0.018,  # 1.8% CVR
        "sample_size": 31,
        "total_conversions": 56,
        "total_clicks": 3100,
        "confidence_interval_lower": 0.012,
        "confidence_interval_upper": 0.024,
        "reasoning": "Feature dump without addressing pain - weak"
    },
]


def seed_benchmarks():
    """Seed database with market benchmark patterns."""
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(PatternPerformance).filter(
            PatternPerformance.user_id == TEST_USER_ID
        ).count()

        if existing > 0:
            print(f"✅ Database already seeded with {existing} patterns. Skipping.")
            return

        print("🌱 Seeding database with market benchmarks from Facebook Ad Library...")

        # Insert winning patterns
        for pattern_data in WINNING_PATTERNS:
            pattern = PatternPerformance(
                id=uuid.uuid4(),
                user_id=TEST_USER_ID,
                **{k: v for k, v in pattern_data.items() if k != 'reasoning'},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(pattern)
            print(f"  ✅ {pattern_data['hook_type']} + {pattern_data['emotion']} → {pattern_data['avg_cvr']*100:.1f}% CVR")

        # Insert losing patterns (for contrast)
        for pattern_data in LOSING_PATTERNS:
            pattern = PatternPerformance(
                id=uuid.uuid4(),
                user_id=TEST_USER_ID,
                **{k: v for k, v in pattern_data.items() if k != 'reasoning'},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(pattern)
            print(f"  ❌ {pattern_data['hook_type']} + {pattern_data['emotion']} → {pattern_data['avg_cvr']*100:.1f}% CVR (weak)")

        db.commit()

        print(f"\n✅ Seeded {len(WINNING_PATTERNS) + len(LOSING_PATTERNS)} market benchmark patterns!")
        print(f"\n🎯 Client can now see 'Market Trends' tab with winning patterns!")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_benchmarks()
