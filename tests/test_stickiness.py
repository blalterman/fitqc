"""Tests for the stickiness module (unified stickiness detection API).

This module tests detect_stickiness(), the primary API for detecting optimizer
stickiness at reference points (x0, L, U).
"""

import inspect

import numpy as np
import pytest

from fitqc.boundary import BoundaryResult, run_boundary_qc
from fitqc.config import BoundaryConfig, InteriorConfig
from fitqc.interior import InteriorResult, run_interior_qc

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rng():
    """Seeded random number generator for reproducibility."""
    return np.random.default_rng(42)


@pytest.fixture
def uniform_data(rng):
    """Uniform data in [0, 10] with no stickiness."""
    return rng.uniform(0, 10, size=1000)


@pytest.fixture
def data_with_x0_spike(rng):
    """Data with 5% spike at x0=5.0."""
    x = rng.uniform(0, 10, size=10000)
    spike_idx = rng.choice(10000, size=500, replace=False)
    x[spike_idx] = 5.0
    return x


@pytest.fixture
def data_with_lower_pileup(rng):
    """Data with 5% pileup at lower boundary."""
    x = rng.uniform(0, 10, size=10000)
    x[:500] = rng.uniform(0, 0.1, size=500)
    return x


@pytest.fixture
def data_with_upper_pileup(rng):
    """Data with 5% pileup at upper boundary."""
    x = rng.uniform(0, 10, size=10000)
    x[:500] = rng.uniform(9.9, 10.0, size=500)
    return x


# =============================================================================
# 1. Module Structure Tests
# =============================================================================


class TestModuleStructure:
    """Tests for module importability and function signature."""

    def test_importable_from_fitqc(self):
        """detect_stickiness should be importable from fitqc package."""
        from fitqc import detect_stickiness

        assert callable(detect_stickiness)
        assert detect_stickiness.__name__ == "detect_stickiness"

    def test_importable_from_module(self):
        """detect_stickiness should be importable from fitqc.stickiness."""
        from fitqc.stickiness import detect_stickiness

        assert callable(detect_stickiness)
        assert detect_stickiness.__name__ == "detect_stickiness"

    def test_signature_matches_spec(self):
        """Document and verify the detect_stickiness API contract.

        API Contract
        ------------
        Required parameters:
            x: NDArray[np.floating] - fitted parameter values from optimization
            ref: float - reference point (x0 for interior, bound value for boundary)
            L: float | None - lower bound of parameter range
            U: float | None - upper bound of parameter range

        Optional parameters with defaults:
            mode: Literal["interior", "lower", "upper", "all"] = "all"
                Which stickiness checks to perform
            scale: float | Literal["std", "iqr", "range"] | None = None
                Normalization scale for unbounded parameters
            interior_config: InteriorConfig | None = None
                Configuration for interior detection
            boundary_config: BoundaryConfig | None = None
                Configuration for boundary detection
        """
        from fitqc.stickiness import detect_stickiness

        sig = inspect.signature(detect_stickiness)
        params = list(sig.parameters.keys())

        # Required parameters
        assert "x" in params
        assert "ref" in params
        assert "L" in params
        assert "U" in params

        # Optional parameters with defaults
        assert "mode" in params
        assert sig.parameters["mode"].default == "all"

        assert "scale" in params
        assert sig.parameters["scale"].default is None

        assert "interior_config" in params
        assert sig.parameters["interior_config"].default is None

        assert "boundary_config" in params
        assert sig.parameters["boundary_config"].default is None


# =============================================================================
# 2. Mode Dispatch Tests
# =============================================================================


class TestModeDispatch:
    """Tests for correct return types based on mode."""

    def test_mode_interior_returns_interior_result(self, uniform_data):
        """mode='interior' should return InteriorResult."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert isinstance(result.spike_detected, bool)
        assert isinstance(result.eps_grid, np.ndarray)
        assert result.eps_grid.dtype == np.float64
        assert len(result.eps_grid) == len(result.mass_curve)

    def test_mode_lower_returns_boundary_result(self, uniform_data):
        """mode='lower' should return BoundaryResult."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="lower")

        assert isinstance(result, BoundaryResult)
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)

    def test_mode_upper_returns_boundary_result(self, uniform_data):
        """mode='upper' should return BoundaryResult."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="upper")

        assert isinstance(result, BoundaryResult)
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)

    def test_mode_all_returns_tuple(self, uniform_data):
        """mode='all' should return tuple of (InteriorResult, BoundaryResult)."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], InteriorResult)
        assert isinstance(result[1], BoundaryResult)

    def test_mode_boundary_returns_boundary_result(self, uniform_data):
        """mode='boundary' should return BoundaryResult."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        assert isinstance(result, BoundaryResult)
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)


# =============================================================================
# 3. Boundary Mode Field Nulling Tests
# =============================================================================


class TestBoundaryModeFieldNulling:
    """Tests for correct field nulling in lower/upper modes."""

    def test_lower_mode_nulls_upper_fields(self, uniform_data):
        """mode='lower' should null all upper-related fields."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="lower")

        # Upper fields must be nulled
        assert result.upper_pileup_detected is False
        assert result.t_hi_star is None
        assert result.upper_mass_curve is None

    def test_lower_mode_preserves_lower_fields(self, uniform_data):
        """mode='lower' should preserve all lower-related fields."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="lower")

        # Lower fields must be populated
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.shape[0] > 0
        assert isinstance(result.lower_mass_curve, np.ndarray)
        np.testing.assert_array_equal(result.tol_grid.shape, result.lower_mass_curve.shape)
        # Mass curve should be monotonically increasing
        assert np.all(np.diff(result.lower_mass_curve) >= 0)

    def test_upper_mode_nulls_lower_fields(self, uniform_data):
        """mode='upper' should null all lower-related fields."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="upper")

        # Lower fields must be nulled
        assert result.lower_pileup_detected is False
        assert result.t_lo_star is None
        assert result.lower_mass_curve is None

    def test_upper_mode_preserves_upper_fields(self, uniform_data):
        """mode='upper' should preserve all upper-related fields."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="upper")

        # Upper fields must be populated
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.shape[0] > 0
        assert isinstance(result.upper_mass_curve, np.ndarray)
        np.testing.assert_array_equal(result.tol_grid.shape, result.upper_mass_curve.shape)
        # Mass curve should be monotonically increasing
        assert np.all(np.diff(result.upper_mass_curve) >= 0)


# =============================================================================
# 4. All Mode Structure Tests
# =============================================================================


class TestAllModeStructure:
    """Tests for mode='all' tuple structure and content."""

    def test_all_mode_tuple_length(self, uniform_data):
        """mode='all' should return exactly 2 elements."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        assert len(result) == 2

    def test_all_mode_tuple_types(self, uniform_data):
        """mode='all' tuple should contain (InteriorResult, BoundaryResult)."""
        from fitqc.stickiness import detect_stickiness

        interior, boundary = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        assert isinstance(interior, InteriorResult)
        assert isinstance(interior.spike_detected, bool)
        assert isinstance(interior.eps_grid, np.ndarray)

        assert isinstance(boundary, BoundaryResult)
        assert isinstance(boundary.lower_pileup_detected, bool)
        assert isinstance(boundary.upper_pileup_detected, bool)
        assert isinstance(boundary.tol_grid, np.ndarray)

    def test_all_mode_interior_matches_interior_mode(self, uniform_data):
        """Interior result from mode='all' should match mode='interior'."""
        from fitqc.stickiness import detect_stickiness

        interior_direct = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")
        interior_all, _ = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        assert interior_all.spike_detected == interior_direct.spike_detected
        np.testing.assert_array_equal(interior_all.eps_grid, interior_direct.eps_grid)
        np.testing.assert_array_equal(interior_all.mass_curve, interior_direct.mass_curve)
        np.testing.assert_array_equal(interior_all.hist_counts, interior_direct.hist_counts)

    def test_all_mode_boundary_has_both_directions(self, uniform_data):
        """Boundary result from mode='all' should have both lower and upper data."""
        from fitqc.stickiness import detect_stickiness

        _, boundary = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        # Both mass curves should be present and populated
        assert boundary.lower_mass_curve is not None
        assert boundary.upper_mass_curve is not None
        assert isinstance(boundary.lower_mass_curve, np.ndarray)
        assert isinstance(boundary.upper_mass_curve, np.ndarray)
        assert boundary.lower_mass_curve.shape[0] > 0
        assert boundary.upper_mass_curve.shape[0] > 0


# =============================================================================
# 4a. Boundary Mode Structure Tests
# =============================================================================


class TestBoundaryModeStructure:
    """Tests for mode='boundary' structure and content."""

    def test_boundary_mode_has_both_lower_and_upper(self, uniform_data):
        """mode='boundary' should populate both lower and upper fields."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        # Both lower fields must be populated
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.shape[0] > 0
        assert isinstance(result.lower_mass_curve, np.ndarray)
        np.testing.assert_array_equal(result.tol_grid.shape, result.lower_mass_curve.shape)

        # Both upper fields must be populated
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.upper_mass_curve, np.ndarray)
        np.testing.assert_array_equal(result.tol_grid.shape, result.upper_mass_curve.shape)

        # Both mass curves should be monotonically increasing
        assert np.all(np.diff(result.lower_mass_curve) >= 0)
        assert np.all(np.diff(result.upper_mass_curve) >= 0)

    def test_boundary_mode_matches_run_boundary_qc_directly(self, uniform_data):
        """mode='boundary' result should match run_boundary_qc directly."""
        from fitqc.stickiness import detect_stickiness

        wrapper_result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")
        direct_result = run_boundary_qc(uniform_data, L=0.0, U=10.0)

        # Field-by-field equality check
        assert wrapper_result.lower_pileup_detected == direct_result.lower_pileup_detected
        assert wrapper_result.upper_pileup_detected == direct_result.upper_pileup_detected
        assert wrapper_result.t_lo_star == direct_result.t_lo_star
        assert wrapper_result.t_hi_star == direct_result.t_hi_star
        np.testing.assert_array_equal(wrapper_result.tol_grid, direct_result.tol_grid)
        np.testing.assert_array_equal(
            wrapper_result.lower_mass_curve, direct_result.lower_mass_curve
        )
        np.testing.assert_array_equal(
            wrapper_result.upper_mass_curve, direct_result.upper_mass_curve
        )

    def test_boundary_mode_matches_mode_all_boundary_part(self, uniform_data):
        """mode='boundary' should match the boundary part of mode='all'."""
        from fitqc.stickiness import detect_stickiness

        boundary_direct = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")
        _, boundary_from_all = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        # Should produce identical results
        assert boundary_direct.lower_pileup_detected == boundary_from_all.lower_pileup_detected
        assert boundary_direct.upper_pileup_detected == boundary_from_all.upper_pileup_detected
        assert boundary_direct.t_lo_star == boundary_from_all.t_lo_star
        assert boundary_direct.t_hi_star == boundary_from_all.t_hi_star
        np.testing.assert_array_equal(boundary_direct.tol_grid, boundary_from_all.tol_grid)
        np.testing.assert_array_equal(
            boundary_direct.lower_mass_curve, boundary_from_all.lower_mass_curve
        )
        np.testing.assert_array_equal(
            boundary_direct.upper_mass_curve, boundary_from_all.upper_mass_curve
        )


# =============================================================================
# 5. Scale Parameter Tests
# =============================================================================


class TestScaleParameter:
    """Tests for scale parameter behavior."""

    def test_scale_float_works(self, rng):
        """scale=float uses the provided value directly as normalization scale.

        Formula: effective_scale = scale (the provided float value)
        Effective bounds: [ref - scale, ref + scale]

        This allows users to specify an exact scale when they know the
        appropriate normalization for their parameter.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)
        scale_value = 3.0

        result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=scale_value)

        # Should produce valid InteriorResult
        assert isinstance(result, InteriorResult)
        assert isinstance(result.spike_detected, bool)
        assert result.eps_grid.dtype == np.float64

        # Compare with direct call using synthetic bounds
        effective_L = 5.0 - scale_value
        effective_U = 5.0 + scale_value
        direct = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)

        np.testing.assert_array_almost_equal(result.mass_curve, direct.mass_curve)

    def test_scale_int_works(self, rng):
        """scale=int should work the same as scale=float.

        The implementation accepts both int and float for the scale parameter.
        An integer scale is converted to float internally.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)
        scale_int = 3  # int, not float

        result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=scale_int)

        # Should produce valid InteriorResult
        assert isinstance(result, InteriorResult)
        assert result.eps_grid.dtype == np.float64

        # Compare with float version - should be identical
        result_float = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=3.0)
        np.testing.assert_array_equal(result.mass_curve, result_float.mass_curve)

    def test_scale_std_works(self, rng):
        """scale='std' uses standard deviation as normalization scale.

        Formula: effective_scale = np.std(x)
        Effective bounds: [ref - std(x), ref + std(x)]

        Standard deviation is a natural choice when the data spread
        is well-characterized by its variance.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)
        expected_scale = float(np.std(x))

        result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="std")

        assert isinstance(result, InteriorResult)

        # Compare with direct call using std-derived bounds
        effective_L = 5.0 - expected_scale
        effective_U = 5.0 + expected_scale
        direct = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)

        np.testing.assert_array_almost_equal(result.mass_curve, direct.mass_curve)

    def test_scale_iqr_works(self, rng):
        """scale='iqr' uses interquartile range as normalization scale.

        Formula: effective_scale = np.percentile(x, 75) - np.percentile(x, 25)
        Effective bounds: [ref - iqr, ref + iqr]

        IQR is robust to outliers, making it a good choice when the data
        may contain extreme values that shouldn't dominate the scale.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)
        q75, q25 = np.percentile(x, [75, 25])
        expected_scale = float(q75 - q25)

        result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="iqr")

        assert isinstance(result, InteriorResult)

        # Compare with direct call using IQR-derived bounds
        effective_L = 5.0 - expected_scale
        effective_U = 5.0 + expected_scale
        direct = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)

        np.testing.assert_array_almost_equal(result.mass_curve, direct.mass_curve)

    def test_scale_range_works(self, rng):
        """scale='range' uses data range as normalization scale.

        Formula: effective_scale = np.max(x) - np.min(x)
        Effective bounds: [ref - range, ref + range]

        Range captures the full span of observed data, useful when the
        extremes are meaningful rather than outliers.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)
        expected_scale = float(np.max(x) - np.min(x))

        result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="range")

        assert isinstance(result, InteriorResult)

        # Compare with direct call using range-derived bounds
        effective_L = 5.0 - expected_scale
        effective_U = 5.0 + expected_scale
        direct = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)

        np.testing.assert_array_almost_equal(result.mass_curve, direct.mass_curve)

    def test_scale_ignored_when_bounds_complete_warns(self, uniform_data):
        """When both L and U provided, scale is ignored and a warning is issued.

        When bounds are complete, the effective scale is computed from bounds:
            effective_scale = max(ref - L, U - ref)

        Any provided scale parameter is ignored, and a UserWarning is issued
        to alert the user that their scale parameter had no effect.
        """
        import warnings

        from fitqc.stickiness import detect_stickiness

        # Run with scale - should warn that it's ignored
        with pytest.warns(UserWarning, match=r"scale.*ignored.*bounds"):
            result_with_scale = detect_stickiness(
                uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior", scale=1000.0
            )

        # Run without scale - no warning expected
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            result_without_scale = detect_stickiness(
                uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior", scale=None
            )

        # Results should be identical (scale was ignored)
        np.testing.assert_array_equal(result_with_scale.mass_curve, result_without_scale.mass_curve)
        np.testing.assert_array_equal(result_with_scale.eps_grid, result_without_scale.eps_grid)

    def test_invalid_scale_ignored_when_bounds_complete(self, uniform_data):
        """Invalid scale values are ignored (with warning) when bounds are complete.

        When both L and U are provided, the scale parameter is not used.
        Even invalid values like 0.0 or negative numbers should be ignored
        rather than raising an error, since the scale is never actually used.
        """
        from fitqc.stickiness import detect_stickiness

        # scale=0.0 would error if used, but should be ignored when bounds complete
        with pytest.warns(UserWarning, match=r"scale.*ignored.*bounds"):
            result_zero = detect_stickiness(
                uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior", scale=0.0
            )

        # scale=-1.0 would also error if used
        with pytest.warns(UserWarning, match=r"scale.*ignored.*bounds"):
            result_negative = detect_stickiness(
                uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior", scale=-1.0
            )

        # Both should produce valid results identical to no-scale call
        assert isinstance(result_zero, InteriorResult)
        assert isinstance(result_negative, InteriorResult)

        # Compare with no-scale call
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result_none = detect_stickiness(
                uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior", scale=None
            )

        np.testing.assert_array_equal(result_zero.mass_curve, result_none.mass_curve)
        np.testing.assert_array_equal(result_negative.mass_curve, result_none.mass_curve)

    def test_scale_methods_produce_different_results(self, rng):
        """Different scale methods compute different values and produce different results.

        This test verifies that each scale method (std, iqr, range) actually
        computes a different scale value, resulting in different effective bounds
        and therefore different z-distributions. This catches bugs where all methods
        accidentally use the same formula.

        Uses exponential data where std, iqr, and range differ significantly.
        We verify the scale values themselves are different, and that this produces
        different histogram distributions (hist_counts).
        """
        from fitqc.stickiness import detect_stickiness

        # Exponential data has std != iqr != range
        x = rng.exponential(scale=2.0, size=1000)

        # Compute the expected scale values
        scale_std = float(np.std(x))
        q75, q25 = np.percentile(x, [75, 25])
        scale_iqr = float(q75 - q25)
        scale_range = float(np.max(x) - np.min(x))

        # Verify the scale values are actually different
        assert scale_std != pytest.approx(scale_iqr, rel=0.01), (
            f"std ({scale_std}) and iqr ({scale_iqr}) are too similar"
        )
        assert scale_std != pytest.approx(scale_range, rel=0.01), (
            f"std ({scale_std}) and range ({scale_range}) are too similar"
        )
        assert scale_iqr != pytest.approx(scale_range, rel=0.01), (
            f"iqr ({scale_iqr}) and range ({scale_range}) are too similar"
        )

        result_std = detect_stickiness(x, ref=2.0, L=None, U=None, mode="interior", scale="std")
        result_iqr = detect_stickiness(x, ref=2.0, L=None, U=None, mode="interior", scale="iqr")
        result_range = detect_stickiness(x, ref=2.0, L=None, U=None, mode="interior", scale="range")

        # Different scales produce different z-distributions, which show up in histograms
        # (The mass_curve may be all zeros at tiny epsilon values, but hist_counts differ)
        assert not np.allclose(result_std.hist_counts, result_iqr.hist_counts), (
            "std and iqr produced identical histograms - methods may be using same formula"
        )
        assert not np.allclose(result_std.hist_counts, result_range.hist_counts), (
            "std and range produced identical histograms - methods may be using same formula"
        )
        assert not np.allclose(result_iqr.hist_counts, result_range.hist_counts), (
            "iqr and range produced identical histograms - methods may be using same formula"
        )

    def test_scale_required_when_L_none(self, rng):
        """scale is required when L is None for interior mode."""
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)

        with pytest.raises(ValueError, match=r"requires.*scale"):
            detect_stickiness(x, ref=5.0, L=None, U=10.0, mode="interior", scale=None)

    def test_scale_required_when_U_none(self, rng):
        """scale is required when U is None for interior mode."""
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)

        with pytest.raises(ValueError, match=r"requires.*scale"):
            detect_stickiness(x, ref=5.0, L=0.0, U=None, mode="interior", scale=None)

    def test_scale_must_be_positive(self, rng):
        """Numeric scale must be positive."""
        from fitqc.stickiness import detect_stickiness

        x = rng.normal(5.0, 2.0, size=1000)

        with pytest.raises(ValueError, match=r"scale must be positive"):
            detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=-1.0)

        with pytest.raises(ValueError, match=r"scale must be positive"):
            detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale=0.0)


# =============================================================================
# 6. Validation Error Tests
# =============================================================================


class TestValidationErrors:
    """Tests for validation error messages."""

    def test_invalid_mode_raises_valueerror(self, uniform_data):
        """Invalid mode should raise ValueError with helpful message."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"Invalid mode.*'invalid'"):
            detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="invalid")

    def test_invalid_mode_suggests_alternatives(self, uniform_data):
        """Invalid mode error should mention valid alternatives."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"'interior'.*'lower'.*'upper'.*'boundary'.*'all'"):
            detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="invalid_mode")

    def test_lower_mode_requires_L(self, uniform_data):
        """mode='lower' requires L to be specified."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"mode='lower' requires L"):
            detect_stickiness(uniform_data, ref=5.0, L=None, U=10.0, mode="lower")

    def test_upper_mode_requires_U(self, uniform_data):
        """mode='upper' requires U to be specified."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"mode='upper' requires U"):
            detect_stickiness(uniform_data, ref=5.0, L=0.0, U=None, mode="upper")

    def test_boundary_mode_requires_both_L_and_U(self, uniform_data):
        """mode='boundary' requires both L and U to be specified."""
        from fitqc.stickiness import detect_stickiness

        # Missing L
        with pytest.raises(ValueError, match=r"mode='boundary' requires both L and U"):
            detect_stickiness(uniform_data, ref=5.0, L=None, U=10.0, mode="boundary")

        # Missing U
        with pytest.raises(ValueError, match=r"mode='boundary' requires both L and U"):
            detect_stickiness(uniform_data, ref=5.0, L=0.0, U=None, mode="boundary")

        # Missing both
        with pytest.raises(ValueError, match=r"mode='boundary' requires both L and U"):
            detect_stickiness(uniform_data, ref=5.0, L=None, U=None, mode="boundary")

    def test_interior_without_bounds_or_scale_raises(self, uniform_data):
        """mode='interior' without bounds or scale should raise."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"mode='interior' requires"):
            detect_stickiness(uniform_data, ref=5.0, L=None, U=None, mode="interior", scale=None)

    def test_unknown_scale_method_raises(self, uniform_data):
        """Unknown scale method should raise ValueError."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"Unknown scale method.*'invalid'"):
            detect_stickiness(
                uniform_data, ref=5.0, L=None, U=None, mode="interior", scale="invalid"
            )

    def test_unknown_scale_suggests_alternatives(self, uniform_data):
        """Unknown scale error should mention valid methods."""
        from fitqc.stickiness import detect_stickiness

        with pytest.raises(ValueError, match=r"'std'.*'iqr'.*'range'"):
            detect_stickiness(
                uniform_data, ref=5.0, L=None, U=None, mode="interior", scale="variance"
            )


# =============================================================================
# 7. Config Passthrough Tests
# =============================================================================


class TestConfigPassthrough:
    """Tests for configuration passthrough to underlying functions."""

    def test_interior_config_affects_result(self, uniform_data):
        """Custom InteriorConfig should affect interior result."""
        from fitqc.stickiness import detect_stickiness

        # Default config
        result_default = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")

        # Custom config with different n_eps
        custom_config = InteriorConfig(n_eps=100)
        result_custom = detect_stickiness(
            uniform_data,
            ref=5.0,
            L=0.0,
            U=10.0,
            mode="interior",
            interior_config=custom_config,
        )

        # Verify config affected the result
        assert len(result_default.eps_grid) == 50  # default n_eps
        assert len(result_custom.eps_grid) == 100  # custom n_eps
        assert len(result_custom.mass_curve) == 100

    def test_boundary_config_affects_result(self, uniform_data):
        """Custom BoundaryConfig should affect boundary result."""
        from fitqc.stickiness import detect_stickiness

        # Default config
        result_default = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="lower")

        # Custom config with different n_tols
        custom_config = BoundaryConfig(n_tols=100)
        result_custom = detect_stickiness(
            uniform_data,
            ref=5.0,
            L=0.0,
            U=10.0,
            mode="lower",
            boundary_config=custom_config,
        )

        # Verify config affected the result
        assert len(result_default.tol_grid) == 41  # default n_tols
        assert len(result_custom.tol_grid) == 100  # custom n_tols
        assert len(result_custom.lower_mass_curve) == 100

    def test_default_config_when_none(self, uniform_data):
        """None configs should use defaults."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(
            uniform_data,
            ref=5.0,
            L=0.0,
            U=10.0,
            mode="all",
            interior_config=None,
            boundary_config=None,
        )

        interior, boundary = result

        # Should use default InteriorConfig (n_eps=50)
        assert len(interior.eps_grid) == 50
        # Should use default BoundaryConfig (n_tols=41)
        assert len(boundary.tol_grid) == 41

    def test_both_configs_in_all_mode(self, uniform_data):
        """Both configs should be used in mode='all'."""
        from fitqc.stickiness import detect_stickiness

        interior_config = InteriorConfig(n_eps=75)
        boundary_config = BoundaryConfig(n_tols=80)

        interior, boundary = detect_stickiness(
            uniform_data,
            ref=5.0,
            L=0.0,
            U=10.0,
            mode="all",
            interior_config=interior_config,
            boundary_config=boundary_config,
        )

        assert len(interior.eps_grid) == 75
        assert len(boundary.tol_grid) == 80

    def test_boundary_config_affects_boundary_mode(self, uniform_data):
        """Custom BoundaryConfig should affect mode='boundary' result."""
        from fitqc.stickiness import detect_stickiness

        # Default config
        result_default = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        # Custom config with different n_tols
        custom_config = BoundaryConfig(n_tols=100)
        result_custom = detect_stickiness(
            uniform_data,
            ref=5.0,
            L=0.0,
            U=10.0,
            mode="boundary",
            boundary_config=custom_config,
        )

        # Verify config affected the result
        assert len(result_default.tol_grid) == 41  # default n_tols
        assert len(result_custom.tol_grid) == 100  # custom n_tols
        assert len(result_custom.lower_mass_curve) == 100
        assert len(result_custom.upper_mass_curve) == 100


# =============================================================================
# 8. Detection Correctness Tests
# =============================================================================


class TestDetectionCorrectness:
    """Tests for detection accuracy matching direct function calls."""

    def test_interior_detection_matches_direct_call(self, uniform_data):
        """Interior result should match run_interior_qc directly."""
        from fitqc.stickiness import detect_stickiness

        wrapper_result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")
        direct_result = run_interior_qc(uniform_data, x0=5.0, L=0.0, U=10.0)

        assert wrapper_result.spike_detected == direct_result.spike_detected
        assert wrapper_result.spike_z_loc == direct_result.spike_z_loc
        assert wrapper_result.eps_star == direct_result.eps_star
        np.testing.assert_array_equal(wrapper_result.eps_grid, direct_result.eps_grid)
        np.testing.assert_array_equal(wrapper_result.mass_curve, direct_result.mass_curve)
        np.testing.assert_array_equal(wrapper_result.hist_counts, direct_result.hist_counts)
        np.testing.assert_array_equal(wrapper_result.hist_edges, direct_result.hist_edges)

    def test_boundary_detection_matches_direct_call(self, uniform_data):
        """Full boundary result should match run_boundary_qc directly."""
        from fitqc.stickiness import detect_stickiness

        _, wrapper_result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")
        direct_result = run_boundary_qc(uniform_data, L=0.0, U=10.0)

        assert wrapper_result.lower_pileup_detected == direct_result.lower_pileup_detected
        assert wrapper_result.upper_pileup_detected == direct_result.upper_pileup_detected
        assert wrapper_result.t_lo_star == direct_result.t_lo_star
        assert wrapper_result.t_hi_star == direct_result.t_hi_star
        np.testing.assert_array_equal(wrapper_result.tol_grid, direct_result.tol_grid)
        np.testing.assert_array_equal(
            wrapper_result.lower_mass_curve, direct_result.lower_mass_curve
        )
        np.testing.assert_array_equal(
            wrapper_result.upper_mass_curve, direct_result.upper_mass_curve
        )

    def test_detects_spike_at_x0(self, data_with_x0_spike):
        """Should detect spike at x0."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(data_with_x0_spike, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert result.spike_detected is True
        assert result.spike_z_loc is not None
        assert result.spike_z_loc < 0.05  # Near z=0
        assert result.eps_star is not None
        assert result.eps_star < 0.01  # Tight tolerance

    def test_detects_lower_pileup(self, data_with_lower_pileup):
        """Should detect pileup at lower boundary."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(data_with_lower_pileup, ref=5.0, L=0.0, U=10.0, mode="lower")

        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.005

    def test_detects_upper_pileup(self, data_with_upper_pileup):
        """Should detect pileup at upper boundary."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(data_with_upper_pileup, ref=5.0, L=0.0, U=10.0, mode="upper")

        assert result.upper_pileup_detected is True
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.005

    def test_no_false_positive_uniform(self, uniform_data):
        """Uniform data should not trigger false positives."""
        from fitqc.stickiness import detect_stickiness

        interior, boundary = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        assert interior.spike_detected is False
        # Uniform data should not have significant pileup
        if boundary.t_lo_star is not None:
            assert boundary.t_lo_star < 0.01
        if boundary.t_hi_star is not None:
            assert boundary.t_hi_star < 0.01

    def test_boundary_mode_detects_lower_pileup(self, data_with_lower_pileup):
        """mode='boundary' should detect pileup at lower boundary."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(data_with_lower_pileup, ref=5.0, L=0.0, U=10.0, mode="boundary")

        assert result.lower_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_lo_star > 0.005

    def test_boundary_mode_detects_upper_pileup(self, data_with_upper_pileup):
        """mode='boundary' should detect pileup at upper boundary."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(data_with_upper_pileup, ref=5.0, L=0.0, U=10.0, mode="boundary")

        assert result.upper_pileup_detected is True
        assert result.t_hi_star is not None
        assert result.t_hi_star > 0.005

    def test_boundary_mode_detects_both_pileups(self, rng):
        """mode='boundary' should detect pileup at both boundaries simultaneously."""
        from fitqc.stickiness import detect_stickiness

        # Create data with pileup at BOTH boundaries
        x = rng.uniform(0, 10, size=10000)
        # Add 5% pileup at lower bound
        x[:500] = rng.uniform(0, 0.1, size=500)
        # Add 5% pileup at upper bound
        x[500:1000] = rng.uniform(9.9, 10.0, size=500)

        result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="boundary")

        # Both should be detected
        assert result.lower_pileup_detected is True
        assert result.upper_pileup_detected is True
        assert result.t_lo_star is not None
        assert result.t_hi_star is not None
        assert result.t_lo_star > 0.005
        assert result.t_hi_star > 0.005

    def test_boundary_mode_no_false_positive_uniform(self, uniform_data):
        """mode='boundary' should not trigger false positives on uniform data."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        # Uniform data should not have significant pileup
        if result.t_lo_star is not None:
            assert result.t_lo_star < 0.01
        if result.t_hi_star is not None:
            assert result.t_hi_star < 0.01


# =============================================================================
# 9. Array Properties Tests
# =============================================================================


class TestArrayProperties:
    """Tests for array dtype, shape, and value properties."""

    def test_interior_eps_grid_dtype_shape(self, uniform_data):
        """Interior eps_grid should have correct dtype and shape."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert result.eps_grid.dtype == np.float64
        assert result.eps_grid.ndim == 1
        assert result.eps_grid.shape[0] == 50  # default n_eps
        # eps_grid should be monotonically increasing (logspace)
        assert np.all(np.diff(result.eps_grid) > 0)

    def test_interior_mass_curve_dtype_shape(self, uniform_data):
        """Interior mass_curve should have correct dtype and shape."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert result.mass_curve.dtype == np.float64
        assert result.mass_curve.ndim == 1
        assert result.mass_curve.shape == result.eps_grid.shape
        # mass_curve values should be in [0, 1]
        assert np.all(result.mass_curve >= 0)
        assert np.all(result.mass_curve <= 1)
        # mass_curve should be monotonically increasing
        assert np.all(np.diff(result.mass_curve) >= 0)

    def test_boundary_tol_grid_dtype_shape(self, uniform_data):
        """Boundary tol_grid should have correct dtype and shape."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="lower")

        assert result.tol_grid.dtype == np.float64
        assert result.tol_grid.ndim == 1
        assert result.tol_grid.shape[0] == 41  # default n_tols
        # tol_grid should be monotonically increasing (linspace)
        assert np.all(np.diff(result.tol_grid) > 0)

    def test_boundary_mass_curves_monotonic(self, uniform_data):
        """Boundary mass curves should be monotonically increasing."""
        from fitqc.stickiness import detect_stickiness

        _, boundary = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="all")

        # Both mass curves should be monotonically increasing
        assert np.all(np.diff(boundary.lower_mass_curve) >= 0)
        assert np.all(np.diff(boundary.upper_mass_curve) >= 0)
        # Values should be in [0, 1]
        assert np.all(boundary.lower_mass_curve >= 0)
        assert np.all(boundary.lower_mass_curve <= 1)
        assert np.all(boundary.upper_mass_curve >= 0)
        assert np.all(boundary.upper_mass_curve <= 1)

    def test_boundary_mode_array_properties(self, uniform_data):
        """mode='boundary' arrays should have correct dtype, shape, and properties."""
        from fitqc.stickiness import detect_stickiness

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        # tol_grid properties
        assert result.tol_grid.dtype == np.float64
        assert result.tol_grid.ndim == 1
        assert result.tol_grid.shape[0] == 41  # default n_tols
        assert np.all(np.diff(result.tol_grid) > 0)  # monotonically increasing

        # lower_mass_curve properties
        assert result.lower_mass_curve.dtype == np.float64
        assert result.lower_mass_curve.ndim == 1
        assert result.lower_mass_curve.shape == result.tol_grid.shape
        assert np.all(result.lower_mass_curve >= 0)
        assert np.all(result.lower_mass_curve <= 1)
        assert np.all(np.diff(result.lower_mass_curve) >= 0)

        # upper_mass_curve properties
        assert result.upper_mass_curve.dtype == np.float64
        assert result.upper_mass_curve.ndim == 1
        assert result.upper_mass_curve.shape == result.tol_grid.shape
        assert np.all(result.upper_mass_curve >= 0)
        assert np.all(result.upper_mass_curve <= 1)
        assert np.all(np.diff(result.upper_mass_curve) >= 0)


# =============================================================================
# 10. Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_single_sample(self):
        """Should handle single sample without crashing."""
        from fitqc.stickiness import detect_stickiness

        x = np.array([5.0])

        # Should not raise
        result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert isinstance(result.spike_detected, bool)

    def test_all_identical_values(self):
        """Should handle all identical values."""
        from fitqc.stickiness import detect_stickiness

        x = np.full(100, 5.0)

        result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        # All values at ref should likely detect a spike
        assert result.spike_detected is True

    def test_ref_at_lower_bound(self, rng):
        """Should handle ref at lower bound.

        When ref=L=0.0, the scale computation becomes:
            max(ref - L, U - ref) = max(0 - 0, 10 - 0) = max(0, 10) = 10

        This tests the edge case where one side of the max() is zero.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)

        result = detect_stickiness(x, ref=0.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert result.eps_grid.dtype == np.float64

        # Verify result matches direct call (scale should be 10)
        direct = run_interior_qc(x, x0=0.0, L=0.0, U=10.0)
        np.testing.assert_array_equal(result.mass_curve, direct.mass_curve)

    def test_ref_at_upper_bound(self, rng):
        """Should handle ref at upper bound.

        When ref=U=10.0, the scale computation becomes:
            max(ref - L, U - ref) = max(10 - 0, 10 - 10) = max(10, 0) = 10

        This tests the edge case where one side of the max() is zero.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)

        result = detect_stickiness(x, ref=10.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert result.eps_grid.dtype == np.float64

        # Verify result matches direct call (scale should be 10)
        direct = run_interior_qc(x, x0=10.0, L=0.0, U=10.0)
        np.testing.assert_array_equal(result.mass_curve, direct.mass_curve)

    def test_symmetric_bounds(self, rng):
        """Should handle symmetric bounds around ref.

        When ref is centered between L and U:
            max(ref - L, U - ref) = max(0 - (-10), 10 - 0) = max(10, 10) = 10

        Both sides of the max() are equal.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(-10, 10, size=1000)

        result = detect_stickiness(x, ref=0.0, L=-10.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert result.eps_grid.dtype == np.float64

        # Verify result matches direct call
        direct = run_interior_qc(x, x0=0.0, L=-10.0, U=10.0)
        np.testing.assert_array_equal(result.mass_curve, direct.mass_curve)

    def test_asymmetric_bounds(self, rng):
        """Should handle asymmetric bounds (ref closer to one bound).

        When ref=2.0 is closer to L=0.0 than to U=10.0:
            max(ref - L, U - ref) = max(2 - 0, 10 - 2) = max(2, 8) = 8

        The larger distance (to U) determines the scale.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)

        result = detect_stickiness(x, ref=2.0, L=0.0, U=10.0, mode="interior")

        assert isinstance(result, InteriorResult)
        assert result.eps_grid.dtype == np.float64

        # Verify result matches direct call (scale should be 8)
        direct = run_interior_qc(x, x0=2.0, L=0.0, U=10.0)
        np.testing.assert_array_equal(result.mass_curve, direct.mass_curve)

    def test_lower_mode_with_U_none(self, rng):
        """mode='lower' should work when U is None.

        When U is not provided, mode='lower' should still function correctly,
        computing lower boundary detection while nulling upper fields.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)

        result = detect_stickiness(x, ref=5.0, L=0.0, U=None, mode="lower")

        assert isinstance(result, BoundaryResult)
        # Lower fields should be properly populated
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.shape[0] > 0
        assert isinstance(result.lower_mass_curve, np.ndarray)
        # Upper fields should be nulled
        assert result.upper_pileup_detected is False
        assert result.t_hi_star is None
        assert result.upper_mass_curve is None

    def test_upper_mode_with_L_none(self, rng):
        """mode='upper' should work when L is None.

        When L is not provided, mode='upper' should still function correctly,
        computing upper boundary detection while nulling lower fields.
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)

        result = detect_stickiness(x, ref=5.0, L=None, U=10.0, mode="upper")

        assert isinstance(result, BoundaryResult)
        # Upper fields should be properly populated
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert result.tol_grid.shape[0] > 0
        assert isinstance(result.upper_mass_curve, np.ndarray)
        # Lower fields should be nulled
        assert result.lower_pileup_detected is False
        assert result.t_lo_star is None
        assert result.lower_mass_curve is None

    def test_all_mode_with_only_L(self, rng):
        """mode='all' with only L should use scale for interior.

        When U is None:
        - Interior check uses scale parameter for effective bounds
        - Boundary check can only compute lower boundary detection
        - Upper boundary fields should be handled gracefully
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)
        expected_scale = float(np.std(x))

        interior, boundary = detect_stickiness(x, ref=5.0, L=0.0, U=None, mode="all", scale="std")

        # Interior should use scale-derived bounds
        assert isinstance(interior, InteriorResult)
        assert isinstance(interior.spike_detected, bool)
        assert interior.eps_grid.dtype == np.float64

        # Verify interior used the correct scale by comparing with direct call
        effective_L = 5.0 - expected_scale
        effective_U = 5.0 + expected_scale
        direct_interior = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)
        np.testing.assert_array_almost_equal(interior.mass_curve, direct_interior.mass_curve)

        # Boundary should have lower fields populated
        assert isinstance(boundary, BoundaryResult)
        assert isinstance(boundary.lower_pileup_detected, bool)
        assert isinstance(boundary.lower_mass_curve, np.ndarray)

    def test_all_mode_with_only_U(self, rng):
        """mode='all' with only U should use scale for interior.

        When L is None:
        - Interior check uses scale parameter for effective bounds
        - Boundary check can only compute upper boundary detection
        - Lower boundary fields should be handled gracefully
        """
        from fitqc.stickiness import detect_stickiness

        x = rng.uniform(0, 10, size=1000)
        expected_scale = float(np.std(x))

        interior, boundary = detect_stickiness(x, ref=5.0, L=None, U=10.0, mode="all", scale="std")

        # Interior should use scale-derived bounds
        assert isinstance(interior, InteriorResult)
        assert isinstance(interior.spike_detected, bool)
        assert interior.eps_grid.dtype == np.float64

        # Verify interior used the correct scale by comparing with direct call
        effective_L = 5.0 - expected_scale
        effective_U = 5.0 + expected_scale
        direct_interior = run_interior_qc(x, x0=5.0, L=effective_L, U=effective_U)
        np.testing.assert_array_almost_equal(interior.mass_curve, direct_interior.mass_curve)

        # Boundary should have upper fields populated
        assert isinstance(boundary, BoundaryResult)
        assert isinstance(boundary.upper_pileup_detected, bool)
        assert isinstance(boundary.upper_mass_curve, np.ndarray)

    def test_constant_data_scale_raises(self):
        """Constant data with data-driven scale should raise."""
        from fitqc.stickiness import detect_stickiness

        x = np.full(100, 5.0)

        # std of constant data is 0, which is non-positive
        with pytest.raises(ValueError, match=r"non-positive"):
            detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="std")


# =============================================================================
# 11. Boundary Mode Performance Tests
# =============================================================================


class TestBoundaryModeDoesNotRunInterior:
    """Critical test: mode='boundary' must NOT run interior QC."""

    def test_boundary_mode_does_not_call_run_interior_qc(self, monkeypatch, uniform_data):
        """mode='boundary' must NOT call run_interior_qc (performance requirement)."""
        from fitqc import stickiness
        from fitqc.stickiness import detect_stickiness

        # Track whether run_interior_qc was called
        called = []
        original = stickiness.run_interior_qc

        def mock_interior(*args, **kwargs):
            called.append(True)
            return original(*args, **kwargs)

        monkeypatch.setattr(stickiness, "run_interior_qc", mock_interior)

        result = detect_stickiness(uniform_data, ref=5.0, L=0.0, U=10.0, mode="boundary")

        assert len(called) == 0, "run_interior_qc was called but should not be for mode='boundary'"
        assert isinstance(result, BoundaryResult)
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)
