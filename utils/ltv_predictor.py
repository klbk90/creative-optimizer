"""
LTV Predictor - Predict lifetime value from early signals.

For subscription apps, LTV is more important than CVR.

Predict 180-day LTV from first 7 days of user behavior.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.models import Creative
import statistics


class LTVPredictor:
    """Predict user lifetime value."""

    def __init__(self, db: Session):
        self.db = db

    def predict_ltv(
        self,
        day_7_sessions: int,
        day_7_time_in_app: float,  # minutes
        features_used: int,
        category: str = "language_learning"
    ) -> Dict:
        """
        Predict 180-day LTV from first 7 days.

        Simple heuristic model (can be replaced with ML later).
        """

        # Category-specific coefficients
        COEFFICIENTS = {
            "language_learning": {
                "session_weight": 5.0,
                "time_weight": 0.8,
                "feature_weight": 3.0,
                "base_ltv": 20.0
            },
            "coding": {
                "session_weight": 8.0,
                "time_weight": 1.2,
                "feature_weight": 5.0,
                "base_ltv": 40.0
            },
            "fitness": {
                "session_weight": 4.0,
                "time_weight": 0.6,
                "feature_weight": 2.5,
                "base_ltv": 15.0
            }
        }

        coef = COEFFICIENTS.get(category, COEFFICIENTS["language_learning"])

        # Calculate LTV
        predicted_ltv = (
            coef["base_ltv"] +
            (day_7_sessions * coef["session_weight"]) +
            (day_7_time_in_app * coef["time_weight"]) +
            (features_used * coef["feature_weight"])
        )

        # Retention estimates
        retention_d30 = self._estimate_retention(day_7_sessions, 30)
        retention_d90 = self._estimate_retention(day_7_sessions, 90)
        retention_d180 = self._estimate_retention(day_7_sessions, 180)

        return {
            "predicted_ltv_d30": round(predicted_ltv * 0.3, 2),
            "predicted_ltv_d90": round(predicted_ltv * 0.7, 2),
            "predicted_ltv_d180": round(predicted_ltv, 2),
            "estimated_retention": {
                "day_30": round(retention_d30, 2),
                "day_90": round(retention_d90, 2),
                "day_180": round(retention_d180, 2)
            },
            "confidence": self._calculate_confidence(
                day_7_sessions,
                day_7_time_in_app,
                features_used
            ),
            "user_segment": self._classify_user_segment(
                day_7_sessions,
                day_7_time_in_app
            )
        }

    def predict_creative_ltv(
        self,
        creative_id: str,
        user_behavior_cohort: Dict
    ) -> Dict:
        """
        Predict LTV for creative based on user cohort behavior.

        Args:
            creative_id: Creative UUID
            user_behavior_cohort: Avg behavior of users from this creative
        """

        creative = self.db.query(Creative).filter(
            Creative.id == creative_id
        ).first()

        if not creative:
            return {}

        # Extract cohort behavior
        avg_sessions = user_behavior_cohort.get("avg_sessions_d7", 5)
        avg_time = user_behavior_cohort.get("avg_time_in_app_d7", 45)
        avg_features = user_behavior_cohort.get("avg_features_used_d7", 8)

        # Predict LTV
        category = creative.product_category or "language_learning"
        ltv = self.predict_ltv(avg_sessions, avg_time, avg_features, category)

        return {
            "creative_id": str(creative.id),
            "creative_name": creative.name,
            "user_cohort": user_behavior_cohort,
            "ltv_prediction": ltv,
            "roas_projection": self._calculate_roas(
                creative.media_spend or 0,
                creative.paid_conversions or 1,
                ltv["predicted_ltv_d180"]
            )
        }

    def _estimate_retention(self, day_7_sessions: int, target_day: int) -> float:
        """Estimate retention at target_day based on day 7 sessions."""

        # Power law decay
        # High day-7 engagement → higher retention
        if day_7_sessions >= 10:
            base_retention = 0.4  # 40%
        elif day_7_sessions >= 5:
            base_retention = 0.25  # 25%
        else:
            base_retention = 0.15  # 15%

        # Decay over time
        decay_factor = (7 / target_day) ** 0.5
        retention = base_retention * decay_factor

        return max(0.05, min(0.6, retention))  # Clamp 5-60%

    def _calculate_confidence(
        self,
        sessions: int,
        time: float,
        features: int
    ) -> float:
        """Calculate prediction confidence."""

        # More data = higher confidence
        confidence = 0.5  # Base

        if sessions >= 7:
            confidence += 0.2
        if time >= 60:  # 60+ minutes
            confidence += 0.2
        if features >= 5:
            confidence += 0.1

        return round(min(1.0, confidence), 2)

    def _classify_user_segment(
        self,
        sessions: int,
        time: float
    ) -> str:
        """Classify user into segment."""

        if sessions >= 10 and time >= 90:
            return "power_user"  # High LTV
        elif sessions >= 5 and time >= 45:
            return "active_user"  # Medium LTV
        else:
            return "casual_user"  # Low LTV

    def _calculate_roas(
        self,
        media_spend: int,
        conversions: int,
        ltv: float
    ) -> Dict:
        """Calculate projected ROAS."""

        if conversions == 0:
            return {"roas": 0, "status": "no_conversions"}

        total_ltv = ltv * conversions
        media_spend_dollars = media_spend / 100

        roas = total_ltv / media_spend_dollars if media_spend_dollars > 0 else 0

        return {
            "roas": round(roas, 2),
            "total_ltv": round(total_ltv, 2),
            "media_spend": media_spend_dollars,
            "status": "profitable" if roas > 1.5 else ("break_even" if roas > 0.8 else "losing")
        }


# Industry benchmarks for validation
LTV_BENCHMARKS = {
    "language_learning": {
        "avg_ltv_d180": 120.0,
        "top_10_percent": 250.0,
        "power_user_ltv": 400.0
    },
    "coding": {
        "avg_ltv_d180": 180.0,
        "top_10_percent": 350.0,
        "power_user_ltv": 600.0
    },
    "fitness": {
        "avg_ltv_d180": 90.0,
        "top_10_percent": 180.0,
        "power_user_ltv": 300.0
    }
}
