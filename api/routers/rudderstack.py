"""
RudderStack Webhook Router - автоматическая атрибуция конверсий.

Обрабатывает события от RudderStack:
- Page Viewed (UTM tracking)
- Order Completed (Conversion tracking)

Использует Байесовское обновление (Beta-распределение) для
точного пересчета avg_cvr в pattern_performance.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import expression
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import random
import numpy as np

# Байесовское обновление
try:
    from scipy.stats import beta as beta_dist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    import warnings
    warnings.warn("scipy not installed. Using simplified Bayesian update.")

from database.base import get_db
from database.models import (
    Creative, TrafficSource, Conversion,
    PatternPerformance, User
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/rudderstack", tags=["RudderStack Integration"])


# ========== SCHEMAS ==========

class RudderStackEvent(BaseModel):
    """
    RudderStack event format.

    Документация: https://www.rudderstack.com/docs/event-spec/
    """
    event: str  # "Page Viewed", "Order Completed"
    userId: Optional[str] = None
    anonymousId: Optional[str] = None
    properties: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


# ========== HELPERS ==========

def get_pattern_hash(creative: Creative) -> str:
    """
    Создает pattern_hash из паттернов креатива.

    Для EdTech включает target_audience_pain - критически важно!
    """
    return (
        f"hook:{creative.hook_type or 'unknown'}"
        f"|emo:{creative.emotion or 'unknown'}"
        f"|pace:{creative.pacing or 'medium'}"
        f"|pain:{getattr(creative, 'target_audience_pain', None) or 'unknown'}"
        f"|cta:{creative.cta_type or 'unknown'}"
    )


def bayesian_update_cvr(
    total_conversions: int,
    total_clicks: int,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0
) -> tuple[float, float, float]:
    """
    Байесовское обновление CVR используя Beta-распределение.

    Beta-распределение параметризовано:
    - alpha = количество успехов (conversions) + prior
    - beta = количество неудач (clicks - conversions) + prior

    Args:
        total_conversions: Общее количество конверсий
        total_clicks: Общее количество кликов
        alpha_prior: Prior для Beta (по умолчанию 1 = uniform prior)
        beta_prior: Prior для Beta (по умолчанию 1 = uniform prior)

    Returns:
        (mean_cvr, lower_95, upper_95) - средний CVR и 95% доверительный интервал

    Пример:
        total_conversions=10, total_clicks=100
        → alpha = 10 + 1 = 11
        → beta = 90 + 1 = 91
        → mean = 11/(11+91) = 10.8%
        → CI: [5.7%, 17.8%]
    """

    # Вычисляем alpha и beta
    # alpha = успехи (conversions)
    # beta = неудачи (clicks - conversions)
    alpha = alpha_prior + total_conversions
    beta_param = beta_prior + (total_clicks - total_conversions)

    # Среднее значение Beta-распределения: alpha / (alpha + beta)
    mean_cvr = alpha / (alpha + beta_param)

    # 95% доверительный интервал
    if SCIPY_AVAILABLE:
        # Точный расчет через scipy
        lower_bound = beta_dist.ppf(0.025, alpha, beta_param)
        upper_bound = beta_dist.ppf(0.975, alpha, beta_param)
    else:
        # Упрощенный расчет через variance
        variance = (alpha * beta_param) / ((alpha + beta_param) ** 2 * (alpha + beta_param + 1))
        std_dev = variance ** 0.5
        lower_bound = max(0, mean_cvr - 1.96 * std_dev)
        upper_bound = min(1, mean_cvr + 1.96 * std_dev)

    return mean_cvr, lower_bound, upper_bound


def thompson_sampling(patterns: list[PatternPerformance], n_samples: int = 5) -> list[dict]:
    """
    Thompson Sampling для выбора паттернов на тестирование.

    Для каждого паттерна:
    1. Берем bayesian_alpha, bayesian_beta из БД (уже обновляются атомарно)
    2. Делаем sample = numpy.random.beta(alpha, beta)
    3. Применяем weight multiplier (benchmark patterns имеют вес 2.0)
    4. Сортируем по weighted_score (выше = лучше)
    5. Возвращаем top-N

    Баланс Exploration vs Exploitation:
    - Паттерны с высоким CVR и большой выборкой → высокий sample (exploit)
    - Паттерны с малой выборкой → высокая вариативность sample (explore)
    - Benchmark паттерны (weight=2.0) получают приоритет

    Args:
        patterns: Список PatternPerformance объектов
        n_samples: Сколько паттернов рекомендовать

    Returns:
        Список рекомендаций с thompson_score
    """

    recommendations = []

    for pattern in patterns:
        # Beta параметры из БД (атомарно обновляются в вебхуках)
        alpha = pattern.bayesian_alpha or 1.0
        beta_param = pattern.bayesian_beta or 1.0

        # Thompson Sampling: сэмплируем из Beta-распределения
        # Используем numpy для производительности
        thompson_score = np.random.beta(alpha, beta_param)

        # Вычисляем среднее CVR = α / (α + β)
        mean_cvr = alpha / (alpha + beta_param)

        # Weight multiplier (benchmark=2.0, client=1.0)
        weight = pattern.weight or 1.0

        # Взвешенный score для сортировки
        weighted_score = thompson_score * weight

        recommendations.append({
            "pattern_hash": pattern.pattern_hash,
            "hook_type": pattern.hook_type,
            "emotion": pattern.emotion,
            "pacing": pattern.pacing,
            "psychotype": pattern.psychotype,
            "thompson_score": float(thompson_score),  # Для сортировки
            "weighted_score": float(weighted_score),
            "mean_cvr": float(mean_cvr),
            "sample_size": pattern.sample_size or 0,
            "total_conversions": pattern.total_conversions or 0,
            "alpha": float(alpha),
            "beta": float(beta_param),
            "weight": float(weight),
            "source": pattern.source or 'client',
            "reasoning": (
                f"Benchmark winner (n={pattern.sample_size}, weight={weight}x)" if pattern.source == 'benchmark'
                else f"High confidence winner (n={pattern.sample_size})" if pattern.sample_size and pattern.sample_size > 20
                else f"Promising, needs more data (n={pattern.sample_size or 0})" if pattern.sample_size and pattern.sample_size > 5
                else "New pattern, high exploration value"
            )
        })

    # Сортируем по weighted_score (выше = лучше)
    recommendations.sort(key=lambda x: x['weighted_score'], reverse=True)

    return recommendations[:n_samples]


# ========== ENDPOINTS ==========

@router.post("/track")
async def rudderstack_webhook(
    event: RudderStackEvent,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook для обработки событий от RudderStack.

    События:
    1. "Page Viewed" → Трекаем UTM, создаем user_session
    2. "Order Completed" → Трекаем конверсию, обновляем ML модель

    Example payload:
    ```json
    {
      "event": "Order Completed",
      "userId": "user_123",
      "anonymousId": "anon_456",
      "properties": {
        "order_id": "ord_789",
        "total": 50.00,
        "currency": "USD",
        "utm_id": "creative_abc123"  // или получаем из context
      },
      "context": {
        "campaign": {
          "source": "instagram",
          "medium": "influencer",
          "name": "jan_fitness"
        }
      }
    }
    ```
    """

    logger.info(f"RudderStack event: {event.event} from {event.userId or event.anonymousId}")

    # Определяем customer_id (userId или anonymousId)
    customer_id = event.userId or event.anonymousId

    if not customer_id:
        logger.warning("No userId or anonymousId in RudderStack event")
        return {"success": False, "error": "Missing customer identifier"}

    # Обрабатываем разные типы событий
    if event.event == "Page Viewed":
        return await handle_page_view(event, customer_id, db)

    elif event.event == "Video View":
        return await handle_video_view(event, customer_id, db)

    elif event.event == "Order Completed":
        return await handle_order_completed(event, customer_id, db)

    else:
        logger.info(f"Ignoring event type: {event.event}")
        return {"success": True, "message": f"Event {event.event} logged"}


async def handle_page_view(
    event: RudderStackEvent,
    customer_id: str,
    db: Session
) -> Dict:
    """
    Обработка Page Viewed - сохранение UTM сессии.

    Извлекает utm_id из:
    1. properties.utm_id
    2. context.campaign (utm_source, utm_campaign)
    3. URL parameters
    """

    # Извлекаем UTM
    utm_id = event.properties.get("utm_id")

    if not utm_id and event.context:
        # Попробовать извлечь из context.campaign
        campaign = event.context.get("campaign", {})
        if campaign:
            # Ищем traffic_source по utm_campaign
            utm_campaign = campaign.get("name")
            if utm_campaign:
                ts = db.query(TrafficSource).filter(
                    TrafficSource.utm_campaign == utm_campaign
                ).first()

                if ts:
                    utm_id = ts.utm_id

    if not utm_id:
        logger.warning(f"No UTM found in Page Viewed event for {customer_id}")
        return {"success": False, "error": "No UTM found"}

    # Найти traffic_source
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.utm_id == utm_id
    ).first()

    if not traffic_source:
        logger.warning(f"Traffic source not found: {utm_id}")
        return {"success": False, "error": "Traffic source not found"}

    # Сохранить/обновить user_session
    from database.models import UserSession

    session = db.query(UserSession).filter(
        UserSession.customer_id == customer_id,
        UserSession.utm_id == utm_id
    ).first()

    if session:
        # Обновить существующую сессию
        session.last_interaction = datetime.utcnow()
        session.touch_count += 1
    else:
        # Создать новую сессию
        session = UserSession(
            id=uuid.uuid4(),
            customer_id=customer_id,
            external_id=event.anonymousId,
            utm_id=utm_id,
            traffic_source_id=traffic_source.id,
            creative_id=traffic_source.creative_id,
            first_interaction=datetime.utcnow(),
            device_type=event.context.get("device", {}).get("type") if event.context else None,
            ip_address=event.context.get("ip") if event.context else None
        )
        db.add(session)

    # Обновить клики в traffic_source
    traffic_source.clicks += 1
    traffic_source.last_click = datetime.utcnow()
    traffic_source.external_id = event.anonymousId

    db.commit()

    logger.info(f"User session tracked: {customer_id} → {utm_id}")

    return {
        "success": True,
        "message": "Page view tracked",
        "utm_id": utm_id,
        "customer_id": customer_id
    }


async def handle_video_view(
    event: RudderStackEvent,
    customer_id: str,
    db: Session
) -> Dict:
    """
    Обработка Video View - инкремент β (неудачи) для Thompson Sampling.

    При просмотре видео БЕЗ конверсии - это "неудача" в терминах Beta-распределения.
    Инкрементируем bayesian_beta для соответствующего паттерна АТОМАРНО.

    Args:
        event: RudderStack событие
        customer_id: ID пользователя
        db: Database session

    Returns:
        Dict с результатом обработки
    """

    # Извлечь creative_id из properties
    creative_id_str = event.properties.get("creative_id")

    if not creative_id_str:
        logger.warning(f"No creative_id in Video View event for {customer_id}")
        return {"success": False, "error": "No creative_id found"}

    try:
        creative_id = uuid.UUID(creative_id_str)
    except ValueError:
        logger.error(f"Invalid creative_id format: {creative_id_str}")
        return {"success": False, "error": "Invalid creative_id"}

    # Найти креатив
    creative = db.query(Creative).filter(Creative.id == creative_id).first()

    if not creative:
        logger.warning(f"Creative not found: {creative_id}")
        return {"success": False, "error": "Creative not found"}

    # Получить pattern_hash
    pattern_hash = get_pattern_hash(creative)

    # Найти или создать pattern_performance
    pattern_perf = db.query(PatternPerformance).filter(
        PatternPerformance.pattern_hash == pattern_hash,
        PatternPerformance.product_category == creative.product_category
    ).first()

    if pattern_perf:
        # 🔥 АТОМАРНЫЙ ИНКРЕМЕНТ β (неудачи)
        # Используем F-expression для избежания race condition
        db.query(PatternPerformance).filter(
            PatternPerformance.id == pattern_perf.id
        ).update({
            "bayesian_beta": PatternPerformance.bayesian_beta + 1,
            "total_clicks": PatternPerformance.total_clicks + 1,
            "updated_at": datetime.utcnow()
        }, synchronize_session=False)

        db.commit()

        # Пересчитываем avg_cvr на основе обновленных α и β
        # Refresh объект чтобы получить новые значения
        db.refresh(pattern_perf)

        alpha = pattern_perf.bayesian_alpha
        beta_val = pattern_perf.bayesian_beta

        # Среднее CVR = α / (α + β)
        mean_cvr = alpha / (alpha + beta_val)

        # Обновляем avg_cvr
        pattern_perf.avg_cvr = int(mean_cvr * 10000)
        db.commit()

        logger.info(
            f"Pattern β incremented: {pattern_hash} | "
            f"α={alpha}, β={beta_val} | "
            f"CVR={mean_cvr*100:.2f}%"
        )
    else:
        # Создать новый паттерн с начальными prior
        # Для новых клиентских паттернов: α=1, β=2 (1 просмотр без конверсии)
        pattern_perf = PatternPerformance(
            id=uuid.uuid4(),
            user_id=creative.user_id,
            pattern_hash=pattern_hash,
            hook_type=creative.hook_type,
            emotion=creative.emotion,
            pacing=creative.pacing,
            cta_type=creative.cta_type,
            target_audience_pain=getattr(creative, 'target_audience_pain', None),
            psychotype=getattr(creative, 'psychotype', None),
            product_category=creative.product_category,
            source='client',
            weight=1.0,
            bayesian_alpha=1.0,  # Neutral prior
            bayesian_beta=2.0,   # +1 для просмотра без конверсии
            sample_size=0,
            total_conversions=0,
            total_clicks=1,
            avg_cvr=int(0.33 * 10000),  # α/(α+β) = 1/3 = 33%
            created_at=datetime.utcnow()
        )
        db.add(pattern_perf)
        db.commit()

        logger.info(f"New pattern created from Video View: {pattern_hash}")

    return {
        "success": True,
        "message": "Video view tracked (β incremented)",
        "creative_id": str(creative.id),
        "pattern_hash": pattern_hash,
        "bayesian_alpha": pattern_perf.bayesian_alpha,
        "bayesian_beta": pattern_perf.bayesian_beta
    }


async def handle_order_completed(
    event: RudderStackEvent,
    customer_id: str,
    db: Session
) -> Dict:
    """
    Обработка Order Completed - автоатрибуция + обновление ML.

    Алгоритм:
    1. Найти user_session по customer_id (last-click attribution)
    2. Найти traffic_source и creative
    3. Создать conversion запись
    4. Обновить метрики creative и traffic_source
    5. Обновить pattern_performance с Байесовским методом
    """

    # 1. Найти сессию (last-click attribution)
    from database.models import UserSession

    session = db.query(UserSession).filter(
        UserSession.customer_id == customer_id
    ).order_by(UserSession.last_interaction.desc()).first()

    if not session:
        logger.warning(f"No session found for customer: {customer_id}")
        return {"success": False, "error": "No attribution data found"}

    # 2. Получить traffic_source и creative
    traffic_source = db.query(TrafficSource).filter(
        TrafficSource.id == session.traffic_source_id
    ).first()

    creative = db.query(Creative).filter(
        Creative.id == session.creative_id
    ).first() if session.creative_id else None

    if not traffic_source:
        logger.error(f"Traffic source not found: {session.traffic_source_id}")
        return {"success": False, "error": "Traffic source not found"}

    # Извлечь данные о покупке
    amount_cents = int(event.properties.get("total", 0) * 100)  # USD to cents
    currency = event.properties.get("currency", "USD")
    order_id = event.properties.get("order_id")

    # 3. Создать conversion
    time_to_conversion = int((datetime.utcnow() - session.first_interaction).total_seconds())

    conversion = Conversion(
        id=uuid.uuid4(),
        traffic_source_id=traffic_source.id,
        user_id=traffic_source.user_id,
        conversion_type="purchase",
        customer_id=customer_id,
        amount=amount_cents,
        currency=currency,
        product_id=order_id,
        product_name=event.properties.get("product_name", "Product"),
        time_to_conversion=time_to_conversion,
        extra_data=event.properties,
        external_id=event.anonymousId,
        created_at=datetime.utcnow()
    )

    db.add(conversion)

    # 4. Обновить traffic_source
    traffic_source.conversions = (traffic_source.conversions or 0) + 1
    traffic_source.revenue = (traffic_source.revenue or 0) + amount_cents

    # 5. Обновить creative (если есть)
    if creative:
        creative.conversions = (creative.conversions or 0) + 1
        creative.revenue = (creative.revenue or 0) + amount_cents

        # Пересчитать CVR креатива
        if creative.impressions and creative.impressions > 0:
            creative.cvr = int((creative.conversions / creative.impressions) * 10000)

        creative.last_stats_update = datetime.utcnow()

        # 🎯 TRIGGER DEEP ANALYSIS (если креатив достиг порога)
        from utils.analysis_orchestrator import check_analysis_trigger
        try:
            check_analysis_trigger(creative.id, db)
        except Exception as analysis_error:
            logger.warning(f"Analysis trigger failed: {analysis_error}")

        # 6. Обновить pattern_performance с Байесовским методом
        pattern_hash = get_pattern_hash(creative)

        pattern_perf = db.query(PatternPerformance).filter(
            PatternPerformance.pattern_hash == pattern_hash,
            PatternPerformance.product_category == creative.product_category
        ).first()

        if pattern_perf:
            # 🔥 АТОМАРНЫЙ ИНКРЕМЕНТ α (успехи)
            # Используем F-expression для избежания race condition
            db.query(PatternPerformance).filter(
                PatternPerformance.id == pattern_perf.id
            ).update({
                "bayesian_alpha": PatternPerformance.bayesian_alpha + 1,
                "total_conversions": PatternPerformance.total_conversions + 1,
                "sample_size": PatternPerformance.sample_size + 1,
                "updated_at": datetime.utcnow()
            }, synchronize_session=False)

            db.commit()

            # Пересчитываем avg_cvr на основе обновленных α и β
            # Refresh объект чтобы получить новые значения
            db.refresh(pattern_perf)

            alpha = pattern_perf.bayesian_alpha
            beta_val = pattern_perf.bayesian_beta

            # Среднее CVR = α / (α + β)
            mean_cvr = alpha / (alpha + beta_val)

            # Доверительный интервал (используя scipy если доступен)
            if SCIPY_AVAILABLE:
                lower_bound = beta_dist.ppf(0.025, alpha, beta_val)
                upper_bound = beta_dist.ppf(0.975, alpha, beta_val)
            else:
                # Упрощенный расчет через variance
                variance = (alpha * beta_val) / ((alpha + beta_val) ** 2 * (alpha + beta_val + 1))
                std_dev = variance ** 0.5
                lower_bound = max(0, mean_cvr - 1.96 * std_dev)
                upper_bound = min(1, mean_cvr + 1.96 * std_dev)

            # Обновляем вычисляемые поля
            pattern_perf.avg_cvr = int(mean_cvr * 10000)
            pattern_perf.confidence_interval_lower = int(lower_bound * 10000)
            pattern_perf.confidence_interval_upper = int(upper_bound * 10000)
            db.commit()

            logger.info(
                f"Pattern α incremented: {pattern_hash} | "
                f"α={alpha}, β={beta_val} | "
                f"CVR={mean_cvr*100:.2f}% (CI: {lower_bound*100:.1f}%-{upper_bound*100:.1f}%) | "
                f"n={pattern_perf.sample_size}"
            )
        else:
            # Создать новый паттерн
            # Для benchmark паттернов: α=50, β=950 (5% CVR, низкая дисперсия)
            # Для клиентских паттернов: α=2, β=1 (первая конверсия)
            is_benchmark = getattr(creative, 'is_benchmark', False)

            if is_benchmark:
                # Benchmark prior: α=50, β=950 → CVR = 50/1000 = 5%
                initial_alpha = 50.0
                initial_beta = 950.0
                source = 'benchmark'
                weight = 2.0
            else:
                # Client prior: α=2, β=1 (первая конверсия, оптимистичный prior)
                initial_alpha = 2.0
                initial_beta = 1.0
                source = 'client'
                weight = 1.0

            mean_cvr = initial_alpha / (initial_alpha + initial_beta)

            pattern_perf = PatternPerformance(
                id=uuid.uuid4(),
                user_id=traffic_source.user_id,
                pattern_hash=pattern_hash,
                hook_type=creative.hook_type,
                emotion=creative.emotion,
                pacing=creative.pacing,
                cta_type=creative.cta_type,
                target_audience_pain=getattr(creative, 'target_audience_pain', None),
                psychotype=getattr(creative, 'psychotype', None),
                product_category=creative.product_category,
                source=source,
                weight=weight,
                bayesian_alpha=initial_alpha,
                bayesian_beta=initial_beta,
                sample_size=1,
                total_conversions=1,
                total_clicks=1,
                avg_cvr=int(mean_cvr * 10000),
                confidence_interval_lower=0,
                confidence_interval_upper=int(1.0 * 10000),
                created_at=datetime.utcnow()
            )
            db.add(pattern_perf)

            logger.info(
                f"New pattern created: {pattern_hash} | "
                f"source={source}, α={initial_alpha}, β={initial_beta}"
            )

    db.commit()

    logger.info(
        f"Conversion tracked: {customer_id} → {session.utm_id} → "
        f"{creative.name if creative else 'N/A'} | ${amount_cents/100:.2f}"
    )

    return {
        "success": True,
        "message": "Order completed and attributed",
        "conversion_id": str(conversion.id),
        "utm_id": session.utm_id,
        "creative_id": str(creative.id) if creative else None,
        "amount": amount_cents / 100,
        "pattern_updated": creative is not None
    }


@router.get("/thompson-sampling")
async def get_thompson_sampling_recommendations(
    product_category: str = "language_learning",
    n_recommendations: int = 5,
    db: Session = Depends(get_db)
):
    """
    Thompson Sampling рекомендации - какие паттерны тестить дальше.

    Использует random.betavariate(alpha, beta) для сэмплирования из
    Beta-распределения каждого паттерна.

    Баланс Exploration vs Exploitation:
    - Высокий CVR + много данных = стабильно высокий sample (exploit)
    - Мало данных = высокая вариативность sample (explore)

    Example:
        GET /thompson-sampling?product_category=fitness&n_recommendations=3

    Returns:
        [
            {
                "pattern_hash": "hook:before_after|emo:achievement|...",
                "hook_type": "before_after",
                "emotion": "achievement",
                "thompson_score": 0.15,  # Sampled value
                "mean_cvr": 0.12,        # Expected CVR
                "alpha": 13,             # Beta params
                "beta": 95,
                "sample_size": 10,
                "reasoning": "High confidence winner (n=10)"
            },
            ...
        ]
    """

    # Получить все паттерны для категории
    patterns = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == product_category,
        PatternPerformance.sample_size > 0
    ).all()

    if not patterns:
        return {
            "recommendations": [],
            "message": f"No patterns found for {product_category}"
        }

    # Thompson Sampling
    recommendations = thompson_sampling(patterns, n_samples=n_recommendations)

    return {
        "product_category": product_category,
        "n_patterns_evaluated": len(patterns),
        "recommendations": recommendations,
        "algorithm": "Thompson Sampling with Beta prior",
        "note": "thompson_score is sampled from Beta(alpha, beta). Higher = recommend testing this pattern next."
    }
