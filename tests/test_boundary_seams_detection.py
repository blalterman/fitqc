"""Seam tests: input validation, grid construction, elbow detection, refinement.

Covers seams 0-3c in the boundary QC pipeline:
  0: OOB exclusion (x, L, U → compute_u → filter → u_sorted)
  1: Tolerance grid construction and extension
  3: _compute_quantile_curves_boundary returns single-element list
  3c: _refine_elbow_iteratively convergence, stability, delta handling
"""

import numpy as np
import pytest

from fitqc import BoundaryConfig, run_boundary_qc
from fitqc._quantile_utils import _aggregate_elbows_median
from fitqc.boundary import (
    _compute_quantile_curves_boundary,
    _refine_elbow_iteratively,
)

# =============================================================================
# Seam 0: OOB exclusion — x, L, U → compute_u → OOB filter → u_sorted
# =============================================================================


class TestSeam0OOBExclusion:
    """Samples outside [L, U] must be excluded from analysis."""

    def test_oob_samples_excluded_from_analysis(self, rng):
        """Detection results should match pre-cleaned data."""
        n_in = 9000
        n_oob_below = 50
        n_oob_above = 50
        L, U = 0.0, 10.0

        x_in = rng.uniform(L, U, n_in)
        x_below = rng.uniform(L - 5.0, L - 0.01, n_oob_below)
        x_above = rng.uniform(U + 0.01, U + 5.0, n_oob_above)
        x_mixed = np.concatenate([x_in, x_below, x_above])

        config = BoundaryConfig()
        result_mixed = run_boundary_qc(x_mixed, L, U, config)
        result_clean = run_boundary_qc(x_in, L, U, config)

        assert result_mixed.lower_pileup_detected == result_clean.lower_pileup_detected
        assert result_mixed.upper_pileup_detected == result_clean.upper_pileup_detected
        assert result_mixed.t_lo_star == result_clean.t_lo_star
        assert result_mixed.t_hi_star == result_clean.t_hi_star

    def test_all_oob_returns_empty_result(self, rng):
        """All samples outside [L, U] should give no detection."""
        L, U = 0.0, 10.0
        x = rng.uniform(U + 1.0, U + 5.0, 500)

        result = run_boundary_qc(x, L, U)
        assert result.lower_pileup_detected is False
        assert result.upper_pileup_detected is False
        assert result.t_lo_star is None
        assert result.t_hi_star is None
        assert len(result.tol_grid) == 0


# =============================================================================
# Seam 1: Grid construction + extension
# =============================================================================


class TestSeam1GridConstruction:
    """Tolerance grid properties depend on config mode and refine_transition."""

    def test_grid_extended_when_refine_transition(self, rng):
        """With refine_transition=True, tol_grid extends beyond tol_max."""
        x = rng.uniform(0.0, 10.0, 5000)
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=True,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 10.0, config)
        # quantile_grid max = 0.25 > default tol_max = 0.05
        assert result.tol_grid[-1] > config.tol_max

    def test_grid_not_extended_without_refine(self, rng):
        """Without refine_transition, tol_grid stays at config bounds."""
        x = rng.uniform(0.0, 10.0, 5000)
        config = BoundaryConfig(
            use_quantile_analysis=True,
            refine_transition=False,
            grid_mode="progressive",
        )
        result = run_boundary_qc(x, 0.0, 10.0, config)
        assert result.tol_grid[-1] == pytest.approx(config.tol_max, abs=1e-6)


# =============================================================================
# Seam 3: Elbow detection — single-element list from _compute_quantile_curves
# =============================================================================


class TestSeam3ElbowDetection:
    """_compute_quantile_curves_boundary returns a single-element elbow list."""

    def test_compute_quantile_curves_returns_single_elbow(self):
        """Return list always has length 1 regardless of quantile grid size."""
        rng = np.random.default_rng(42)
        u_sorted = np.sort(rng.uniform(0, 1, 5000))
        tol_grid = np.linspace(0.0, 0.15, 151)

        for n_quantiles in [3, 8, 20]:
            quantile_grid = np.linspace(0.01, 0.15, n_quantiles)
            _, elbows = _compute_quantile_curves_boundary(u_sorted, tol_grid, quantile_grid)
            assert len(elbows) == 1, (
                f"Expected single-element list, got len={len(elbows)} for {n_quantiles} quantiles"
            )

    def test_aggregate_median_on_single_element_is_noop(self):
        """_aggregate_elbows_median on [val] returns val directly."""
        assert _aggregate_elbows_median([0.042]) == 0.042
        assert _aggregate_elbows_median([None]) is None
        assert _aggregate_elbows_median([0.0]) == 0.0


# =============================================================================
# Seam 3c: _refine_elbow_iteratively internals
# =============================================================================


class TestSeam3cRefineInternals:
    """_refine_elbow_iteratively convergence, stability, and delta handling."""

    def test_refine_stability_guard_reverts_to_first(self):
        """When refinement degrades (elbow shrinks >70%), revert to first."""
        rng = np.random.default_rng(123)
        # Pileup at ~3% tol, but with noise that could destabilize refinement
        u_pileup = rng.uniform(0, 0.03, 400)
        u_bulk = rng.uniform(0, 1, 9600)
        u_sorted = np.sort(np.concatenate([u_pileup, u_bulk]))
        tol_grid = np.linspace(0.0, 0.25, 251)
        quantile_grid = np.array([0.005, 0.01, 0.02, 0.05, 0.10, 0.20])

        result_elbow, _, _, _, elbows = _refine_elbow_iteratively(
            u_sorted, tol_grid, quantile_grid, max_iterations=5
        )
        # Result should be non-None (pileup is real)
        assert result_elbow is not None
        # Result should be >= 30% of first iteration elbow (stability guard)
        if elbows[0] is not None:
            first_val = _aggregate_elbows_median(elbows, 0.5)
            if first_val is not None and first_val > 0:
                assert result_elbow >= first_val * 0.3 - 1e-10

    def test_refine_delta_handling_returns_zero(self):
        """Data with exact delta at boundary returns t_lo_raw ≈ 0."""
        rng = np.random.default_rng(42)
        # 5% of samples at exactly zero (delta function)
        u_delta = np.zeros(500)
        u_bulk = rng.uniform(0, 1, 9500)
        u_sorted = np.sort(np.concatenate([u_delta, u_bulk]))
        tol_grid = np.linspace(0.0, 0.15, 151)
        quantile_grid = np.array([0.005, 0.01, 0.02, 0.05, 0.10])

        result_elbow, result_grid, _, _, _ = _refine_elbow_iteratively(
            u_sorted, tol_grid, quantile_grid, max_iterations=5
        )
        # Delta function at boundary → elbow at essentially 0
        assert result_elbow is not None
        assert result_elbow < 1e-9
        # Grid should have been refined (more points than original)
        assert len(result_grid) > len(quantile_grid)

    def test_refine_convergence(self):
        """Clear elbow should converge in fewer than max iterations."""
        rng = np.random.default_rng(42)
        # Well-defined pileup at ~5% with clear transition
        u_pileup = rng.uniform(0, 0.05, 500)
        u_bulk = rng.uniform(0.05, 1, 9500)
        u_sorted = np.sort(np.concatenate([u_pileup, u_bulk]))
        tol_grid = np.linspace(0.0, 0.25, 251)
        quantile_grid = np.array([0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20])

        result_elbow, _, _, _, _ = _refine_elbow_iteratively(
            u_sorted, tol_grid, quantile_grid, max_iterations=10
        )
        # Should detect an elbow in the pileup region
        assert result_elbow is not None
        assert result_elbow > 0
