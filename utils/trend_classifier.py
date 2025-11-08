"""
Trend vs Stable Classifier - Filter temporary trends from stable patterns.

Key concept:
- STABLE pattern: Works consistently over time (e.g., "before_after" hook)
- TREND: Works for 1-2 weeks then dies (e.g., viral dance challenge)

WHY THIS MATTERS:
- Copying a stable pattern → Good investment
- Copying a dead trend → Waste of money

This classifier analyzes:
1. Lifespan: How long creatives with this pattern live
2. Performance consistency: Does CVR stay stable or drop?
3. Seasonality: Does it spike then crash?
4. Public data aging: How old are top performers?
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database.models import Creative
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class TrendClassifier:
    """
    Classify patterns as STABLE or TREND.
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category

    def classify_pattern(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        public_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Classify pattern as STABLE or TREND.

        Args:
            hook_type: Hook type
            emotion: Emotion
            pacing: Pacing
            public_data: Optional public data with timestamps

        Returns:
            Classification with confidence and reasoning
        """

        # Analyze your historical data
        your_analysis = self._analyze_your_history(hook_type, emotion, pacing)

        # Analyze public data if available
        public_analysis = self._analyze_public_data(
            hook_type,
            emotion,
            pacing,
            public_data
        ) if public_data else None

        # Combine analyses
        classification = self._determine_classification(
            your_analysis,
            public_analysis
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(classification)

        return {
            "pattern": f"{hook_type} + {emotion} + {pacing}",
            "classification": classification["type"],  # "stable" or "trend"
            "confidence": classification["confidence"],
            "stability_score": classification["stability_score"],  # 0-100
            "verdict": classification["verdict"],
            "reasoning": classification["reasoning"],
            "recommendations": recommendations,
            "details": {
                "your_data": your_analysis,
                "public_data": public_analysis
            }
        }

    def classify_all_patterns(
        self,
        min_sample_size: int = 3
    ) -> List[Dict]:
        """
        Classify all patterns you've tested.

        Returns list sorted by stability (most stable first).
        """

        # Get all unique patterns
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category
        ).all()

        patterns = {}
        for creative in creatives:
            key = (creative.hook_type, creative.emotion, creative.pacing)
            if key not in patterns:
                patterns[key] = []
            patterns[key].append(creative)

        # Classify each pattern
        results = []

        for (hook, emotion, pacing), creatives_list in patterns.items():
            if len(creatives_list) < min_sample_size:
                continue  # Skip patterns with low sample size

            classification = self.classify_pattern(hook, emotion, pacing)
            classification["sample_size"] = len(creatives_list)

            results.append(classification)

        # Sort by stability score (descending)
        results.sort(key=lambda x: x["stability_score"], reverse=True)

        return results

    def detect_dying_trend(
        self,
        hook_type: str,
        emotion: str,
        public_data: List[Dict]
    ) -> Dict:
        """
        Detect if a currently popular pattern is dying.

        WARNING: High engagement today ≠ good performance tomorrow!
        """

        if not public_data:
            return {"is_dying": False, "confidence": 0.0}

        # Analyze temporal pattern
        temporal = self._analyze_temporal_pattern(
            hook_type,
            emotion,
            public_data
        )

        # Check for warning signs
        warning_signs = []

        # Sign 1: Peak was 2+ weeks ago
        if temporal["days_since_peak"] > 14:
            warning_signs.append(
                f"Peak was {temporal['days_since_peak']} days ago - trend is aging"
            )

        # Sign 2: Declining engagement
        if temporal["engagement_trend"] == "declining":
            warning_signs.append(
                "Engagement is declining - audience fatigue"
            )

        # Sign 3: Short average lifespan
        if temporal["avg_lifespan"] < 7:
            warning_signs.append(
                f"Creatives die quickly (avg {temporal['avg_lifespan']} days) - viral trend"
            )

        # Determine if dying
        is_dying = len(warning_signs) >= 2

        return {
            "is_dying": is_dying,
            "confidence": min(1.0, len(warning_signs) / 3),
            "warning_signs": warning_signs,
            "recommendation": (
                "⚠️  AVOID - Trend is dying, high risk of poor performance"
                if is_dying
                else "✅ Safe to test"
            ),
            "temporal_analysis": temporal
        }

    # ==================== PRIVATE METHODS ====================

    def _analyze_your_history(
        self,
        hook_type: str,
        emotion: str,
        pacing: str
    ) -> Dict:
        """Analyze this pattern in your historical data."""

        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.hook_type == hook_type,
            Creative.emotion == emotion,
            Creative.pacing == pacing
        ).order_by(Creative.created_at).all()

        if not creatives:
            return {
                "sample_size": 0,
                "has_data": False
            }

        # Calculate metrics
        cvrs = [c.cvr / 10000 for c in creatives if c.cvr]
        dates = [c.created_at for c in creatives]

        # Lifespan (days between first and last test)
        if len(dates) > 1:
            lifespan = (dates[-1] - dates[0]).days
        else:
            lifespan = 0

        # CVR consistency (low variance = stable)
        cvr_variance = statistics.variance(cvrs) if len(cvrs) > 1 else 0

        # Performance trend (improving/stable/declining)
        if len(cvrs) >= 3:
            early_cvr = statistics.mean(cvrs[:len(cvrs)//2])
            late_cvr = statistics.mean(cvrs[len(cvrs)//2:])
            trend = "improving" if late_cvr > early_cvr * 1.1 else ("declining" if late_cvr < early_cvr * 0.9 else "stable")
        else:
            trend = "unknown"

        return {
            "sample_size": len(creatives),
            "has_data": True,
            "lifespan_days": lifespan,
            "avg_cvr": statistics.mean(cvrs) if cvrs else 0,
            "cvr_variance": cvr_variance,
            "performance_trend": trend,
            "first_test": dates[0],
            "last_test": dates[-1]
        }

    def _analyze_public_data(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        public_data: List[Dict]
    ) -> Dict:
        """Analyze pattern in public data."""

        # Filter creatives matching this pattern
        matching = [
            p for p in public_data
            if (p.get("hook_type") == hook_type and
                p.get("emotion") == emotion and
                p.get("pacing") == pacing)
        ]

        if not matching:
            return {
                "sample_size": 0,
                "has_data": False
            }

        # Analyze temporal distribution
        if all("created_at" in p for p in matching):
            dates = [
                datetime.fromisoformat(p["created_at"])
                if isinstance(p["created_at"], str)
                else p["created_at"]
                for p in matching
            ]

            # Spread (days between oldest and newest)
            spread = (max(dates) - min(dates)).days if len(dates) > 1 else 0

            # Recency (days since newest)
            recency = (datetime.now() - max(dates)).days

        else:
            spread = 0
            recency = 0

        # Engagement analysis
        if all("engagement_rate" in p for p in matching):
            engagements = [p["engagement_rate"] for p in matching]
            avg_engagement = statistics.mean(engagements)
        else:
            avg_engagement = 0

        return {
            "sample_size": len(matching),
            "has_data": True,
            "temporal_spread_days": spread,
            "days_since_newest": recency,
            "avg_engagement": avg_engagement,
            "popularity": len(matching) / len(public_data) if public_data else 0
        }

    def _determine_classification(
        self,
        your_analysis: Dict,
        public_analysis: Optional[Dict]
    ) -> Dict:
        """Determine if pattern is STABLE or TREND."""

        # Start with neutral score
        stability_score = 50

        reasoning_parts = []

        # Factor 1: Your data performance trend
        if your_analysis.get("has_data"):
            trend = your_analysis["performance_trend"]
            if trend == "stable":
                stability_score += 15
                reasoning_parts.append("Performance stable over time in your tests")
            elif trend == "declining":
                stability_score -= 20
                reasoning_parts.append("Performance declining in your tests (warning)")
            elif trend == "improving":
                stability_score += 10
                reasoning_parts.append("Performance improving in your tests")

            # Low variance = stable
            variance = your_analysis.get("cvr_variance", 0)
            if variance < 0.01:  # Low variance
                stability_score += 10
                reasoning_parts.append("Low variance (consistent results)")
            elif variance > 0.05:  # High variance
                stability_score -= 15
                reasoning_parts.append("High variance (inconsistent results)")

        # Factor 2: Public data analysis
        if public_analysis and public_analysis.get("has_data"):
            # Long temporal spread = stable
            spread = public_analysis.get("temporal_spread_days", 0)
            if spread > 90:  # 3+ months
                stability_score += 20
                reasoning_parts.append(f"Pattern active for {spread} days (stable)")
            elif spread < 21:  # < 3 weeks
                stability_score -= 20
                reasoning_parts.append(f"Pattern only {spread} days old (likely trend)")

            # Old but still popular = stable
            recency = public_analysis.get("days_since_newest", 0)
            if recency > 30 and public_analysis.get("popularity", 0) > 0.1:
                stability_score += 15
                reasoning_parts.append("Old but still popular (proven stable)")
            elif recency < 7:
                stability_score -= 10
                reasoning_parts.append("Very recent pattern (may be temporary trend)")

        # Clamp to 0-100
        stability_score = max(0, min(100, stability_score))

        # Determine type
        if stability_score >= 65:
            classification_type = "stable"
            verdict = "✅ STABLE - Safe to invest"
        elif stability_score >= 40:
            classification_type = "uncertain"
            verdict = "⚠️  UNCERTAIN - Moderate risk"
        else:
            classification_type = "trend"
            verdict = "❌ TREND - High risk, likely temporary"

        # Confidence (based on data availability)
        confidence = 0.5  # Base confidence
        if your_analysis.get("has_data") and your_analysis.get("sample_size", 0) >= 5:
            confidence += 0.2
        if public_analysis and public_analysis.get("has_data") and public_analysis.get("sample_size", 0) >= 10:
            confidence += 0.3

        return {
            "type": classification_type,
            "stability_score": int(stability_score),
            "confidence": round(confidence, 2),
            "verdict": verdict,
            "reasoning": " | ".join(reasoning_parts) if reasoning_parts else "Insufficient data for classification"
        }

    def _analyze_temporal_pattern(
        self,
        hook_type: str,
        emotion: str,
        public_data: List[Dict]
    ) -> Dict:
        """Analyze temporal pattern for dying trend detection."""

        # Filter matching patterns
        matching = [
            p for p in public_data
            if (p.get("hook_type") == hook_type and
                p.get("emotion") == emotion)
        ]

        if not matching or not all("created_at" in p for p in matching):
            return {
                "days_since_peak": 0,
                "engagement_trend": "unknown",
                "avg_lifespan": 0
            }

        # Parse dates
        dated_creatives = []
        for p in matching:
            created_at = p["created_at"]
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            engagement = p.get("engagement_rate", 0)

            dated_creatives.append({
                "date": created_at,
                "engagement": engagement
            })

        # Sort by date
        dated_creatives.sort(key=lambda x: x["date"])

        # Find peak
        peak_idx = max(range(len(dated_creatives)), key=lambda i: dated_creatives[i]["engagement"])
        peak_date = dated_creatives[peak_idx]["date"]

        days_since_peak = (datetime.now() - peak_date).days

        # Engagement trend (last 7 days vs prev 7 days)
        now = datetime.now()
        recent = [c for c in dated_creatives if (now - c["date"]).days <= 7]
        prev = [c for c in dated_creatives if 7 < (now - c["date"]).days <= 14]

        if recent and prev:
            recent_avg = statistics.mean([c["engagement"] for c in recent])
            prev_avg = statistics.mean([c["engagement"] for c in prev])

            if recent_avg < prev_avg * 0.8:
                trend = "declining"
            elif recent_avg > prev_avg * 1.2:
                trend = "growing"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        # Average lifespan (how long creatives live before dying)
        if all("lifespan_days" in p for p in matching):
            lifespans = [p["lifespan_days"] for p in matching if p["lifespan_days"] > 0]
            avg_lifespan = statistics.mean(lifespans) if lifespans else 0
        else:
            avg_lifespan = 0

        return {
            "days_since_peak": days_since_peak,
            "engagement_trend": trend,
            "avg_lifespan": int(avg_lifespan),
            "peak_date": peak_date.isoformat()
        }

    def _generate_recommendations(self, classification: Dict) -> List[str]:
        """Generate actionable recommendations."""

        recommendations = []

        if classification["type"] == "stable":
            recommendations.append(
                "✅ Safe to invest - Pattern has proven longevity"
            )
            recommendations.append(
                "Create your unique version (don't copy exactly)"
            )
        elif classification["type"] == "uncertain":
            recommendations.append(
                "⚠️  Test cautiously - Start with small budget ($10-20)"
            )
            recommendations.append(
                "Monitor performance closely in first 48h"
            )
        else:  # trend
            recommendations.append(
                "❌ High risk - Pattern likely temporary"
            )
            recommendations.append(
                "Consider waiting for stable patterns instead"
            )

        return recommendations


def quick_trend_check(
    db: Session,
    user_id: str,
    product_category: str,
    hook_type: str,
    emotion: str,
    pacing: str
) -> bool:
    """
    Quick check: Is this a stable pattern?

    Returns True if stable, False if trend/uncertain.
    """

    classifier = TrendClassifier(db, user_id, product_category)
    result = classifier.classify_pattern(hook_type, emotion, pacing)

    return result["classification"] == "stable"
