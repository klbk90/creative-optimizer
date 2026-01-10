"""
Conversion Observer - автоматический триггер глубокого анализа.

Когда креатив достигает порога конверсий → запускается Claude Vision.
"""

from sqlalchemy.orm import Session
from database.models import Creative, PatternPerformance
from utils.logger import setup_logger
from typing import Optional
import uuid
from datetime import datetime

logger = setup_logger(__name__)

# Порог конверсий для глубокого анализа
DEEP_ANALYSIS_THRESHOLD = 5


def check_and_trigger_deep_analysis(creative_id: uuid.UUID, db: Session) -> bool:
    """
    Проверяет, нужен ли глубокий анализ креатива.

    Триггерится когда:
    - Креатив достиг DEEP_ANALYSIS_THRESHOLD конверсий
    - Креатив еще не был deeply analyzed

    Args:
        creative_id: UUID креатива
        db: Database session

    Returns:
        True if analysis was triggered, False otherwise
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        logger.warning(f"Creative {creative_id} not found")
        return False

    # Уже проанализирован?
    if creative.deeply_analyzed:
        return False

    # Достиг порога?
    conversions = creative.conversions or 0
    if conversions < DEEP_ANALYSIS_THRESHOLD:
        logger.info(
            f"Creative {creative.name} has {conversions}/{DEEP_ANALYSIS_THRESHOLD} conversions. "
            f"Waiting for more data before deep analysis."
        )
        return False

    # Триггерим анализ!
    logger.info(f"🎯 WINNER DETECTED: {creative.name} reached {conversions} conversions!")

    # Запускаем фоновую задачу
    from utils.background_tasks import enqueue_deep_analysis
    enqueue_deep_analysis(creative_id)

    # Помечаем что анализ запущен
    creative.analysis_status = "pending"
    creative.analysis_triggered_at = datetime.utcnow()
    db.commit()

    return True


def on_conversion_created(creative_id: uuid.UUID, db: Session):
    """
    Event handler: вызывается каждый раз когда создается новая конверсия.

    Args:
        creative_id: UUID креатива, который получил конверсию
        db: Database session
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        return

    conversions = creative.conversions or 0

    logger.info(f"📊 Conversion tracked: {creative.name} → {conversions} total conversions")

    # Проверяем пороги
    if conversions == DEEP_ANALYSIS_THRESHOLD:
        logger.info(f"🚨 THRESHOLD REACHED: Triggering deep analysis for {creative.name}")
        check_and_trigger_deep_analysis(creative_id, db)

    elif conversions == DEEP_ANALYSIS_THRESHOLD - 1:
        logger.info(
            f"⚠️ ALMOST THERE: {creative.name} needs 1 more conversion for deep analysis "
            f"({conversions}/{DEEP_ANALYSIS_THRESHOLD})"
        )


def mark_as_deeply_analyzed(creative_id: uuid.UUID, analysis_result: dict, db: Session):
    """
    Отмечает креатив как deeply analyzed и сохраняет результаты.

    Args:
        creative_id: UUID креатива
        analysis_result: Результат от Claude Vision
        db: Database session
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        logger.error(f"Creative {creative_id} not found")
        return

    # Обновляем AI-теги из Claude Vision
    creative.hook_type = analysis_result.get("hook_type", creative.hook_type)
    creative.emotion = analysis_result.get("emotion", creative.emotion)
    creative.pacing = analysis_result.get("pacing", creative.pacing)
    creative.target_audience_pain = analysis_result.get("target_audience_pain", creative.target_audience_pain)

    # Сохраняем reasoning
    creative.ai_reasoning = analysis_result.get("reasoning", "")

    # Помечаем как deeply analyzed
    creative.deeply_analyzed = True
    creative.analysis_status = "completed"
    creative.analyzed_at = datetime.utcnow()

    db.commit()

    logger.info(f"✅ WINNER DECONSTRUCTED: {creative.name} → {creative.hook_type} + {creative.emotion}")

    # Добавляем в Market Winners
    add_to_market_winners(creative, db)


def add_to_market_winners(creative: Creative, db: Session):
    """
    Добавляет успешный паттерн в базу Market Winners.

    Это позволяет другим клиентам видеть winning patterns.
    """
    # Создаем или обновляем PatternPerformance
    pattern_hash = (
        f"hook:{creative.hook_type}|emo:{creative.emotion}|"
        f"pace:{creative.pacing}|pain:{creative.target_audience_pain}|cta:{creative.cta_type}"
    )

    pattern = db.query(PatternPerformance).filter(
        PatternPerformance.pattern_hash == pattern_hash,
        PatternPerformance.product_category == creative.product_category
    ).first()

    cvr_value = (creative.cvr or 0) / 10000  # Convert from int to float

    if pattern:
        # Обновляем существующий
        old_total = pattern.avg_cvr * pattern.sample_size
        new_total = old_total + cvr_value
        pattern.sample_size += 1
        pattern.avg_cvr = new_total / pattern.sample_size
        pattern.total_conversions = (pattern.total_conversions or 0) + (creative.conversions or 0)
        pattern.total_clicks = (pattern.total_clicks or 0) + (creative.impressions or 0)
        pattern.updated_at = datetime.utcnow()
    else:
        # Создаем новый Market Winner
        pattern = PatternPerformance(
            id=uuid.uuid4(),
            user_id=creative.user_id,
            pattern_hash=pattern_hash,
            hook_type=creative.hook_type,
            emotion=creative.emotion,
            pacing=creative.pacing,
            cta_type=creative.cta_type,
            target_audience_pain=creative.target_audience_pain,
            product_category=creative.product_category,
            avg_cvr=cvr_value,
            sample_size=1,
            total_conversions=creative.conversions or 0,
            total_clicks=creative.impressions or 0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(pattern)

    db.commit()

    logger.info(
        f"🏆 MARKET WINNER ADDED: {creative.hook_type} + {creative.emotion} "
        f"→ {cvr_value*100:.1f}% CVR (n={pattern.sample_size})"
    )
