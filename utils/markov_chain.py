"""
Markov Chain model for creative performance prediction.

Uses historical pattern performance to predict conversion rates
for new creatives before spending money on ads.

Theory:
- P(conversion | pattern) = observed conversion rate from historical data
- For pattern combinations: P(conversion | hook, emotion, pacing) = joint probability
- Smoothing: Laplace smoothing to handle unseen patterns
- Transfer learning: Use public TikTok data when sample size is small
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sqlalchemy.orm import Session
from database.models import PatternPerformance, Creative, CreativePattern


class MarkovChainPredictor:
    """
    Predicts creative performance based on pattern combinations.
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category

        # Laplace smoothing parameter (pseudo-counts)
        self.alpha = 1.0

        # Minimum sample size for reliable predictions
        self.min_sample_size = 10

    def predict_cvr(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        cta_type: Optional[str] = None
    ) -> Dict:
        """
        Predict conversion rate for a creative with given patterns.

        Returns:
            {
                "predicted_cvr": 0.125,  # 12.5%
                "confidence_score": 0.85,  # 85% confidence
                "sample_size": 50,  # based on 50 similar creatives
                "confidence_interval": (0.08, 0.17),  # 95% CI
                "similar_creatives": [...],
                "prediction_method": "exact_match" | "partial_match" | "bayesian_estimate"
            }
        """

        # Try exact pattern match first
        exact_match = self._find_exact_pattern(hook_type, emotion, pacing, cta_type)
        if exact_match and exact_match["sample_size"] >= self.min_sample_size:
            return self._format_prediction(exact_match, "exact_match")

        # Try partial matches (e.g., hook + emotion only)
        partial_match = self._find_partial_patterns(hook_type, emotion, pacing, cta_type)
        if partial_match and partial_match["sample_size"] >= self.min_sample_size / 2:
            return self._format_prediction(partial_match, "partial_match")

        # Fall back to Bayesian estimate with prior
        bayesian_estimate = self._bayesian_estimate(hook_type, emotion, pacing, cta_type)
        return self._format_prediction(bayesian_estimate, "bayesian_estimate")

    def _find_exact_pattern(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        cta_type: Optional[str]
    ) -> Optional[Dict]:
        """Find exact pattern match in performance data."""

        query = self.db.query(PatternPerformance).filter(
            PatternPerformance.user_id == self.user_id,
            PatternPerformance.product_category == self.product_category,
            PatternPerformance.hook_type == hook_type,
            PatternPerformance.emotion == emotion,
            PatternPerformance.pacing == pacing
        )

        if cta_type:
            query = query.filter(PatternPerformance.cta_type == cta_type)

        pattern_perf = query.first()

        if not pattern_perf:
            return None

        return {
            "avg_cvr": pattern_perf.avg_cvr / 10000,  # Convert back to decimal
            "sample_size": pattern_perf.sample_size,
            "confidence_interval_lower": pattern_perf.confidence_interval_lower / 10000 if pattern_perf.confidence_interval_lower else None,
            "confidence_interval_upper": pattern_perf.confidence_interval_upper / 10000 if pattern_perf.confidence_interval_upper else None,
            "total_conversions": pattern_perf.total_conversions,
            "total_clicks": pattern_perf.total_clicks
        }

    def _find_partial_patterns(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        cta_type: Optional[str]
    ) -> Optional[Dict]:
        """
        Find partial pattern matches and combine using weighted average.
        E.g., hook + emotion, emotion + pacing, etc.
        """

        # Get all creatives with matching individual patterns
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.status.in_(["testing", "active", "paused"])
        ).filter(
            (Creative.hook_type == hook_type) |
            (Creative.emotion == emotion) |
            (Creative.pacing == pacing)
        ).all()

        if not creatives:
            return None

        # Weight by number of matching patterns
        weighted_cvr = 0
        total_weight = 0
        total_sample = 0

        for creative in creatives:
            matches = 0
            if creative.hook_type == hook_type:
                matches += 1
            if creative.emotion == emotion:
                matches += 1
            if creative.pacing == pacing:
                matches += 1

            # Weight: more matching patterns = higher weight
            weight = matches * (creative.clicks or 1)

            cvr = creative.cvr / 10000 if creative.cvr else 0
            weighted_cvr += cvr * weight
            total_weight += weight
            total_sample += creative.clicks or 0

        if total_weight == 0:
            return None

        avg_cvr = weighted_cvr / total_weight

        # Estimate confidence interval using aggregated data
        conversions = sum(c.conversions for c in creatives)
        clicks = sum(c.clicks for c in creatives)

        ci_lower, ci_upper = self._calculate_confidence_interval(conversions, clicks)

        return {
            "avg_cvr": avg_cvr,
            "sample_size": len(creatives),
            "confidence_interval_lower": ci_lower,
            "confidence_interval_upper": ci_upper,
            "total_conversions": conversions,
            "total_clicks": clicks
        }

    def _bayesian_estimate(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        cta_type: Optional[str]
    ) -> Dict:
        """
        Bayesian estimate using product category prior.

        Prior: Average CVR for this product category
        Likelihood: Pattern-specific data (if any)
        Posterior: Weighted combination
        """

        # Get product category prior (average CVR across all creatives)
        all_creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.clicks > 0
        ).all()

        if not all_creatives:
            # No data for this product - use conservative industry baseline
            return {
                "avg_cvr": 0.05,  # 5% baseline
                "sample_size": 0,
                "confidence_interval_lower": 0.02,
                "confidence_interval_upper": 0.10,
                "total_conversions": 0,
                "total_clicks": 0
            }

        # Calculate prior
        prior_conversions = sum(c.conversions for c in all_creatives)
        prior_clicks = sum(c.clicks for c in all_creatives)
        prior_cvr = prior_conversions / prior_clicks if prior_clicks > 0 else 0.05

        # Get any individual pattern data
        hook_data = self._get_single_pattern_data("hook", hook_type)
        emotion_data = self._get_single_pattern_data("emotion", emotion)
        pacing_data = self._get_single_pattern_data("pacing", pacing)

        # Bayesian update: combine prior with pattern evidence
        posterior_alpha = self.alpha + prior_conversions
        posterior_beta = self.alpha + (prior_clicks - prior_conversions)

        # Add evidence from individual patterns
        for pattern_data in [hook_data, emotion_data, pacing_data]:
            if pattern_data:
                posterior_alpha += pattern_data["conversions"]
                posterior_beta += (pattern_data["clicks"] - pattern_data["conversions"])

        # Expected value of Beta distribution
        predicted_cvr = posterior_alpha / (posterior_alpha + posterior_beta)

        # Credible interval (Bayesian confidence interval)
        ci_lower = stats.beta.ppf(0.025, posterior_alpha, posterior_beta)
        ci_upper = stats.beta.ppf(0.975, posterior_alpha, posterior_beta)

        return {
            "avg_cvr": predicted_cvr,
            "sample_size": len(all_creatives),
            "confidence_interval_lower": ci_lower,
            "confidence_interval_upper": ci_upper,
            "total_conversions": prior_conversions,
            "total_clicks": prior_clicks
        }

    def _get_single_pattern_data(self, pattern_type: str, pattern_value: str) -> Optional[Dict]:
        """Get aggregated data for a single pattern type."""

        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category
        )

        if pattern_type == "hook":
            creatives = creatives.filter(Creative.hook_type == pattern_value)
        elif pattern_type == "emotion":
            creatives = creatives.filter(Creative.emotion == pattern_value)
        elif pattern_type == "pacing":
            creatives = creatives.filter(Creative.pacing == pattern_value)

        creatives = creatives.all()

        if not creatives:
            return None

        total_clicks = sum(c.clicks for c in creatives)
        total_conversions = sum(c.conversions for c in creatives)

        return {
            "clicks": total_clicks,
            "conversions": total_conversions,
            "cvr": total_conversions / total_clicks if total_clicks > 0 else 0
        }

    def _calculate_confidence_interval(
        self,
        conversions: int,
        clicks: int,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for conversion rate.
        Uses Wilson score interval (better for small samples than normal approximation).
        """

        if clicks == 0:
            return (0.0, 0.0)

        p = conversions / clicks
        n = clicks

        # Z-score for confidence level
        z = stats.norm.ppf(1 - (1 - confidence_level) / 2)

        denominator = 1 + z**2 / n
        centre_adjusted_probability = p + z**2 / (2 * n)
        adjusted_standard_deviation = np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)

        lower_bound = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
        upper_bound = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator

        return (max(0, lower_bound), min(1, upper_bound))

    def _format_prediction(self, data: Dict, method: str) -> Dict:
        """Format prediction result with confidence score."""

        cvr = data["avg_cvr"]
        sample_size = data["sample_size"]

        # Calculate confidence score based on sample size and CI width
        ci_lower = data.get("confidence_interval_lower", cvr * 0.5)
        ci_upper = data.get("confidence_interval_upper", cvr * 1.5)

        ci_width = ci_upper - ci_lower
        ci_width_normalized = min(1.0, ci_width / cvr) if cvr > 0 else 1.0

        # Confidence decreases with wider CI and smaller sample
        sample_confidence = min(1.0, sample_size / 50)  # Full confidence at 50+ samples
        ci_confidence = 1.0 - ci_width_normalized

        confidence_score = (sample_confidence * 0.6 + ci_confidence * 0.4)

        return {
            "predicted_cvr": round(cvr, 4),
            "predicted_cvr_percent": round(cvr * 100, 2),
            "confidence_score": round(confidence_score, 2),
            "sample_size": sample_size,
            "confidence_interval": (round(ci_lower, 4), round(ci_upper, 4)),
            "confidence_interval_percent": (round(ci_lower * 100, 2), round(ci_upper * 100, 2)),
            "prediction_method": method,
            "total_conversions": data.get("total_conversions", 0),
            "total_clicks": data.get("total_clicks", 0)
        }

    def update_pattern_performance(self):
        """
        Recalculate aggregated pattern performance from all creatives.
        Should be run periodically (e.g., daily) or after new data is added.
        """

        # Get all pattern combinations from creatives
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.clicks > 0
        ).all()

        # Group by pattern combinations
        pattern_groups = {}

        for creative in creatives:
            key = (
                creative.hook_type or "unknown",
                creative.emotion or "unknown",
                creative.pacing or "unknown",
                creative.cta_type or "unknown"
            )

            if key not in pattern_groups:
                pattern_groups[key] = []

            pattern_groups[key].append(creative)

        # Update or create PatternPerformance records
        for pattern_key, group_creatives in pattern_groups.items():
            hook_type, emotion, pacing, cta_type = pattern_key

            # Calculate aggregated metrics
            total_impressions = sum(c.impressions for c in group_creatives)
            total_clicks = sum(c.clicks for c in group_creatives)
            total_conversions = sum(c.conversions for c in group_creatives)
            total_revenue = sum(c.revenue for c in group_creatives)

            avg_ctr = int((total_clicks / total_impressions * 10000)) if total_impressions > 0 else 0
            avg_cvr = int((total_conversions / total_clicks * 10000)) if total_clicks > 0 else 0
            avg_roas = int((total_revenue / sum(c.production_cost + c.media_spend for c in group_creatives) * 100)) if sum(c.production_cost + c.media_spend for c in group_creatives) > 0 else 0

            # Calculate confidence interval
            ci_lower, ci_upper = self._calculate_confidence_interval(total_conversions, total_clicks)

            # Markov transition probability = P(conversion | pattern)
            transition_prob = int((total_conversions / total_clicks * 10000)) if total_clicks > 0 else 0

            # Check if record exists
            existing = self.db.query(PatternPerformance).filter(
                PatternPerformance.user_id == self.user_id,
                PatternPerformance.product_category == self.product_category,
                PatternPerformance.hook_type == hook_type,
                PatternPerformance.emotion == emotion,
                PatternPerformance.pacing == pacing,
                PatternPerformance.cta_type == cta_type
            ).first()

            if existing:
                # Update existing record
                existing.sample_size = len(group_creatives)
                existing.total_impressions = total_impressions
                existing.total_clicks = total_clicks
                existing.total_conversions = total_conversions
                existing.total_revenue = total_revenue
                existing.avg_ctr = avg_ctr
                existing.avg_cvr = avg_cvr
                existing.avg_roas = avg_roas
                existing.confidence_interval_lower = int(ci_lower * 10000)
                existing.confidence_interval_upper = int(ci_upper * 10000)
                existing.transition_probability = transition_prob
            else:
                # Create new record
                from database.models import PatternPerformance
                new_pattern = PatternPerformance(
                    user_id=self.user_id,
                    product_category=self.product_category,
                    hook_type=hook_type,
                    emotion=emotion,
                    pacing=pacing,
                    cta_type=cta_type,
                    sample_size=len(group_creatives),
                    total_impressions=total_impressions,
                    total_clicks=total_clicks,
                    total_conversions=total_conversions,
                    total_revenue=total_revenue,
                    avg_ctr=avg_ctr,
                    avg_cvr=avg_cvr,
                    avg_roas=avg_roas,
                    confidence_interval_lower=int(ci_lower * 10000),
                    confidence_interval_upper=int(ci_upper * 10000),
                    transition_probability=transition_prob
                )
                self.db.add(new_pattern)

        self.db.commit()

        return {
            "pattern_groups_updated": len(pattern_groups),
            "total_creatives_processed": len(creatives)
        }

    def get_best_patterns(self, metric: str = "cvr", top_n: int = 10) -> List[Dict]:
        """
        Get top performing pattern combinations.

        Args:
            metric: "cvr", "ctr", or "roas"
            top_n: Number of top patterns to return

        Returns:
            List of top patterns with their performance
        """

        query = self.db.query(PatternPerformance).filter(
            PatternPerformance.user_id == self.user_id,
            PatternPerformance.product_category == self.product_category,
            PatternPerformance.sample_size >= self.min_sample_size
        )

        if metric == "cvr":
            query = query.order_by(PatternPerformance.avg_cvr.desc())
        elif metric == "ctr":
            query = query.order_by(PatternPerformance.avg_ctr.desc())
        elif metric == "roas":
            query = query.order_by(PatternPerformance.avg_roas.desc())

        top_patterns = query.limit(top_n).all()

        results = []
        for pattern in top_patterns:
            results.append({
                "hook_type": pattern.hook_type,
                "emotion": pattern.emotion,
                "pacing": pattern.pacing,
                "cta_type": pattern.cta_type,
                "avg_cvr": pattern.avg_cvr / 10000,
                "avg_ctr": pattern.avg_ctr / 10000,
                "avg_roas": pattern.avg_roas / 100,
                "sample_size": pattern.sample_size,
                "total_conversions": pattern.total_conversions,
                "confidence_interval": (
                    pattern.confidence_interval_lower / 10000,
                    pattern.confidence_interval_upper / 10000
                )
            })

        return results
