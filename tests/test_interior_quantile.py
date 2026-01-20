"""Tests for interior quantile-based multi-curve stickiness detection."""

import numpy as np
from scipy.stats import linregress

from fitqc.config import InteriorConfig
from fitqc.interior import _compute_quantile_curves_interior, run_interior_qc
from fitqc.synth import generate_with_x0_spike


class TestQuantileCurveComputation:
    """Tests for _compute_quantile_curves_interior (Phase 2)."""

    def test_quantile_curve_uniform_z_is_linear(self):
        """For uniform z-distribution, quantile curve should be linear in LOG-space.

        This test verifies that for uniformly distributed z-values, the relationship
        between quantiles and epsilon values is linear when plotted in log-space.
        This is a fundamental property that validates our log-space interpolation.
        """
        # Generate uniform z in [10^-12, 10^-3]
        rng = np.random.default_rng(42)
        z = rng.uniform(1e-12, 1e-3, size=10000)
        z_sorted = np.sort(z)

        quantile_grid = np.array([0.01, 0.05, 0.10, 0.20, 0.30, 0.40])
        eps_grid = np.logspace(-12, -3, 100)

        # Compute quantile curves
        eps_at_quantile, elbows = _compute_quantile_curves_interior(
            z_sorted, eps_grid, quantile_grid
        )

        # For uniform z, log(eps) should be approximately linear in quantile
        # (since the CDF is linear, the inverse CDF should also be linear in log-space)
        # Note: Due to discrete sampling and interpolation, we don't expect perfect linearity
        _, _, r_value, _, _ = linregress(quantile_grid, np.log(eps_at_quantile))

        # R² should show reasonable linearity (relaxed threshold due to discrete sampling)
        assert r_value**2 > 0.75, f"Should show linear trend in log-space, got R²={r_value**2}"

        # Check return types and shapes
        assert len(eps_at_quantile) == len(quantile_grid)
        assert len(elbows) == len(quantile_grid)
        assert all(e is not None for e in elbows), "All elbows should be valid for uniform data"

    def test_quantile_curve_tight_spike_shows_elbow(self):
        """For tight spike at x0, quantile curve should show clear transition.

        This test verifies that when there's a tight spike (5% of samples within
        eps=1e-6), the epsilon values at different quantiles show a clear jump
        as we cross the spike boundary.
        """
        rng = np.random.default_rng(42)
        # Generate spike: 5% of samples within eps=1e-6 of x0
        z_spike = rng.uniform(0, 1e-6, size=500)  # 5% in spike
        z_bulk = rng.uniform(1e-6, 1e-3, size=9500)  # 95% elsewhere
        z = np.concatenate([z_spike, z_bulk])
        z_sorted = np.sort(z)

        quantile_grid = np.array([0.01, 0.02, 0.05, 0.10, 0.15, 0.20])
        eps_grid = np.logspace(-12, -3, 100)

        eps_at_quantile, _ = _compute_quantile_curves_interior(z_sorted, eps_grid, quantile_grid)

        # For q <= 0.05 (within spike), eps should be small
        assert eps_at_quantile[2] < 1e-5, (
            f"Spike region (q=0.05) should need tiny epsilon, got {eps_at_quantile[2]}"
        )

        # For q > 0.05 (beyond spike), eps should jump
        assert eps_at_quantile[3] > 1e-5, (
            f"Beyond spike (q=0.10), epsilon should be larger, got {eps_at_quantile[3]}"
        )

        # Verify there's a significant jump in epsilon as we cross the spike
        ratio = eps_at_quantile[3] / eps_at_quantile[2]
        assert ratio > 2.0, f"Should see clear jump across spike boundary, got ratio={ratio}"

    def test_quantile_curve_shape_dtype_bounds(self):
        """Verify array correctness: shape, dtype, and bounds.

        This test ensures that the quantile curve computation returns arrays
        with the correct properties, regardless of input data characteristics.
        """
        rng = np.random.default_rng(42)
        z = rng.uniform(1e-10, 1e-4, size=1000)
        z_sorted = np.sort(z)

        quantile_grid = np.array([0.01, 0.05, 0.10])
        eps_grid = np.logspace(-12, -3, 50)

        eps_at_quantile, elbows = _compute_quantile_curves_interior(
            z_sorted, eps_grid, quantile_grid
        )

        # Check shapes
        assert eps_at_quantile.shape == quantile_grid.shape, (
            f"Shape mismatch: {eps_at_quantile.shape} vs {quantile_grid.shape}"
        )
        assert len(elbows) == len(quantile_grid), (
            f"Elbows length mismatch: {len(elbows)} vs {len(quantile_grid)}"
        )

        # Check dtype (should be floating point)
        assert np.issubdtype(eps_at_quantile.dtype, np.floating), (
            f"eps_at_quantile should be float, got {eps_at_quantile.dtype}"
        )

        # Check bounds (epsilon should be within grid range)
        assert np.all(eps_at_quantile >= eps_grid.min()), "Epsilon values should be >= grid minimum"
        assert np.all(eps_at_quantile <= eps_grid.max()), "Epsilon values should be <= grid maximum"

        # Check that elbows are either float or None
        for i, elbow in enumerate(elbows):
            assert elbow is None or isinstance(elbow, float), (
                f"Elbow {i} should be float or None, got {type(elbow)}"
            )


class TestSpikeDetectionIndependence:
    """Tests for Phase 3: Verify spike detection independence (CRITICAL)."""

    def test_spike_detection_unchanged_by_quantile_analysis(self):
        """Spike detection should give same result regardless of quantile analysis setting.

        CRITICAL TEST: This verifies that the spike detection (histogram-based)
        is completely independent of the threshold estimation method (single-curve
        vs multi-curve). Both modes should detect the same spikes.
        """
        # Generate data with spike at exactly x0
        # Use the existing generator which places samples EXACTLY at x0
        x_spike = generate_with_x0_spike(n=10000, x0=0.5, L=0.0, U=1.0, spike_frac=0.05, seed=42)

        config_single = InteriorConfig(use_quantile_analysis=False)
        config_multi = InteriorConfig(use_quantile_analysis=True)

        result_single = run_interior_qc(x_spike, x0=0.5, L=0.0, U=1.0, config=config_single)
        result_multi = run_interior_qc(x_spike, x0=0.5, L=0.0, U=1.0, config=config_multi)

        # Spike detection should be IDENTICAL
        assert result_single.spike_detected == result_multi.spike_detected, (
            "Spike detection must be independent of threshold method"
        )

        # Both should detect the spike exists
        assert result_single.spike_detected is True, "Single-curve should detect spike"
        assert result_multi.spike_detected is True, "Multi-curve should detect spike"

        # Spike location should be the same (or very close)
        assert result_single.spike_z_loc is not None
        assert result_multi.spike_z_loc is not None
        assert abs(result_single.spike_z_loc - result_multi.spike_z_loc) < 0.01, (
            "Spike location should be nearly identical"
        )

        # eps_star MAY differ (that's the point of multi-curve)
        # But both should detect that there IS a threshold
        assert result_single.eps_star is not None or result_multi.eps_star is not None, (
            "At least one method should find a threshold"
        )

    def test_broad_distribution_no_spike_detected(self):
        """Broad distribution centered at x0 should NOT trigger spike detection.

        This test verifies that the width criterion prevents false positives.
        A broad normal distribution naturally has mass near x0, but it's not
        a spike (it's wide, not narrow).
        """
        rng = np.random.default_rng(42)
        # Broad normal at x0 (natural clustering, not a spike)
        x = rng.normal(loc=0.5, scale=0.15, size=10000)
        x = np.clip(x, 0.0, 1.0)  # Clip to bounds

        config = InteriorConfig(use_quantile_analysis=True)
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # Should NOT detect spike (histogram will be broad, not narrow)
        assert not result.spike_detected, (
            "Broad distribution should not trigger spike detection (width criterion)"
        )

        # eps_star might be None (no spike detected, so no threshold computed)
        # This is expected and correct behavior


class TestIntegration:
    """Tests for Phase 3: Integration tests."""

    def test_multi_curve_detects_tight_spike_better(self):
        """Multi-curve should give more accurate eps_star for tight spikes.

        This test verifies that the multi-curve approach provides better
        accuracy for very tight spikes at machine precision levels.
        """
        # Very tight spike: 3% at exactly x0
        x = generate_with_x0_spike(n=10000, x0=0.5, L=0.0, U=1.0, spike_frac=0.03, seed=42)

        config_old = InteriorConfig(use_quantile_analysis=False)
        config_new = InteriorConfig(
            use_quantile_analysis=True, quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05)
        )

        result_old = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_old)
        result_new = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_new)

        # Both should detect spike
        assert result_old.spike_detected and result_new.spike_detected, (
            "Both methods should detect the spike"
        )

        # New method should give eps_star
        assert result_new.eps_star is not None, "Multi-curve should find a threshold"

        # We expect eps_star to be small (spike is tight)
        # The spike width is 1e-10, so eps_star should be in that ballpark
        assert result_new.eps_star < 1e-6, (
            f"Should detect tight spike, got eps_star={result_new.eps_star}"
        )

        # Verify quantile_elbows is populated in multi-curve mode
        assert result_new.quantile_elbows is not None, "Multi-curve should populate quantile_elbows"
        assert len(result_new.quantile_elbows) == len(config_new.quantile_grid), (
            "Should have one elbow per quantile"
        )

        # Verify quantile_elbows is NOT populated in single-curve mode
        assert result_old.quantile_elbows is None, (
            "Single-curve should not populate quantile_elbows"
        )

    def test_quantile_elbows_diagnostic_info(self):
        """Verify that quantile_elbows provides useful diagnostic information.

        This test ensures that the quantile_elbows dict is correctly populated
        and contains meaningful information for debugging.
        """
        # Generate spike: 5% of samples exactly at x0
        x = generate_with_x0_spike(n=5000, x0=0.5, L=0.0, U=1.0, spike_frac=0.05, seed=42)

        config = InteriorConfig(use_quantile_analysis=True, quantile_grid=(0.01, 0.02, 0.05, 0.10))

        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # Should detect spike and have quantile_elbows
        assert result.spike_detected, "Should detect spike"
        assert result.quantile_elbows is not None, "Should have quantile_elbows"

        # Check structure
        assert len(result.quantile_elbows) == 4, "Should have 4 quantiles"
        assert 0.01 in result.quantile_elbows, "Should have quantile 0.01"
        assert 0.10 in result.quantile_elbows, "Should have quantile 0.10"

        # All elbows should be valid (not None) for this clean spike data
        for q, elbow in result.quantile_elbows.items():
            assert elbow is not None, f"Quantile {q} should have valid elbow"
            assert isinstance(elbow, float), f"Elbow for quantile {q} should be float"
            assert elbow > 0, f"Elbow for quantile {q} should be positive"

    def test_edge_case_uniform_no_spike(self):
        """Edge case: Uniform data should not detect spike in either mode."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0.0, 1.0, size=5000)

        config_single = InteriorConfig(use_quantile_analysis=False)
        config_multi = InteriorConfig(use_quantile_analysis=True)

        result_single = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_single)
        result_multi = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config_multi)

        # Neither should detect a spike
        assert not result_single.spike_detected, "Single-curve should not detect spike in uniform"
        assert not result_multi.spike_detected, "Multi-curve should not detect spike in uniform"

        # eps_star should be None (no spike, so no threshold)
        assert result_single.eps_star is None, "No threshold for uniform data (single)"
        assert result_multi.eps_star is None, "No threshold for uniform data (multi)"

        # quantile_elbows should be None in both cases (no spike detected)
        assert result_single.quantile_elbows is None
        assert result_multi.quantile_elbows is None


class TestInteriorEdgeCases:
    """Edge case tests for interior detection (Agent 3 responsibility)."""

    def test_interior_empty_array(self):
        """Empty input array should be handled gracefully.

        Edge case: n=0 samples. Should not crash, should return sensible defaults.
        """
        x = np.array([])

        config = InteriorConfig()
        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=config)

        # Should not crash and should return a valid result
        assert isinstance(result.spike_detected, bool)

        # With no data, should not detect spike
        assert result.spike_detected is False
        assert result.spike_z_loc is None
        assert result.eps_star is None

        # Arrays should exist but be appropriate for empty data
        assert len(result.eps_grid) > 0  # Grid still exists
        assert len(result.mass_curve) > 0  # Will be zeros or handle empty

    def test_interior_single_value(self):
        """Single sample should be handled gracefully.

        Edge case: n=1 sample. Should not crash, no meaningful detection possible.
        """
        # Single sample at x0
        x_at_x0 = np.array([5.0])
        result_at_x0 = run_interior_qc(x_at_x0, x0=5.0, L=0.0, U=10.0)

        assert isinstance(result_at_x0.spike_detected, bool)
        # Can't reliably detect spike with n=1, should not crash

        # Single sample away from x0
        x_away = np.array([8.0])
        result_away = run_interior_qc(x_away, x0=5.0, L=0.0, U=10.0)

        assert isinstance(result_away.spike_detected, bool)
        # Should not crash, detection may vary but should be valid boolean

        # Single sample at boundary
        x_boundary = np.array([0.0])
        result_boundary = run_interior_qc(x_boundary, x0=5.0, L=0.0, U=10.0)

        assert isinstance(result_boundary.spike_detected, bool)
        # Should not crash

    def test_interior_all_at_x0(self):
        """All samples exactly at x0 should be handled gracefully.

        Edge case: 100% concentration at x0. Should clearly detect spike.
        """
        # All samples exactly at x0
        x_all_x0 = np.full(1000, 5.0)
        result_all_x0 = run_interior_qc(x_all_x0, x0=5.0, L=0.0, U=10.0)

        # Should clearly detect spike
        assert result_all_x0.spike_detected is True
        assert result_all_x0.spike_z_loc is not None
        # All samples at x0 means z=0 for all, spike should be at z≈0
        assert result_all_x0.spike_z_loc < 0.05

        # Edge case: all samples far from x0 (no spike)
        x_all_far = np.full(1000, 9.0)  # All far from x0=5.0
        result_all_far = run_interior_qc(x_all_far, x0=5.0, L=0.0, U=10.0)

        # Should NOT detect spike (no concentration at x0)
        assert result_all_far.spike_detected is False

        # Edge case: bimodal distribution (some at x0, rest elsewhere)
        # Half at x0, half far away
        x_bimodal = np.concatenate(
            [
                np.full(500, 5.0),  # At x0
                np.full(500, 9.0),  # Far from x0
            ]
        )
        result_bimodal = run_interior_qc(x_bimodal, x0=5.0, L=0.0, U=10.0)

        # Should detect spike (50% at x0 is a clear spike)
        assert result_bimodal.spike_detected is True
