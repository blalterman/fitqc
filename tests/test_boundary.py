"""Tests for the boundary module."""

import numpy as np

from fitqc.boundary import compute_u, run_boundary_qc
from fitqc.config import BoundaryConfig


class TestComputeU:
    """Tests for the compute_u function."""

    def test_compute_u_at_bounds(self):
        """Test that u=0 at L, u=1 at U, u=0.5 at midpoint."""
        x = np.array([0.0, 5.0, 10.0])
        u = compute_u(x, L=0.0, U=10.0)
        np.testing.assert_array_equal(u, [0.0, 0.5, 1.0])

    def test_compute_u_outside_bounds(self):
        """Test u values outside [0, 1] for values outside [L, U]."""
        x = np.array([-5.0, 15.0])
        u = compute_u(x, L=0.0, U=10.0)
        np.testing.assert_array_equal(u, [-0.5, 1.5])

    def test_compute_u_different_scale(self):
        """Test u computation with different scale parameters."""
        x = np.array([100.0, 150.0, 200.0])
        u = compute_u(x, L=100.0, U=200.0)
        np.testing.assert_array_equal(u, [0.0, 0.5, 1.0])


class TestBoundaryQC:
    """Tests for the run_boundary_qc function."""

    def test_boundary_qc_detects_lower_pileup(self):
        """Test detection of pileup at lower boundary."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        x[:500] = rng.uniform(0, 0.1, size=500)  # 5% near lower

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.005
        assert result.lower_pileup_detected is True

    def test_boundary_qc_detects_upper_pileup(self):
        """Test detection of pileup at upper boundary."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        x[:500] = rng.uniform(9.9, 10.0, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.005
        assert result.upper_pileup_detected is True

    def test_boundary_qc_no_pileup_uniform(self):
        """Test that uniform data does not detect significant pileup."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # For uniform data, tolerances should be small or None
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01

    def test_boundary_qc_asymmetric_tolerances(self):
        """Test asymmetric detection with pileup at only one boundary."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        x[:500] = rng.uniform(0, 0.1, size=500)  # Only lower pileup

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Lower should be detected, upper should not (or be much smaller)
        assert result.lower_pileup_detected is True
        # Upper tolerance should be smaller than lower
        if result.t_lo_star and result.t_hi_star:
            assert result.t_lo_star > result.t_hi_star * 2

    def test_boundary_qc_detects_both_boundaries(self):
        """Test detection when pileup exists at BOTH boundaries simultaneously.

        This is a realistic scenario: constrained optimization where some fits
        hit the lower bound and others hit the upper bound (e.g., a parameter
        that should be in [0, 1] but the true value is outside that range).
        """
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        # Add 5% pileup at lower bound
        x[:500] = rng.uniform(0, 0.1, size=500)
        # Add 5% pileup at upper bound
        x[500:1000] = rng.uniform(9.9, 10.0, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Both boundaries should be detected
        assert result.lower_pileup_detected is True
        assert result.upper_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_hi_star is not None
        # Both tolerances should be significant
        assert result.t_lo_star > 0.005
        assert result.t_hi_star > 0.005

    def test_boundary_qc_returns_correct_grid_shapes(self):
        """Test that result arrays have expected shapes."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=1000)
        config = BoundaryConfig(n_tols=41)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=config)

        assert result.tol_grid.shape == (41,)
        assert result.lower_mass_curve.shape == (41,)
        assert result.upper_mass_curve.shape == (41,)

    def test_boundary_qc_mass_curves_increasing(self):
        """Test that mass curves are monotonically increasing."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=1000)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Mass curves should be monotonically increasing
        assert np.all(np.diff(result.lower_mass_curve) >= 0)
        assert np.all(np.diff(result.upper_mass_curve) >= 0)

    def test_boundary_qc_default_config(self):
        """Test that run_boundary_qc works with default config."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=1000)

        # Should not raise with config=None
        result = run_boundary_qc(x, L=0.0, U=10.0, config=None)

        assert result is not None
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)
