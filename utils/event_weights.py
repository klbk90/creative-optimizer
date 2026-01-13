"""
Event Weights for Bayesian Update - Early Signal Logic.

Веса событий для обновления α и β в зависимости от типа события.

RETENTION FOCUS:
- INSTALL = 0.1 (слабый сигнал)
- TRIAL_START = 0.5 (средний сигнал, early predictor)
- PURCHASE = 1.0 (сильный сигнал)
- RETENTION_D7 = 1.2 (самый сильный сигнал!)

Early Signal Logic:
Если данных мало (< 100 installs), приоритет TRIAL_START и ONBOARDING_COMPLETE
как ранние предикторы успеха для микро-инфлюенсеров.
"""

from typing import Dict, Tuple
from database.models import EVENT_WEIGHTS

# Early signal threshold
EARLY_SIGNAL_THRESHOLD = 100  # Если < 100 installs, используем early signals


def get_event_weight(event_name: str) -> float:
    """
    Получить вес события для Bayesian update.

    Args:
        event_name: Название события (INSTALL, TRIAL_START, PURCHASE, RETENTION_D7)

    Returns:
        Вес события (0.1 - 1.2)
    """
    return EVENT_WEIGHTS.get(event_name, 0.0)


def calculate_bayesian_update(
    event_name: str,
    is_success: bool,
    current_installs: int = 0
) -> Tuple[float, float]:
    """
    Рассчитать обновление α и β для события.

    Early Signal Logic:
    - Если installs < 100, увеличиваем вес TRIAL_START и ONBOARDING_COMPLETE
    - Это ранние предикторы успеха для микро-инфлюенсеров

    Args:
        event_name: Название события
        is_success: True если событие успешное (конверсия), False если просмотр/неудача
        current_installs: Текущее количество установок (для early signal logic)

    Returns:
        (delta_alpha, delta_beta) - изменения для атомарного update
    """
    # Базовый вес события
    weight = get_event_weight(event_name)

    # Early Signal Logic: если данных мало, повышаем приоритет ранних событий
    if current_installs < EARLY_SIGNAL_THRESHOLD:
        if event_name in ['TRIAL_START', 'ONBOARDING_COMPLETE']:
            # Увеличиваем вес ранних событий на 50% для Early Signal
            weight *= 1.5
            weight = min(weight, 1.0)  # Cap at 1.0

    # Рассчитываем delta для α и β
    if is_success:
        # Успех → увеличиваем α (успехи)
        delta_alpha = weight
        delta_beta = 0.0
    else:
        # Неудача → увеличиваем β (неудачи)
        delta_alpha = 0.0
        delta_beta = weight

    return (delta_alpha, delta_beta)


def get_priority_metric(total_installs: int) -> str:
    """
    Определить приоритетную метрику в зависимости от количества данных.

    Args:
        total_installs: Общее количество установок

    Returns:
        Название приоритетной метрики
    """
    if total_installs < EARLY_SIGNAL_THRESHOLD:
        return "TRIAL_START"  # Early Signal - фокус на триал
    else:
        return "RETENTION_D7"  # Достаточно данных - фокус на retention


# Mapping событий RudderStack → наши event names
RUDDERSTACK_EVENT_MAP = {
    "Application Installed": "INSTALL",
    "Onboarding Complete": "ONBOARDING_COMPLETE",
    "Trial Started": "TRIAL_START",
    "Order Completed": "PURCHASE",
    "Subscription Started": "PURCHASE",
    "Day 7 Active": "RETENTION_D7",
    "Week 1 Retention": "RETENTION_D7",
}


def map_rudderstack_event(rudderstack_event_name: str) -> str:
    """
    Преобразовать название события RudderStack в наше внутреннее название.

    Args:
        rudderstack_event_name: Название события от RudderStack

    Returns:
        Внутреннее название события или пустая строка если не найдено
    """
    return RUDDERSTACK_EVENT_MAP.get(rudderstack_event_name, "")
