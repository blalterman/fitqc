"""Tests for the report module (QCReport and JSON serialization).

These tests verify that:
1. NumpyEncoder correctly serializes NumPy types to JSON
2. QCReport correctly aggregates results from multiple parameters
3. run_qc provides a convenient high-level API for multi-parameter QC
"""

import json

import numpy as np

from fitqc.boundary import BoundaryResult
from fitqc.config import BoundaryConfig, InteriorConfig, PrecisionConfig, QCSpec
from fitqc.interior import InteriorResult
from fitqc.report import NumpyEncoder, QCReport, run_qc
from fitqc.synth import generate_uniform, generate_with_boundary_pileup, generate_with_x0_spike


class TestNumpyEncoder:
    """Tests for the NumpyEncoder JSON encoder."""

    def test_encodes_ndarray_to_list(self):
        """NumPy arrays should serialize to JSON lists."""
        arr = np.array([1.0, 2.0, 3.0])
        result = json.dumps(arr, cls=NumpyEncoder)
        assert result == "[1.0, 2.0, 3.0]"

    def test_encodes_numpy_float(self):
        """NumPy floating types should serialize to Python floats."""
        val = np.float64(3.14159)
        result = json.dumps({"value": val}, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["value"] == 3.14159
        assert isinstance(parsed["value"], float)

    def test_encodes_numpy_int(self):
        """NumPy integer types should serialize to Python ints."""
        val = np.int64(42)
        result = json.dumps({"value": val}, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["value"] == 42
        assert isinstance(parsed["value"], int)

    def test_encodes_numpy_bool(self):
        """NumPy bool_ should serialize to Python bool."""
        val = np.bool_(True)
        result = json.dumps({"value": val}, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["value"] is True
        assert isinstance(parsed["value"], bool)

    def test_encodes_nested_structures(self):
        """Encoder should handle nested dicts and lists with NumPy types."""
        data = {
            "array": np.array([1, 2, 3]),
            "float": np.float32(1.5),
            "nested": {"int": np.int32(10)},
        }
        result = json.dumps(data, cls=NumpyEncoder)
        parsed = json.loads(result)
        assert parsed["array"] == [1, 2, 3]
        assert parsed["float"] == 1.5
        assert parsed["nested"]["int"] == 10


class TestQCReport:
    """Tests for the QCReport dataclass."""

    def test_to_dict_returns_dict(self):
        """to_dict should return a dictionary representation."""
        # Create minimal mock results
        interior_result = InteriorResult(
            spike_detected=False,
            spike_z_loc=None,
            eps_star=None,
            eps_grid=np.array([1e-6, 1e-5]),
            mass_curve=np.array([0.0, 0.01]),
            hist_counts=np.array([10.0, 20.0]),
            hist_edges=np.array([0.0, 0.5, 1.0]),
        )
        boundary_result = BoundaryResult(
            lower_pileup_detected=False,
            upper_pileup_detected=False,
            t_lo_star=None,
            t_hi_star=None,
            tol_grid=np.array([0.0, 0.01]),
            lower_mass_curve=np.array([0.0, 0.01]),
            upper_mass_curve=np.array([0.0, 0.01]),
        )
        spec = QCSpec(
            param_names=["alpha"],
            x0={"alpha": 1.0},
            bounds={"alpha": (0.0, 10.0)},
        )
        report = QCReport(
            interior_results={"alpha": interior_result},
            boundary_results={"alpha": boundary_result},
            spec=spec,
        )

        result = report.to_dict()

        assert isinstance(result, dict)
        assert "interior_results" in result
        assert "boundary_results" in result
        assert "spec" in result
        assert "alpha" in result["interior_results"]

    def test_to_json_returns_valid_json(self):
        """to_json should return a valid JSON string."""
        interior_result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.005,
            eps_star=0.001,
            eps_grid=np.array([1e-6, 1e-5]),
            mass_curve=np.array([0.05, 0.06]),
            hist_counts=np.array([100.0, 20.0]),
            hist_edges=np.array([0.0, 0.5, 1.0]),
        )
        boundary_result = BoundaryResult(
            lower_pileup_detected=True,
            upper_pileup_detected=False,
            t_lo_star=0.02,
            t_hi_star=None,
            tol_grid=np.array([0.0, 0.01, 0.02]),
            lower_mass_curve=np.array([0.0, 0.05, 0.08]),
            upper_mass_curve=np.array([0.0, 0.01, 0.02]),
        )
        spec = QCSpec(
            param_names=["beta"],
            x0={"beta": 5.0},
            bounds={"beta": (0.0, 10.0)},
        )
        report = QCReport(
            interior_results={"beta": interior_result},
            boundary_results={"beta": boundary_result},
            spec=spec,
        )

        json_str = report.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        # Check that arrays are converted to lists
        assert isinstance(parsed["interior_results"]["beta"]["eps_grid"], list)

    def test_json_roundtrip(self):
        """Serialize to JSON and parse back, values should match.

        This test verifies that we can serialize a QCReport to JSON and
        recover all the important values. This is critical for:
        - Saving QC results to disk
        - Transmitting results over APIs
        - Generating reports for downstream analysis
        """
        interior_result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.0025,
            eps_star=0.0005,
            eps_grid=np.logspace(-6, -3, 10),
            mass_curve=np.linspace(0.05, 0.1, 10),
            hist_counts=np.array([50.0, 30.0, 20.0, 10.0]),
            hist_edges=np.array([0.0, 0.25, 0.5, 0.75, 1.0]),
        )
        boundary_result = BoundaryResult(
            lower_pileup_detected=True,
            upper_pileup_detected=True,
            t_lo_star=0.015,
            t_hi_star=0.02,
            tol_grid=np.linspace(0.0, 0.05, 10),
            lower_mass_curve=np.linspace(0.0, 0.1, 10),
            upper_mass_curve=np.linspace(0.0, 0.08, 10),
        )
        spec = QCSpec(
            param_names=["gamma"],
            x0={"gamma": 2.5},
            bounds={"gamma": (-5.0, 5.0)},
        )
        original_report = QCReport(
            interior_results={"gamma": interior_result},
            boundary_results={"gamma": boundary_result},
            spec=spec,
        )

        # Roundtrip through JSON
        json_str = original_report.to_json()
        parsed = json.loads(json_str)

        # Check key values survive roundtrip
        assert parsed["interior_results"]["gamma"]["spike_detected"] is True
        assert parsed["interior_results"]["gamma"]["spike_z_loc"] == 0.0025
        assert parsed["interior_results"]["gamma"]["eps_star"] == 0.0005
        assert parsed["boundary_results"]["gamma"]["lower_pileup_detected"] is True
        assert parsed["boundary_results"]["gamma"]["upper_pileup_detected"] is True
        assert parsed["boundary_results"]["gamma"]["t_lo_star"] == 0.015
        assert parsed["boundary_results"]["gamma"]["t_hi_star"] == 0.02
        assert parsed["spec"]["param_names"] == ["gamma"]
        assert parsed["spec"]["x0"]["gamma"] == 2.5
        assert parsed["spec"]["bounds"]["gamma"] == [-5.0, 5.0]

        # Check arrays are preserved as lists with correct values
        assert len(parsed["interior_results"]["gamma"]["eps_grid"]) == 10
        assert len(parsed["boundary_results"]["gamma"]["tol_grid"]) == 10


class TestRunQC:
    """Tests for the run_qc high-level API function."""

    def test_run_qc_single_parameter_clean_data(self):
        """run_qc should work with a single clean parameter."""
        # Generate clean uniform data
        x = generate_uniform(n=5000, low=0.0, high=10.0, seed=42)

        spec = QCSpec(
            param_names=["theta"],
            x0={"theta": 5.0},
            bounds={"theta": (0.0, 10.0)},
        )
        params = {"theta": x}

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=None,
            boundary_config=None,
            precision_config=None,
        )

        # Should have results for theta
        assert "theta" in report.interior_results
        assert "theta" in report.boundary_results
        assert "theta" in masks

        # Clean data should not detect issues
        assert report.interior_results["theta"].spike_detected is False

        # Mask should exist and be mostly True (most samples are "good")
        assert masks["theta"].dtype == np.bool_
        assert len(masks["theta"]) == len(x)

    def test_run_qc_detects_x0_stickiness(self):
        """run_qc should detect x0 stickiness when present."""
        x = generate_with_x0_spike(n=10000, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=42)

        spec = QCSpec(
            param_names=["mu"],
            x0={"mu": 5.0},
            bounds={"mu": (0.0, 10.0)},
        )
        params = {"mu": x}

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=None,
            boundary_config=None,
            precision_config=None,
        )

        # Should detect the x0 spike
        assert report.interior_results["mu"].spike_detected is True
        assert report.interior_results["mu"].eps_star is not None

        # Mask should mark stuck samples as False
        good_count = np.sum(masks["mu"])
        # Should have filtered out roughly the spike fraction
        assert good_count < len(x)

    def test_run_qc_detects_boundary_pileup(self):
        """run_qc should detect boundary pileup when present."""
        x = generate_with_boundary_pileup(n=10000, L=0.0, U=10.0, lower_pileup_frac=0.05, seed=42)

        spec = QCSpec(
            param_names=["sigma"],
            x0={"sigma": 5.0},
            bounds={"sigma": (0.0, 10.0)},
        )
        params = {"sigma": x}

        report, _masks = run_qc(
            params=params,
            spec=spec,
            interior_config=None,
            boundary_config=None,
            precision_config=None,
        )

        # Should detect lower boundary pileup
        assert report.boundary_results["sigma"].lower_pileup_detected is True

    def test_full_pipeline_multi_parameter(self):
        """End-to-end test with multiple parameters.

        This test simulates a realistic scenario where we have multiple
        fitted parameters, some with QC issues and some clean:
        - alpha: Clean uniform data (no issues)
        - beta: Has x0 stickiness (5% stuck at initial guess)
        - gamma: Has lower boundary pileup (5% stuck at lower bound)

        This verifies that run_qc correctly handles the multi-parameter
        case and produces sensible masks for filtering bad samples.
        """
        rng = np.random.default_rng(42)
        n_samples = 10000

        # alpha: Clean uniform
        alpha = rng.uniform(0.0, 10.0, size=n_samples)

        # beta: x0 stickiness at 5.0
        beta = generate_with_x0_spike(n=n_samples, x0=5.0, L=0.0, U=10.0, spike_frac=0.05, seed=43)

        # gamma: Lower boundary pileup
        gamma = generate_with_boundary_pileup(
            n=n_samples, L=0.0, U=10.0, lower_pileup_frac=0.05, seed=44
        )

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

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=InteriorConfig(),
            boundary_config=BoundaryConfig(),
            precision_config=None,
        )

        # Verify report structure
        assert len(report.interior_results) == 3
        assert len(report.boundary_results) == 3
        assert len(masks) == 3

        # alpha should be clean
        assert report.interior_results["alpha"].spike_detected is False

        # beta should have x0 stickiness
        assert report.interior_results["beta"].spike_detected is True

        # gamma should have boundary pileup
        assert report.boundary_results["gamma"].lower_pileup_detected is True

        # Masks should have correct lengths
        for name in spec.param_names:
            assert len(masks[name]) == n_samples
            assert masks[name].dtype == np.bool_

        # Report should be serializable to JSON
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert "alpha" in parsed["interior_results"]
        assert "beta" in parsed["interior_results"]
        assert "gamma" in parsed["interior_results"]

    def test_run_qc_with_custom_configs(self):
        """run_qc should accept and use custom configs."""
        x = generate_uniform(n=1000, low=0.0, high=10.0, seed=42)

        spec = QCSpec(
            param_names=["param"],
            x0={"param": 5.0},
            bounds={"param": (0.0, 10.0)},
        )
        params = {"param": x}

        # Use custom configs with different parameters
        interior_config = InteriorConfig(n_bins=50, n_eps=25)
        boundary_config = BoundaryConfig(n_tols=21)
        precision_config = PrecisionConfig(precision_mode="float64")

        report, _masks = run_qc(
            params=params,
            spec=spec,
            interior_config=interior_config,
            boundary_config=boundary_config,
            precision_config=precision_config,
        )

        # Should have used custom interior config (check n_eps)
        assert len(report.interior_results["param"].eps_grid) == 25
        # Should have used custom boundary config (check n_tols)
        assert len(report.boundary_results["param"].tol_grid) == 21

    def test_run_qc_mask_excludes_bad_samples(self):
        """Masks should correctly identify samples to exclude.

        The mask should be False for samples that are:
        1. Stuck at x0 (if x0 stickiness detected)
        2. Stuck at lower boundary (if lower pileup detected)
        3. Stuck at upper boundary (if upper pileup detected)
        """
        # Create data with known bad samples
        n = 10000
        rng = np.random.default_rng(42)
        x = rng.uniform(1.0, 9.0, size=n)  # Base uniform in interior

        # Inject samples exactly at x0
        x[:200] = 5.0  # 2% at x0

        # Inject samples at lower boundary
        x[200:400] = 0.0  # 2% at L

        # Inject samples at upper boundary
        x[400:600] = 10.0  # 2% at U

        spec = QCSpec(
            param_names=["x"],
            x0={"x": 5.0},
            bounds={"x": (0.0, 10.0)},
        )
        params = {"x": x}

        report, masks = run_qc(
            params=params,
            spec=spec,
            interior_config=None,
            boundary_config=None,
            precision_config=None,
        )

        # The mask should exclude bad samples
        mask = masks["x"]
        good_count = np.sum(mask)

        # Should have filtered some samples
        assert good_count < n, "Mask should exclude some bad samples"

        # Specifically, samples at x0=5.0 should be masked if spike detected
        if report.interior_results["x"].spike_detected:
            at_x0 = np.isclose(x, 5.0, atol=1e-9)
            # At least some of the x0 samples should be masked
            assert np.any(~mask & at_x0), "Samples at x0 should be masked"
