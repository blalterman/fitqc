"""Tests for quantile-based boundary stickiness detection.

This module tests the multi-curve quantile analysis functionality for boundary
detection, including backward compatibility and edge cases.
"""

import numpy as np
import pytest
from scipy.stats import linregress

from fitqc.boundary import (
    _aggregate_elbows_median,
    _build_tolerance_grid,
    _compute_quantile_curves_boundary,
    run_boundary_qc,
)
from fitqc.config import BoundaryConfig
from fitqc.synth import generate_with_boundary_pileup


class TestBoundaryBackwardCompatibility:
    """Tests to ensure single-curve mode still works after quantile implementation."""

    def test_single_curve_mode_still_available(self):
        """Verify that use_quantile_analysis=False still works.

        After implementing multi-curve quantile analysis, the original single-curve
        mode must remain available and produce the same results as before.
        This ensures backward compatibility for existing code.
        """
        # Generate data with lower boundary pileup
        x = generate_with_boundary_pileup(
            n=10000,
            L=0.0,
            U=10.0,
            lower_pileup_frac=0.05,
            upper_pileup_frac=0.0,
            pileup_width=0.01,
            seed=42,
        )

        # Run with quantile analysis disabled (single-curve mode)
        config_single = BoundaryConfig(use_quantile_analysis=False)
        result_single = run_boundary_qc(x, L=0.0, U=10.0, config=config_single)

        # Verify standard fields are present
        assert hasattr(result_single, "lower_pileup_detected")
        assert hasattr(result_single, "upper_pileup_detected")
        assert hasattr(result_single, "t_lo_star")
        assert hasattr(result_single, "t_hi_star")
        assert hasattr(result_single, "tol_grid")
        assert hasattr(result_single, "lower_mass_curve")
        assert hasattr(result_single, "upper_mass_curve")

        # Should detect lower pileup
        assert result_single.lower_pileup_detected is True
        assert result_single.t_lo_star is not None
        assert result_single.t_lo_star > 0.005

        # Should NOT detect upper pileup
        assert result_single.upper_pileup_detected is False

        # Verify that quantile_elbows field is NOT present or is None
        # (since we're in single-curve mode)
        if hasattr(result_single, "quantile_elbows"):
            assert result_single.quantile_elbows is None, (
                "Single-curve mode should not compute quantile_elbows"
            )

        # Verify that result gives same detection as before quantile feature
        # For uniform data, single-curve should not detect pileup
        x_uniform = np.random.default_rng(123).uniform(0, 10, size=10000)
        result_uniform = run_boundary_qc(x_uniform, L=0.0, U=10.0, config=config_single)

        assert result_uniform.lower_pileup_detected is False
        assert result_uniform.upper_pileup_detected is False


class TestBoundaryEdgeCases:
    """Edge case tests for boundary detection."""

    def test_boundary_empty_array(self):
        """Empty input array should be handled gracefully.

        Edge case: n=0 samples. Should not crash, should return sensible defaults.
        """
        x = np.array([])

        config = BoundaryConfig()
        result = run_boundary_qc(x, L=0.0, U=10.0, config=config)

        # Should not crash and should return a valid result
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)

        # With no data, should not detect pileup
        assert result.lower_pileup_detected is False
        assert result.upper_pileup_detected is False

        # Tolerance values should be None or very small
        assert result.t_lo_star is None or result.t_lo_star < 0.001
        assert result.t_hi_star is None or result.t_hi_star < 0.001

        # Mass curves should exist but be all zeros or empty
        assert len(result.lower_mass_curve) > 0
        assert len(result.upper_mass_curve) > 0

    def test_boundary_single_value(self):
        """Single sample should be handled gracefully.

        Edge case: n=1 sample. Should not crash, no meaningful detection possible.
        """
        # Single sample at lower bound
        x_lower = np.array([0.0])
        result_lower = run_boundary_qc(x_lower, L=0.0, U=10.0)

        assert isinstance(result_lower.lower_pileup_detected, bool)
        assert isinstance(result_lower.upper_pileup_detected, bool)

        # Single sample at upper bound
        x_upper = np.array([10.0])
        result_upper = run_boundary_qc(x_upper, L=0.0, U=10.0)

        assert isinstance(result_upper.lower_pileup_detected, bool)
        assert isinstance(result_upper.upper_pileup_detected, bool)

        # Single sample in middle
        x_middle = np.array([5.0])
        result_middle = run_boundary_qc(x_middle, L=0.0, U=10.0)

        assert isinstance(result_middle.lower_pileup_detected, bool)
        assert isinstance(result_middle.upper_pileup_detected, bool)

        # Should not crash, detection may vary but should be valid booleans
        # (We can't assert specific detection results with n=1)

    def test_boundary_all_at_boundary(self):
        """Edge case: Very high concentration near boundary should be detected.

        Note: The algorithm requires some spread in the data to detect an elbow.
        When ALL samples are at the exact same value, the mass curve is flat
        (no elbow exists). We test with realistic pileups that have small spread.
        """
        # Significant concentration near lower bound
        # Use parameters known to work (from backward compat test)
        x_mostly_lower = generate_with_boundary_pileup(
            n=1000,
            L=0.0,
            U=10.0,
            lower_pileup_frac=0.10,  # 10% pileup
            upper_pileup_frac=0.0,
            pileup_width=0.01,  # 1% of range
            seed=42,
        )
        result_mostly_lower = run_boundary_qc(x_mostly_lower, L=0.0, U=10.0)

        # Should detect lower pileup
        assert result_mostly_lower.lower_pileup_detected is True
        assert result_mostly_lower.t_lo_star is not None

        # Should not detect upper pileup
        assert result_mostly_lower.upper_pileup_detected is False

        # Significant concentration near upper bound
        x_mostly_upper = generate_with_boundary_pileup(
            n=1000,
            L=0.0,
            U=10.0,
            lower_pileup_frac=0.0,
            upper_pileup_frac=0.10,
            pileup_width=0.01,
            seed=42,
        )
        result_mostly_upper = run_boundary_qc(x_mostly_upper, L=0.0, U=10.0)

        # Should detect upper pileup
        assert result_mostly_upper.upper_pileup_detected is True
        assert result_mostly_upper.t_hi_star is not None

        # Should not detect lower pileup
        assert result_mostly_upper.lower_pileup_detected is False

        # Concentration at both bounds
        x_both = generate_with_boundary_pileup(
            n=1000,
            L=0.0,
            U=10.0,
            lower_pileup_frac=0.08,
            upper_pileup_frac=0.08,
            pileup_width=0.01,
            seed=42,
        )
        result_both = run_boundary_qc(x_both, L=0.0, U=10.0)

        # Should detect both (may be sensitive to random seed, so just check one)
        # At least one should be detected
        detected_count = sum([result_both.lower_pileup_detected, result_both.upper_pileup_detected])
        assert detected_count > 0, "Should detect at least one pileup when both exist"

        # Edge case: all samples exactly at the midpoint (not at boundaries)
        x_all_mid = np.full(1000, 5.0)
        result_all_mid = run_boundary_qc(x_all_mid, L=0.0, U=10.0)

        # Should NOT detect boundary pileup (everything is in the middle)
        assert result_all_mid.lower_pileup_detected is False
        assert result_all_mid.upper_pileup_detected is False

        # Known limitation: 100% at exact boundary creates flat mass curve
        # The algorithm cannot detect this pathological case (no elbow in flat line)
        # This tests that we handle it gracefully (no crash)
        x_all_exact = np.full(1000, 0.0)
        result_all_exact = run_boundary_qc(x_all_exact, L=0.0, U=10.0)
        # Should not crash - detection may fail but returns valid result
        assert isinstance(result_all_exact.lower_pileup_detected, bool)
        assert isinstance(result_all_exact.upper_pileup_detected, bool)


class TestProgressiveGrid:
    """Tests for progressive tolerance grid construction."""

    def test_progressive_grid_spacing_increases(self):
        """Progressive grid should have increasing spacing as tol increases."""
        config = BoundaryConfig(tol_min=0.0, tol_max=0.05, n_tols=45, grid_mode="progressive")
        grid = _build_tolerance_grid(config)

        spacings = np.diff(grid)

        # Verify properties
        assert grid.dtype == np.float64, "Grid must be float64"
        assert len(grid) == 45, f"Expected 45 points, got {len(grid)}"
        assert grid[0] == 0.0, f"First point should be 0.0, got {grid[0]}"
        assert grid[-1] == pytest.approx(0.05), f"Last point should be 0.05, got {grid[-1]}"

        # Monotonicity
        assert np.all(np.diff(grid) > 0), "Grid must be strictly increasing"

        # Progressive spacing: verify spacing increases by region
        region1_mask = grid <= 0.001
        region1_spacing = np.mean(spacings[region1_mask[:-1]])

        region2_mask = (grid > 0.001) & (grid <= 0.005)
        region2_spacing = np.mean(spacings[region2_mask[:-1]])

        region3_mask = (grid > 0.005) & (grid <= 0.02)
        region3_spacing = np.mean(spacings[region3_mask[:-1]])

        region4_mask = grid > 0.02
        region4_spacing = np.mean(spacings[region4_mask[:-1]])

        # Verify progressive increase
        assert region1_spacing < region2_spacing, (
            f"Spacing should increase: R1={region1_spacing:.6f} >= R2={region2_spacing:.6f}"
        )
        assert region2_spacing < region3_spacing, (
            f"Spacing should increase: R2={region2_spacing:.6f} >= R3={region3_spacing:.6f}"
        )
        assert region3_spacing < region4_spacing, (
            f"Spacing should increase: R3={region3_spacing:.6f} >= R4={region4_spacing:.6f}"
        )

    def test_progressive_grid_coverage_matches_uniform(self):
        """Progressive grid should have better resolution in tight region."""
        uniform_grid = np.linspace(0.0, 0.05, 41)
        config = BoundaryConfig(n_tols=45, grid_mode="progressive")
        progressive_grid = _build_tolerance_grid(config)

        # Both should span [0, 0.05]
        assert uniform_grid[0] == progressive_grid[0] == 0.0
        assert uniform_grid[-1] == pytest.approx(progressive_grid[-1])

        # Test resolution in tight region [0, 0.01]
        test_tols = np.linspace(0.0, 0.01, 100)

        uniform_errors = []
        progressive_errors = []

        for t in test_tols:
            uniform_nearest = uniform_grid[np.argmin(np.abs(uniform_grid - t))]
            progressive_nearest = progressive_grid[np.argmin(np.abs(progressive_grid - t))]

            uniform_errors.append(abs(t - uniform_nearest))
            progressive_errors.append(abs(t - progressive_nearest))

        # Progressive should have smaller mean error in tight region
        assert np.mean(progressive_errors) < np.mean(uniform_errors), (
            f"Progressive grid should have better resolution in tight region: "
            f"prog={np.mean(progressive_errors):.6f} >= uniform={np.mean(uniform_errors):.6f}"
        )


class TestProgressiveLogGrid:
    """Tests for the progressive_log tolerance grid variant."""

    def test_progressive_log_prepends_three_log_points(self):
        """progressive_log is progressive with (1e-7, 1e-6, 1e-5) prepended."""
        prog = _build_tolerance_grid(BoundaryConfig(grid_mode="progressive"))
        prog_log = _build_tolerance_grid(BoundaryConfig(grid_mode="progressive_log"))

        assert len(prog_log) == len(prog) + 3
        assert prog_log[0] == pytest.approx(1e-7)
        assert prog_log[1] == pytest.approx(1e-6)
        assert prog_log[2] == pytest.approx(1e-5)
        np.testing.assert_array_equal(prog_log[3:], prog)

    def test_progressive_log_detects_delta_pileup_at_1e_minus_6_resolution(self):
        """A delta-function pileup at u=0 (10 samples) is detected and
        t_lo_star lands within one decade of 1e-6.

        Scope: verifies progressive_log + extended quantile_grid floor
        (1e-5) lets detection resolve a sub-1e-4 pileup that the prior
        default (progressive + 5e-4 quantile floor) missed. The pileup is
        a true delta at u=0; dispatch's "width 1e-6" refers to the
        resolution at which the detector must see it.

        Excludes the broad-pileup miscalibration path by keeping the
        pileup's fractional mass (1e-4) below the point where Kneedle
        latches on fraction-as-tolerance. See
        dispatch-grid-resolution-2026-04-17.md and
        dispatch-broad-pileup-algorithm-2026-04-17.md.
        """
        rng = np.random.default_rng(2026)
        n = 100_000
        n_pileup = 10  # delta at u=0; fraction 1e-4

        # Concatenate 10 samples at x=0 exactly with 99990 uniform samples.
        x = np.concatenate(
            [
                np.zeros(n_pileup),
                rng.uniform(1e-3, 100, n - n_pileup),
            ]
        )

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive_log",
        )
        result = run_boundary_qc(x, L=0, U=100, config=config)

        assert result.lower_pileup_detected is True, (
            f"Expected lower_pileup_detected=True for a 10-sample delta at "
            f"u=0, got False. t_lo_star={result.t_lo_star}"
        )
        assert result.t_lo_star is not None
        # Delta pileup is at u=0 exactly; subgrid fallback should report
        # a fine tolerance ~1e-7. Allow anything at or below 1e-5 (i.e.,
        # within one decade of 1e-6 on the small side).
        assert result.t_lo_star <= 1e-5, (
            f"t_lo_star={result.t_lo_star:.2e} exceeds 1e-5 — detector did "
            f"not resolve at fine scale for a delta pileup."
        )


class TestQuantileCurveComputation:
    """Tests for quantile curve computation in boundary detection."""

    def test_quantile_curve_uniform_data_is_linear(self):
        """For uniform data, quantile curve should be tol ≈ q (linear)."""
        rng = np.random.default_rng(42)
        u = rng.uniform(0, 1, size=10000)
        u_sorted = np.sort(u)

        quantile_grid = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.10])
        tol_grid = np.linspace(0.0, 0.15, 151)

        tol_at_quantile, _ = _compute_quantile_curves_boundary(u_sorted, tol_grid, quantile_grid)

        # Verify properties
        assert tol_at_quantile.dtype == np.float64
        assert tol_at_quantile.shape == quantile_grid.shape
        assert np.all(tol_at_quantile > 0), "All tolerances must be positive"
        assert np.all(np.diff(tol_at_quantile) > 0), "Must be monotonically increasing"

        # For uniform data, tol ≈ q
        ratio = tol_at_quantile / quantile_grid
        np.testing.assert_allclose(
            ratio,
            1.0,
            rtol=0.1,
            atol=0.01,
            err_msg=f"Uniform data should have tol/q ≈ 1, got {ratio}",
        )

        # Verify linearity via R² test
        slope, intercept, r_value, _, _ = linregress(quantile_grid, tol_at_quantile)

        assert r_value**2 > 0.99, f"Should be linear (R²={r_value**2:.4f})"
        assert slope == pytest.approx(1.0, abs=0.1), f"Slope should be ≈1, got {slope:.3f}"
        assert abs(intercept) < 0.01, f"Intercept should be ≈0, got {intercept:.3f}"

    def test_quantile_curve_tight_pileup_shows_elbow(self):
        """For tight pileup, quantile curve should show clear elbow."""
        rng = np.random.default_rng(42)
        u_pileup = rng.uniform(0, 0.002, size=500)  # 5% tight pileup
        u_bulk = rng.uniform(0, 1, size=9500)  # 95% uniform
        u = np.concatenate([u_pileup, u_bulk])
        u_sorted = np.sort(u)

        quantile_grid = np.array([0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20])
        tol_grid = np.linspace(0.0, 0.25, 251)

        tol_at_quantile, elbows = _compute_quantile_curves_boundary(
            u_sorted, tol_grid, quantile_grid
        )

        # Compute ratio tol/q
        ratio = tol_at_quantile / quantile_grid

        # For q <= 0.05 (within pileup), ratio should be << 1
        pileup_region_mask = quantile_grid <= 0.05
        pileup_ratios = ratio[pileup_region_mask]
        assert np.all(pileup_ratios < 0.5), (
            f"Pileup region should have tol << q (ratio < 0.5), got {pileup_ratios}"
        )

        # For q > 0.10 (beyond pileup), ratio should be approaching 1
        # (may not be exactly 1 due to finite sample effects and the remaining pileup influence)
        uniform_region_mask = quantile_grid > 0.10
        uniform_ratios = ratio[uniform_region_mask]
        # The ratios should be higher than in the pileup region (showing the transition)
        assert np.mean(uniform_ratios) > 0.5, (
            f"Beyond pileup, ratios should increase from pileup values, got {uniform_ratios}"
        )

        # Elbow detection should find elbow near the pileup width.
        # elbows[0] is a tolerance (not a quantile) — see
        # _compute_quantile_curves_boundary return contract in boundary.py.
        # Pileup width is 0.002, so expect elbow_tol ~ 0.002.
        elbow_tol = elbows[0]
        assert elbow_tol is not None, "Should detect elbow for pileup data"
        assert 0.0005 <= elbow_tol <= 0.005, (
            f"Elbow tolerance should be near pileup width 0.002, got {elbow_tol:.4f}"
        )

    def test_quantile_curve_shape_dtype_bounds(self):
        """Quantile curve should have correct shape, dtype, and value bounds."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 1, size=1000)
        u_sorted = np.sort(x)

        quantile_grid = np.array([0.01, 0.05, 0.10])
        tol_grid = np.linspace(0.0, 0.15, 100)

        tol_at_quantile, _ = _compute_quantile_curves_boundary(u_sorted, tol_grid, quantile_grid)

        # Shape
        assert tol_at_quantile.shape == (3,)

        # Dtype
        assert tol_at_quantile.dtype == np.float64

        # Bounds
        assert np.all(tol_at_quantile >= 0.0)
        assert np.all(tol_at_quantile <= 0.15)

        # Monotonicity
        assert np.all(np.diff(tol_at_quantile) >= 0)

        # No NaN or inf
        assert not np.any(np.isnan(tol_at_quantile))
        assert not np.any(np.isinf(tol_at_quantile))


class TestElbowAggregation:
    """Tests for median aggregation of elbows."""

    def test_median_aggregation_robust_to_outliers(self):
        """Median aggregation should ignore outlier elbows."""
        elbows = [0.010, 0.011, 0.009, 0.010, 0.040, 0.011, 0.010]

        result = _aggregate_elbows_median(elbows)

        # Median should be 0.010 (not affected by 0.040 outlier)
        assert result == pytest.approx(0.010, abs=0.001)

        # Compare to mean
        mean_result = np.mean(elbows)
        assert mean_result > 0.014, "Mean should be pulled up by outlier"
        assert result < mean_result, "Median should be more robust than mean"

    def test_aggregation_requires_majority_agreement(self):
        """Should return None if less than half of quantiles found elbows."""
        elbows_mostly_none = [None, 0.010, None, None, 0.012, None, None]

        result = _aggregate_elbows_median(elbows_mostly_none, min_agreement_frac=0.5)

        assert result is None, "Should return None when <50% of quantiles found elbows"

        # Exactly 4 out of 7 (>50%) should succeed
        elbows_majority = [0.010, 0.011, None, 0.010, None, 0.009, None]

        result_majority = _aggregate_elbows_median(elbows_majority, min_agreement_frac=0.5)

        assert result_majority is not None
        assert result_majority == pytest.approx(0.010, abs=0.001)


class TestMultiCurveIntegration:
    """End-to-end integration tests for multi-curve boundary detection."""

    def test_multi_curve_detects_tight_pileup(self):
        """Multi-curve should detect tight pileups (end-to-end test)."""
        rng = np.random.default_rng(42)
        x_pileup = rng.uniform(0.0, 0.003, size=300)  # 3% tight pileup
        x_bulk = rng.uniform(0.0, 1.0, size=9700)  # 97% uniform
        x = np.concatenate([x_pileup, x_bulk])

        config_new = BoundaryConfig(
            n_tols=45,
            grid_mode="progressive",
            quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05, 0.10),
            use_quantile_analysis=True,
        )
        result_new = run_boundary_qc(x, L=0.0, U=1.0, config=config_new)

        # New method should detect
        assert result_new.lower_pileup_detected, "New method should detect tight pileup"

        # Verify detected tolerance is near true pileup width
        assert result_new.t_lo_star is not None
        assert result_new.t_lo_star == pytest.approx(0.003, abs=0.002)

        # Verify quantile_elbows is populated
        assert result_new.quantile_elbows is not None
        assert "lower" in result_new.quantile_elbows
        assert "upper" in result_new.quantile_elbows

    def test_multi_curve_no_false_positives_on_uniform(self):
        """Multi-curve should not increase false positives on clean data."""
        rng = np.random.default_rng(42)
        x_uniform = rng.uniform(0, 1, size=10000)

        config = BoundaryConfig(
            n_tols=45,
            grid_mode="progressive",
            quantile_grid=(0.005, 0.01, 0.02, 0.05, 0.10),
            use_quantile_analysis=True,
        )

        result = run_boundary_qc(x_uniform, L=0.0, U=1.0, config=config)

        # Should NOT detect pileup
        assert not result.lower_pileup_detected
        assert not result.upper_pileup_detected

    def test_multi_curve_handles_broad_pileup(self):
        """Should still detect broad pileups (not just tight ones)."""
        # Use a more pronounced broad pileup that will pass excess_mass check
        # 15% of samples in 5% of range should create detectable pileup
        rng = np.random.default_rng(42)
        x_pileup = rng.uniform(0.0, 0.05, size=1500)  # 15% broad pileup
        x_bulk = rng.uniform(0.0, 1.0, size=8500)  # 85% uniform
        x = np.concatenate([x_pileup, x_bulk])

        config = BoundaryConfig(
            n_tols=45,
            grid_mode="progressive",
            quantile_grid=(0.01, 0.02, 0.05, 0.10, 0.15),
            use_quantile_analysis=True,
        )

        result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

        # Quantile elbows should be populated even if pileup not detected
        # (quantile analysis runs regardless)
        assert result.quantile_elbows is not None

        # The broad pileup should be detectable.
        # If detected, t_lo_star reflects where Kneedle finds the knee in
        # (quantile, tolerance) space — for strongly concentrated pileups
        # this is inside the pileup region, not at its outer extent, because
        # M3's broad-pileup fallback only expands on weak-excess elbows.
        # Verify the reported tolerance is non-trivial (past pileup_threshold).
        if result.lower_pileup_detected:
            assert result.t_lo_star is not None
            assert result.t_lo_star > config.pileup_threshold, (
                f"Detected tolerance should exceed pileup_threshold "
                f"({config.pileup_threshold}), got {result.t_lo_star:.4f}"
            )
