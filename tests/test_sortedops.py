"""Tests for sortedops module - O(log n) operations on sorted arrays."""

import numpy as np
import pytest

from fitqc.sortedops import quantile_by_index, slice_by_range, tail_mass


class TestSortedOps:
    """Test suite for sorted array operations."""

    def test_tail_mass_uniform_midpoint(self):
        """Tail mass at midpoint of uniform data should be ~0.5."""
        x_sorted = np.linspace(0, 1, 10001)
        mass = tail_mass(x_sorted, 0.5)
        assert mass == pytest.approx(0.5, abs=1e-4)

    def test_tail_mass_at_zero(self):
        """Tail mass at 0 for positive data should be 0."""
        x_sorted = np.sort(np.abs(np.random.default_rng(42).standard_normal(1000)) + 0.01)
        mass = tail_mass(x_sorted, 0.0)
        assert mass == 0.0

    def test_tail_mass_beyond_max(self):
        """Tail mass beyond max value should be 1.0."""
        x_sorted = np.array([1.0, 2.0, 3.0])
        mass = tail_mass(x_sorted, 4.0)
        assert mass == 1.0

    def test_tail_mass_increasing(self):
        """Tail mass should be monotonically increasing with threshold."""
        x_sorted = np.sort(np.random.default_rng(42).standard_normal(1000))
        thresholds = np.linspace(-3, 3, 50)
        masses = [tail_mass(x_sorted, t) for t in thresholds]
        assert all(masses[i] <= masses[i + 1] for i in range(len(masses) - 1))

    def test_quantile_median_known(self):
        """Median of [0,1,2,3,4] should be 2.0."""
        x_sorted = np.array([0, 1, 2, 3, 4], dtype=float)
        assert quantile_by_index(x_sorted, 0.5) == 2.0

    def test_quantile_endpoints(self):
        """Quantile at 0 and 1 should return min and max."""
        x_sorted = np.array([10.0, 20.0, 30.0])
        assert quantile_by_index(x_sorted, 0.0) == 10.0
        assert quantile_by_index(x_sorted, 1.0) == 30.0

    def test_quantile_array_input(self):
        """Quantile should work with array of q values."""
        x_sorted = np.linspace(0, 100, 101)
        q = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        result = quantile_by_index(x_sorted, q)
        np.testing.assert_array_equal(result, [0, 25, 50, 75, 100])

    def test_quantile_shape_preserved(self):
        """Quantile output shape should match input q shape."""
        x_sorted = np.sort(np.random.default_rng(42).standard_normal(1000))
        q = np.array([[0.1, 0.2], [0.8, 0.9]])
        result = quantile_by_index(x_sorted, q)
        assert result.shape == (2, 2)

    def test_slice_excludes_boundaries(self):
        """Slice should return open interval (lo, hi), excluding boundaries."""
        x_sorted = np.array([0.1, 0.2, 0.5, 0.8, 0.9])
        lo_idx, hi_idx = slice_by_range(x_sorted, 0.2, 0.8)
        result = x_sorted[lo_idx:hi_idx]
        np.testing.assert_array_equal(result, [0.5])

    def test_slice_full_range(self):
        """Slice with -inf to inf should return full array indices."""
        x_sorted = np.array([1.0, 2.0, 3.0])
        lo_idx, hi_idx = slice_by_range(x_sorted, -np.inf, np.inf)
        assert lo_idx == 0
        assert hi_idx == 3

    def test_slice_empty_when_no_match(self):
        """Slice should return empty range when no values in interval."""
        x_sorted = np.array([1.0, 2.0, 3.0])
        lo_idx, hi_idx = slice_by_range(x_sorted, 5.0, 10.0)
        assert lo_idx == hi_idx
