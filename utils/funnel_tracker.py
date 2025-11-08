"""
Funnel Tracking - Track complete user journey for apps.

For white themes (edtech/fitness/finance), track:
Ad → Click → Install → Trial → Paid → Retention

This provides much richer data than simple CVR tracking.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.models import Creative
from datetime import datetime, timedelta
import statistics


class FunnelTracker:
    """Track app install funnel."""

    def __init__(self, db: Session):
        self.db = db

    def track_install(
        self,
        creative_id: str,
        device_id: str,
        platform: str  # "ios" or "android"
    ) -> Dict:
        """Track app install event."""

        # Update creative with install
        creative = self.db.query(Creative).filter(
            Creative.id == creative_id
        ).first()

        if creative:
            creative.installs = (creative.installs or 0) + 1
            self.db.commit()

        return {
            "event": "install",
            "creative_id": creative_id,
            "device_id": device_id,
            "platform": platform,
            "timestamp": datetime.utcnow()
        }

    def track_trial_start(
        self,
        creative_id: str,
        device_id: str
    ) -> Dict:
        """Track trial activation."""

        creative = self.db.query(Creative).filter(
            Creative.id == creative_id
        ).first()

        if creative:
            creative.trial_starts = (creative.trial_starts or 0) + 1
            self.db.commit()

        return {
            "event": "trial_start",
            "creative_id": creative_id,
            "device_id": device_id
        }

    def track_paid_conversion(
        self,
        creative_id: str,
        device_id: str,
        amount: int  # cents
    ) -> Dict:
        """Track paid conversion."""

        creative = self.db.query(Creative).filter(
            Creative.id == creative_id
        ).first()

        if creative:
            creative.paid_conversions = (creative.paid_conversions or 0) + 1
            creative.revenue = (creative.revenue or 0) + amount
            self.db.commit()

        return {
            "event": "paid_conversion",
            "creative_id": creative_id,
            "amount": amount
        }

    def get_funnel_metrics(self, creative_id: str) -> Dict:
        """Get complete funnel metrics for creative."""

        creative = self.db.query(Creative).filter(
            Creative.id == creative_id
        ).first()

        if not creative:
            return {}

        # Calculate rates
        clicks = creative.clicks or 0
        installs = getattr(creative, 'installs', 0) or 0
        trial_starts = getattr(creative, 'trial_starts', 0) or 0
        paid_conversions = getattr(creative, 'paid_conversions', 0) or 0

        install_rate = (installs / clicks * 100) if clicks > 0 else 0
        trial_rate = (trial_starts / installs * 100) if installs > 0 else 0
        conversion_rate = (paid_conversions / trial_starts * 100) if trial_starts > 0 else 0

        return {
            "creative_id": str(creative.id),
            "creative_name": creative.name,
            "funnel": {
                "clicks": clicks,
                "installs": installs,
                "trial_starts": trial_starts,
                "paid_conversions": paid_conversions
            },
            "rates": {
                "install_rate": round(install_rate, 2),
                "trial_activation_rate": round(trial_rate, 2),
                "trial_to_paid_rate": round(conversion_rate, 2)
            },
            "revenue": (creative.revenue or 0) / 100,  # dollars
            "cpa": (creative.media_spend or 0) / paid_conversions if paid_conversions > 0 else 0
        }


def calculate_funnel_health(
    install_rate: float,
    trial_rate: float,
    conversion_rate: float,
    category: str = "language_learning"
) -> Dict:
    """
    Calculate funnel health vs benchmarks.

    Benchmarks by category (industry averages).
    """

    BENCHMARKS = {
        "language_learning": {
            "install_rate": 25.0,  # 25%
            "trial_rate": 40.0,
            "conversion_rate": 15.0
        },
        "coding": {
            "install_rate": 28.0,
            "trial_rate": 42.0,
            "conversion_rate": 18.0
        },
        "fitness": {
            "install_rate": 22.0,
            "trial_rate": 35.0,
            "conversion_rate": 12.0
        }
    }

    benchmark = BENCHMARKS.get(category, BENCHMARKS["language_learning"])

    health = {
        "install_rate": {
            "actual": install_rate,
            "benchmark": benchmark["install_rate"],
            "status": "good" if install_rate >= benchmark["install_rate"] else "poor"
        },
        "trial_rate": {
            "actual": trial_rate,
            "benchmark": benchmark["trial_rate"],
            "status": "good" if trial_rate >= benchmark["trial_rate"] else "poor"
        },
        "conversion_rate": {
            "actual": conversion_rate,
            "benchmark": benchmark["conversion_rate"],
            "status": "good" if conversion_rate >= benchmark["conversion_rate"] else "poor"
        }
    }

    # Overall health
    good_stages = sum(1 for stage in health.values() if stage["status"] == "good")
    overall = "excellent" if good_stages == 3 else ("good" if good_stages == 2 else "needs_improvement")

    return {
        "overall_health": overall,
        "stages": health,
        "recommendation": _get_funnel_recommendation(health)
    }


def _get_funnel_recommendation(health: Dict) -> str:
    """Get recommendation based on funnel health."""

    weak_stages = [stage for stage, data in health.items() if data["status"] == "poor"]

    if not weak_stages:
        return "✅ All funnel stages performing well!"

    recommendations = {
        "install_rate": "Improve ad creative or targeting - low install rate",
        "trial_rate": "Improve onboarding flow - users install but don't activate",
        "conversion_rate": "Improve trial experience - users try but don't convert"
    }

    return "Fix: " + ", ".join([recommendations[stage] for stage in weak_stages])
