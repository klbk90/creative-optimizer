"""
Pattern Gap Finder - Find untested pattern combinations.

This module identifies "gaps" - pattern combinations that should work
but haven't been tested yet. These gaps represent competitive advantages.

Key concept:
- Public data shows: hook="before_after" is popular
- Your data shows: tested with emotion="achievement" (saturated)
- GAP: hook="before_after" + emotion="curiosity" (untested!)
  → This is GOLD - proven hook + fresh angle
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from database.models import Creative, PatternPerformance
from collections import defaultdict
import itertools


class PatternGapFinder:
    """
    Find untested pattern combinations that represent opportunities.
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category

    def find_gaps(
        self,
        min_gap_score: float = 0.7,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Find pattern gaps - untested combinations with high potential.

        Args:
            min_gap_score: Minimum gap score (0-1)
            top_n: Return top N gaps

        Returns:
            List of gaps with scores and reasoning
        """

        # Get all tested patterns
        tested_patterns = self._get_tested_patterns()

        # Get successful patterns (CVR > median)
        successful_patterns = self._get_successful_patterns()

        # Generate all possible combinations
        possible_combinations = self._generate_combinations()

        # Find gaps
        gaps = []

        for combo in possible_combinations:
            # Skip if already tested
            if self._is_tested(combo, tested_patterns):
                continue

            # Calculate gap score
            gap_score = self._calculate_gap_score(
                combo,
                successful_patterns,
                tested_patterns
            )

            if gap_score >= min_gap_score:
                gaps.append({
                    "pattern": combo,
                    "hook_type": combo[0],
                    "emotion": combo[1],
                    "pacing": combo[2],
                    "cta_type": combo[3] if len(combo) > 3 else None,
                    "gap_score": gap_score,
                    "expected_performance": self._estimate_performance(
                        combo,
                        successful_patterns
                    ),
                    "reasoning": self._generate_reasoning(
                        combo,
                        successful_patterns
                    ),
                    "competitive_advantage": "high" if gap_score > 0.85 else "medium"
                })

        # Sort by gap score
        gaps.sort(key=lambda x: x["gap_score"], reverse=True)

        return gaps[:top_n]

    def find_competitor_gaps(
        self,
        public_patterns: List[Dict],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Find patterns popular with competitors but not tested by you.

        Args:
            public_patterns: Patterns from public data (TikTok Creative Center)
            top_n: Return top N gaps

        Returns:
            List of competitor gaps
        """

        # Get your tested patterns
        your_patterns = self._get_tested_patterns()

        # Find popular patterns you haven't tested
        gaps = []

        for public_pattern in public_patterns:
            pattern_tuple = (
                public_pattern["hook_type"],
                public_pattern["emotion"],
                public_pattern["pacing"],
                public_pattern.get("cta_type", "none")
            )

            # Skip if you already tested
            if self._is_tested(pattern_tuple, your_patterns):
                continue

            # High popularity but untested by you = gap
            popularity = public_pattern.get("frequency", 0)

            if popularity > 0.15:  # Popular (>15% of creatives use it)
                gaps.append({
                    "pattern": pattern_tuple,
                    "hook_type": pattern_tuple[0],
                    "emotion": pattern_tuple[1],
                    "pacing": pattern_tuple[2],
                    "cta_type": pattern_tuple[3],
                    "popularity": popularity,
                    "avg_engagement": public_pattern.get("avg_engagement", 0),
                    "gap_type": "competitor_popular",
                    "reasoning": f"Popular with competitors ({popularity*100:.1f}% use it) but untested by you",
                    "priority": popularity  # Higher popularity = higher priority
                })

        # Sort by priority
        gaps.sort(key=lambda x: x["priority"], reverse=True)

        return gaps[:top_n]

    def find_combination_gaps(
        self,
        proven_dimensions: List[str] = ["hook_type", "emotion"]
    ) -> List[Dict]:
        """
        Find untested combinations of proven individual dimensions.

        Example:
        - hook="before_after" works (proven)
        - emotion="curiosity" works (proven)
        - BUT: hook="before_after" + emotion="curiosity" untested (GAP!)

        Args:
            proven_dimensions: Which dimensions to combine

        Returns:
            List of combination gaps
        """

        # Get proven values for each dimension
        proven_values = {}

        for dimension in proven_dimensions:
            proven_values[dimension] = self._get_proven_dimension_values(dimension)

        # Generate all combinations of proven values
        if "hook_type" in proven_values and "emotion" in proven_values:
            hooks = proven_values["hook_type"]
            emotions = proven_values["emotion"]

            gaps = []

            for hook in hooks:
                for emotion in emotions:
                    # Check if this specific combination was tested
                    combo = self._find_combo_performance(hook["value"], emotion["value"])

                    if combo is None:  # Not tested = GAP
                        # Estimate performance from individual dimensions
                        estimated_cvr = (hook["avg_cvr"] + emotion["avg_cvr"]) / 2

                        gaps.append({
                            "hook_type": hook["value"],
                            "emotion": emotion["value"],
                            "hook_avg_cvr": hook["avg_cvr"],
                            "emotion_avg_cvr": emotion["avg_cvr"],
                            "estimated_cvr": estimated_cvr,
                            "gap_type": "untested_combination",
                            "reasoning": (
                                f"Both dimensions work individually: "
                                f"hook={hook['value']} (CVR {hook['avg_cvr']*100:.1f}%), "
                                f"emotion={emotion['value']} (CVR {emotion['avg_cvr']*100:.1f}%), "
                                f"but combination untested → potential {estimated_cvr*100:.1f}% CVR"
                            ),
                            "priority": estimated_cvr
                        })

            # Sort by estimated performance
            gaps.sort(key=lambda x: x["priority"], reverse=True)

            return gaps

        return []

    # ==================== PRIVATE METHODS ====================

    def _get_tested_patterns(self) -> set:
        """Get all pattern combinations you've tested."""

        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.status.in_(["testing", "active", "paused"])
        ).all()

        tested = set()

        for creative in creatives:
            pattern = (
                creative.hook_type or "unknown",
                creative.emotion or "unknown",
                creative.pacing or "unknown",
                creative.cta_type or "none"
            )
            tested.add(pattern)

        return tested

    def _get_successful_patterns(self) -> Dict:
        """Get patterns that performed well."""

        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.cvr > 0
        ).all()

        if not creatives:
            return {}

        # Calculate median CVR
        cvrs = [c.cvr for c in creatives if c.cvr]
        median_cvr = sorted(cvrs)[len(cvrs) // 2] if cvrs else 0

        # Group by dimensions
        successful = {
            "hooks": defaultdict(list),
            "emotions": defaultdict(list),
            "pacing": defaultdict(list),
            "cta": defaultdict(list)
        }

        for creative in creatives:
            if creative.cvr >= median_cvr:  # Above median = successful
                successful["hooks"][creative.hook_type].append(creative.cvr)
                successful["emotions"][creative.emotion].append(creative.cvr)
                successful["pacing"][creative.pacing].append(creative.cvr)
                successful["cta"][creative.cta_type or "none"].append(creative.cvr)

        # Calculate averages
        result = {}
        for dimension, values in successful.items():
            result[dimension] = {
                k: sum(v) / len(v) for k, v in values.items()
            }

        return result

    def _generate_combinations(self) -> List[Tuple]:
        """Generate all possible pattern combinations."""

        # Known pattern values (could be loaded from config)
        PATTERNS = {
            "hooks": ["before_after", "wait", "pain_point", "social_proof", "objection_handling", "authority", "time_efficiency"],
            "emotions": ["achievement", "excitement", "curiosity", "hope", "fomo", "fun", "motivation"],
            "pacing": ["fast", "medium", "slow"],
            "cta": ["urgency", "free_trial", "no_commitment", "instant_access", "none"]
        }

        # Generate all combinations
        combinations = list(itertools.product(
            PATTERNS["hooks"],
            PATTERNS["emotions"],
            PATTERNS["pacing"],
            PATTERNS["cta"]
        ))

        return combinations

    def _is_tested(self, combo: Tuple, tested_patterns: set) -> bool:
        """Check if combination was tested."""
        return combo in tested_patterns

    def _calculate_gap_score(
        self,
        combo: Tuple,
        successful_patterns: Dict,
        tested_patterns: set
    ) -> float:
        """
        Calculate gap score (0-1).

        High score = high potential, low competition
        """

        hook, emotion, pacing, cta = combo

        # Score based on individual dimension success
        hook_score = successful_patterns.get("hooks", {}).get(hook, 0) / 10000 if successful_patterns.get("hooks") else 0.5
        emotion_score = successful_patterns.get("emotions", {}).get(emotion, 0) / 10000 if successful_patterns.get("emotions") else 0.5
        pacing_score = successful_patterns.get("pacing", {}).get(pacing, 0) / 10000 if successful_patterns.get("pacing") else 0.5

        # Average score
        base_score = (hook_score + emotion_score + pacing_score) / 3

        # Boost if dimensions are proven individually
        boost = 0
        if hook in successful_patterns.get("hooks", {}):
            boost += 0.1
        if emotion in successful_patterns.get("emotions", {}):
            boost += 0.1

        # Penalty if too many similar patterns tested
        similar_tested = sum(
            1 for p in tested_patterns
            if (p[0] == hook or p[1] == emotion)
        )
        penalty = min(0.2, similar_tested * 0.02)

        final_score = min(1.0, base_score + boost - penalty)

        return final_score

    def _estimate_performance(
        self,
        combo: Tuple,
        successful_patterns: Dict
    ) -> str:
        """Estimate performance level."""

        hook, emotion, pacing, cta = combo

        # Check if dimensions are proven
        proven_count = 0
        if hook in successful_patterns.get("hooks", {}):
            proven_count += 1
        if emotion in successful_patterns.get("emotions", {}):
            proven_count += 1
        if pacing in successful_patterns.get("pacing", {}):
            proven_count += 1

        if proven_count >= 2:
            return "high"
        elif proven_count == 1:
            return "medium"
        else:
            return "experimental"

    def _generate_reasoning(
        self,
        combo: Tuple,
        successful_patterns: Dict
    ) -> str:
        """Generate human-readable reasoning."""

        hook, emotion, pacing, cta = combo

        reasons = []

        if hook in successful_patterns.get("hooks", {}):
            reasons.append(f"Proven hook ({hook})")
        if emotion in successful_patterns.get("emotions", {}):
            reasons.append(f"Proven emotion ({emotion})")
        if pacing in successful_patterns.get("pacing", {}):
            reasons.append(f"Proven pacing ({pacing})")

        if reasons:
            return " + ".join(reasons) + " → Fresh combination, untested angle"
        else:
            return "Experimental combination - high risk, high reward"

    def _get_proven_dimension_values(self, dimension: str) -> List[Dict]:
        """Get proven values for a dimension (e.g., hooks that work)."""

        column_map = {
            "hook_type": Creative.hook_type,
            "emotion": Creative.emotion,
            "pacing": Creative.pacing,
            "cta_type": Creative.cta_type
        }

        if dimension not in column_map:
            return []

        column = column_map[dimension]

        # Get creatives with good CVR
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.cvr > 500,  # > 5% CVR
            column is not None
        ).all()

        # Group by dimension value
        values = defaultdict(list)
        for creative in creatives:
            value = getattr(creative, dimension)
            if value:
                values[value].append(creative.cvr / 10000)

        # Calculate averages
        result = []
        for value, cvrs in values.items():
            if len(cvrs) >= 2:  # At least 2 tests
                result.append({
                    "value": value,
                    "avg_cvr": sum(cvrs) / len(cvrs),
                    "sample_size": len(cvrs)
                })

        # Sort by CVR
        result.sort(key=lambda x: x["avg_cvr"], reverse=True)

        return result

    def _find_combo_performance(self, hook: str, emotion: str) -> Optional[float]:
        """Find if specific hook+emotion combo was tested."""

        creative = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.hook_type == hook,
            Creative.emotion == emotion,
            Creative.cvr > 0
        ).first()

        return creative.cvr / 10000 if creative else None


def find_all_gaps(
    db: Session,
    user_id: str,
    product_category: str,
    public_patterns: Optional[List[Dict]] = None
) -> Dict:
    """
    Comprehensive gap analysis.

    Returns all types of gaps:
    - Pattern gaps (untested combinations)
    - Competitor gaps (popular but not tested by you)
    - Combination gaps (proven dimensions, untested combo)
    """

    finder = PatternGapFinder(db, user_id, product_category)

    result = {
        "pattern_gaps": finder.find_gaps(top_n=10),
        "combination_gaps": finder.find_combination_gaps(),
    }

    if public_patterns:
        result["competitor_gaps"] = finder.find_competitor_gaps(
            public_patterns,
            top_n=5
        )

    # Summary
    total_gaps = (
        len(result["pattern_gaps"]) +
        len(result["combination_gaps"]) +
        len(result.get("competitor_gaps", []))
    )

    result["summary"] = {
        "total_gaps_found": total_gaps,
        "high_priority": sum(
            1 for gap in result["pattern_gaps"]
            if gap["gap_score"] > 0.85
        ),
        "recommendation": (
            "Test high-priority gaps first - proven dimensions + fresh angles"
            if total_gaps > 0
            else "No gaps found - expand testing to new patterns"
        )
    }

    return result
