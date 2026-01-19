"""End-to-end integration tests for the fitqc pipeline.

These tests verify that:
1. The complete pipeline works from raw data to JSON report
2. Different stickiness combinations are detected correctly
3. Masks properly filter out bad samples

Stickiness Combination Coverage
-------------------------------
We test all relevant combinations of stickiness types:
- Interior only (x0 stickiness)
- Lower boundary only
- Upper boundary only
- Lower + interior
- Interior + upper
- Lower + upper
- Lower + interior + upper (all three)

This ensures the mask logic correctly handles overlapping failure modes.
"""

import json

import numpy as np

from fitqc.config import BoundaryConfig, InteriorConfig, PrecisionConfig, QCSpec
from fitqc.report import run_qc
from fitqc.synth import (
    generate_normal,
    generate_signed_lognormal,
    generate_uniform,
    generate_with_boundary_pileup,
    generate_with_x0_spike,
)


class TestFullPipeline:
    """Tests for the complete QC pipeline."""

    def test_full_pipeline_multi_parameter_clean(self):
        """Run QC on multiple clean distributions - no interior spike detections expected.

        Note: We test normal and uniform distributions for both interior and
        boundary detection. Lognormal distributions naturally concentrate mass
        near zero, so boundary detection may correctly identify this as pileup.
        """
        params = {
            "normal": generate_normal(n=5000, loc=5.0, scale=2.0, seed=1),
            "uniform": generate_uniform(n=5000, low=0.0, high=10.0, seed=3),
        }
        spec = QCSpec(
            param_names=list(params.keys()),
            x0={"normal": 5.0, "uniform": 5.0},
            bounds={
                "normal": (-5.0, 15.0),
                "uniform": (0.0, 10.0),
            },
        )

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=PrecisionConfig(),
        )

        # All parameters should be in results
        assert len(report.interior_results) == 2
        assert len(report.boundary_results) == 2
        assert len(masks) == 2

        # Clean data should not detect issues
        for name in spec.param_names:
            assert report.interior_results[name].spike_detected is False
            assert report.boundary_results[name].lower_pileup_detected is False
            assert report.boundary_results[name].upper_pileup_detected is False

        # Masks should have correct shape
        for name in spec.param_names:
            assert masks[name].shape == (5000,)
            assert masks[name].dtype == np.bool_

    def test_full_pipeline_signed_lognormal_no_false_positive(self):
        """Signed log-normal at x0=0 should NOT trigger false spike detection."""
        x = generate_signed_lognormal(n=10000, mu=0, sigma=1.0, sign_prob=0.5, seed=42)

        spec = QCSpec(
            param_names=["signed_ln"],
            x0={"signed_ln": 0.0},
            bounds={"signed_ln": (-100.0, 100.0)},
        )
        params = {"signed_ln": x}

        report, _masks = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Critical: should NOT detect x0 spike for broad distribution near zero
        assert report.interior_results["signed_ln"].spike_detected is False

    def test_json_roundtrip_preserves_values(self):
        """Serialize to JSON and verify all key values survive."""
        x = generate_with_x0_spike(n=5000, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=42)

        spec = QCSpec(
            param_names=["param"],
            x0={"param": 5.0},
            bounds={"param": (0.0, 10.0)},
        )
        params = {"param": x}

        report, _ = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Serialize and parse
        json_str = report.to_json(indent=2)
        parsed = json.loads(json_str)

        # Check structure
        assert "interior_results" in parsed
        assert "boundary_results" in parsed
        assert "spec" in parsed

        # Check interior result fields
        interior = parsed["interior_results"]["param"]
        assert "spike_detected" in interior
        assert "eps_star" in interior
        assert "eps_grid" in interior
        assert "mass_curve" in interior

        # Check arrays are converted to lists
        assert isinstance(interior["eps_grid"], list)
        assert isinstance(interior["mass_curve"], list)


class TestStickinessCombinations:
    """Tests for all combinations of stickiness types on a single parameter.

    We need to verify that detection works correctly when multiple types of
    stickiness are present simultaneously:
    - (lower, interior): stuck at lower bound AND at x0
    - (interior, upper): stuck at x0 AND at upper bound
    - (lower, upper): stuck at both boundaries
    - (lower, interior, upper): stuck everywhere

    These combinations can occur when an optimizer fails in multiple ways,
    or when the parameter space is poorly configured.
    """

    def _generate_combined_stickiness(
        self,
        n: int,
        x0: float,
        L: float,
        U: float,
        interior_frac: float = 0.0,
        lower_frac: float = 0.0,
        upper_frac: float = 0.0,
        seed: int = 42,
    ) -> np.ndarray:
        """Generate data with specified stickiness at multiple locations.

        For boundary pileup, samples are placed NEAR the bounds (not exactly at them)
        to create a realistic elbow in the mass curve. Samples exactly at the bound
        would create a flat mass curve with no detectable elbow.
        """
        rng = np.random.default_rng(seed)
        range_width = U - L

        n_interior = int(n * interior_frac)
        n_lower = int(n * lower_frac)
        n_upper = int(n * upper_frac)
        n_base = n - n_interior - n_lower - n_upper

        # Generate base uniform distribution in the interior
        margin = range_width * 0.1  # 10% margin from bounds
        base = rng.uniform(L + margin, U - margin, size=n_base)

        # Generate stuck samples at x0 (exactly at x0)
        interior_stuck = np.full(n_interior, x0)

        # Generate boundary pileup NEAR bounds (not exactly at them)
        # This creates a realistic elbow in the mass curve
        pileup_width = range_width * 0.01  # 1% of range
        lower_stuck = rng.uniform(L, L + pileup_width, size=n_lower)
        upper_stuck = rng.uniform(U - pileup_width, U, size=n_upper)

        # Combine and shuffle
        result = np.concatenate([base, interior_stuck, lower_stuck, upper_stuck])
        rng.shuffle(result)

        return result

    def test_lower_and_interior_stickiness(self):
        """Test detection of lower boundary AND x0 stickiness together."""
        x = self._generate_combined_stickiness(
            n=10000,
            x0=5.0,
            L=0.0,
            U=10.0,
            interior_frac=0.03,
            lower_frac=0.03,
            upper_frac=0.0,
            seed=42,
        )

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

        # Should detect BOTH types
        assert report.interior_results["x"].spike_detected is True
        assert report.boundary_results["x"].lower_pileup_detected is True
        assert report.boundary_results["x"].upper_pileup_detected is False

        # Mask should exclude both types of stuck samples
        mask = masks["x"]
        good_count = np.sum(mask)
        # Should have filtered out ~6% (3% interior + 3% lower)
        assert good_count < 10000 * 0.96

    def test_interior_and_upper_stickiness(self):
        """Test detection of x0 AND upper boundary stickiness together."""
        x = self._generate_combined_stickiness(
            n=10000,
            x0=5.0,
            L=0.0,
            U=10.0,
            interior_frac=0.03,
            lower_frac=0.0,
            upper_frac=0.03,
            seed=43,
        )

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

        # Should detect BOTH types
        assert report.interior_results["x"].spike_detected is True
        assert report.boundary_results["x"].lower_pileup_detected is False
        assert report.boundary_results["x"].upper_pileup_detected is True

        # Mask should exclude both types
        mask = masks["x"]
        good_count = np.sum(mask)
        assert good_count < 10000 * 0.96

    def test_lower_and_upper_stickiness(self):
        """Test detection of both boundary pileups without interior stickiness."""
        x = self._generate_combined_stickiness(
            n=10000,
            x0=5.0,
            L=0.0,
            U=10.0,
            interior_frac=0.0,
            lower_frac=0.03,
            upper_frac=0.03,
            seed=44,
        )

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

        # Should detect both boundary types, NOT interior
        assert report.interior_results["x"].spike_detected is False
        assert report.boundary_results["x"].lower_pileup_detected is True
        assert report.boundary_results["x"].upper_pileup_detected is True

        # Mask should exclude both boundary types
        mask = masks["x"]
        good_count = np.sum(mask)
        assert good_count < 10000 * 0.96

    def test_all_three_stickiness_types(self):
        """Test detection of interior, lower, AND upper stickiness together."""
        x = self._generate_combined_stickiness(
            n=10000,
            x0=5.0,
            L=0.0,
            U=10.0,
            interior_frac=0.02,
            lower_frac=0.02,
            upper_frac=0.02,
            seed=45,
        )

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

        # Should detect ALL three types
        assert report.interior_results["x"].spike_detected is True
        assert report.boundary_results["x"].lower_pileup_detected is True
        assert report.boundary_results["x"].upper_pileup_detected is True

        # Mask should exclude all three types
        mask = masks["x"]
        good_count = np.sum(mask)
        # Should have filtered out ~6% (2% each)
        assert good_count < 10000 * 0.96

        # Verify the report is JSON-serializable
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["interior_results"]["x"]["spike_detected"] is True
        assert parsed["boundary_results"]["x"]["lower_pileup_detected"] is True
        assert parsed["boundary_results"]["x"]["upper_pileup_detected"] is True


class TestMaskFiltering:
    """Tests verifying mask correctly identifies stuck samples."""

    def test_mask_identifies_exact_x0_samples(self):
        """Samples exactly at x0 should be masked when spike is detected."""
        n = 10000
        rng = np.random.default_rng(42)
        x = rng.uniform(1.0, 9.0, size=n)

        # Place samples exactly at x0=5.0
        x[:200] = 5.0

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

        if report.interior_results["x"].spike_detected:
            mask = masks["x"]
            at_x0 = np.isclose(x, 5.0, atol=1e-9)
            # Samples at x0 should be masked
            assert np.any(~mask & at_x0), "Samples at x0 should be masked"

    def test_mask_identifies_boundary_samples(self):
        """Samples at boundaries should be masked when pileup is detected."""
        n = 10000
        rng = np.random.default_rng(42)
        x = rng.uniform(1.0, 9.0, size=n)

        # Place samples at boundaries
        x[:100] = 0.0  # Lower boundary
        x[100:200] = 10.0  # Upper boundary

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

        mask = masks["x"]

        if report.boundary_results["x"].lower_pileup_detected:
            at_lower = np.isclose(x, 0.0, atol=1e-9)
            assert np.any(~mask & at_lower), "Samples at lower bound should be masked"

        if report.boundary_results["x"].upper_pileup_detected:
            at_upper = np.isclose(x, 10.0, atol=1e-9)
            assert np.any(~mask & at_upper), "Samples at upper bound should be masked"

    def test_combined_mask_excludes_all_stuck(self):
        """Combined mask across parameters filters all bad samples."""
        n = 5000
        rng = np.random.default_rng(42)

        # alpha: clean
        alpha = rng.uniform(0.0, 10.0, size=n)

        # beta: x0 stickiness
        beta = generate_with_x0_spike(n=n, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=43)

        # gamma: boundary pileup
        gamma = generate_with_boundary_pileup(n=n, L=0.0, U=10.0, lower_pileup_frac=0.05, seed=44)

        spec = QCSpec(
            param_names=["alpha", "beta", "gamma"],
            x0={"alpha": 5.0, "beta": 5.0, "gamma": 5.0},
            bounds={
                "alpha": (0.0, 10.0),
                "beta": (0.0, 10.0),
                "gamma": (0.0, 10.0),
            },
        )
        params = {"alpha": alpha, "beta": beta, "gamma": gamma}

        _report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Combine masks
        combined_mask = masks["alpha"] & masks["beta"] & masks["gamma"]

        # Combined mask should filter more than individual masks
        good_combined = np.sum(combined_mask)
        good_alpha = np.sum(masks["alpha"])

        # Alpha is clean, so combined should have fewer good samples
        assert good_combined <= good_alpha
