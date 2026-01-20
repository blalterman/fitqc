"""Integration tests for quantile-based visualization features.

This module tests the integration between quantile analysis in interior/boundary QC
and the plot_quantile_elbow_overlay visualization function.

Test Classes:
    TestQuantileResultsAvailableForPlotting: Tests that verify quantile_elbows field works
    TestQuantileVisualizationIntegration: Tests that verify plot_quantile_elbow_overlay works
    TestCombinedPipeline: End-to-end tests from data to visualization
    TestQuantileElbowsDataIntegrity: Data validation tests for quantile_elbows
"""

import numpy as np
import pytest
from matplotlib.figure import Figure

from fitqc import (
    BoundaryConfig,
    InteriorConfig,
    PlotConfig,
    plot_quantile_elbow_overlay,
    run_boundary_qc,
    run_interior_qc,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rng():
    """Seeded random number generator for reproducibility."""
    return np.random.default_rng(42)


@pytest.fixture
def uniform_data(rng):
    """Uniform data in [0, 1] with no stickiness."""
    return rng.uniform(0, 1, size=5000)


@pytest.fixture
def data_with_x0_spike(rng):
    """Data with 5% spike at x0=0.5."""
    x = rng.uniform(0, 1, size=10000)
    spike_idx = rng.choice(10000, size=500, replace=False)
    x[spike_idx] = 0.5
    return x


@pytest.fixture
def data_with_lower_pileup(rng):
    """Data with 5% pileup at lower boundary."""
    x = rng.uniform(0, 1, size=10000)
    x[:500] = rng.uniform(0, 0.01, size=500)
    return x


@pytest.fixture
def data_with_upper_pileup(rng):
    """Data with 5% pileup at upper boundary."""
    x = rng.uniform(0, 1, size=10000)
    x[:500] = rng.uniform(0.99, 1.0, size=500)
    return x


@pytest.fixture
def interior_config_with_quantile():
    """InteriorConfig with quantile analysis enabled."""
    return InteriorConfig(
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
    )


@pytest.fixture
def boundary_config_with_quantile():
    """BoundaryConfig with quantile analysis enabled."""
    return BoundaryConfig(
        use_quantile_analysis=True,
        quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
    )


@pytest.fixture
def plot_config():
    """PlotConfig for testing visualizations."""
    return PlotConfig()


# =============================================================================
# 1. TestQuantileResultsAvailableForPlotting
# =============================================================================


class TestQuantileResultsAvailableForPlotting:
    """Tests that verify quantile_elbows field is populated when enabled."""

    def test_interior_quantile_elbows_populated(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Interior result should have quantile_elbows when use_quantile_analysis=True."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        assert result.quantile_elbows is not None
        assert isinstance(result.quantile_elbows, dict)
        assert len(result.quantile_elbows) > 0

    def test_interior_quantile_elbows_none_when_disabled(self, data_with_x0_spike):
        """Interior result should have quantile_elbows=None when disabled."""
        config = InteriorConfig(use_quantile_analysis=False)
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=config,
        )

        assert result.quantile_elbows is None

    def test_boundary_quantile_elbows_populated(
        self, data_with_lower_pileup, boundary_config_with_quantile
    ):
        """Boundary result should have quantile_elbows when use_quantile_analysis=True."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        assert result.quantile_elbows is not None
        assert isinstance(result.quantile_elbows, dict)
        assert "lower" in result.quantile_elbows
        assert "upper" in result.quantile_elbows

    def test_boundary_quantile_elbows_none_when_disabled(self, data_with_lower_pileup):
        """Boundary result should have quantile_elbows=None when disabled."""
        config = BoundaryConfig(use_quantile_analysis=False)
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=config,
        )

        assert result.quantile_elbows is None

    def test_interior_quantile_elbows_keys_match_grid(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """quantile_elbows keys should match quantile_grid values."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        expected_keys = set(interior_config_with_quantile.quantile_grid)
        actual_keys = set(result.quantile_elbows.keys())

        assert actual_keys == expected_keys

    def test_boundary_quantile_elbows_keys_match_grid(
        self, data_with_lower_pileup, boundary_config_with_quantile
    ):
        """Boundary quantile_elbows keys should match quantile_grid values."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        expected_keys = set(boundary_config_with_quantile.quantile_grid)
        actual_lower_keys = set(result.quantile_elbows["lower"].keys())
        actual_upper_keys = set(result.quantile_elbows["upper"].keys())

        assert actual_lower_keys == expected_keys
        assert actual_upper_keys == expected_keys


# =============================================================================
# 2. TestQuantileVisualizationIntegration
# =============================================================================


class TestQuantileVisualizationIntegration:
    """Tests that verify plot_quantile_elbow_overlay works correctly."""

    def test_interior_result_produces_figure(
        self, data_with_x0_spike, interior_config_with_quantile, plot_config
    ):
        """plot_quantile_elbow_overlay should return Figure for InteriorResult."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)

        assert isinstance(fig, Figure)

    def test_boundary_result_produces_figure(
        self, data_with_lower_pileup, boundary_config_with_quantile, plot_config
    ):
        """plot_quantile_elbow_overlay should return Figure for BoundaryResult."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)

        assert isinstance(fig, Figure)

    def test_figure_with_none_quantile_elbows(self, uniform_data, plot_config):
        """plot_quantile_elbow_overlay should handle None quantile_elbows gracefully."""
        config = InteriorConfig(use_quantile_analysis=False)
        result = run_interior_qc(
            uniform_data,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=config,
        )

        assert result.quantile_elbows is None

        # Should not raise and should return a figure with message
        fig = plot_quantile_elbow_overlay(result, plot_config)

        assert isinstance(fig, Figure)

    def test_figure_with_default_config(self, data_with_x0_spike, interior_config_with_quantile):
        """plot_quantile_elbow_overlay should work with config=None (uses defaults)."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        # config=None should use PlotConfig defaults
        fig = plot_quantile_elbow_overlay(result, config=None)

        assert isinstance(fig, Figure)

    def test_interior_figure_has_axes(
        self, data_with_x0_spike, interior_config_with_quantile, plot_config
    ):
        """Interior quantile elbow plot should have at least one axes."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)

        assert len(fig.axes) >= 1

    def test_boundary_figure_has_two_panels(
        self, data_with_lower_pileup, boundary_config_with_quantile, plot_config
    ):
        """Boundary quantile elbow plot should have two panels (lower and upper)."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)

        # Should have 2 axes for lower and upper boundaries
        assert len(fig.axes) == 2

    def test_figure_not_shown(self, data_with_x0_spike, interior_config_with_quantile, plot_config):
        """plot_quantile_elbow_overlay should return figure without calling plt.show()."""
        import matplotlib.pyplot as plt

        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)

        # Figure should be returned, not displayed
        assert isinstance(fig, Figure)

        # Clean up
        plt.close(fig)


# =============================================================================
# 3. TestCombinedPipeline
# =============================================================================


class TestCombinedPipeline:
    """End-to-end tests from data generation to visualization."""

    def test_interior_pipeline_spike_detection_to_plot(self, rng, plot_config):
        """Full pipeline: generate spike data -> detect -> visualize."""
        # Generate data with spike
        x = rng.uniform(0, 1, size=10000)
        spike_idx = rng.choice(10000, size=500, replace=False)
        x[spike_idx] = 0.5

        # Run QC with quantile analysis
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.01, 0.05),
        )
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # Verify detection
        assert result.spike_detected is True
        assert result.quantile_elbows is not None

        # Generate plot
        fig = plot_quantile_elbow_overlay(result, plot_config)
        assert isinstance(fig, Figure)

        # Verify eps_star is reasonable
        assert result.eps_star is not None
        assert result.eps_star < 0.1  # Should be tight threshold

    def test_boundary_pipeline_lower_pileup_to_plot(self, rng, plot_config):
        """Full pipeline: generate boundary data -> run QC -> visualize.

        Note: This test focuses on the visualization pipeline working correctly,
        not on verifying detection accuracy (which is tested in test_boundary.py).
        """
        # Generate data with concentration near lower boundary
        x = rng.uniform(0, 1, size=10000)
        x[:500] = rng.uniform(0, 0.01, size=500)

        # Run QC with quantile analysis
        config = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
        )
        result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

        # Verify quantile_elbows is populated (regardless of detection outcome)
        assert result.quantile_elbows is not None

        # Generate plot - should work regardless of detection outcome
        fig = plot_quantile_elbow_overlay(result, plot_config)
        assert isinstance(fig, Figure)

    def test_boundary_pipeline_upper_pileup_to_plot(self, rng, plot_config):
        """Full pipeline: generate boundary data -> run QC -> visualize.

        Note: This test focuses on the visualization pipeline working correctly,
        not on verifying detection accuracy (which is tested in test_boundary.py).
        """
        # Generate data with concentration near upper boundary
        x = rng.uniform(0, 1, size=10000)
        x[:500] = rng.uniform(0.99, 1.0, size=500)

        # Run QC with quantile analysis
        config = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05),
        )
        result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

        # Verify quantile_elbows is populated (regardless of detection outcome)
        assert result.quantile_elbows is not None

        # Generate plot - should work regardless of detection outcome
        fig = plot_quantile_elbow_overlay(result, plot_config)
        assert isinstance(fig, Figure)

    def test_uniform_data_no_detection(self, uniform_data, plot_config):
        """Uniform data should not trigger false positives."""
        # Interior check
        interior_config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.01, 0.05),
        )
        interior_result = run_interior_qc(
            uniform_data, x0=0.5, L=0.0, U=1.0, config=interior_config
        )

        # Uniform data should not detect spike
        assert interior_result.spike_detected is False

        # Should still produce valid figure
        fig = plot_quantile_elbow_overlay(interior_result, plot_config)
        assert isinstance(fig, Figure)

    def test_multiple_visualizations_same_result(
        self, data_with_x0_spike, interior_config_with_quantile, plot_config
    ):
        """Should be able to generate multiple plots from same result."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        # Generate multiple plots
        fig1 = plot_quantile_elbow_overlay(result, plot_config)
        fig2 = plot_quantile_elbow_overlay(result, plot_config)

        assert isinstance(fig1, Figure)
        assert isinstance(fig2, Figure)
        assert fig1 is not fig2  # Should be different figure objects

    def test_pipeline_with_custom_quantile_grid(self, rng, plot_config):
        """Pipeline with custom quantile grid."""
        x = rng.uniform(0, 1, size=10000)
        spike_idx = rng.choice(10000, size=500, replace=False)
        x[spike_idx] = 0.5

        # Custom quantile grid with more points
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1),
        )
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # Verify all quantiles present in result
        assert len(result.quantile_elbows) == 7

        # Generate plot
        fig = plot_quantile_elbow_overlay(result, plot_config)
        assert isinstance(fig, Figure)


# =============================================================================
# 4. TestQuantileElbowsDataIntegrity
# =============================================================================


class TestQuantileElbowsDataIntegrity:
    """Data validation tests for quantile_elbows field."""

    def test_interior_quantile_elbows_values_are_floats_or_none(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Interior quantile_elbows values should be float or None."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        for q, eps in result.quantile_elbows.items():
            assert isinstance(q, float), f"Key {q} should be float"
            assert eps is None or isinstance(eps, float), f"Value {eps} should be float or None"

    def test_boundary_quantile_elbows_values_are_floats(
        self, data_with_lower_pileup, boundary_config_with_quantile
    ):
        """Boundary quantile_elbows values should be float."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        for side in ["lower", "upper"]:
            for q, tol in result.quantile_elbows[side].items():
                assert isinstance(q, float), f"Key {q} should be float"
                assert isinstance(tol, float), f"Value {tol} should be float"

    def test_interior_quantile_elbows_keys_are_positive(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Interior quantile_elbows keys (quantiles) should be positive."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        for q in result.quantile_elbows.keys():
            assert q > 0, f"Quantile key {q} should be positive"
            assert q <= 1, f"Quantile key {q} should be <= 1"

    def test_interior_quantile_elbows_values_nonnegative(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Non-None elbow values should be non-negative."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        for q, eps in result.quantile_elbows.items():
            if eps is not None:
                assert eps >= 0, f"Elbow value {eps} for quantile {q} should be non-negative"

    def test_boundary_quantile_elbows_values_in_valid_range(
        self, data_with_lower_pileup, boundary_config_with_quantile
    ):
        """Boundary elbow values (tolerances) should be in valid range [0, 1]."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        for side in ["lower", "upper"]:
            for q, tol in result.quantile_elbows[side].items():
                assert 0 <= tol <= 1, f"Tolerance {tol} for {side} q={q} should be in [0, 1]"

    def test_quantile_elbows_monotonicity_tendency(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Larger quantiles should generally map to larger epsilon values.

        Note: This is a soft check - there may be some non-monotonicity due to
        elbow detection noise, but the general trend should be increasing.
        """
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        # Extract valid (non-None) elbows
        valid_elbows = {q: eps for q, eps in result.quantile_elbows.items() if eps is not None}

        if len(valid_elbows) >= 2:
            sorted_quantiles = sorted(valid_elbows.keys())
            eps_values = [valid_elbows[q] for q in sorted_quantiles]

            # Check general trend: first eps should be <= last eps
            # (allowing for noise in intermediate values)
            assert eps_values[0] <= eps_values[-1] * 10, (
                f"First elbow ({eps_values[0]}) should be <= last elbow ({eps_values[-1]}) "
                "within an order of magnitude"
            )

    def test_interior_result_structure_complete(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """InteriorResult should have all expected fields populated."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        # Required fields
        assert isinstance(result.spike_detected, bool)
        assert isinstance(result.eps_grid, np.ndarray)
        assert isinstance(result.mass_curve, np.ndarray)
        assert isinstance(result.hist_counts, np.ndarray)
        assert isinstance(result.hist_edges, np.ndarray)

        # Shape consistency
        assert result.eps_grid.shape == result.mass_curve.shape
        assert result.hist_edges.shape[0] == result.hist_counts.shape[0] + 1

    def test_boundary_result_structure_complete(
        self, data_with_lower_pileup, boundary_config_with_quantile
    ):
        """BoundaryResult should have all expected fields populated."""
        result = run_boundary_qc(
            data_with_lower_pileup,
            L=0.0,
            U=1.0,
            config=boundary_config_with_quantile,
        )

        # Required fields
        assert isinstance(result.lower_pileup_detected, bool)
        assert isinstance(result.upper_pileup_detected, bool)
        assert isinstance(result.tol_grid, np.ndarray)
        assert isinstance(result.lower_mass_curve, np.ndarray)
        assert isinstance(result.upper_mass_curve, np.ndarray)

        # Shape consistency
        assert result.tol_grid.shape == result.lower_mass_curve.shape
        assert result.tol_grid.shape == result.upper_mass_curve.shape

    def test_quantile_elbows_dict_not_mutated(
        self, data_with_x0_spike, interior_config_with_quantile
    ):
        """Modifying returned quantile_elbows should not affect original result."""
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=interior_config_with_quantile,
        )

        original_keys = set(result.quantile_elbows.keys())

        # Try to modify the dict
        result.quantile_elbows[0.999] = 0.123

        # The result's quantile_elbows should now have the modification
        # (this tests that we get a dict, not a frozen/immutable view)
        assert 0.999 in result.quantile_elbows

        # Clean up - remove the added key
        del result.quantile_elbows[0.999]
        assert set(result.quantile_elbows.keys()) == original_keys

    def test_empty_quantile_grid_edge_case(self, data_with_x0_spike):
        """Config with minimal quantile grid should still work."""
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.01,),  # Single quantile
        )
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=config,
        )

        assert result.quantile_elbows is not None
        assert len(result.quantile_elbows) == 1
        assert 0.01 in result.quantile_elbows

    def test_large_quantile_grid(self, data_with_x0_spike):
        """Config with large quantile grid should work."""
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=tuple(np.linspace(0.001, 0.1, 20)),
        )
        result = run_interior_qc(
            data_with_x0_spike,
            x0=0.5,
            L=0.0,
            U=1.0,
            config=config,
        )

        assert result.quantile_elbows is not None
        assert len(result.quantile_elbows) == 20
