"""
Uniqueness Score - Verify creative is not a copy of competitors.

Prevents copying saturated patterns and ensures fresh angles.

Key metrics:
- Pattern uniqueness: How rare is this pattern combination?
- Similarity to public data: Is this too similar to top ads?
- Freshness score: How long since this pattern was popular?
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database.models import Creative
from collections import Counter
import hashlib


class UniquenessScorer:
    """
    Score creative uniqueness to avoid copying competitors.
    """

    def __init__(self, db: Session, user_id: str, product_category: str):
        self.db = db
        self.user_id = user_id
        self.product_category = product_category

    def calculate_uniqueness(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        caption: Optional[str] = None,
        cta_type: Optional[str] = None,
        public_patterns: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculate uniqueness score (0-100).

        Args:
            hook_type: Creative hook type
            emotion: Emotion
            pacing: Pacing
            caption: Optional caption text
            cta_type: Optional CTA type
            public_patterns: Public data from TikTok Creative Center

        Returns:
            Uniqueness analysis with score and recommendations
        """

        # Pattern uniqueness (within your tests)
        pattern_uniqueness = self._calculate_pattern_uniqueness(
            hook_type,
            emotion,
            pacing,
            cta_type
        )

        # Public saturation (how common in public data)
        public_saturation = self._calculate_public_saturation(
            hook_type,
            emotion,
            pacing,
            public_patterns
        ) if public_patterns else 0.0

        # Caption uniqueness (if provided)
        caption_uniqueness = self._calculate_caption_uniqueness(
            caption
        ) if caption else 1.0

        # Combine scores
        # Higher pattern uniqueness = good
        # Higher public saturation = bad (subtract)
        # Higher caption uniqueness = good

        base_score = (
            pattern_uniqueness * 0.4 +
            (1 - public_saturation) * 0.4 +
            caption_uniqueness * 0.2
        )

        # Convert to 0-100 scale
        final_score = int(base_score * 100)

        # Generate verdict
        verdict = self._generate_verdict(final_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            pattern_uniqueness,
            public_saturation,
            caption_uniqueness,
            hook_type,
            emotion
        )

        return {
            "uniqueness_score": final_score,
            "verdict": verdict,
            "breakdown": {
                "pattern_uniqueness": round(pattern_uniqueness, 2),
                "public_saturation": round(public_saturation, 2),
                "caption_uniqueness": round(caption_uniqueness, 2)
            },
            "is_unique": final_score >= 60,  # 60+ = unique
            "is_copy": final_score < 30,  # <30 = likely copy
            "recommendations": recommendations
        }

    def compare_with_public(
        self,
        hook_type: str,
        emotion: str,
        caption: str,
        public_creatives: List[Dict]
    ) -> Dict:
        """
        Compare creative with specific public creatives.

        Detects near-exact copies.
        """

        # Generate fingerprint for your creative
        your_fingerprint = self._generate_fingerprint(
            hook_type,
            emotion,
            caption
        )

        # Compare with public creatives
        similarities = []

        for public_creative in public_creatives:
            public_fingerprint = self._generate_fingerprint(
                public_creative.get("hook_type", ""),
                public_creative.get("emotion", ""),
                public_creative.get("caption", "")
            )

            # Calculate similarity
            similarity = self._calculate_fingerprint_similarity(
                your_fingerprint,
                public_fingerprint
            )

            if similarity > 0.7:  # >70% similar
                similarities.append({
                    "public_creative": public_creative.get("name", "Unknown"),
                    "similarity": round(similarity, 2),
                    "warning": "Potential copy" if similarity > 0.9 else "Very similar"
                })

        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "exact_copies": [s for s in similarities if s["similarity"] > 0.9],
            "similar_creatives": [s for s in similarities if 0.7 <= s["similarity"] <= 0.9],
            "is_copy": len([s for s in similarities if s["similarity"] > 0.9]) > 0,
            "recommendation": (
                "⚠️  This is too similar to existing creatives - create a unique angle!"
                if len([s for s in similarities if s["similarity"] > 0.9]) > 0
                else "✅ Sufficiently unique"
            )
        }

    def suggest_unique_variations(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        public_patterns: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Suggest variations to make creative more unique.

        Returns alternative patterns with higher uniqueness.
        """

        # Find alternative emotions that are underused
        alternative_emotions = self._find_alternative_dimension(
            "emotion",
            emotion,
            public_patterns
        )

        # Find alternative hooks
        alternative_hooks = self._find_alternative_dimension(
            "hook_type",
            hook_type,
            public_patterns
        )

        suggestions = []

        # Suggest emotion swaps
        for alt_emotion in alternative_emotions[:3]:
            uniqueness = self.calculate_uniqueness(
                hook_type,
                alt_emotion["value"],
                pacing,
                public_patterns=public_patterns
            )

            suggestions.append({
                "type": "emotion_swap",
                "original": f"{hook_type} + {emotion}",
                "suggested": f"{hook_type} + {alt_emotion['value']}",
                "uniqueness_gain": uniqueness["uniqueness_score"],
                "reasoning": f"Same hook, but {alt_emotion['value']} is underused → more unique"
            })

        # Suggest hook swaps
        for alt_hook in alternative_hooks[:3]:
            uniqueness = self.calculate_uniqueness(
                alt_hook["value"],
                emotion,
                pacing,
                public_patterns=public_patterns
            )

            suggestions.append({
                "type": "hook_swap",
                "original": f"{hook_type} + {emotion}",
                "suggested": f"{alt_hook['value']} + {emotion}",
                "uniqueness_gain": uniqueness["uniqueness_score"],
                "reasoning": f"Same emotion, but {alt_hook['value']} hook is underused → more unique"
            })

        # Sort by uniqueness gain
        suggestions.sort(key=lambda x: x["uniqueness_gain"], reverse=True)

        return suggestions[:5]  # Top 5 suggestions

    # ==================== PRIVATE METHODS ====================

    def _calculate_pattern_uniqueness(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        cta_type: Optional[str]
    ) -> float:
        """
        Calculate how unique this pattern is within your tests.

        Returns 0-1 (1 = very unique, 0 = very common)
        """

        # Count how many of your creatives use this exact pattern
        exact_matches = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category,
            Creative.hook_type == hook_type,
            Creative.emotion == emotion,
            Creative.pacing == pacing
        ).count()

        # Count similar patterns (2 out of 3 match)
        similar_matches = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category
        ).filter(
            ((Creative.hook_type == hook_type) & (Creative.emotion == emotion)) |
            ((Creative.hook_type == hook_type) & (Creative.pacing == pacing)) |
            ((Creative.emotion == emotion) & (Creative.pacing == pacing))
        ).count()

        # Total creatives
        total = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.product_category == self.product_category
        ).count()

        if total == 0:
            return 1.0  # First creative = 100% unique

        # Calculate uniqueness
        exact_ratio = exact_matches / total
        similar_ratio = similar_matches / total

        # Penalty for exact matches and similar patterns
        uniqueness = 1.0 - (exact_ratio * 0.8 + similar_ratio * 0.2)

        return max(0.0, min(1.0, uniqueness))

    def _calculate_public_saturation(
        self,
        hook_type: str,
        emotion: str,
        pacing: str,
        public_patterns: List[Dict]
    ) -> float:
        """
        Calculate saturation in public data.

        Returns 0-1 (1 = highly saturated, 0 = fresh)
        """

        if not public_patterns:
            return 0.0

        # Count how many public creatives use this pattern
        matches = 0
        total = len(public_patterns)

        for pattern in public_patterns:
            if (
                pattern.get("hook_type") == hook_type and
                pattern.get("emotion") == emotion and
                pattern.get("pacing") == pacing
            ):
                matches += 1

        # Saturation ratio
        saturation = matches / total if total > 0 else 0.0

        return saturation

    def _calculate_caption_uniqueness(self, caption: str) -> float:
        """
        Calculate caption uniqueness.

        Checks for overused phrases.
        """

        if not caption:
            return 1.0

        # Common overused phrases (from analysis of saturated creatives)
        OVERUSED_PHRASES = [
            "wait until",
            "you won't believe",
            "this changed my life",
            "i was shocked",
            "secret method",
            "game changer",
            "must try",
            "life hack",
            "blew my mind",
            "can't believe i",
        ]

        caption_lower = caption.lower()

        # Count overused phrases
        overused_count = sum(
            1 for phrase in OVERUSED_PHRASES
            if phrase in caption_lower
        )

        # Penalty for overused phrases
        penalty = min(0.5, overused_count * 0.2)

        uniqueness = 1.0 - penalty

        return max(0.0, uniqueness)

    def _generate_fingerprint(
        self,
        hook_type: str,
        emotion: str,
        caption: str
    ) -> str:
        """Generate fingerprint for creative."""

        # Normalize caption (remove punctuation, lowercase)
        normalized_caption = ''.join(
            c.lower() for c in caption
            if c.isalnum() or c.isspace()
        )

        # Create fingerprint
        fingerprint_str = f"{hook_type}:{emotion}:{normalized_caption}"

        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _calculate_fingerprint_similarity(
        self,
        fp1: str,
        fp2: str
    ) -> float:
        """Calculate similarity between fingerprints (simple version)."""

        # Simple character-level similarity
        matches = sum(c1 == c2 for c1, c2 in zip(fp1, fp2))
        similarity = matches / len(fp1)

        return similarity

    def _generate_verdict(self, score: int) -> str:
        """Generate verdict based on score."""

        if score >= 80:
            return "🌟 Highly unique - fresh angle!"
        elif score >= 60:
            return "✅ Unique enough - good to test"
        elif score >= 40:
            return "⚠️  Moderately unique - consider variations"
        elif score >= 30:
            return "❌ Low uniqueness - saturated pattern"
        else:
            return "🚫 Likely copy - create unique version"

    def _generate_recommendations(
        self,
        pattern_uniqueness: float,
        public_saturation: float,
        caption_uniqueness: float,
        hook_type: str,
        emotion: str
    ) -> List[str]:
        """Generate actionable recommendations."""

        recommendations = []

        if pattern_uniqueness < 0.5:
            recommendations.append(
                f"Pattern {hook_type}+{emotion} is overused in your tests - try different combination"
            )

        if public_saturation > 0.3:
            recommendations.append(
                f"This pattern is popular with competitors (30%+ use it) - audience may be saturated"
            )

        if caption_uniqueness < 0.7:
            recommendations.append(
                "Caption uses overused phrases - rewrite with fresh language"
            )

        if not recommendations:
            recommendations.append(
                "✅ Creative is sufficiently unique - proceed with testing"
            )

        return recommendations

    def _find_alternative_dimension(
        self,
        dimension: str,  # "hook_type" or "emotion"
        current_value: str,
        public_patterns: Optional[List[Dict]]
    ) -> List[Dict]:
        """Find alternative values for dimension that are underused."""

        if not public_patterns:
            return []

        # Count frequency of each value in public data
        counter = Counter()

        for pattern in public_patterns:
            value = pattern.get(dimension)
            if value:
                counter[value] += 1

        total = len(public_patterns)

        # Calculate saturation for each value
        saturations = []
        for value, count in counter.items():
            if value != current_value:  # Don't suggest current value
                saturation = count / total
                saturations.append({
                    "value": value,
                    "saturation": saturation,
                    "frequency": count
                })

        # Sort by saturation (ascending - less saturated = better)
        saturations.sort(key=lambda x: x["saturation"])

        return saturations  # Return least saturated first


def quick_uniqueness_check(
    db: Session,
    user_id: str,
    product_category: str,
    hook_type: str,
    emotion: str,
    pacing: str,
    caption: Optional[str] = None,
    public_patterns: Optional[List[Dict]] = None
) -> Dict:
    """
    Quick uniqueness check.

    Returns simple yes/no + score.
    """

    scorer = UniquenessScorer(db, user_id, product_category)

    result = scorer.calculate_uniqueness(
        hook_type,
        emotion,
        pacing,
        caption,
        public_patterns=public_patterns
    )

    return {
        "is_unique": result["is_unique"],
        "is_copy": result["is_copy"],
        "score": result["uniqueness_score"],
        "verdict": result["verdict"],
        "proceed_with_test": result["uniqueness_score"] >= 60
    }
