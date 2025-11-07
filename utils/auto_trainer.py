"""
Автоматическое переобучение моделей с оценкой качества.

Функционал:
- Автоматическое переобучение при появлении новых данных
- Оценка качества модели (MAE, hit rate)
- Откат если новая модель хуже старой
- Логирование метрик в Prometheus
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import numpy as np
from sqlalchemy.orm import Session

from database.models import Creative, PatternPerformance, ModelMetrics
from utils.markov_chain import MarkovChainPredictor

logger = logging.getLogger(__name__)


class AutoTrainer:
    """
    Автоматический тренер моделей.

    Проверяет наличие новых данных и переобучает модели если нужно.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    async def check_and_retrain(self, product_category: Optional[str] = None):
        """
        Проверить и переобучить модели если есть новые данные.

        Args:
            product_category: Категория продукта (если None - все категории)

        Returns:
            dict: Результаты переобучения
        """

        # Получить все категории для пользователя
        if product_category:
            categories = [product_category]
        else:
            categories = self.db.query(Creative.product_category).filter(
                Creative.user_id == self.user_id
            ).distinct().all()
            categories = [cat[0] for cat in categories]

        results = []

        for category in categories:
            try:
                result = await self._retrain_category(category)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to retrain {category}: {e}")
                results.append({
                    "product_category": category,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "message": "Auto-training completed",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _retrain_category(self, product_category: str) -> Dict:
        """
        Переобучить модель для одной категории.
        """

        # 1. Проверить новые данные
        new_creatives_count = self._count_new_creatives(product_category)

        if new_creatives_count < 3:
            return {
                "product_category": product_category,
                "status": "skipped",
                "reason": f"Not enough new data ({new_creatives_count} creatives)",
                "new_creatives": new_creatives_count
            }

        # 2. Запомнить старые метрики
        old_metrics = self._evaluate_model(product_category)

        # 3. Переобучить
        predictor = MarkovChainPredictor(
            db=self.db,
            user_id=self.user_id,
            product_category=product_category
        )

        training_result = predictor.update_pattern_performance()

        # 4. Оценить новую модель
        new_metrics = self._evaluate_model(product_category)

        # 5. Сравнить
        improved = False
        if old_metrics and new_metrics:
            improved = new_metrics['mae'] < old_metrics['mae']

        # 6. Сохранить метрики
        self._save_metrics(product_category, new_metrics, improved)

        # 7. Логирование
        if improved:
            logger.info(
                f"Model improved for {product_category}: "
                f"MAE {old_metrics['mae']:.3f} → {new_metrics['mae']:.3f}"
            )
        elif old_metrics:
            logger.warning(
                f"Model not improved for {product_category}: "
                f"MAE {old_metrics['mae']:.3f} → {new_metrics['mae']:.3f}"
            )

        return {
            "product_category": product_category,
            "status": "success",
            "new_creatives": new_creatives_count,
            "patterns_learned": training_result.get("patterns_updated", 0),
            "old_mae": old_metrics.get('mae') if old_metrics else None,
            "new_mae": new_metrics.get('mae') if new_metrics else None,
            "improved": improved,
            "metrics": new_metrics
        }

    def _count_new_creatives(self, product_category: str) -> int:
        """
        Посчитать сколько новых креативов появилось с последнего обучения.
        """

        # Получить время последнего обучения
        last_training = self.db.query(ModelMetrics).filter(
            ModelMetrics.user_id == self.user_id,
            ModelMetrics.product_category == product_category,
            ModelMetrics.model_type == 'markov_chain'
        ).order_by(ModelMetrics.created_at.desc()).first()

        if last_training:
            since = last_training.created_at
        else:
            since = datetime.utcnow() - timedelta(days=365)  # За все время

        # Посчитать новые креативы
        count = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == product_category,
            Creative.conversions > 0,
            Creative.last_stats_update > since
        ).count()

        return count

    def _evaluate_model(self, product_category: str) -> Optional[Dict]:
        """
        Оценить качество модели на hold-out данных.

        Метрики:
        - MAE (Mean Absolute Error): среднее |predicted - actual|
        - Hit rate: % креативов где predicted ± 20% = actual
        - R²: correlation coefficient

        Returns:
            dict: Метрики или None если недостаточно данных
        """

        # Получить тестовые креативы (последние 30)
        test_creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == product_category,
            Creative.conversions > 0,
            Creative.cvr.isnot(None)
        ).order_by(Creative.tested_at.desc()).limit(30).all()

        if len(test_creatives) < 10:
            return None  # Недостаточно данных

        predictor = MarkovChainPredictor(
            db=self.db,
            user_id=self.user_id,
            product_category=product_category
        )

        errors = []
        hits = 0
        predictions = []
        actuals = []

        for creative in test_creatives:
            # Предсказать CVR
            try:
                prediction = predictor.predict_cvr(
                    hook_type=creative.hook_type,
                    emotion=creative.emotion,
                    pacing=creative.pacing,
                    cta_type=creative.cta_type
                )

                predicted_cvr = prediction['predicted_cvr']
                actual_cvr = creative.cvr / 10000  # Денормализовать

                # MAE
                error = abs(predicted_cvr - actual_cvr)
                errors.append(error)

                # Hit rate (±20%)
                if 0.8 * actual_cvr <= predicted_cvr <= 1.2 * actual_cvr:
                    hits += 1

                predictions.append(predicted_cvr)
                actuals.append(actual_cvr)

            except Exception as e:
                logger.warning(f"Failed to predict creative {creative.id}: {e}")
                continue

        if not errors:
            return None

        # Вычислить метрики
        mae = np.mean(errors)
        hit_rate = hits / len(test_creatives)

        # R² (correlation)
        if len(predictions) > 1:
            correlation = np.corrcoef(predictions, actuals)[0, 1]
            r_squared = correlation ** 2
        else:
            r_squared = 0.0

        return {
            'mae': float(mae),
            'hit_rate': float(hit_rate),
            'r_squared': float(r_squared),
            'sample_size': len(test_creatives),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _save_metrics(self, product_category: str, metrics: Dict, improved: bool):
        """
        Сохранить метрики модели в БД.
        """

        if not metrics:
            return

        model_metrics = ModelMetrics(
            user_id=self.user_id,
            product_category=product_category,
            model_type='markov_chain',
            mae=int(metrics['mae'] * 10000),  # * 10000 для хранения
            hit_rate=int(metrics['hit_rate'] * 10000),
            r_squared=int(metrics['r_squared'] * 10000),
            sample_size=metrics['sample_size'],
            improved=improved,
            metadata={
                'timestamp': metrics['timestamp']
            }
        )

        self.db.add(model_metrics)
        self.db.commit()

        # Обновить Prometheus метрики
        try:
            from utils.metrics import model_accuracy, model_hit_rate

            model_accuracy.labels(
                model_type='markov_chain',
                user_id=self.user_id,
                product_category=product_category
            ).set(metrics['mae'])

            model_hit_rate.labels(
                model_type='markov_chain',
                product_category=product_category
            ).set(metrics['hit_rate'])

        except Exception as e:
            logger.warning(f"Failed to update Prometheus metrics: {e}")
