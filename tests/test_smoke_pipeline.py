"""Multi-distribution smoke tests for the fitqc pipeline.

These tests verify that the QC pipeline produces sensible results across
a variety of common distribution types encountered in scientific fitting:

1. Normal distribution
2. Log-normal distribution (positive-only parameters)
3. Signed log-normal (can be positive or negative)
4. Uniform distribution
5. Beta-like distributions (bounded parameters)

Purpose
-------
Smoke tests answer: "Does the pipeline run without crashing and produce
reasonable output for typical scientific data?"

They are NOT testing:
- Specific detection thresholds (those are in unit tests)
- Edge cases (those are in integration tests)
- JSON serialization (that's in test_report.py)

These tests complement the unit tests by ensuring the algorithms
work on realistic distributions, not just synthetic test cases.
"""

import numpy as np
import pytest

from fitqc.config import BoundaryConfig, InteriorConfig, QCSpec
from fitqc.report import run_qc
from fitqc.synth import (
    generate_lognormal,
    generate_normal,
    generate_signed_lognormal,
    generate_uniform,
)


class TestDistributionSmoke:
    """Smoke tests for various distribution types."""

    @pytest.mark.parametrize(
        "distribution,gen_func,gen_kwargs,x0,bounds",
        [
            # Normal: standard parameters
            (
                "normal_standard",
                generate_normal,
                {"n": 5000, "loc": 0.0, "scale": 1.0, "seed": 1},
                0.0,
                (-10.0, 10.0),
            ),
            # Normal: shifted and scaled
            (
                "normal_shifted",
                generate_normal,
                {"n": 5000, "loc": 50.0, "scale": 10.0, "seed": 2},
                50.0,
                (0.0, 100.0),
            ),
            # Uniform: flat prior
            (
                "uniform_standard",
                generate_uniform,
                {"n": 5000, "low": 0.0, "high": 1.0, "seed": 5},
                0.5,
                (0.0, 1.0),
            ),
            # Signed log-normal: symmetric around zero
            (
                "signed_lognormal_symmetric",
                generate_signed_lognormal,
                {"n": 5000, "mu": 0.0, "sigma": 1.0, "sign_prob": 0.5, "seed": 6},
                0.0,
                (-100.0, 100.0),
            ),
            # Signed log-normal: asymmetric
            (
                "signed_lognormal_asymmetric",
                generate_signed_lognormal,
                {"n": 5000, "mu": 0.0, "sigma": 1.0, "sign_prob": 0.7, "seed": 7},
                0.0,
                (-100.0, 100.0),
            ),
        ],
    )
    def test_distribution_no_false_positive(self, distribution, gen_func, gen_kwargs, x0, bounds):
        """Clean distribution should not trigger false positive detection."""
        x = gen_func(**gen_kwargs)

        spec = QCSpec(
            param_names=["param"],
            x0={"param": x0},
            bounds={"param": bounds},
        )

        report, masks = run_qc(
            params={"param": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Should NOT detect false positives for interior spike
        assert report.interior_results["param"].spike_detected is False, (
            f"False positive spike for {distribution}"
        )

        # Mask should keep most samples
        mask = masks["param"]
        good_fraction = np.mean(mask)
        assert good_fraction > 0.95, f"Mask filtered too many samples for {distribution}"

    @pytest.mark.parametrize(
        "distribution,gen_func,gen_kwargs,x0,bounds",
        [
            # Log-normal distributions naturally concentrate mass near zero,
            # which boundary detection may correctly identify. We only test
            # that interior detection doesn't produce false positives.
            (
                "lognormal_rate",
                generate_lognormal,
                {"n": 5000, "mean": 0.0, "sigma": 0.5, "seed": 3},
                1.0,
                (0.0, 100.0),
            ),
            (
                "lognormal_wide",
                generate_lognormal,
                {"n": 5000, "mean": 0.0, "sigma": 1.5, "seed": 4},
                1.0,
                (0.0, 10000.0),
            ),
        ],
    )
    def test_lognormal_no_false_spike(self, distribution, gen_func, gen_kwargs, x0, bounds):
        """Log-normal distributions should NOT trigger false interior spike detection.

        Note: Log-normal distributions naturally concentrate mass near zero,
        which boundary detection may correctly identify as pileup. We only
        verify that interior (x0 stickiness) detection doesn't false positive.
        """
        x = gen_func(**gen_kwargs)

        spec = QCSpec(
            param_names=["param"],
            x0={"param": x0},
            bounds={"param": bounds},
        )

        report, _masks = run_qc(
            params={"param": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Should NOT detect false interior spike
        assert report.interior_results["param"].spike_detected is False, (
            f"False positive interior spike for {distribution}"
        )

    def test_multi_distribution_simultaneous(self):
        """Run QC on multiple distributions simultaneously."""
        n = 5000
        params = {
            "normal": generate_normal(n=n, loc=5.0, scale=2.0, seed=10),
            "lognormal": generate_lognormal(n=n, mean=0.5, sigma=0.5, seed=11),
            "signed_ln": generate_signed_lognormal(n=n, mu=0.0, sigma=1.0, seed=12),
            "uniform": generate_uniform(n=n, low=0.0, high=10.0, seed=13),
        }

        spec = QCSpec(
            param_names=list(params.keys()),
            x0={
                "normal": 5.0,
                "lognormal": 1.5,
                "signed_ln": 0.0,
                "uniform": 5.0,
            },
            bounds={
                "normal": (-10.0, 20.0),
                "lognormal": (0.0, 100.0),  # Lower bound at 0 for lognormal
                "signed_ln": (-100.0, 100.0),
                "uniform": (0.0, 10.0),
            },
        )

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # All parameters should have results
        for name in spec.param_names:
            assert name in report.interior_results
            assert name in report.boundary_results
            assert name in masks

        # No false positives
        for name in spec.param_names:
            assert report.interior_results[name].spike_detected is False

    def test_small_sample_size(self):
        """Pipeline should work with small sample sizes (edge case)."""
        n = 500  # Small sample
        x = generate_uniform(n=n, low=0.0, high=10.0, seed=20)

        spec = QCSpec(
            param_names=["x"],
            x0={"x": 5.0},
            bounds={"x": (0.0, 10.0)},
        )

        # Should not raise
        report, masks = run_qc(
            params={"x": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        assert "x" in report.interior_results
        assert masks["x"].shape == (n,)

    def test_large_sample_size(self):
        """Pipeline should handle large sample sizes efficiently."""
        n = 100000  # Large sample
        x = generate_uniform(n=n, low=0.0, high=10.0, seed=30)

        spec = QCSpec(
            param_names=["x"],
            x0={"x": 5.0},
            bounds={"x": (0.0, 10.0)},
        )

        report, masks = run_qc(
            params={"x": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        assert "x" in report.interior_results
        assert masks["x"].shape == (n,)

    def test_narrow_bounds(self):
        """Pipeline handles very narrow parameter bounds."""
        n = 5000
        x = generate_uniform(n=n, low=4.99, high=5.01, seed=40)

        spec = QCSpec(
            param_names=["x"],
            x0={"x": 5.0},
            bounds={"x": (4.99, 5.01)},
        )

        # Should not raise
        report, _masks = run_qc(
            params={"x": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        assert "x" in report.interior_results

    def test_wide_bounds(self):
        """Pipeline handles very wide parameter bounds."""
        n = 5000
        x = generate_normal(n=n, loc=0.0, scale=1.0, seed=50)

        spec = QCSpec(
            param_names=["x"],
            x0={"x": 0.0},
            bounds={"x": (-1e6, 1e6)},
        )

        report, _masks = run_qc(
            params={"x": x},
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        assert "x" in report.interior_results
        # Clean normal data should not trigger false positive
        assert report.interior_results["x"].spike_detected is False
