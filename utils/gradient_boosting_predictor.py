"""
Gradient Boosting (LightGBM) предсказатель CVR креативов.

Используется когда данных > 50 креативов.
Более точный чем Markov Chain, но требует больше данных.
"""

import logging
from typing import Dict, Optional, List
import numpy as np
from sqlalchemy.orm import Session
import pickle
import os

from database.models import Creative, PatternPerformance

logger = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    LIGHTGBM_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not installed. Run: pip install lightgbm scikit-learn")
    LIGHTGBM_AVAILABLE = False


class GradientBoostingPredictor:
    """
    LightGBM модель для предсказания CVR креативов.

    Features:
    - Categorical: hook_type, emotion, pacing, cta_type
    - Numerical: duration, has_text_overlay, has_voiceover
    - Historical: avg CVR по каждому признаку
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category
        self.model = None
        self.feature_names = []
        self.encoders = {}

        # Путь для сохранения модели
        self.model_path = f"models/lgbm_{user_id}_{product_category}.pkl"

    def prepare_features(self, creative: Creative) -> Dict:
        """
        Создать feature vector для креатива.

        Returns:
            Dict[str, float]: Features
        """

        features = {}

        # Categorical features (one-hot encoding)
        categorical_features = {
            'hook_type': creative.hook_type or 'unknown',
            'emotion': creative.emotion or 'unknown',
            'pacing': creative.pacing or 'unknown',
            'cta_type': creative.cta_type or 'unknown'
        }

        for feat_name, feat_value in categorical_features.items():
            if feat_name not in self.encoders:
                continue

            # One-hot encoding
            encoder = self.encoders[feat_name]
            if feat_value in encoder.classes_:
                encoded = encoder.transform([feat_value])[0]
            else:
                encoded = -1  # Unknown category

            features[feat_name] = encoded

        # Numerical features
        features['duration_seconds'] = creative.duration_seconds or 15
        features['has_text_overlay'] = int(creative.has_text_overlay or False)
        features['has_voiceover'] = int(creative.has_voiceover or False)

        # Historical features (avg CVR для каждого признака)
        features['hook_avg_cvr'] = self._get_historical_cvr('hook_type', creative.hook_type)
        features['emotion_avg_cvr'] = self._get_historical_cvr('emotion', creative.emotion)
        features['pacing_avg_cvr'] = self._get_historical_cvr('pacing', creative.pacing)
        features['cta_avg_cvr'] = self._get_historical_cvr('cta_type', creative.cta_type)

        return features

    def _get_historical_cvr(self, feature_type: str, feature_value: Optional[str]) -> float:
        """
        Получить исторический средний CVR для признака.

        Args:
            feature_type: Тип признака (hook_type, emotion, etc)
            feature_value: Значение признака

        Returns:
            float: Средний CVR (0-1)
        """

        if not feature_value:
            return 0.0

        # Найти в PatternPerformance
        filter_dict = {
            'user_id': self.user_id,
            'product_category': self.product_category,
            feature_type: feature_value
        }

        pattern = self.db.query(PatternPerformance).filter_by(**filter_dict).first()

        if pattern and pattern.avg_cvr:
            return pattern.avg_cvr / 10000
        else:
            return 0.0

    def train(self, test_size: float = 0.2) -> Dict:
        """
        Обучить LightGBM модель.

        Args:
            test_size: Доля данных для test set (0-1)

        Returns:
            dict: Метрики обучения
        """

        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not installed")

        # Загрузить креативы с данными
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.conversions > 0,
            Creative.cvr.isnot(None)
        ).all()

        if len(creatives) < 50:
            raise ValueError(
                f"Need at least 50 creatives to train GBM. "
                f"Found: {len(creatives)}. Use Markov Chain instead."
            )

        # Создать LabelEncoders для categorical features
        self._fit_encoders(creatives)

        # Подготовить данные
        X = []
        y = []

        for creative in creatives:
            try:
                features = self.prepare_features(creative)
                X.append(list(features.values()))
                y.append(creative.cvr / 10000)  # Target = actual CVR (0-1)
                self.feature_names = list(features.keys())
            except Exception as e:
                logger.warning(f"Failed to prepare features for {creative.id}: {e}")
                continue

        if len(X) < 50:
            raise ValueError(f"Only {len(X)} valid samples. Need at least 50.")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Создать LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.feature_names)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data, feature_name=self.feature_names)

        # Параметры LightGBM
        params = {
            'objective': 'regression',
            'metric': 'mae',
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }

        # Обучить модель
        self.model = lgb.train(
            params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=200,
            callbacks=[lgb.early_stopping(stopping_rounds=20)]
        )

        # Оценить качество
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        mae_train = np.mean(np.abs(np.array(y_train) - y_pred_train))
        mae_test = np.mean(np.abs(np.array(y_test) - y_pred_test))

        # Hit rate (±20%)
        hits_test = sum(
            1 for true, pred in zip(y_test, y_pred_test)
            if 0.8 * true <= pred <= 1.2 * true
        )
        hit_rate = hits_test / len(y_test)

        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importance(importance_type='gain').tolist()
        ))

        # Сохранить модель
        self._save_model()

        return {
            'model_type': 'gradient_boosting',
            'algorithm': 'lightgbm',
            'mae_train': round(float(mae_train), 4),
            'mae_test': round(float(mae_test), 4),
            'hit_rate': round(float(hit_rate), 3),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_importance': feature_importance,
            'best_iteration': self.model.best_iteration
        }

    def _fit_encoders(self, creatives: List[Creative]):
        """
        Создать LabelEncoders для categorical features.
        """

        categorical_cols = ['hook_type', 'emotion', 'pacing', 'cta_type']

        for col in categorical_cols:
            values = [getattr(c, col) or 'unknown' for c in creatives]
            unique_values = list(set(values))

            encoder = LabelEncoder()
            encoder.fit(unique_values)

            self.encoders[col] = encoder

    def predict(self, creative: Creative) -> Dict:
        """
        Предсказать CVR для креатива.

        Args:
            creative: Creative object

        Returns:
            dict: Prediction result
        """

        if not self.model:
            # Попробовать загрузить модель
            if not self._load_model():
                raise ValueError("Model not trained yet. Call train() first.")

        # Подготовить features
        features = self.prepare_features(creative)
        X = [list(features.values())]

        # Предсказать
        predicted_cvr = self.model.predict(X)[0]

        # Feature importance для этого креатива
        feature_contributions = dict(zip(
            self.feature_names,
            self.model.predict(X, pred_contrib=True)[0][:-1]  # Исключить bias
        ))

        return {
            'predicted_cvr': float(predicted_cvr),
            'predicted_cvr_percent': round(float(predicted_cvr) * 100, 2),
            'model_type': 'gradient_boosting',
            'confidence_score': 0.85,  # TODO: вычислить confidence interval
            'feature_contributions': feature_contributions,
            'top_features': sorted(
                feature_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]
        }

    def _save_model(self):
        """
        Сохранить модель в файл.
        """

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'encoders': self.encoders,
            'feature_names': self.feature_names
        }

        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {self.model_path}")

    def _load_model(self) -> bool:
        """
        Загрузить модель из файла.

        Returns:
            bool: True если загрузилась, False если нет
        """

        if not os.path.exists(self.model_path):
            return False

        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.encoders = model_data['encoders']
            self.feature_names = model_data['feature_names']

            logger.info(f"Model loaded from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


def select_best_predictor(db: Session, user_id: str, product_category: str):
    """
    Автоматически выбрать лучший предсказатель в зависимости от данных.

    Args:
        db: Database session
        user_id: User ID
        product_category: Product category

    Returns:
        str: 'markov_chain' или 'gradient_boosting'
    """

    # Посчитать креативы с данными
    n_creatives = db.query(Creative).filter(
        Creative.user_id == user_id,
        Creative.product_category == product_category,
        Creative.conversions > 0
    ).count()

    if n_creatives < 20:
        return 'baseline'  # Просто AVG CVR
    elif n_creatives < 50:
        return 'markov_chain'  # Markov Chain
    else:
        return 'gradient_boosting'  # LightGBM (если установлен)
