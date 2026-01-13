"""
Thompson Sampling для оптимизации выбора паттернов.

Баланс между:
- Exploitation: Тестировать проверенные паттерны (высокий CVR)
- Exploration: Пробовать новые паттерны (может быть сюрприз)

Используется для выбора следующих креативов на тест.
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from sqlalchemy.orm import Session

from database.models import PatternPerformance, Creative

logger = logging.getLogger(__name__)


class ThompsonSamplingOptimizer:
    """
    Thompson Sampling для Multi-Armed Bandit задачи.

    Выбирает топ-N паттернов для следующего теста,
    балансируя между exploit (известные winners) и explore (новые паттерны).
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category

    def select_next_patterns(self, n_patterns: int = 5) -> List[Dict]:
        """
        Выбрать топ-N паттернов для следующего теста.

        Args:
            n_patterns: Количество паттернов

        Returns:
            List[Dict]: Паттерны отсортированные по priority
        """

        # Получить все протестированные паттерны
        patterns = self.db.query(PatternPerformance).filter(
            PatternPerformance.user_id == self.user_id,
            PatternPerformance.product_category == self.product_category
        ).all()

        if not patterns:
            # Если нет данных - вернуть базовые паттерны
            return self._get_default_patterns(n_patterns)

        pattern_scores = []

        for pattern in patterns:
            score = self._calculate_thompson_score(pattern)
            pattern_scores.append(score)

        # Сортировать по priority (Thompson Sampling score)
        pattern_scores.sort(key=lambda x: x['priority'], reverse=True)

        # Добавить рекомендации
        for i, pattern in enumerate(pattern_scores[:n_patterns]):
            pattern['rank'] = i + 1
            pattern['reasoning'] = self._generate_reasoning(pattern)

        return pattern_scores[:n_patterns]

    def _calculate_thompson_score(self, pattern: PatternPerformance) -> Dict:
        """
        Вычислить Thompson Sampling score для паттерна.

        Использует Beta distribution: Beta(alpha, beta)
        - alpha = bayesian_alpha (успехи из БД)
        - beta = bayesian_beta (провалы из БД)

        Формула Thompson Sampling:
        score = numpy.random.beta(α, β)

        Это балансирует между:
        - Exploitation: использование проверенных паттернов (высокий α)
        - Exploration: тестирование новых паттернов (высокая дисперсия)
        """

        # Beta distribution параметры из БД (уже обновляются атомарно в rudderstack.py)
        alpha = pattern.bayesian_alpha or 1.0
        beta = pattern.bayesian_beta or 1.0

        # Thompson Sampling: случайная выборка из Beta distribution
        # Используем numpy для производительности и стабильности
        sampled_cvr = np.random.beta(alpha, beta)

        # Uncertainty (высокая = нужно больше данных)
        uncertainty = beta / (alpha + beta)

        # Expected CVR (среднее) = α / (α + β)
        expected_cvr = alpha / (alpha + beta)

        # Weight multiplier (benchmark patterns имеют weight=2.0)
        weight = pattern.weight or 1.0

        return {
            'hook_type': pattern.hook_type,
            'emotion': pattern.emotion,
            'pacing': pattern.pacing,
            'cta_type': pattern.cta_type,
            'psychotype': pattern.psychotype,
            'expected_cvr': round(expected_cvr, 4),
            'sampled_cvr': round(float(sampled_cvr), 4),
            'uncertainty': round(float(uncertainty), 3),
            'priority': float(sampled_cvr) * weight,  # Weight влияет на приоритет
            'sample_size': pattern.sample_size,
            'total_conversions': pattern.total_conversions,
            'alpha': alpha,
            'beta': beta,
            'weight': weight,
            'source': pattern.source or 'client'
        }

    def _generate_reasoning(self, pattern: Dict) -> str:
        """
        Сгенерировать человекочитаемое объяснение почему выбран этот паттерн.
        """

        cvr = pattern['expected_cvr']
        uncertainty = pattern['uncertainty']
        sample_size = pattern['sample_size']

        if cvr > 0.10 and uncertainty < 0.3:
            return f"High CVR ({cvr:.1%}) + low uncertainty (tested {sample_size} times) - proven winner!"

        elif cvr > 0.10 and uncertainty >= 0.3:
            return f"High CVR ({cvr:.1%}) but high uncertainty - needs more tests to confirm"

        elif cvr < 0.05 and uncertainty > 0.5:
            return f"Low CVR ({cvr:.1%}) + high uncertainty - risky, but might surprise (explore)"

        elif uncertainty > 0.6:
            return f"High uncertainty (only {sample_size} tests) - exploration opportunity"

        else:
            return f"Moderate CVR ({cvr:.1%}) - balanced choice"

    def _get_default_patterns(self, n_patterns: int) -> List[Dict]:
        """
        Вернуть базовые паттерны если нет данных.

        Основаны на индустрии best practices.
        """

        default = [
            {
                'hook_type': 'wait',
                'emotion': 'excitement',
                'pacing': 'fast',
                'cta_type': 'urgency',
                'expected_cvr': 0.0,
                'priority': 1.0,
                'reasoning': 'Industry best practice - high engagement hook'
            },
            {
                'hook_type': 'shock',
                'emotion': 'curiosity',
                'pacing': 'medium',
                'cta_type': 'benefit',
                'expected_cvr': 0.0,
                'priority': 0.9,
                'reasoning': 'Strong pattern - curiosity gap drives clicks'
            },
            {
                'hook_type': 'question',
                'emotion': 'curiosity',
                'pacing': 'slow',
                'cta_type': 'benefit',
                'expected_cvr': 0.0,
                'priority': 0.8,
                'reasoning': 'Question hook - engages viewer thinking'
            },
            {
                'hook_type': 'urgency',
                'emotion': 'fomo',
                'pacing': 'fast',
                'cta_type': 'urgency',
                'expected_cvr': 0.0,
                'priority': 0.7,
                'reasoning': 'FOMO + urgency - time-sensitive offers'
            },
            {
                'hook_type': 'relatable',
                'emotion': 'trust',
                'pacing': 'medium',
                'cta_type': 'social_proof',
                'expected_cvr': 0.0,
                'priority': 0.6,
                'reasoning': 'Relatable content builds trust'
            }
        ]

        for i, pattern in enumerate(default[:n_patterns]):
            pattern['rank'] = i + 1
            pattern['sample_size'] = 0
            pattern['uncertainty'] = 1.0

        return default[:n_patterns]


class CrossProductOptimizer:
    """
    Оптимизатор для раскатки паттернов на схожие продукты.

    Используется для:
    - Lootbox паттерны → Casino (схожие продукты)
    - Betting паттерны → Sports (схожая аудитория)
    """

    # Карта схожести продуктов (0-1)
    PRODUCT_SIMILARITY = {
        'lootbox': {
            'lootbox': 1.0,
            'casino': 0.8,
            'betting': 0.6,
            'gaming': 0.7,
            'crypto': 0.4
        },
        'casino': {
            'casino': 1.0,
            'lootbox': 0.8,
            'betting': 0.7,
            'gaming': 0.5,
            'crypto': 0.3
        },
        'betting': {
            'betting': 1.0,
            'casino': 0.7,
            'sports': 0.9,
            'lootbox': 0.6,
            'gaming': 0.5
        }
    }

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def recommend_cross_product_patterns(
        self,
        target_product: str,
        n_patterns: int = 5
    ) -> List[Dict]:
        """
        Порекомендовать паттерны для нового продукта на основе схожих.

        Args:
            target_product: Целевой продукт (новый, для которого мало данных)
            n_patterns: Количество паттернов

        Returns:
            List[Dict]: Топ паттерны с корректировкой на схожесть продуктов
        """

        # Найти схожие продукты
        similar_products = self._get_similar_products(target_product)

        if not similar_products:
            logger.warning(f"No similar products found for {target_product}")
            return []

        # Собрать паттерны со всех схожих продуктов
        all_patterns = []

        for product, similarity in similar_products:
            patterns = self.db.query(PatternPerformance).filter(
                PatternPerformance.user_id == self.user_id,
                PatternPerformance.product_category == product
            ).all()

            for pattern in patterns:
                # Скорректировать CVR на схожесть продуктов
                adjusted_cvr = (pattern.avg_cvr / 10000) * similarity

                all_patterns.append({
                    'hook_type': pattern.hook_type,
                    'emotion': pattern.emotion,
                    'pacing': pattern.pacing,
                    'cta_type': pattern.cta_type,
                    'source_product': product,
                    'target_product': target_product,
                    'original_cvr': pattern.avg_cvr / 10000,
                    'adjusted_cvr': round(adjusted_cvr, 4),
                    'similarity': similarity,
                    'sample_size': pattern.sample_size,
                    'reasoning': f"Proven in {product} (CVR {pattern.avg_cvr / 10000:.1%}), "
                                f"adjusted for {target_product} similarity ({similarity:.0%})"
                })

        # Сортировать по adjusted_cvr
        all_patterns.sort(key=lambda x: x['adjusted_cvr'], reverse=True)

        return all_patterns[:n_patterns]

    def _get_similar_products(self, target_product: str) -> List[tuple]:
        """
        Получить список схожих продуктов отсортированных по similarity.

        Returns:
            List[tuple]: [(product, similarity), ...]
        """

        if target_product not in self.PRODUCT_SIMILARITY:
            return []

        similar = self.PRODUCT_SIMILARITY[target_product]

        # Сортировать по similarity (исключить сам продукт)
        similar_products = [
            (product, similarity)
            for product, similarity in similar.items()
            if product != target_product and similarity > 0.5
        ]

        similar_products.sort(key=lambda x: x[1], reverse=True)

        return similar_products


# Helper function for recommendations.py
def thompson_sampling(product_category: str, db: Session, n_recommendations: int = 5, niche: str = None):
    """
    Thompson Sampling для получения топ паттернов.
    
    Wrapper функция для использования в recommendations.py
    
    Args:
        product_category: Категория продукта
        db: Database session
        n_recommendations: Количество рекомендаций
        niche: EDTECH или HEALTH (опционально)
    
    Returns:
        List[Dict] с топ паттернами
    """
    from database.models import PatternPerformance
    import numpy as np
    
    # Фильтр паттернов
    query = db.query(PatternPerformance).filter(
        PatternPerformance.product_category == product_category
    )
    
    # Фильтр по niche если указан
    if niche:
        query = query.filter(PatternPerformance.niche == niche)
    
    patterns = query.all()
    
    if not patterns:
        logger.warning(f"No patterns found for category: {product_category}, niche: {niche}")
        return []
    
    # Thompson Sampling для каждого паттерна
    results = []
    for pattern in patterns:
        alpha = pattern.bayesian_alpha or 1.0
        beta = pattern.bayesian_beta or 1.0
        weight = pattern.weight or 1.0
        
        # Thompson score
        thompson_score = np.random.beta(alpha, beta) * weight
        
        results.append({
            'pattern_id': str(pattern.id),
            'hook_type': pattern.hook_type,
            'emotion': pattern.emotion,
            'pacing': pattern.pacing,
            'psychotype': pattern.psychotype,
            'target_audience_pain': pattern.target_audience_pain,
            'thompson_score': thompson_score,
            'alpha': alpha,
            'beta': beta,
            'weight': weight,
            'sample_size': pattern.sample_size or 0,
            'mean_cvr': alpha / (alpha + beta) if (alpha + beta) > 0 else 0,
        })
    
    # Сортировать по Thompson score
    results.sort(key=lambda x: x['thompson_score'], reverse=True)
    
    return results[:n_recommendations]
