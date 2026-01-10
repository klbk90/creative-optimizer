"""
Market Data Ingestion Script - загрузка бенчмарков из FB Ad Library / TikTok.

Этот скрипт:
1. Загружает видео-бенчмарки в R2 (bucket: market-benchmarks)
2. Создает Creative записи с is_benchmark=True, is_public=True
3. Триггерит Claude Vision анализ СРАЗУ
4. Создает PatternPerformance с Bayesian Prior на основе market_longevity_days

Bayesian Prior Logic:
- Если ролик крутился 30 дней с CVR 5% → α=50, β=950 (50 успехов, 950 провалов)
- Формула: α = conversions_estimate, β = clicks_estimate - conversions_estimate
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import SessionLocal
from database.models import Creative, PatternPerformance
from utils.storage import get_storage
from utils.analysis_orchestrator import trigger_analysis
from datetime import datetime
import uuid


# Public user ID для market benchmarks (доступны всем)
MARKET_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


def calculate_bayesian_prior(
    cvr: float,
    market_longevity_days: int,
    avg_daily_clicks: int = 1000
) -> tuple[float, float]:
    """
    Вычисляет Bayesian Prior (α, β) на основе рыночных данных.

    Args:
        cvr: Conversion rate (e.g., 0.05 = 5%)
        market_longevity_days: Сколько дней ролик крутился
        avg_daily_clicks: Средний трафик в день (default: 1000 кликов/день)

    Returns:
        (alpha, beta) для Beta-распределения

    Example:
        cvr=0.05, market_longevity_days=30, avg_daily_clicks=1000
        → total_clicks = 30,000
        → conversions = 1,500
        → α = 1500, β = 28500
    """
    # Estimate total clicks
    total_clicks = market_longevity_days * avg_daily_clicks

    # Estimate conversions
    conversions = int(total_clicks * cvr)

    # Bayesian parameters
    alpha = conversions + 1  # +1 for smoothing (uniform prior)
    beta = (total_clicks - conversions) + 1

    return alpha, beta


def ingest_benchmark_video(
    video_url: str,
    creative_name: str,
    product_category: str,
    market_cvr: float,
    market_longevity_days: int,
    source_platform: str = "facebook_ad_library",
    avg_daily_clicks: int = 1000,
    hook_type: str = None,
    emotion: str = None,
    pacing: str = None,
    target_audience_pain: str = None,
    db: SessionLocal = None
) -> dict:
    """
    Загружает benchmark video в систему.

    Args:
        video_url: URL видео из FB Ad Library или TikTok
        creative_name: Название креатива
        product_category: Категория продукта
        market_cvr: Observed CVR (e.g., 0.05 = 5%)
        market_longevity_days: Сколько дней ролик крутился
        source_platform: facebook_ad_library, tiktok, youtube
        avg_daily_clicks: Estimated daily clicks
        hook_type: (Optional) Если уже известно из ручного анализа
        emotion: (Optional)
        pacing: (Optional)
        target_audience_pain: (Optional)

    Returns:
        {
            "creative_id": str,
            "analysis_triggered": bool,
            "bayesian_prior": {"alpha": float, "beta": float}
        }
    """
    if db is None:
        db = SessionLocal()

    try:
        # 1. Calculate Bayesian Prior
        alpha, beta = calculate_bayesian_prior(
            cvr=market_cvr,
            market_longevity_days=market_longevity_days,
            avg_daily_clicks=avg_daily_clicks
        )

        print(f"📊 Bayesian Prior: α={alpha:.0f}, β={beta:.0f} (CVR={market_cvr*100:.1f}%, {market_longevity_days} days)")

        # 2. Upload video to R2 (market-benchmarks bucket)
        storage = get_storage()

        # Note: video_url может быть внешний URL, мы его не загружаем,
        # а просто сохраняем ссылку. Если нужно загрузить - используй upload_benchmark()
        video_storage_url = video_url  # External URL for now

        # 3. Create Creative record
        creative = Creative(
            id=uuid.uuid4(),
            user_id=MARKET_USER_ID,
            name=creative_name,
            creative_type="ugc",
            product_category=product_category,
            video_url=video_storage_url,

            # Benchmark flags
            is_benchmark=True,
            is_public=True,  # Accessible to all users

            # Manual tags (if provided)
            hook_type=hook_type or "unknown",
            emotion=emotion or "unknown",
            pacing=pacing or "medium",
            target_audience_pain=target_audience_pain or "unknown",

            # Market data
            predicted_cvr=int(market_cvr * 10000),  # Store as int (150 = 1.5%)

            # Status
            status="active",
            analysis_status="pending",  # Will trigger immediately

            # Metadata
            campaign_tag=f"benchmark_{source_platform}",
            features={
                "source_platform": source_platform,
                "market_longevity_days": market_longevity_days,
                "bayesian_alpha": alpha,
                "bayesian_beta": beta
            },

            created_at=datetime.utcnow()
        )

        db.add(creative)
        db.commit()
        db.refresh(creative)

        print(f"✅ Creative created: {creative.name} (ID: {creative.id})")

        # 4. Trigger Claude Vision analysis IMMEDIATELY (benchmark = instant analysis)
        print(f"🔄 Triggering Claude Vision analysis for benchmark...")
        trigger_analysis(creative, db)

        # 5. Create PatternPerformance with Bayesian Prior
        # Note: Это создастся автоматически после Claude Vision анализа,
        # но мы можем создать pre-seeded версию если паттерны уже известны
        if hook_type and emotion:
            pattern_hash = (
                f"hook:{hook_type}|emo:{emotion}|pace:{pacing or 'medium'}|"
                f"pain:{target_audience_pain or 'unknown'}|cta:unknown"
            )

            # Check if pattern exists
            pattern = db.query(PatternPerformance).filter(
                PatternPerformance.pattern_hash == pattern_hash,
                PatternPerformance.product_category == product_category,
                PatternPerformance.source == 'benchmark'
            ).first()

            if not pattern:
                # Create new benchmark pattern with Bayesian Prior
                pattern = PatternPerformance(
                    id=uuid.uuid4(),
                    user_id=MARKET_USER_ID,
                    pattern_hash=pattern_hash,
                    hook_type=hook_type,
                    emotion=emotion,
                    pacing=pacing or "medium",
                    target_audience_pain=target_audience_pain,
                    product_category=product_category,

                    # Source and weighting
                    source='benchmark',
                    weight=2.0,  # Benchmarks have 2x weight (эталон)
                    market_longevity_days=market_longevity_days,
                    bayesian_alpha=alpha,
                    bayesian_beta=beta,

                    # Metrics (estimated from market data)
                    sample_size=1,
                    total_conversions=int(alpha - 1),  # Remove smoothing
                    total_clicks=int(alpha + beta - 2),  # Total clicks estimate
                    avg_cvr=int(market_cvr * 10000),

                    created_at=datetime.utcnow()
                )
                db.add(pattern)
                db.commit()

                print(f"✅ PatternPerformance created with Bayesian Prior (α={alpha:.0f}, β={beta:.0f})")

        return {
            "success": True,
            "creative_id": str(creative.id),
            "creative_name": creative.name,
            "analysis_triggered": True,
            "bayesian_prior": {
                "alpha": float(alpha),
                "beta": float(beta),
                "market_cvr": market_cvr,
                "market_longevity_days": market_longevity_days
            },
            "is_public": True,
            "message": f"Benchmark video ingested. Claude Vision analysis in progress..."
        }

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    """
    Example: Ingest a winning video from Facebook Ad Library.

    Scenario: Language learning app video that ran for 30 days with 5% CVR.
    """

    result = ingest_benchmark_video(
        video_url="https://facebook.com/ads/library/video/123456789",  # External URL
        creative_name="FB Winner: 'Too Busy to Learn?'",
        product_category="language_learning",
        market_cvr=0.05,  # 5% CVR
        market_longevity_days=30,  # Ran for 30 days
        source_platform="facebook_ad_library",
        avg_daily_clicks=1000,  # 1000 clicks/day

        # Optional: Manual tags (если известны до Claude Vision)
        hook_type="problem_agitation",
        emotion="frustration",
        pacing="fast",
        target_audience_pain="no_time"
    )

    print("\n" + "="*60)
    print("RESULT:")
    print(f"  Creative ID: {result.get('creative_id')}")
    print(f"  Bayesian Prior: α={result['bayesian_prior']['alpha']:.0f}, β={result['bayesian_prior']['beta']:.0f}")
    print(f"  Analysis Triggered: {result.get('analysis_triggered')}")
    print("="*60)
