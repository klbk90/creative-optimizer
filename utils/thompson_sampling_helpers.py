"""
Thompson Sampling Helpers - защита от холодного старта и оптимизация exploration.

Проблемы холодного старта:
1. Нет паттернов в базе → система не знает, что тестировать
2. Первый креатив случайно сработал → система зацикливается на нем

Решения:
1. Seed patterns - стартовые паттерны для exploration
2. Exploration bonus - бонус для новых паттернов
3. Regret monitoring - отслеживание упущенной выгоды
"""

from typing import List, Dict
import random
from sqlalchemy.orm import Session
from database.models import PatternPerformance
from utils.logger import setup_logger

logger = setup_logger(__name__)


# EdTech seed patterns (стартовые комбинации для exploration)
EDTECH_SEED_PATTERNS = [
    # Programming niche
    {
        "hook_type": "question",
        "emotion": "curiosity",
        "pacing": "fast",
        "cta_type": "urgency",
        "target_audience_pain": "no_time",
        "description": "Question hook + curiosity + urgency (classic EdTech)"
    },
    {
        "hook_type": "bold_claim",
        "emotion": "excitement",
        "pacing": "fast",
        "cta_type": "direct",
        "target_audience_pain": "fear_failure",
        "description": "Bold claim + excitement (achievement-focused)"
    },
    {
        "hook_type": "wait",
        "emotion": "curiosity",
        "pacing": "medium",
        "cta_type": "soft",
        "target_audience_pain": "no_progress",
        "description": "Wait hook + curiosity (mystery-based)"
    },
    # Design niche
    {
        "hook_type": "question",
        "emotion": "greed",
        "pacing": "fast",
        "cta_type": "urgency",
        "target_audience_pain": "too_expensive",
        "description": "Question + greed (price-focused)"
    },
    # Career switch niche
    {
        "hook_type": "bold_claim",
        "emotion": "fear",
        "pacing": "fast",
        "cta_type": "scarcity",
        "target_audience_pain": "need_career_switch",
        "description": "Bold claim + fear + scarcity (FOMO-driven)"
    },
]


def create_seed_patterns(
    db: Session,
    user_id: str,
    product_category: str,
    force: bool = False
) -> int:
    """
    Создает seed patterns для холодного старта.

    Args:
        db: Database session
        user_id: User UUID
        product_category: Product category
        force: Создать даже если паттерны уже есть

    Returns:
        Количество созданных seed patterns

    Usage:
        ```python
        from utils.thompson_sampling_helpers import create_seed_patterns

        n_created = create_seed_patterns(
            db=db,
            user_id="user-uuid",
            product_category="language_learning",
            force=False
        )

        print(f"Created {n_created} seed patterns")
        ```
    """

    # Проверить, есть ли уже паттерны
    if not force:
        existing_count = db.query(PatternPerformance).filter(
            PatternPerformance.user_id == user_id,
            PatternPerformance.product_category == product_category
        ).count()

        if existing_count > 0:
            logger.info(f"Seed patterns not needed - {existing_count} patterns already exist")
            return 0

    # Создать seed patterns
    created = 0

    for seed in EDTECH_SEED_PATTERNS:
        # Создать pattern_hash
        pattern_hash = (
            f"hook:{seed['hook_type']}"
            f"|emo:{seed['emotion']}"
            f"|pace:{seed['pacing']}"
            f"|pain:{seed['target_audience_pain']}"
            f"|cta:{seed['cta_type']}"
        )

        # Проверить, существует ли уже
        existing = db.query(PatternPerformance).filter(
            PatternPerformance.pattern_hash == pattern_hash,
            PatternPerformance.product_category == product_category
        ).first()

        if existing and not force:
            continue

        # Создать новый паттерн с нулевыми метриками (exploration)
        import uuid
        pattern = PatternPerformance(
            id=uuid.uuid4(),
            user_id=user_id,
            pattern_hash=pattern_hash,
            hook_type=seed['hook_type'],
            emotion=seed['emotion'],
            pacing=seed['pacing'],
            cta_type=seed['cta_type'],
            target_audience_pain=seed['target_audience_pain'],
            product_category=product_category,
            sample_size=0,
            total_impressions=0,
            total_clicks=0,
            total_conversions=0,
            total_revenue=0,
            avg_cvr=0,
            avg_ctr=0,
            avg_roas=0,
            confidence_interval_lower=0,
            confidence_interval_upper=0
        )

        db.add(pattern)
        created += 1

    db.commit()

    logger.info(f"✅ Created {created} seed patterns for {product_category}")

    return created


def thompson_sampling_with_exploration_bonus(
    patterns: List[PatternPerformance],
    n_samples: int = 5,
    exploration_bonus: float = 0.05
) -> List[Dict]:
    """
    Thompson Sampling с бонусом для новых паттернов (exploration).

    Добавляет exploration_bonus к thompson_score для паттернов с малой выборкой.

    Args:
        patterns: Список PatternPerformance объектов
        n_samples: Количество рекомендаций
        exploration_bonus: Бонус для новых паттернов (0.0 - 0.1)

    Returns:
        Список рекомендаций с thompson_score + exploration_bonus

    Пример:
        - Паттерн с sample_size=0: bonus = 0.05
        - Паттерн с sample_size=10: bonus = 0.025
        - Паттерн с sample_size=50+: bonus = 0
    """

    recommendations = []

    for pattern in patterns:
        total_conversions = pattern.total_conversions or 0
        total_clicks = pattern.total_clicks or 0

        # Beta параметры
        alpha = 1.0 + total_conversions
        beta_param = 1.0 + max(0, total_clicks - total_conversions)

        # Thompson Sampling
        thompson_score = random.betavariate(alpha, beta_param)

        # Exploration bonus (уменьшается с ростом sample_size)
        sample_size = pattern.sample_size or 0
        bonus = exploration_bonus * max(0, 1 - sample_size / 50)

        final_score = thompson_score + bonus

        # Mean CVR
        mean_cvr = alpha / (alpha + beta_param)

        recommendations.append({
            "pattern_hash": pattern.pattern_hash,
            "hook_type": pattern.hook_type,
            "emotion": pattern.emotion,
            "pacing": pattern.pacing,
            "target_audience_pain": pattern.target_audience_pain,
            "thompson_score": thompson_score,
            "exploration_bonus": bonus,
            "final_score": final_score,
            "mean_cvr": mean_cvr,
            "sample_size": sample_size,
            "total_conversions": total_conversions,
            "alpha": alpha,
            "beta": beta_param,
            "reasoning": (
                f"High confidence winner (n={sample_size})" if sample_size > 20
                else f"Promising, needs more data (n={sample_size})" if sample_size > 5
                else f"New pattern, high exploration value (bonus={bonus:.3f})"
            )
        })

    # Сортируем по final_score (thompson_score + exploration_bonus)
    recommendations.sort(key=lambda x: x['final_score'], reverse=True)

    return recommendations[:n_samples]


def calculate_regret(
    actual_pattern: str,
    best_pattern: str,
    actual_cvr: float,
    best_cvr: float,
    n_trials: int
) -> Dict:
    """
    Вычисляет regret (упущенную выгоду) от выбора неоптимального паттерна.

    Regret = (Best CVR - Actual CVR) * N trials

    Args:
        actual_pattern: Паттерн, который выбрали
        best_pattern: Лучший паттерн (в hindsight)
        actual_cvr: CVR выбранного паттерна
        best_cvr: CVR лучшего паттерна
        n_trials: Количество trials (impressions/clicks)

    Returns:
        {
            "regret": 0.05,  # Упущенная выгода (5%)
            "regret_conversions": 5,  # Упущенные конверсии
            "actual_pattern": "hook:question|...",
            "best_pattern": "hook:bold_claim|...",
            "recommendation": "..."
        }

    Цель Thompson Sampling: минимизировать cumulative regret.
    """

    regret = best_cvr - actual_cvr
    regret_conversions = regret * n_trials

    return {
        "regret": round(regret, 4),
        "regret_percent": round(regret * 100, 2),
        "regret_conversions": int(regret_conversions),
        "actual_pattern": actual_pattern,
        "best_pattern": best_pattern,
        "actual_cvr": round(actual_cvr, 4),
        "best_cvr": round(best_cvr, 4),
        "n_trials": n_trials,
        "recommendation": (
            "Low regret - good exploration!" if abs(regret) < 0.02
            else "Moderate regret - acceptable" if abs(regret) < 0.05
            else "High regret - consider adjusting exploration bonus"
        )
    }


def simulate_thompson_sampling_performance(
    patterns: List[Dict],
    n_simulations: int = 1000
) -> Dict:
    """
    Симуляция Thompson Sampling для оценки exploration/exploitation баланса.

    Args:
        patterns: Список паттернов с true_cvr
            [{"pattern": "A", "true_cvr": 0.15}, ...]
        n_simulations: Количество симуляций

    Returns:
        {
            "average_regret": 0.03,
            "best_pattern_selected_pct": 0.75,
            "exploration_rate": 0.25
        }
    """

    if not patterns:
        return {"error": "No patterns provided"}

    # Найти лучший паттерн
    best_pattern = max(patterns, key=lambda x: x['true_cvr'])

    selected_counts = {p['pattern']: 0 for p in patterns}
    total_regret = 0

    for _ in range(n_simulations):
        # Thompson Sampling для каждого паттерна
        samples = []

        for p in patterns:
            # Для симуляции: alpha ~ conversions, beta ~ failures
            # Используем true_cvr для генерации alpha/beta
            alpha = p['true_cvr'] * 100 + 1
            beta = (1 - p['true_cvr']) * 100 + 1

            score = random.betavariate(alpha, beta)
            samples.append((p['pattern'], score, p['true_cvr']))

        # Выбрать паттерн с highest score
        selected = max(samples, key=lambda x: x[1])
        selected_pattern, _, selected_cvr = selected

        selected_counts[selected_pattern] += 1

        # Вычислить regret
        regret = best_pattern['true_cvr'] - selected_cvr
        total_regret += regret

    # Результаты
    avg_regret = total_regret / n_simulations
    best_selected_pct = selected_counts[best_pattern['pattern']] / n_simulations
    exploration_rate = 1 - best_selected_pct

    return {
        "average_regret": round(avg_regret, 4),
        "average_regret_percent": round(avg_regret * 100, 2),
        "best_pattern_selected_pct": round(best_selected_pct, 3),
        "exploration_rate": round(exploration_rate, 3),
        "selected_counts": selected_counts,
        "n_simulations": n_simulations,
        "recommendation": (
            "Excellent balance!" if 0.7 <= best_selected_pct <= 0.85
            else "Too much exploration (increase sample size)" if best_selected_pct < 0.7
            else "Too much exploitation (add exploration bonus)"
        )
    }


if __name__ == "__main__":
    # Демо: симуляция Thompson Sampling
    print("🎲 Thompson Sampling Simulation")
    print("="*60)

    # Паттерны с разными true CVR
    test_patterns = [
        {"pattern": "question + curiosity", "true_cvr": 0.15},  # Best
        {"pattern": "bold_claim + excitement", "true_cvr": 0.12},
        {"pattern": "wait + fear", "true_cvr": 0.08},
        {"pattern": "urgency + greed", "true_cvr": 0.10},
    ]

    result = simulate_thompson_sampling_performance(test_patterns, n_simulations=10000)

    print(f"\nBest pattern: question + curiosity (CVR=15%)")
    print(f"Average regret: {result['average_regret_percent']:.2f}%")
    print(f"Best pattern selected: {result['best_pattern_selected_pct']*100:.1f}% of time")
    print(f"Exploration rate: {result['exploration_rate']*100:.1f}%")
    print(f"\n{result['recommendation']}")

    print(f"\nSelection distribution:")
    for pattern, count in result['selected_counts'].items():
        pct = count / result['n_simulations'] * 100
        print(f"  {pattern}: {pct:.1f}%")
