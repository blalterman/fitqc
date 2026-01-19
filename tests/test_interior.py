"""Tests for the interior module (x0 stickiness detection)."""

import numpy as np

from fitqc.config import InteriorConfig
from fitqc.interior import InteriorResult, compute_z, run_interior_qc
from fitqc.synth import generate_signed_lognormal


class TestComputeZ:
    """Tests for the compute_z function."""

    def test_compute_z_at_x0(self):
        """Values at x0 should have z=0."""
        x = np.array([5.0, 5.0, 5.0])
        z = compute_z(x, x0=5.0, L=0.0, U=10.0)
        np.testing.assert_array_equal(z, [0.0, 0.0, 0.0])

    def test_compute_z_at_bounds(self):
        """Values at bounds should have z = |x - x0| / max(x0 - L, U - x0)."""
        x = np.array([0.0, 10.0])
        z = compute_z(x, x0=5.0, L=0.0, U=10.0)
        # |0 - 5| / max(5 - 0, 10 - 5) = 5 / 5 = 1.0
        # |10 - 5| / max(5 - 0, 10 - 5) = 5 / 5 = 1.0
        np.testing.assert_array_equal(z, [1.0, 1.0])

    def test_compute_z_asymmetric_bounds(self):
        """Test z computation with asymmetric bounds."""
        # x0 = 2, L = 0, U = 10, so max(2-0, 10-2) = 8
        x = np.array([0.0, 2.0, 10.0])
        z = compute_z(x, x0=2.0, L=0.0, U=10.0)
        # |0 - 2| / 8 = 0.25
        # |2 - 2| / 8 = 0.0
        # |10 - 2| / 8 = 1.0
        np.testing.assert_array_almost_equal(z, [0.25, 0.0, 1.0])


class TestRunInteriorQC:
    """Tests for the run_interior_qc function."""

    def test_interior_qc_detects_spike(self):
        """Test that run_interior_qc detects an artificial spike at x0."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        spike_idx = rng.choice(10000, size=500, replace=False)
        x[spike_idx] = 5.0  # 5% exactly at x0

        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=InteriorConfig())

        assert result.spike_detected is True
        assert result.spike_z_loc is not None
        assert result.spike_z_loc < 0.01  # spike near z=0
        assert result.eps_star is not None
        assert result.eps_star < 0.01

    def test_interior_qc_no_false_positive_uniform(self):
        """Uniform distribution should not trigger false positive."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)

        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=InteriorConfig())

        assert result.spike_detected is False

    def test_interior_qc_signed_lognormal_no_false_spike(self):
        """Critical: signed log-normal with x0 approx 0 should NOT trigger false spike.

        Signed log-normal naturally has mass near zero, but it's BROAD, not a spike.
        The width criterion should prevent false positives.
        """
        x = generate_signed_lognormal(n=10000, mu=0, sigma=1, sign_prob=0.5, seed=42)

        result = run_interior_qc(x, x0=0.0, L=-100.0, U=100.0, config=InteriorConfig())

        assert result.spike_detected is False

    def test_interior_result_structure(self):
        """Test that InteriorResult has the expected fields."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=1000)

        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0)

        # Verify result structure
        assert isinstance(result, InteriorResult)
        assert isinstance(result.spike_detected, bool)
        assert isinstance(result.eps_grid, np.ndarray)
        assert isinstance(result.mass_curve, np.ndarray)
        assert isinstance(result.hist_counts, np.ndarray)
        assert isinstance(result.hist_edges, np.ndarray)

        # Verify array shapes are consistent
        assert len(result.eps_grid) == len(result.mass_curve)
        assert len(result.hist_edges) == len(result.hist_counts) + 1

    def test_interior_qc_with_default_config(self):
        """Test that run_interior_qc works with default config (None)."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=1000)

        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=None)

        assert isinstance(result, InteriorResult)
        assert result.spike_detected is False
