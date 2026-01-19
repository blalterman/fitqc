"""Tests for shared quantile utilities (_quantile_utils module)."""

import numpy as np
import pytest

from fitqc._quantile_utils import _aggregate_elbows_median


class TestAggregateElbowsMedian:
    """Tests for the _aggregate_elbows_median function."""

    def test_aggregate_elbows_median_robust_to_outliers(self):
        """Verify median aggregation is more robust to outliers than mean.

        The median should be resilient to outliers in the elbow estimates,
        whereas the mean would be pulled significantly by a single outlier.
        This is critical when one quantile curve gives a spurious elbow.
        """
        # Most elbows agree around 0.010, but one outlier at 0.050
        elbows = [0.010, 0.011, 0.009, 0.010, 0.050]

        median_result = _aggregate_elbows_median(elbows)
        mean_result = np.mean(elbows)

        # Median should be close to the cluster
        assert median_result == pytest.approx(0.010, abs=0.002)

        # Mean should be pulled significantly higher by the outlier
        assert mean_result == pytest.approx(0.018, abs=0.002)

        # Median should be much closer to the true value (0.010) than mean
        true_value = 0.010
        median_error = abs(median_result - true_value)
        mean_error = abs(mean_result - true_value)
        assert median_error < mean_error / 2, \
            f"Median error ({median_error}) should be < half of mean error ({mean_error})"

    def test_aggregation_requires_majority_agreement(self):
        """Verify that aggregation requires minimum fraction of valid elbows.

        If too few quantile curves detect an elbow, we shouldn't trust the
        aggregation. This test verifies the min_agreement_frac threshold works.
        """
        # Test default threshold (0.5 = 50%)
        elbows_poor = [0.010, None, None, 0.011, None]  # Only 2/5 = 40% valid
        result_poor = _aggregate_elbows_median(elbows_poor, min_agreement_frac=0.5)
        assert result_poor is None, "Should reject when < 50% agreement"

        elbows_good = [0.010, 0.011, 0.009, None, None]  # 3/5 = 60% valid
        result_good = _aggregate_elbows_median(elbows_good, min_agreement_frac=0.5)
        assert result_good is not None, "Should accept when >= 50% agreement"
        assert result_good == pytest.approx(0.010, abs=0.002)

        # Test custom threshold (0.75 = 75%)
        elbows_borderline = [0.010, 0.011, 0.009, None]  # 3/4 = 75% valid
        result_exact = _aggregate_elbows_median(elbows_borderline, min_agreement_frac=0.75)
        assert result_exact is not None, "Should accept at exact threshold"

        result_reject = _aggregate_elbows_median(elbows_borderline, min_agreement_frac=0.76)
        assert result_reject is None, "Should reject just above threshold"

        # Edge case: all None
        elbows_none = [None, None, None]
        result_none = _aggregate_elbows_median(elbows_none)
        assert result_none is None, "Should return None when all are None"

    def test_aggregate_elbows_median_works_for_both(self):
        """Verify aggregation works for both boundary tolerances AND interior epsilons.

        The same function should handle:
        - Boundary tolerances (linear scale, typical values 0.005 to 0.05)
        - Interior epsilons (log scale, typical values 1e-12 to 1e-3)

        The aggregation is scale-agnostic: median works in any numeric space.
        """
        # Test 1: Boundary tolerances (linear scale)
        boundary_tols = [0.010, 0.011, 0.009, 0.010, 0.011]
        tol_result = _aggregate_elbows_median(boundary_tols)

        assert tol_result is not None
        assert tol_result == pytest.approx(0.010, abs=0.001)

        # Test 2: Interior epsilons (log scale, small values)
        interior_eps_small = [1e-6, 1.2e-6, 0.9e-6, 1.1e-6, 1.0e-6]
        eps_small_result = _aggregate_elbows_median(interior_eps_small)

        assert eps_small_result is not None
        assert eps_small_result == pytest.approx(1e-6, rel=0.15)

        # Test 3: Interior epsilons (log scale, very small values near machine precision)
        interior_eps_tiny = [1e-10, 1.2e-10, 0.9e-10, 1.1e-10, 1.0e-10]
        eps_tiny_result = _aggregate_elbows_median(interior_eps_tiny)

        assert eps_tiny_result is not None
        assert eps_tiny_result == pytest.approx(1e-10, rel=0.15)

        # Test 4: Interior epsilons (log scale, larger values)
        interior_eps_large = [1e-4, 1.2e-4, 0.9e-4, 1.1e-4, 1.0e-4]
        eps_large_result = _aggregate_elbows_median(interior_eps_large)

        assert eps_large_result is not None
        assert eps_large_result == pytest.approx(1e-4, rel=0.15)

        # Verify that results are in the expected ranges for each domain
        assert 0.005 < tol_result < 0.020, "Boundary tolerance in expected range"
        assert 1e-11 < eps_tiny_result < 1e-9, "Tiny epsilon in expected range"
        assert 5e-7 < eps_small_result < 2e-6, "Small epsilon in expected range"
        assert 5e-5 < eps_large_result < 2e-4, "Large epsilon in expected range"

        # Test 5: Mixed with None values (should work for both domains)
        boundary_with_none = [0.010, None, 0.011, 0.009, None]  # 3/5 valid
        result_boundary_none = _aggregate_elbows_median(boundary_with_none)
        assert result_boundary_none == pytest.approx(0.010, abs=0.002)

        eps_with_none = [1e-6, None, 1.2e-6, None, 1.0e-6]  # 3/5 valid
        result_eps_none = _aggregate_elbows_median(eps_with_none)
        assert result_eps_none == pytest.approx(1e-6, rel=0.15)
