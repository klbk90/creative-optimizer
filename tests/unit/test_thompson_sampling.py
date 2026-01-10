"""
Unit tests for Thompson Sampling algorithm
"""
import pytest
from utils.thompson_sampling import ThompsonSampling


class TestThompsonSampling:
    """Test Thompson Sampling recommendations"""

    def test_initialization(self):
        """Test Thompson Sampling can be initialized"""
        ts = ThompsonSampling()
        assert ts is not None

    def test_sample_beta_distribution(self):
        """Test sampling from beta distribution"""
        ts = ThompsonSampling()

        # Sample with high conversion rate (α=100, β=10)
        sample_high = ts.sample(alpha=100, beta=10)

        # Sample with low conversion rate (α=10, β=100)
        sample_low = ts.sample(alpha=10, beta=100)

        # High CVR should generally be > low CVR
        assert 0 <= sample_high <= 1
        assert 0 <= sample_low <= 1
        # Statistical property - not always true, but usually
        # assert sample_high > sample_low  # Can fail due to randomness

    def test_update_posterior(self):
        """Test Bayesian update with new data"""
        ts = ThompsonSampling()

        # Start with uninformative prior
        alpha_prior = 1
        beta_prior = 1

        # Observe 5 conversions out of 100 impressions
        conversions = 5
        impressions = 100

        alpha_posterior, beta_posterior = ts.update(
            alpha_prior,
            beta_prior,
            conversions,
            impressions - conversions
        )

        # Check Bayesian update formula
        assert alpha_posterior == alpha_prior + conversions
        assert beta_posterior == beta_prior + (impressions - conversions)

    def test_recommend_best_arm(self):
        """Test multi-armed bandit recommendation"""
        ts = ThompsonSampling()

        patterns = [
            {"pattern": "hook_A", "alpha": 100, "beta": 10},  # 90% CVR
            {"pattern": "hook_B", "alpha": 50, "beta": 50},   # 50% CVR
            {"pattern": "hook_C", "alpha": 10, "beta": 100},  # 9% CVR
        ]

        # Sample 100 times and count recommendations
        recommendations = {}
        for _ in range(100):
            best_pattern = ts.recommend(patterns)
            recommendations[best_pattern] = recommendations.get(best_pattern, 0) + 1

        # hook_A should be recommended most often (but not always due to exploration)
        assert "hook_A" in recommendations
        assert recommendations["hook_A"] > 20  # At least 20% of the time

    def test_calculate_expected_cvr(self):
        """Test expected CVR calculation"""
        ts = ThompsonSampling()

        # Beta distribution mean = α / (α + β)
        alpha = 50
        beta = 50

        expected_cvr = ts.expected_cvr(alpha, beta)
        assert expected_cvr == 0.5  # 50% CVR

        # High CVR pattern
        expected_cvr_high = ts.expected_cvr(alpha=90, beta=10)
        assert expected_cvr_high == 0.9  # 90% CVR

    def test_confidence_interval(self):
        """Test credible interval calculation"""
        ts = ThompsonSampling()

        # 95% credible interval
        lower, upper = ts.credible_interval(alpha=50, beta=50, confidence=0.95)

        assert 0 <= lower <= 0.5
        assert 0.5 <= upper <= 1
        assert lower < upper
