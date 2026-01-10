"""
Unit tests for Markov Chain CVR prediction
"""
import pytest
from utils.markov_chain import MarkovChainPredictor


class TestMarkovChainPredictor:
    """Test Markov Chain pattern prediction"""

    def test_initialization(self):
        """Test Markov Chain can be initialized"""
        mc = MarkovChainPredictor()
        assert mc is not None

    def test_add_pattern(self):
        """Test adding pattern to transition matrix"""
        mc = MarkovChainPredictor()

        # Add pattern: problem_agitation → frustration → 15% CVR
        mc.add_pattern(
            hook_type="problem_agitation",
            emotion="frustration",
            cvr=0.15,
            sample_size=100
        )

        # Check pattern was recorded
        assert mc.transition_count > 0

    def test_predict_cvr(self):
        """Test CVR prediction for pattern"""
        mc = MarkovChainPredictor()

        # Train with historical data
        mc.add_pattern("problem_agitation", "frustration", cvr=0.15, sample_size=100)
        mc.add_pattern("problem_agitation", "frustration", cvr=0.14, sample_size=150)
        mc.add_pattern("problem_agitation", "curiosity", cvr=0.10, sample_size=80)

        # Predict CVR for known pattern
        predicted_cvr = mc.predict(
            hook_type="problem_agitation",
            emotion="frustration"
        )

        # Should be close to weighted average of 15% and 14%
        assert 0.13 <= predicted_cvr <= 0.16

    def test_predict_unknown_pattern(self):
        """Test prediction for unknown pattern"""
        mc = MarkovChainPredictor()

        # Train with some data
        mc.add_pattern("hook_A", "emotion_A", cvr=0.12, sample_size=100)

        # Predict unknown pattern (should return baseline or None)
        predicted_cvr = mc.predict(
            hook_type="unknown_hook",
            emotion="unknown_emotion"
        )

        # Should return baseline CVR or indicate uncertainty
        assert predicted_cvr is None or predicted_cvr > 0

    def test_confidence_score(self):
        """Test confidence score based on sample size"""
        mc = MarkovChainPredictor()

        # Large sample size → high confidence
        mc.add_pattern("hook_A", "emotion_A", cvr=0.15, sample_size=1000)
        confidence_high = mc.confidence("hook_A", "emotion_A")

        # Small sample size → low confidence
        mc.add_pattern("hook_B", "emotion_B", cvr=0.15, sample_size=10)
        confidence_low = mc.confidence("hook_B", "emotion_B")

        assert confidence_high > confidence_low
        assert 0 <= confidence_high <= 1
        assert 0 <= confidence_low <= 1

    def test_weighted_average(self):
        """Test weighted average with multiple observations"""
        mc = MarkovChainPredictor()

        # Add same pattern with different sample sizes
        mc.add_pattern("hook_A", "emotion_A", cvr=0.20, sample_size=100)
        mc.add_pattern("hook_A", "emotion_A", cvr=0.10, sample_size=100)

        # Predicted CVR should be average
        predicted = mc.predict("hook_A", "emotion_A")
        assert predicted == pytest.approx(0.15, abs=0.01)
