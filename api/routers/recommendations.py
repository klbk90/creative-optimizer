"""
Recommendations Router - Decision Making Engine для адаптации креативов.

Ключевая фича: на основе Bayesian Score рекомендует какой benchmark креатив
адаптировать для блогера, чтобы получить максимальный ROI.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Optional, List, Dict
from pydantic import BaseModel
import numpy as np
import math

from database.base import get_db
from database.models import Creative, PatternPerformance, User
from utils.thompson_sampling import thompson_sampling
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# Pydantic Schemas

class WinningElement(BaseModel):
    """Выигрышный элемент паттерна."""
    type: str  # visual, structure, tone, unique
    description: str


class ScriptStep(BaseModel):
    """Шаг скрипта для съемки."""
    timestamp: str  # "0-3s", "3-7s", "7-15s"
    action: str
    example: str


class RecommendationResponse(BaseModel):
    """Рекомендация для адаптации креатива."""
    benchmark_creative_id: str
    benchmark_creative_name: str
    benchmark_video_url: Optional[str]
    psychotype: str
    hook_type: str
    emotion: str
    pacing: str
    target_audience_pain: str
    winning_elements: List[WinningElement]
    script_outline: List[ScriptStep]
    adaptation_instructions: str
    expected_roi: float
    confidence: float  # 0-100, рассчитано через Beta дисперсию
    bayesian_stats: Dict
    reasoning: str


class RecommendationRequest(BaseModel):
    """Запрос рекомендации."""
    product_category: str
    influencer_niche: Optional[str] = None
    target_psychotype: Optional[str] = None
    n_recommendations: int = 1


# Helper Functions

def calculate_beta_confidence(alpha: float, beta: float) -> float:
    """
    Рассчитать confidence на основе дисперсии Beta-распределения.

    Чем больше данных (α + β), тем ниже дисперсия, тем выше уверенность.

    Formula:
        variance = (α*β) / ((α+β)²(α+β+1))
        mean = α / (α+β)
        coefficient_of_variation = sqrt(variance) / mean
        confidence = (1 - coefficient_of_variation) * 100

    Args:
        alpha: Bayesian alpha (successes)
        beta: Bayesian beta (failures)

    Returns:
        Confidence score 0-100
    """
    if alpha <= 0 or beta <= 0:
        return 0.0

    # Sample size
    n = alpha + beta

    # Mean CVR
    mean_cvr = alpha / n

    # Variance
    variance = (alpha * beta) / ((n ** 2) * (n + 1))

    # Standard deviation
    std_dev = math.sqrt(variance)

    # Coefficient of variation (relative uncertainty)
    if mean_cvr > 0:
        cv = std_dev / mean_cvr
    else:
        cv = 1.0

    # Confidence: чем меньше CV, тем выше уверенность
    # CV = 0 → confidence = 100
    # CV = 1 → confidence = 0
    confidence = max(0, min(100, (1 - cv) * 100))

    # Boost confidence for large sample sizes
    if n > 100:
        confidence = min(100, confidence + math.log10(n) * 5)

    return round(confidence, 1)


def calculate_expected_roi(alpha: float, beta: float, weight: float = 1.0) -> float:
    """
    Рассчитать ожидаемый ROI на основе Bayesian Score.

    Args:
        alpha: Bayesian alpha
        beta: Bayesian beta
        weight: Pattern weight (benchmark=2.0, client=1.0)

    Returns:
        Expected ROI multiplier (например 2.3 = 230% ROI)
    """
    if alpha <= 0 or beta <= 0:
        return 1.0

    # Mean CVR
    mean_cvr = alpha / (alpha + beta)

    # Thompson Score (sample from Beta distribution)
    thompson_score = np.random.beta(alpha, beta)

    # Expected ROI = weighted Thompson Score * baseline multiplier
    baseline_roi = 1.5  # Baseline ROI для среднего креатива
    expected_roi = baseline_roi * (thompson_score / 0.05) * weight

    return round(expected_roi, 2)


def generate_winning_elements(creative: Creative) -> List[WinningElement]:
    """
    Генерирует список winning elements на основе анализа креатива.

    Args:
        creative: Creative объект с результатами Claude Vision анализа

    Returns:
        Список WinningElement объектов
    """
    elements = []

    # Parse winning_elements из analysis_result
    if hasattr(creative, 'analysis_result') and creative.analysis_result:
        winning_text = creative.analysis_result.get('winning_elements', '')

        # Разбираем текст на элементы
        if 'Text overlay' in winning_text or 'текст' in winning_text.lower():
            elements.append(WinningElement(
                type="visual",
                description="Text overlay в первых 3 секундах с четким value proposition"
            ))

        if 'UGC' in winning_text or 'authentic' in winning_text.lower():
            elements.append(WinningElement(
                type="tone",
                description="Authentic UGC стиль - съемка на смартфон, естественное освещение"
            ))

        if 'Subtitle' in winning_text or 'субтитр' in winning_text.lower():
            elements.append(WinningElement(
                type="visual",
                description="Субтитры для доступности и engagement (люди смотрят без звука)"
            ))

        if 'before' in winning_text.lower() or 'transformation' in winning_text.lower():
            elements.append(WinningElement(
                type="structure",
                description="Контраст До/После - показать трансформацию"
            ))

        if 'CTA' in winning_text or 'call to action' in winning_text.lower():
            elements.append(WinningElement(
                type="structure",
                description="Четкий CTA в конце с кнопкой или ссылкой"
            ))

    # Если элементов нет, добавляем дефолтные на основе hook_type
    if not elements and hasattr(creative, 'hook_type'):
        if creative.hook_type == 'transformation':
            elements.append(WinningElement(
                type="structure",
                description="Transformation hook - показать изменение до/после"
            ))
        elif creative.hook_type == 'problem_agitation':
            elements.append(WinningElement(
                type="structure",
                description="Problem agitation - усилить боль, затем показать решение"
            ))

    return elements


def generate_script_outline(
    creative: Creative,
    winning_elements: List[WinningElement]
) -> List[ScriptStep]:
    """
    Генерирует пошаговый план съемки (script outline) на основе паттерна.

    Args:
        creative: Creative объект
        winning_elements: Список выигрышных элементов

    Returns:
        Список ScriptStep объектов
    """
    steps = []

    # Hook (0-3s)
    hook_action = "Привлечь внимание"
    if creative.hook_type == 'transformation':
        hook_action = "Показать конечный результат или задать вопрос 'Хочешь так же?'"
    elif creative.hook_type == 'problem_agitation':
        hook_action = "Обострить боль: 'Устал от [проблема]?'"
    elif creative.hook_type == 'question':
        hook_action = "Задать провокационный вопрос прямо в камеру"

    steps.append(ScriptStep(
        timestamp="0-3s",
        action=f"HOOK: {hook_action}",
        example=f"Пример: Крупный план лица блогера + текст на экране с ключевой фразой"
    ))

    # Body (3-10s)
    body_action = "Объяснить проблему и решение"
    if creative.emotion == 'hope':
        body_action = "Показать путь к трансформации, вселить надежду"
    elif creative.emotion == 'curiosity':
        body_action = "Раскрыть секрет или инсайд, вызвать любопытство"

    steps.append(ScriptStep(
        timestamp="3-10s",
        action=f"BODY: {body_action}",
        example=f"Пример: B-roll footage + voiceover с объяснением метода"
    ))

    # CTA (10-15s)
    steps.append(ScriptStep(
        timestamp="10-15s",
        action="CTA: Призыв к действию",
        example="Пример: 'Попробуй сейчас, первая неделя бесплатно' + кнопка"
    ))

    return steps


def generate_adaptation_instructions(
    creative: Creative,
    winning_elements: List[WinningElement],
    influencer_niche: Optional[str] = None
) -> str:
    """
    Генерирует инструкции по адаптации креатива под блогера.

    Args:
        creative: Creative объект
        winning_elements: Список выигрышных элементов
        influencer_niche: Ниша блогера (опционально)

    Returns:
        Текстовые инструкции
    """
    instructions = []

    # Format
    instructions.append(f"📹 **Формат:** UGC вертикальное видео 9:16, длительность 15-30 секунд")

    # Hook
    instructions.append(f"🎣 **Hook:** Используй '{creative.hook_type}' - {_get_hook_description(creative.hook_type)}")

    # Emotion
    instructions.append(f"💭 **Emotion:** Вызови эмоцию '{creative.emotion}' через тон голоса и визуал")

    # Pacing
    pacing_desc = "быстрая смена кадров" if creative.pacing == "fast" else "спокойный темп"
    instructions.append(f"⚡ **Pacing:** {pacing_desc}")

    # Winning Elements
    if winning_elements:
        elements_text = ", ".join([el.description for el in winning_elements[:3]])
        instructions.append(f"✨ **Ключевые элементы:** {elements_text}")

    # Psychotype
    if creative.psychotype:
        instructions.append(f"🎯 **Целевой психотип:** {creative.psychotype} - {_get_psychotype_description(creative.psychotype)}")

    # Influencer adaptation
    if influencer_niche:
        instructions.append(f"👤 **Адаптация под блогера:** Попроси блогера добавить личный опыт из ниши '{influencer_niche}'")

    return "\n".join(instructions)


def _get_hook_description(hook_type: str) -> str:
    """Получить описание hook типа."""
    descriptions = {
        "transformation": "Покажи результат ДО/ПОСЛЕ",
        "problem_agitation": "Обостри боль проблемы",
        "question": "Задай провокационный вопрос",
        "social_proof": "Покажи отзывы или цифры",
        "insider_secret": "Раскрой секрет или инсайд",
        "urgency": "Создай срочность (ограничение времени)",
        "before_after": "Покажи контраст до/после",
        "pain_point": "Попади в боль аудитории"
    }
    return descriptions.get(hook_type, "Привлеки внимание первыми 3 секундами")


def _get_psychotype_description(psychotype: str) -> str:
    """Получить описание психотипа."""
    descriptions = {
        "Switcher": "Постоянно ищет 'идеальное решение', нетерпеливый",
        "Status Seeker": "Мотивирован сертификатами и карьерой",
        "Skill Upgrader": "Практик, хочет конкретные навыки СЕЙЧАС",
        "Freedom Hunter": "Ценит гибкость и свободу, хочет escape 9-5",
        "Safety Seeker": "Избегает рисков, нужны гарантии"
    }
    return descriptions.get(psychotype, "")


# Endpoints

@router.get("/creative-to-adapt", response_model=RecommendationResponse)
async def get_creative_to_adapt(
    product_category: str = Query(..., description="Категория продукта (language_learning, fitness, finance)"),
    influencer_niche: Optional[str] = Query(None, description="Ниша блогера для адаптации"),
    target_psychotype: Optional[str] = Query(None, description="Целевой психотип аудитории"),
    db: Session = Depends(get_db)
):
    """
    🎯 **DECISION MAKING ENGINE**: Какой креатив адаптировать для максимального ROI?

    На основе Bayesian Score рекомендует benchmark креатив для адаптации.

    **Как работает:**
    1. Thompson Sampling выбирает топ паттерны с максимальным потенциалом
    2. Находит benchmark креатив с этим паттерном
    3. Рассчитывает confidence через дисперсию Beta-распределения
    4. Генерирует script_outline (пошаговый план съемки)
    5. Создает adaptation_instructions для блогера

    **Пример использования:**
    ```
    GET /api/v1/recommendations/creative-to-adapt?product_category=language_learning&influencer_niche=travel
    ```

    **Response:**
    - benchmark_creative_id: ID эталонного креатива
    - benchmark_video_url: Ссылка на видео (для референса)
    - winning_elements: Что делает это видео хитом
    - script_outline: Пошаговый план съемки (Hook → Body → CTA)
    - adaptation_instructions: Как адаптировать под блогера
    - expected_roi: Ожидаемый ROI (например 2.3 = 230%)
    - confidence: Уверенность в рекомендации (0-100)
    """
    logger.info(f"🎯 Getting creative recommendation for category: {product_category}")

    try:
        # 1. Получаем топ паттерны через Thompson Sampling
        top_patterns = thompson_sampling(
            product_category=product_category,
            db=db,
            n_recommendations=5
        )

        if not top_patterns:
            raise HTTPException(
                status_code=404,
                detail=f"No patterns found for category: {product_category}. Please seed benchmark data first."
            )

        # 2. Фильтруем по психотипу если указан
        if target_psychotype:
            top_patterns = [p for p in top_patterns if p.get('psychotype') == target_psychotype]

        if not top_patterns:
            raise HTTPException(
                status_code=404,
                detail=f"No patterns found for psychotype: {target_psychotype}"
            )

        # 3. Берем топ-1 паттерн
        best_pattern = top_patterns[0]

        logger.info(f"   Best pattern: {best_pattern['hook_type']} + {best_pattern['emotion']} (score: {best_pattern['thompson_score']:.4f})")

        # 4. Находим benchmark креатив с этим паттерном
        benchmark_creative = db.query(Creative).filter(
            and_(
                Creative.is_benchmark == True,
                Creative.product_category == product_category,
                Creative.hook_type == best_pattern['hook_type'],
                Creative.emotion == best_pattern['emotion']
            )
        ).first()

        if not benchmark_creative:
            # Fallback: найти любой benchmark креатив этой категории
            benchmark_creative = db.query(Creative).filter(
                and_(
                    Creative.is_benchmark == True,
                    Creative.product_category == product_category
                )
            ).first()

        if not benchmark_creative:
            raise HTTPException(
                status_code=404,
                detail=f"No benchmark creatives found for category: {product_category}. Please run seed_market_data.py first."
            )

        logger.info(f"   Benchmark creative: {benchmark_creative.name} (id: {benchmark_creative.id})")

        # 5. Генерируем winning elements
        winning_elements = generate_winning_elements(benchmark_creative)

        # 6. Генерируем script outline
        script_outline = generate_script_outline(benchmark_creative, winning_elements)

        # 7. Генерируем adaptation instructions
        adaptation_instructions = generate_adaptation_instructions(
            benchmark_creative,
            winning_elements,
            influencer_niche
        )

        # 8. Рассчитываем confidence через Beta дисперсию
        alpha = best_pattern.get('alpha', 1.0)
        beta = best_pattern.get('beta', 1.0)
        confidence = calculate_beta_confidence(alpha, beta)

        # 9. Рассчитываем expected ROI
        weight = best_pattern.get('weight', 1.0)
        expected_roi = calculate_expected_roi(alpha, beta, weight)

        # 10. Формируем reasoning
        sample_size = alpha + beta
        cvr = alpha / sample_size if sample_size > 0 else 0
        reasoning = (
            f"Паттерн '{best_pattern['hook_type']} + {best_pattern['emotion']}' "
            f"показал CVR {cvr*100:.1f}% (α={alpha:.0f}, β={beta:.0f}) на {sample_size:.0f} тестах. "
        )

        if benchmark_creative.psychotype:
            reasoning += f"Психотип '{benchmark_creative.psychotype}' "
            if influencer_niche:
                reasoning += f"подходит для ниши '{influencer_niche}'. "
            else:
                reasoning += "подходит для целевой аудитории. "

        reasoning += f"Thompson Score: {best_pattern['thompson_score']:.4f} (weight={weight})."

        # 11. Получаем download URL для видео
        video_url = None
        if benchmark_creative.video_url:
            from utils.storage import get_download_url
            try:
                video_url = get_download_url(benchmark_creative.video_url)
            except Exception as e:
                logger.warning(f"Failed to generate download URL: {e}")

        # 12. Формируем ответ
        recommendation = RecommendationResponse(
            benchmark_creative_id=str(benchmark_creative.id),
            benchmark_creative_name=benchmark_creative.name,
            benchmark_video_url=video_url,
            psychotype=benchmark_creative.psychotype or best_pattern.get('psychotype', 'Unknown'),
            hook_type=best_pattern['hook_type'],
            emotion=best_pattern['emotion'],
            pacing=best_pattern.get('pacing', 'medium'),
            target_audience_pain=best_pattern.get('target_audience_pain', 'unknown'),
            winning_elements=winning_elements,
            script_outline=script_outline,
            adaptation_instructions=adaptation_instructions,
            expected_roi=expected_roi,
            confidence=confidence,
            bayesian_stats={
                "alpha": alpha,
                "beta": beta,
                "sample_size": sample_size,
                "mean_cvr": cvr,
                "thompson_score": best_pattern['thompson_score'],
                "weight": weight
            },
            reasoning=reasoning
        )

        logger.info(f"✅ Recommendation generated: {benchmark_creative.name} (confidence: {confidence}%, ROI: {expected_roi}x)")

        return recommendation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
