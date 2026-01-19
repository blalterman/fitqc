"""Tests for the boundary module."""

import numpy as np

from fitqc.config import BoundaryConfig
from fitqc.stickiness import compute_u, run_boundary_qc


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

    def test_boundary_qc_asymmetric_upper_only(self):
        """Test asymmetric detection with pileup ONLY at upper boundary.

        This test mirrors test_boundary_qc_asymmetric_tolerances but for the upper
        bound. While the u-transform is mathematically symmetric, this test serves
        as documentation that upper-only pileup is explicitly tested and works.

        Why this test exists (tests as documentation):
        - A scientist reading these tests should see both lower-only and upper-only
        - Confirms the algorithm treats both boundaries identically
        - Catches any bugs in upper boundary detection that might not affect lower
        """
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 10, size=10000)
        x[:500] = rng.uniform(9.9, 10.0, size=500)  # Only upper pileup

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Upper should be detected, lower should not (or be much smaller)
        assert result.upper_pileup_detected is True
        # Lower tolerance should be smaller than upper
        if result.t_lo_star and result.t_hi_star:
            assert result.t_hi_star > result.t_lo_star * 2

    def test_boundary_qc_no_false_positive_normal(self):
        """Test that normal distribution does NOT trigger false pileup detection.

        Why this test exists:
        - Normal distributions naturally have less mass at tails than uniform
        - A centered normal should have even LESS mass near bounds than uniform
        - This documents that we've verified normal data doesn't false-positive

        Scenario: Parameters drawn from N(5, 2) with bounds [0, 10].
        Most mass is in the center; very little near 0 or 10.
        """
        rng = np.random.default_rng(42)
        # Normal centered at 5 with std=2, clipped to bounds
        x = rng.normal(5.0, 2.0, size=10000)
        x = np.clip(x, 0.0, 10.0)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Normal data should NOT detect significant pileup at either boundary
        # (the clipping might create tiny artifacts, but not significant ones)
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01, "False positive at lower boundary for normal data"
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01, "False positive at upper boundary for normal data"

    def test_boundary_qc_no_false_positive_lognormal(self):
        """Test that log-normal distribution does NOT trigger false pileup detection.

        Why this test exists:
        - Log-normal is heavily skewed right, with natural mass near zero
        - This is a CRITICAL edge case: the distribution naturally has density
          near the lower bound, but it's the TAIL of the distribution, not pileup
        - We must NOT flag this as boundary stickiness

        Scenario: Parameters drawn from LogNormal(1, 0.5) mapped to [0, 10].
        The log-normal has support (0, inf), so we scale it to fit our bounds.
        """
        rng = np.random.default_rng(42)
        # Generate log-normal data
        raw = rng.lognormal(1.0, 0.5, size=10000)
        # Scale to [0, 10] range (using percentiles to avoid outlier issues)
        p01, p99 = np.percentile(raw, [1, 99])
        x = (raw - p01) / (p99 - p01) * 10
        x = np.clip(x, 0.0, 10.0)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Log-normal should NOT trigger pileup detection
        # Even though it has mass near zero, it's the natural distribution shape
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.015, "False positive at lower boundary for log-normal data"
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.015, "False positive at upper boundary for log-normal data"

    def test_boundary_qc_detects_pileup_with_normal_base(self):
        """Test pileup detection works when base distribution is normal.

        Why this test exists:
        - Most tests use uniform base distribution
        - Real data is often approximately normal
        - This documents that detection works regardless of base distribution

        Scenario: Normal(5, 2) base with 5% artificially stuck at lower bound.
        """
        rng = np.random.default_rng(42)
        x = rng.normal(5.0, 2.0, size=10000)
        x = np.clip(x, 0.0, 10.0)
        # Inject 5% pileup at lower boundary
        x[:500] = rng.uniform(0, 0.1, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.005

    def test_boundary_qc_detects_pileup_with_lognormal_base(self):
        """Test pileup detection works when base distribution is log-normal.

        Why this test exists:
        - Log-normal already has natural mass near zero (lower bound)
        - We need to verify we can STILL detect artificial pileup on top of this
        - The pileup should be distinguishable from the natural tail

        Scenario: Log-normal base with 5% additional artificial pileup at lower bound.
        The challenge: can we detect the artificial spike above the natural density?
        """
        rng = np.random.default_rng(42)
        # Generate log-normal base
        raw = rng.lognormal(1.0, 0.5, size=10000)
        p01, p99 = np.percentile(raw, [1, 99])
        x = (raw - p01) / (p99 - p01) * 10
        x = np.clip(x, 0.0, 10.0)
        # Inject 5% VERY tight pileup at lower boundary (tighter than natural tail)
        x[:500] = rng.uniform(0, 0.05, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Should detect the artificial pileup even with log-normal base
        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None

    def test_boundary_qc_detects_upper_pileup_with_normal_base(self):
        """Test UPPER pileup detection works when base distribution is normal.

        Why this test exists (tests as documentation):
        - Completes the matrix: we test lower AND upper for each distribution
        - Normal distributions have thin tails, so upper pileup should be easy to detect
        - Documents that detection is symmetric regardless of base distribution

        Scenario: Normal(5, 2) base with 5% artificially stuck at upper bound.
        """
        rng = np.random.default_rng(42)
        x = rng.normal(5.0, 2.0, size=10000)
        x = np.clip(x, 0.0, 10.0)
        # Inject 5% pileup at upper boundary
        x[:500] = rng.uniform(9.9, 10.0, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        assert result.upper_pileup_detected is True
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.005

    def test_boundary_qc_detects_upper_pileup_with_lognormal_base(self):
        """Test UPPER pileup detection works when base distribution is log-normal.

        Why this test exists (tests as documentation):
        - Log-normal is right-skewed, so it naturally has LESS mass near upper bound
        - This makes upper pileup particularly easy to detect (stands out more)
        - Completes the test matrix for all distribution x boundary combinations

        Scenario: Log-normal base with 5% artificially stuck at upper bound.
        """
        rng = np.random.default_rng(42)
        # Generate log-normal base
        raw = rng.lognormal(1.0, 0.5, size=10000)
        p01, p99 = np.percentile(raw, [1, 99])
        x = (raw - p01) / (p99 - p01) * 10
        x = np.clip(x, 0.0, 10.0)
        # Inject 5% pileup at upper boundary
        x[:500] = rng.uniform(9.9, 10.0, size=500)

        result = run_boundary_qc(x, L=0.0, U=10.0, config=BoundaryConfig())

        # Should detect upper pileup easily (log-normal has thin upper tail)
        assert result.upper_pileup_detected is True
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.005

    def test_boundary_qc_no_false_positive_signed_lognormal(self):
        """Test that signed log-normal does NOT trigger false boundary pileup.

        Why this test exists (critical edge case):
        - Signed log-normal naturally concentrates mass near ZERO (not at bounds)
        - With bounds like [-100, 100], the mass near 0 is INTERIOR, not boundary
        - The distribution has very thin tails at the actual bounds (far from 0)
        - We must NOT confuse the natural mass near 0 with boundary pileup

        This is different from regular log-normal:
        - Regular log-normal: mass near 0 IS near the lower bound (since L >= 0)
        - Signed log-normal: mass near 0 is far from both bounds [-100, 100]

        Scenario: Signed log-normal with bounds [-100, 100].
        Most mass is near 0; very little near -100 or +100.
        """
        from fitqc.synth import generate_signed_lognormal

        x = generate_signed_lognormal(n=10000, mu=0, sigma=1, sign_prob=0.5, seed=42)

        result = run_boundary_qc(x, L=-100.0, U=100.0, config=BoundaryConfig())

        # Signed log-normal should NOT detect boundary pileup
        # The natural mass is near 0, which is interior, not at bounds
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01, "False positive at lower boundary for signed log-normal"
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01, "False positive at upper boundary for signed log-normal"

    def test_boundary_qc_detects_lower_pileup_with_signed_lognormal_base(self):
        """Test pileup detection at LOWER bound with signed log-normal base.

        Why this test exists:
        - Signed log-normal has very thin tails at the actual bounds
        - Artificial pileup at L=-100 should be easy to detect (stands out)
        - Confirms detection works even with this unusual distribution shape

        Scenario: Signed log-normal base with 5% pileup at L=-100.
        """
        from fitqc.synth import generate_signed_lognormal

        x = generate_signed_lognormal(n=10000, mu=0, sigma=1, sign_prob=0.5, seed=42)
        # Inject 5% pileup at lower boundary (near L=-100)
        x[:500] = np.random.default_rng(42).uniform(-100, -99, size=500)

        result = run_boundary_qc(x, L=-100.0, U=100.0, config=BoundaryConfig())

        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.003

    def test_boundary_qc_detects_upper_pileup_with_signed_lognormal_base(self):
        """Test pileup detection at UPPER bound with signed log-normal base.

        Why this test exists:
        - Mirrors lower bound test for completeness
        - Signed log-normal is symmetric around 0, so upper should behave like lower
        - Documents that both boundaries work with this edge-case distribution

        Scenario: Signed log-normal base with 5% pileup at U=+100.
        """
        from fitqc.synth import generate_signed_lognormal

        x = generate_signed_lognormal(n=10000, mu=0, sigma=1, sign_prob=0.5, seed=42)
        # Inject 5% pileup at upper boundary (near U=+100)
        x[:500] = np.random.default_rng(42).uniform(99, 100, size=500)

        result = run_boundary_qc(x, L=-100.0, U=100.0, config=BoundaryConfig())

        assert result.upper_pileup_detected is True
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.003
