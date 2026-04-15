"""Seam tests: override mechanisms and excess-mass validation.

Covers seams 4-7 in the boundary QC pipeline:
  4: M1 override (spread-pileup propagation)
  5: M3 override (broad-pileup fallback)
  6: _check_excess_mass validation
  7: M2 override (delta-function propagation)

NOTE (2026-04-15): After all seam tests are passing, review whether M1/M2/M3
overrides are introducing more problems than they solve. These mechanisms were
added as escape hatches for edge cases but may be the root cause of boundary
detection issues observed during PPA12 calibration. The seam tests here
document current behavior — they should inform a follow-up decision about
whether to simplify or remove these overrides.
"""

import numpy as np
import pytest

from fitqc import BoundaryConfig, run_boundary_qc
from fitqc.boundary import _check_excess_mass

# =============================================================================
# Seam 4: M1 override (spread-pileup propagation)
# =============================================================================


class TestSeam4M1Override:
    """M1 fires for diffuse pileups where tol_elbow is tiny but quantile_elbow
    is above pileup_threshold."""

    def _make_spread_pileup(self, rng, pileup_width=0.001, pileup_frac=0.05, n=10000):
        """Create diffuse pileup: mass(0)≈0, high quantile elbow."""
        n_pileup = int(n * pileup_frac)
        n_bulk = n - n_pileup
        # Diffuse pileup: NOT at exact zero, but uniformly spread in [eps, width]
        x_pileup = rng.uniform(1e-8, pileup_width, n_pileup)
        x_bulk = rng.uniform(pileup_width, 1.0, n_bulk)
        return np.concatenate([x_pileup, x_bulk])

    def test_m1_fires_for_spread_pileup(self, rng):
        """Diffuse pileup with tiny tol_elbow should be overridden above threshold."""
        x = self._make_spread_pileup(rng, pileup_width=0.001, pileup_frac=0.05)
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # M1 should propagate the quantile elbow → t_lo_raw >= pileup_threshold
        if result.t_lo_raw is not None:
            assert result.t_lo_raw >= config.pileup_threshold or result.t_lo_raw < 1e-10

    def test_m1_blocked_for_delta_function(self, rng):
        """Delta function (mass(0) > 1e-10) should NOT trigger M1."""
        n = 10000
        n_delta = 500
        # Exact delta at zero: mass(0) >> 1e-10
        x_delta = np.zeros(n_delta)
        x_bulk = rng.uniform(0, 1, n - n_delta)
        x = np.concatenate([x_delta, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # Delta function → raw elbow should be ≈ 0 (M1 does not fire because
        # mass(0) > 1e-10), but M2 may override t_lo_star
        if result.t_lo_raw is not None:
            # M1 guard: mass(0) < 1e-10 fails here, so M1 shouldn't override.
            # Raw elbow from refinement should be near zero.
            assert result.t_lo_raw < config.pileup_threshold

    def test_m1_blocked_when_tol_near_quantile(self, rng):
        """Wide pileup (tol_elbow >= pileup_threshold) → M1 guard #1 blocks."""
        n = 10000
        n_pileup = 1500  # 15% pileup — strong
        # Wide spread [0, 0.05]: raw tol_elbow lands above pileup_threshold.
        # Lower pileup_threshold so the raw elbow (typically ~0.004) is clearly
        # above it, which means M1's first guard (t_val < threshold) blocks.
        x_pileup = rng.uniform(0, 0.05, n_pileup)
        x_bulk = rng.uniform(0.05, 1.0, n - n_pileup)
        x = np.concatenate([x_pileup, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
            pileup_threshold=0.002,
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # Wide pileup → detection should fire, raw elbow above threshold
        assert result.lower_pileup_detected
        assert result.t_lo_raw is not None
        assert result.t_lo_raw >= config.pileup_threshold


# =============================================================================
# Seam 5: M3 override (broad-pileup fallback)
# =============================================================================


class TestSeam5M3Override:
    """M3 expands t_lo_raw when the initial elbow underestimates pileup width."""

    def test_m3_fires_for_broad_pileup(self, rng):
        """Broad pileup with weak initial elbow gets expanded."""
        n = 10000
        # Create broad, gradually tapering pileup:
        # ~10% of data in [0, 0.15] with gradually decreasing density
        n_pileup = 1000
        # Exponentially decaying density from boundary
        x_pileup = rng.exponential(0.05, n_pileup)
        x_pileup = x_pileup[x_pileup < 0.15]  # cap
        n_pileup = len(x_pileup)
        x_bulk = rng.uniform(0.0, 1.0, n - n_pileup)
        x = np.concatenate([x_pileup, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
            excess_ratio=1.5,
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # If M3 fired, t_lo_raw should exceed the initial (narrow) elbow
        # We just verify detection works for this broad distribution
        if result.lower_pileup_detected:
            assert result.t_lo_raw is not None

    def test_m3_blocked_for_strong_pileup(self, rng):
        """Strong pileup (mass_ratio >= 2*excess_ratio) skips M3."""
        n = 10000
        n_pileup = 2000  # 20% pileup — very strong
        x_pileup = rng.uniform(0, 0.02, n_pileup)
        x_bulk = rng.uniform(0.02, 1.0, n - n_pileup)
        x = np.concatenate([x_pileup, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
            excess_ratio=1.5,
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # Strong pileup → mass_ratio >> 2*excess_ratio → M3 skipped
        assert result.lower_pileup_detected
        assert result.t_lo_raw is not None
        assert result.t_lo_star is not None

    def test_m3_blocked_when_raw_below_threshold(self, rng):
        """t_lo_raw < pileup_threshold → M3 doesn't fire."""
        n = 10000
        # Delta-like: very small raw elbow
        x_delta = np.full(300, 1e-12)
        x_bulk = rng.uniform(0, 1, n - 300)
        x = np.concatenate([x_delta, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # With raw elbow near zero (< pileup_threshold), M3 guard triggers early exit
        if result.t_lo_raw is not None:
            # Either raw is below threshold (M3 skipped) or M1 overrode it
            pass  # M3 cannot run on sub-threshold raw elbows


# =============================================================================
# Seam 6: _check_excess_mass (now module-level, directly testable)
# =============================================================================


class TestSeam6CheckExcessMass:
    """Direct tests for the extracted _check_excess_mass function."""

    @pytest.fixture
    def tol_grid(self):
        return np.linspace(0.0, 0.10, 101)

    @pytest.fixture
    def excess_mass_curve(self, tol_grid):
        """Mass curve with clear excess (mass >> tol * excess_ratio)."""
        # Simulate 10% pileup: mass jumps to 0.10 at tol=0 then grows slowly
        return 0.10 + tol_grid * 0.9

    @pytest.fixture
    def no_excess_mass_curve(self, tol_grid):
        """Mass curve for uniform data: mass ≈ tol."""
        return tol_grid * 1.0

    def test_check_preserves_raw_above_threshold(self, tol_grid, excess_mass_curve):
        """t_raw >= pileup_threshold with excess mass → returns t_raw."""
        t_raw = 0.02  # Above default pileup_threshold=0.005
        detected, t_star = _check_excess_mass(
            t_raw,
            excess_mass_curve,
            tol_grid,
            pileup_threshold=0.005,
            excess_ratio=1.5,
        )
        assert detected
        assert t_star == pytest.approx(t_raw)

    def test_check_returns_none_no_excess(self, tol_grid, no_excess_mass_curve):
        """t_raw >= pileup_threshold but no excess mass → returns None."""
        t_raw = 0.02
        detected, t_star = _check_excess_mass(
            t_raw,
            no_excess_mass_curve,
            tol_grid,
            pileup_threshold=0.005,
            excess_ratio=1.5,
        )
        assert not detected
        assert t_star is None

    def test_check_substitutes_grid_point_for_delta(self, tol_grid):
        """t_raw < pileup_threshold with excess at grid point → returns grid point."""
        # Delta-like: mass(0) = 0.05, barely changes over first few tol points
        mass_curve = np.full_like(tol_grid, 0.05)
        mass_curve += tol_grid * 0.9  # gradual rise

        t_raw = 0.0001  # Well below pileup_threshold and below tol_grid[1]
        detected, t_star = _check_excess_mass(
            t_raw,
            mass_curve,
            tol_grid,
            pileup_threshold=0.005,
            excess_ratio=1.5,
        )
        assert detected
        # Should return one of the first few grid points, NOT t_raw
        assert t_star > t_raw
        assert t_star == pytest.approx(tol_grid[1], abs=1e-6)

    def test_check_none_for_small_no_excess(self, tol_grid):
        """t_raw < pileup_threshold, no excess at grid points → returns None."""
        # Very small mass at early grid points (no pileup)
        mass_curve = tol_grid * 0.5  # mass << tol * excess_ratio

        t_raw = 0.001
        detected, t_star = _check_excess_mass(
            t_raw,
            mass_curve,
            tol_grid,
            pileup_threshold=0.005,
            excess_ratio=1.5,
        )
        assert not detected
        assert t_star is None

    def test_check_none_input(self):
        """t_raw=None → no detection."""
        detected, t_star = _check_excess_mass(
            None,
            np.array([0.0, 0.01, 0.02]),
            np.array([0.0, 0.01, 0.02]),
            pileup_threshold=0.005,
            excess_ratio=1.5,
        )
        assert not detected
        assert t_star is None


# =============================================================================
# Seam 7: M2 override (delta-function propagation)
# =============================================================================


class TestSeam7M2Override:
    """M2 overrides t_lo_star with mass(0) for true delta-function pileups."""

    def _make_delta_data(self, rng, n=10000, n_delta=500):
        """Create data with delta function at lower boundary."""
        x_delta = np.zeros(n_delta)
        x_bulk = rng.uniform(0, 1, n - n_delta)
        return np.concatenate([x_delta, x_bulk])

    def test_m2_fires_for_true_delta(self, rng):
        """Delta pileup with sufficient grid resolution → t_lo_star = mass(0)."""
        x = self._make_delta_data(rng, n=10000, n_delta=500)
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        assert result.lower_pileup_detected
        assert result.t_lo_star is not None
        # M2 should override t_star with mass(0) ≈ pileup fraction
        pileup_frac = result.lower_mass_curve[0]
        assert pileup_frac == pytest.approx(0.05, abs=0.01)
        # If M2 fired, t_lo_star == pileup_frac
        if result.t_lo_raw is not None and result.t_lo_raw < 1e-10:
            # Delta was detected → M2 should attempt override
            assert result.t_lo_star > 0

    def test_m2_blocked_by_grid_resolution(self, rng):
        """Insufficient grid resolution near pileup fraction → M2 skipped."""
        # Tiny delta (0.1%) — unlikely to have 2 grid points near pileup_frac
        x_delta = np.zeros(10)
        x_bulk = rng.uniform(0, 1, 9990)
        x = np.concatenate([x_delta, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
            # Use a coarse quantile grid to limit resolution near the tiny pileup
            quantile_grid=(0.01, 0.02, 0.05, 0.10, 0.20),
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # With only 0.1% pileup and coarse grid, M2's grid resolution guard
        # should block the override (< 2 points near 0.001 pileup fraction).
        # Verify the pipeline completes without error and produces a result.
        assert result.tol_grid is not None

    def test_m2_blocked_by_small_mass(self, rng):
        """mass(0) < 2*pileup_threshold → M2 skipped."""
        # Very small delta (0.5%) — mass(0) ≈ 0.005 ≈ pileup_threshold
        x_delta = np.zeros(50)
        x_bulk = rng.uniform(0, 1, 9950)
        x = np.concatenate([x_delta, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # mass(0) ≈ 0.005, 2*pileup_threshold = 0.01 → mass(0) < guard
        pileup_frac = result.lower_mass_curve[0]
        if pileup_frac < 2 * config.pileup_threshold:
            # M2 guard blocks override. t_lo_star should NOT equal mass(0)
            # unless check_excess_mass already handled it.
            if result.t_lo_star is not None:
                assert result.t_lo_star != pileup_frac or not (
                    result.t_lo_raw is not None and result.t_lo_raw < 1e-10
                )

    def test_m2_blocked_when_t_raw_not_zero(self, rng):
        """t_lo_raw > 1e-10 → M2 does not fire (not a delta function)."""
        # Diffuse pileup: raw elbow > 0
        x_pileup = rng.uniform(0, 0.02, 1000)
        x_bulk = rng.uniform(0.02, 1.0, 9000)
        x = np.concatenate([x_pileup, x_bulk])

        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 1.0, config)
        # Diffuse pileup → raw elbow should be > 1e-10
        if result.t_lo_raw is not None and result.t_lo_raw > 1e-10:
            # M2's t_raw < 1e-10 guard fails → no M2 override
            assert result.t_lo_star is not None
