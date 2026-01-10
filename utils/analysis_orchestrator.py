"""
Analysis Orchestrator - управление Claude Vision анализом.

Умные триггеры на основе CVR + statistical significance:

1. Benchmarks: анализируем СРАЗУ (эталоны рынка)
2. Early Winners: CVR >= 1.5x baseline + min 100 impressions
3. Confirmed Winners: CVR >= baseline + min 500 impressions + 80% confidence
4. Force Analyze: ручной запуск (admin)

Экономия: ~90% AI costs за счет пропуска losers.
"""

from sqlalchemy.orm import Session
from database.models import Creative
from utils.logger import setup_logger
from datetime import datetime
import uuid
import math

logger = setup_logger(__name__)

# Analysis Thresholds
CLAUDE_VISION_COST_PER_REQUEST = 15  # cents

# CVR Baselines by product category (industry averages)
BASELINE_CVR = {
    "fitness": 0.03,          # 3%
    "language_learning": 0.05, # 5%
    "edtech": 0.04,           # 4%
    "gaming": 0.02,           # 2%
    "finance": 0.06,          # 6%
    "default": 0.03           # 3% default
}

# Stage-based triggers
EARLY_TEST_MIN_IMPRESSIONS = 100     # Micro-influencer test
CONFIRMED_TEST_MIN_IMPRESSIONS = 500  # Small ads test
MIN_CONFIDENCE_LEVEL = 0.80          # 80% statistical confidence


def check_analysis_trigger(creative_id: uuid.UUID, db: Session) -> bool:
    """
    Умные триггеры для Claude Vision анализа.

    Логика:
    1. Benchmark → анализ СРАЗУ
    2. Early Winner → CVR >= 1.5x baseline, min 100 impressions
    3. Confirmed Winner → CVR >= baseline, min 500 impressions, 80% confidence
    4. Иначе → SKIP (экономия AI costs)

    Args:
        creative_id: UUID креатива
        db: Database session

    Returns:
        True if analysis was triggered
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        return False

    # Уже проанализирован?
    if creative.analysis_status in ['completed', 'processing']:
        return False

    # ТРИГГЕР 1: Benchmark креативы - анализируем СРАЗУ
    if creative.is_benchmark:
        logger.info(f"🎯 BENCHMARK: {creative.name} - analyzing immediately")
        trigger_analysis(creative, db, reason="benchmark")
        return True

    # Получаем метрики
    impressions = creative.impressions or 0
    conversions = creative.conversions or 0
    clicks = creative.clicks or 0

    # Нет данных → skip
    if impressions == 0:
        return False

    # Считаем CVR
    cvr = conversions / impressions if impressions > 0 else 0

    # Базовая CVR для категории
    category = creative.product_category or "default"
    baseline_cvr = BASELINE_CVR.get(category, BASELINE_CVR["default"])

    # ТРИГГЕР 2: Early Winner Detection (после micro-test)
    if impressions >= EARLY_TEST_MIN_IMPRESSIONS:
        early_winner_threshold = baseline_cvr * 1.5  # 50% выше базовой

        if cvr >= early_winner_threshold:
            logger.info(
                f"🚀 EARLY WINNER: {creative.name} | "
                f"CVR: {cvr*100:.2f}% (baseline: {baseline_cvr*100:.1f}%) | "
                f"Impressions: {impressions} | "
                f"Conversions: {conversions}"
            )
            trigger_analysis(creative, db, reason="early_winner")
            return True

    # ТРИGGЕР 3: Confirmed Winner (после small ads test)
    if impressions >= CONFIRMED_TEST_MIN_IMPRESSIONS:
        # Statistical significance
        confidence = calculate_confidence(impressions, conversions)

        if cvr >= baseline_cvr and confidence >= MIN_CONFIDENCE_LEVEL:
            logger.info(
                f"✅ CONFIRMED WINNER: {creative.name} | "
                f"CVR: {cvr*100:.2f}% (baseline: {baseline_cvr*100:.1f}%) | "
                f"Impressions: {impressions} | "
                f"Conversions: {conversions} | "
                f"Confidence: {confidence*100:.1f}%"
            )
            trigger_analysis(creative, db, reason="confirmed_winner")
            return True

    # Логируем progress
    if impressions >= 50:
        logger.info(
            f"📊 TESTING: {creative.name} | "
            f"CVR: {cvr*100:.2f}% (baseline: {baseline_cvr*100:.1f}%) | "
            f"Impressions: {impressions}/{CONFIRMED_TEST_MIN_IMPRESSIONS} | "
            f"Status: {'promising' if cvr >= baseline_cvr else 'underperforming'}"
        )

    return False


def calculate_confidence(impressions: int, conversions: int) -> float:
    """
    Рассчитать статистическую уверенность (confidence level).

    Использует биномиальное распределение для оценки точности CVR.

    Args:
        impressions: Количество показов
        conversions: Количество конверсий

    Returns:
        Confidence level (0.0 - 1.0)
    """
    if impressions == 0 or conversions == 0:
        return 0.0

    # CVR
    p = conversions / impressions

    # Standard error для биномиального распределения
    se = math.sqrt(p * (1 - p) / impressions)

    # Z-score для 80% confidence (1.28)
    # Чем больше sample size, тем меньше margin of error
    margin_of_error = 1.28 * se

    # Confidence = 1 - (margin / p)
    # Чем меньше margin относительно CVR, тем выше уверенность
    if p == 0:
        return 0.0

    confidence = max(0.0, min(1.0, 1 - (margin_of_error / p)))

    return confidence


def trigger_analysis(creative: Creative, db: Session, reason: str = "unknown"):
    """
    Запускает фоновую задачу на Claude Vision анализ.

    Args:
        creative: Creative object
        db: Database session
        reason: Причина запуска (benchmark/early_winner/confirmed_winner/force)
    """
    from utils.background_tasks import enqueue_deep_analysis

    # Update status
    creative.analysis_status = 'processing'
    creative.analysis_triggered_at = datetime.utcnow()

    # Store trigger reason in features
    if not creative.features:
        creative.features = {}
    creative.features['analysis_trigger_reason'] = reason

    db.commit()

    logger.info(f"🔄 Triggering deep analysis for: {creative.name} (reason: {reason})")

    # Enqueue background task
    try:
        job_id = enqueue_deep_analysis(creative.id)
        logger.info(f"✅ Analysis job enqueued: {job_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue analysis: {e}")
        creative.analysis_status = 'failed'
        db.commit()


def force_analyze(creative_id: uuid.UUID, db: Session) -> dict:
    """
    FORCE manual Claude Vision analysis (bypasses all triggers).

    Use cases:
    - Admin wants to analyze a specific creative immediately
    - Re-analyze a creative after updating tags
    - Benchmark videos that need immediate analysis

    Args:
        creative_id: UUID креатива
        db: Database session

    Returns:
        {
            "success": bool,
            "creative_id": str,
            "message": str,
            "job_id": str (optional)
        }
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        return {
            "success": False,
            "error": "Creative not found"
        }

    # Check if already processing
    if creative.analysis_status == 'processing':
        return {
            "success": False,
            "error": "Analysis already in progress",
            "creative_id": str(creative.id)
        }

    logger.info(f"🚀 FORCE ANALYZE: {creative.name} (manual trigger)")

    # Trigger analysis
    trigger_analysis(creative, db)

    return {
        "success": True,
        "creative_id": str(creative.id),
        "creative_name": creative.name,
        "message": f"Force analysis triggered for {creative.name}",
        "analysis_status": "processing"
    }


def mark_analysis_complete(
    creative_id: uuid.UUID,
    analysis_result: dict,
    db: Session
):
    """
    Отмечает анализ как завершенный и сохраняет результаты.

    Args:
        creative_id: UUID креатива
        analysis_result: Результат от Claude Vision
        db: Database session
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        return

    # Обновляем AI-теги
    creative.hook_type = analysis_result.get('hook_type', creative.hook_type)
    creative.emotion = analysis_result.get('emotion', creative.emotion)
    creative.pacing = analysis_result.get('pacing', creative.pacing)
    creative.target_audience_pain = analysis_result.get('target_audience_pain', creative.target_audience_pain)
    creative.ai_reasoning = analysis_result.get('reasoning', '')

    # Mark as complete
    creative.analysis_status = 'completed'
    creative.deeply_analyzed = True
    creative.analyzed_at = datetime.utcnow()

    # Track cost
    creative.analysis_cost_cents = CLAUDE_VISION_COST_PER_REQUEST

    db.commit()

    # Log cost
    total_cost = creative.analysis_cost_cents / 100
    logger.info(
        f"💰 COST TRACKING: {creative.name} analysis cost ${total_cost:.2f} "
        f"(~{CLAUDE_VISION_COST_PER_REQUEST} cents)"
    )

    logger.info(
        f"✅ WINNER DECONSTRUCTED: {creative.name} → "
        f"{creative.hook_type} + {creative.emotion} "
        f"(CVR: {(creative.cvr or 0)/100:.1f}%)"
    )

    # Add to Market Winners
    from utils.conversion_observer import add_to_market_winners
    add_to_market_winners(creative, db)


def get_analysis_status_label(status: str) -> dict:
    """
    Возвращает UI-friendly статус для админки.

    Args:
        status: analysis_status value

    Returns:
        {
            "label": "Testing in Progress",
            "color": "yellow",
            "icon": "clock"
        }
    """
    status_map = {
        'pending': {
            'label': 'Testing in Progress',
            'color': 'yellow',
            'icon': 'clock',
            'description': 'Gathering conversion data...'
        },
        'processing': {
            'label': 'AI Analyzing...',
            'color': 'blue',
            'icon': 'sparkles',
            'description': 'Claude Vision is deconstructing this winner'
        },
        'completed': {
            'label': 'Winner Patterns Identified',
            'color': 'green',
            'icon': 'check-circle',
            'description': 'AI has identified winning patterns'
        },
        'failed': {
            'label': 'Analysis Failed',
            'color': 'red',
            'icon': 'alert-circle',
            'description': 'Manual review required'
        },
        'skipped': {
            'label': 'Not a Winner',
            'color': 'gray',
            'icon': 'x-circle',
            'description': 'Below conversion threshold'
        }
    }

    return status_map.get(status, status_map['pending'])


def calculate_total_analysis_costs(user_id: uuid.UUID, db: Session) -> dict:
    """
    Подсчитывает общие затраты на AI анализ для пользователя.

    Args:
        user_id: UUID пользователя
        db: Database session

    Returns:
        {
            "total_analyzed": 10,
            "total_cost_cents": 150,
            "total_cost_usd": 1.50,
            "avg_cost_per_winner": 15
        }
    """
    creatives = db.query(Creative).filter(
        Creative.user_id == user_id,
        Creative.deeply_analyzed == True
    ).all()

    total_analyzed = len(creatives)
    total_cost_cents = sum(c.analysis_cost_cents or 0 for c in creatives)

    return {
        "total_analyzed": total_analyzed,
        "total_cost_cents": total_cost_cents,
        "total_cost_usd": total_cost_cents / 100,
        "avg_cost_per_winner": (total_cost_cents / total_analyzed) if total_analyzed > 0 else 0
    }
