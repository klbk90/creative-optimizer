"""
Creative Analysis Filter - оптимизация затрат на Claude Vision API.

ПРАВИЛО: Анализируем только успешные креативы, чтобы не тратить деньги
на анализ провальных паттернов.

Логика:
- Если creative.conversions > MIN_CONVERSIONS → анализируем
- Если creative.conversions <= MIN_CONVERSIONS → пропускаем

Это экономит ~80% затрат на Claude API в EdTech нише, где много видео.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database.models import Creative
from utils.creative_analyzer import CreativeAnalyzer
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Минимум конверсий для анализа
MIN_CONVERSIONS_FOR_ANALYSIS = 3

# Минимум кликов для анализа (альтернативный фильтр)
MIN_CLICKS_FOR_ANALYSIS = 50


def should_analyze_creative(creative: Creative) -> tuple[bool, str]:
    """
    Определяет, нужно ли анализировать креатив через Claude Vision.

    Args:
        creative: Creative объект

    Returns:
        (should_analyze: bool, reason: str)

    Примеры:
        >>> creative.conversions = 5, creative.clicks = 100
        >>> should_analyze_creative(creative)
        (True, "Creative has 5 conversions (>3 threshold)")

        >>> creative.conversions = 1, creative.clicks = 10
        >>> should_analyze_creative(creative)
        (False, "Not enough conversions (1 < 3)")
    """

    # Проверка 1: Уже проанализирован?
    if creative.hook_type and creative.emotion:
        return (False, f"Already analyzed: hook={creative.hook_type}, emotion={creative.emotion}")

    # Проверка 2: Есть ли минимум конверсий?
    conversions = creative.conversions or 0

    if conversions >= MIN_CONVERSIONS_FOR_ANALYSIS:
        return (True, f"Creative has {conversions} conversions (>{MIN_CONVERSIONS_FOR_ANALYSIS} threshold)")

    # Проверка 3: Есть ли минимум кликов? (для early signals)
    clicks = creative.clicks or 0

    if clicks >= MIN_CLICKS_FOR_ANALYSIS and conversions > 0:
        cvr = conversions / clicks
        if cvr >= 0.10:  # CVR > 10% - promising signal
            return (True, f"High CVR={cvr*100:.1f}% with {clicks} clicks (early winner signal)")

    # Не прошел фильтры
    return (
        False,
        f"Not enough conversions ({conversions} < {MIN_CONVERSIONS_FOR_ANALYSIS}) "
        f"and not enough clicks ({clicks} < {MIN_CLICKS_FOR_ANALYSIS})"
    )


def analyze_successful_creatives(
    db: Session,
    user_id: str,
    product_category: str,
    max_to_analyze: int = 10
) -> List[Dict]:
    """
    Анализирует только успешные креативы (conversions > MIN).

    Args:
        db: Database session
        user_id: User UUID
        product_category: Product category filter
        max_to_analyze: Maximum number of creatives to analyze in one run

    Returns:
        List of analysis results

    Usage:
        ```python
        from utils.creative_analysis_filter import analyze_successful_creatives

        results = analyze_successful_creatives(
            db=db,
            user_id="user-uuid",
            product_category="language_learning",
            max_to_analyze=5
        )

        for result in results:
            print(f"{result['creative_name']}: {result['hook_type']} + {result['emotion']}")
        ```
    """

    # Получить все креативы в статусе testing/active
    creatives = db.query(Creative).filter(
        Creative.user_id == user_id,
        Creative.product_category == product_category,
        Creative.status.in_(["testing", "active"])
    ).order_by(Creative.conversions.desc()).all()

    logger.info(f"Found {len(creatives)} creatives for potential analysis")

    analyzer = CreativeAnalyzer()
    results = []
    analyzed_count = 0

    for creative in creatives:
        # Проверить фильтр
        should_analyze, reason = should_analyze_creative(creative)

        if not should_analyze:
            logger.debug(f"Skipping {creative.name}: {reason}")
            continue

        # Лимит на количество анализов в одном запуске
        if analyzed_count >= max_to_analyze:
            logger.info(f"Reached max_to_analyze limit ({max_to_analyze})")
            break

        logger.info(f"✅ Analyzing {creative.name}: {reason}")

        # Анализируем через Claude Vision
        try:
            analysis = analyzer.analyze_video(
                video_url=creative.video_url,
                frames_to_analyze=[0, 2, 5, 8]
            )

            # Обновляем креатив с результатами
            creative.hook_type = analysis.get("hook_type")
            creative.emotion = analysis.get("emotion")
            creative.pacing = analysis.get("pacing")
            creative.cta_type = analysis.get("cta_type")
            creative.has_text_overlay = analysis.get("has_text_overlay", False)
            creative.has_voiceover = analysis.get("has_voiceover", False)
            creative.features = analysis.get("features", {})

            db.commit()

            results.append({
                "creative_id": str(creative.id),
                "creative_name": creative.name,
                "conversions": creative.conversions,
                "clicks": creative.clicks,
                "hook_type": analysis.get("hook_type"),
                "emotion": analysis.get("emotion"),
                "pacing": analysis.get("pacing"),
                "confidence": analysis.get("confidence"),
                "reasoning": analysis.get("reasoning")
            })

            analyzed_count += 1

        except Exception as e:
            logger.error(f"Error analyzing {creative.name}: {e}")
            continue

    logger.info(f"✅ Analyzed {analyzed_count} creatives, skipped {len(creatives) - analyzed_count}")

    return results


def estimate_claude_api_cost(
    n_creatives: int,
    frames_per_video: int = 4,
    cost_per_1k_tokens: float = 0.003
) -> Dict:
    """
    Оценка стоимости Claude Vision API анализа.

    Args:
        n_creatives: Количество креативов для анализа
        frames_per_video: Количество кадров на видео
        cost_per_1k_tokens: Стоимость за 1K tokens (Claude 3.5 Sonnet)

    Returns:
        {
            "total_cost_usd": 12.50,
            "cost_per_creative": 2.50,
            "n_creatives": 5,
            "breakdown": {...}
        }

    Допущения:
    - 1 frame ≈ 1000 tokens (base64 image)
    - Prompt + response ≈ 500 tokens
    - Total per creative ≈ (frames * 1000 + 500) tokens
    """

    tokens_per_frame = 1000
    tokens_prompt_response = 500

    tokens_per_creative = (frames_per_video * tokens_per_frame) + tokens_prompt_response
    total_tokens = tokens_per_creative * n_creatives

    total_cost_usd = (total_tokens / 1000) * cost_per_1k_tokens
    cost_per_creative = total_cost_usd / n_creatives if n_creatives > 0 else 0

    return {
        "total_cost_usd": round(total_cost_usd, 2),
        "cost_per_creative": round(cost_per_creative, 2),
        "n_creatives": n_creatives,
        "breakdown": {
            "tokens_per_creative": tokens_per_creative,
            "total_tokens": total_tokens,
            "frames_per_video": frames_per_video,
            "cost_per_1k_tokens": cost_per_1k_tokens
        }
    }


if __name__ == "__main__":
    # Демо: оценка стоимости
    print("💰 Claude Vision API Cost Estimation")
    print("\n=== Scenario 1: Analyze ALL creatives (100 videos) ===")
    all_creatives = estimate_claude_api_cost(n_creatives=100)
    print(f"Total cost: ${all_creatives['total_cost_usd']}")
    print(f"Per creative: ${all_creatives['cost_per_creative']}")

    print("\n=== Scenario 2: Analyze ONLY successful creatives (5 videos) ===")
    successful_only = estimate_claude_api_cost(n_creatives=5)
    print(f"Total cost: ${successful_only['total_cost_usd']}")
    print(f"Per creative: ${successful_only['cost_per_creative']}")

    savings = all_creatives['total_cost_usd'] - successful_only['total_cost_usd']
    savings_percent = (savings / all_creatives['total_cost_usd']) * 100

    print(f"\n💡 Savings: ${savings:.2f} ({savings_percent:.0f}%)")
    print("\n✅ Фильтрация по conversions > 3 экономит ~95% бюджета на Claude API!")
