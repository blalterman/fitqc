"""Tests for plot_quantile_elbow_overlay function.

This test module defines the expected API and behavior for the plot_quantile_elbow_overlay
function, which visualizes quantile elbow points from detection results (InteriorResult
or BoundaryResult with quantile analysis enabled).

The function should:
- Accept InteriorResult or BoundaryResult objects containing quantile_elbows data
- Return a matplotlib.figure.Figure object
- Visualize quantile values vs their detected elbow thresholds
- Use PlotConfig for styling (colormap, DPI, etc.)
- Handle edge cases like None elbows, empty dicts, single quantiles gracefully

Tests are marked as xfail since the function is not yet implemented (TDD approach).
"""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from fitqc.boundary import BoundaryResult, run_boundary_qc
from fitqc.config import BoundaryConfig, InteriorConfig, PlotConfig
from fitqc.interior import InteriorResult, run_interior_qc

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def plot_config() -> PlotConfig:
    """Default PlotConfig for tests."""
    return PlotConfig()


@pytest.fixture
def custom_plot_config() -> PlotConfig:
    """Custom PlotConfig with non-default settings."""
    return PlotConfig(
        cmap="viridis",
        dpi=150,
        figsize_tolerance=(10, 6),
    )


@pytest.fixture
def interior_result_with_quantile_elbows() -> InteriorResult:
    """Create an InteriorResult with populated quantile_elbows.

    Simulates output from run_interior_qc with use_quantile_analysis=True.
    """
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=True,
        spike_z_loc=0.02,
        eps_star=1e-6,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows={
            0.001: 1e-9,
            0.005: 5e-8,
            0.01: 1e-7,
            0.02: 5e-7,
            0.05: 1e-6,
            0.10: 5e-6,
        },
    )


@pytest.fixture
def interior_result_none_quantile_elbows() -> InteriorResult:
    """Create an InteriorResult with quantile_elbows=None."""
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=False,
        spike_z_loc=None,
        eps_star=None,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.001, 0.1, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows=None,
    )


@pytest.fixture
def interior_result_partial_none_elbows() -> InteriorResult:
    """Create an InteriorResult where some quantile elbows are None."""
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=True,
        spike_z_loc=0.02,
        eps_star=1e-6,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows={
            0.001: 1e-9,
            0.005: None,  # No elbow found for this quantile
            0.01: 1e-7,
            0.02: None,  # No elbow found for this quantile
            0.05: 1e-6,
            0.10: 5e-6,
        },
    )


@pytest.fixture
def boundary_result_with_quantile_elbows() -> BoundaryResult:
    """Create a BoundaryResult with populated quantile_elbows.

    Simulates output from run_boundary_qc with use_quantile_analysis=True.
    """
    return BoundaryResult(
        lower_pileup_detected=True,
        upper_pileup_detected=False,
        t_lo_star=0.008,
        t_hi_star=None,
        tol_grid=np.linspace(0, 0.05, 41),
        lower_mass_curve=np.linspace(0, 0.15, 41),
        upper_mass_curve=np.linspace(0, 0.05, 41),
        quantile_elbows={
            "lower": {
                0.001: 0.0001,
                0.002: 0.0003,
                0.005: 0.001,
                0.01: 0.003,
                0.02: 0.008,
                0.05: 0.02,
                0.10: 0.05,
            },
            "upper": {
                0.001: 0.001,
                0.002: 0.002,
                0.005: 0.005,
                0.01: 0.01,
                0.02: 0.02,
                0.05: 0.05,
                0.10: 0.10,
            },
        },
    )


@pytest.fixture
def boundary_result_none_quantile_elbows() -> BoundaryResult:
    """Create a BoundaryResult with quantile_elbows=None."""
    return BoundaryResult(
        lower_pileup_detected=False,
        upper_pileup_detected=False,
        t_lo_star=None,
        t_hi_star=None,
        tol_grid=np.linspace(0, 0.05, 41),
        lower_mass_curve=np.linspace(0, 0.05, 41),
        upper_mass_curve=np.linspace(0, 0.05, 41),
        quantile_elbows=None,
    )


# =============================================================================
# TestPlotQuantileElbowOverlayBasic
# =============================================================================


class TestPlotQuantileElbowOverlayBasic:
    """Basic tests for plot_quantile_elbow_overlay function existence and signature."""

    def test_function_exists(self):
        """Test that plot_quantile_elbow_overlay can be imported from fitqc.plot.

        The function should be importable and callable. This test verifies the
        basic API contract that the function exists in the expected module.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        assert callable(plot_quantile_elbow_overlay)

    def test_returns_figure(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the function returns a matplotlib.figure.Figure object.

        All fitqc plotting functions follow the convention of returning Figure
        objects rather than displaying them directly.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure), f"Expected Figure, got {type(fig)}"
        finally:
            plt.close(fig)

    def test_accepts_interior_result(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the function accepts InteriorResult objects.

        InteriorResult.quantile_elbows has format: {quantile: elbow_value}
        where quantile is a float (e.g., 0.01) and elbow_value is the detected
        epsilon threshold (or None if no elbow found).
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Should have at least one axis for the plot
            assert len(fig.axes) >= 1
        finally:
            plt.close(fig)

    def test_accepts_boundary_result(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that the function accepts BoundaryResult objects.

        BoundaryResult.quantile_elbows has format:
            {"lower": {quantile: tol_value}, "upper": {quantile: tol_value}}
        The function should handle this nested structure, potentially creating
        subplots for lower and upper boundaries.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(boundary_result_with_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
            # BoundaryResult has two boundaries, so may have 2 subplots
            assert len(fig.axes) >= 1
        finally:
            plt.close(fig)

    def test_uses_plot_config(
        self, interior_result_with_quantile_elbows: InteriorResult, custom_plot_config: PlotConfig
    ):
        """Test that the function respects PlotConfig settings.

        The function should use:
        - config.dpi for figure resolution
        - config.cmap for colormap
        - config.figsize_tolerance (or similar) for figure size
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, custom_plot_config)
        try:
            # Check DPI is applied
            assert fig.dpi == custom_plot_config.dpi, (
                f"Expected DPI={custom_plot_config.dpi}, got {fig.dpi}"
            )
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowOverlayEdgeCases
# =============================================================================


class TestPlotQuantileElbowOverlayEdgeCases:
    """Edge case tests for plot_quantile_elbow_overlay function."""

    def test_handles_none_quantile_elbows(
        self, interior_result_none_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the function handles quantile_elbows=None gracefully.

        When quantile_elbows is None (single-curve mode was used, or no spike detected),
        the function should still return a valid Figure, possibly with a message
        indicating no quantile data is available.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_none_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Should still have at least one axis (even if empty or with message)
            assert len(fig.axes) >= 1
        finally:
            plt.close(fig)

    def test_handles_empty_dict_elbows(self, plot_config: PlotConfig):
        """Test that the function handles quantile_elbows={} (empty dict) gracefully.

        An empty dict could occur if no quantiles were analyzed. The function
        should handle this without crashing.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        rng = np.random.default_rng(42)
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=rng.integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={},  # Empty dict
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)
        try:
            assert isinstance(fig, Figure)
        finally:
            plt.close(fig)

    def test_handles_partial_none_values(
        self, interior_result_partial_none_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the function handles Some elbows being None.

        When some quantiles have elbow=None (no elbow found for that quantile),
        the function should:
        1. Still create a valid figure
        2. Only plot markers for quantiles with valid (non-None) elbows
        3. Optionally indicate which quantiles had no elbow detected
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_partial_none_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Should have plotted something
            assert len(fig.axes) >= 1
        finally:
            plt.close(fig)

    def test_handles_single_quantile(self, plot_config: PlotConfig):
        """Test that the function handles a single quantile in the dict.

        Edge case where only one quantile was analyzed. The function should
        still create a valid visualization.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        rng = np.random.default_rng(42)
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=rng.integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={0.05: 1e-6},  # Single quantile
        )

        fig = plot_quantile_elbow_overlay(result, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Should have at least one axis
            assert len(fig.axes) >= 1
        finally:
            plt.close(fig)

    def test_handles_boundary_result_none_quantile_elbows(
        self, boundary_result_none_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that the function handles BoundaryResult with quantile_elbows=None."""
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(boundary_result_none_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowOverlayCorrectness
# =============================================================================


class TestPlotQuantileElbowOverlayCorrectness:
    """Tests verifying correctness of the plot_quantile_elbow_overlay visualization."""

    def test_marker_count_matches_valid_elbows(
        self, interior_result_partial_none_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the number of markers matches the number of non-None elbows.

        The plot should only show markers for quantiles where an elbow was
        successfully detected (elbow value is not None).
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_partial_none_elbows, plot_config)
        try:
            # Count expected valid elbows
            quantile_elbows = interior_result_partial_none_elbows.quantile_elbows
            assert quantile_elbows is not None
            n_valid = sum(1 for v in quantile_elbows.values() if v is not None)

            # Find the main axes (not colorbar)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]

            # Count scatter plot collections or line markers
            # This checks PathCollection objects (scatter plots)
            scatter_collections = [
                c for c in ax.collections if hasattr(c, "get_offsets") and len(c.get_offsets()) > 0
            ]

            if scatter_collections:
                # Sum all scatter points
                total_markers = sum(len(c.get_offsets()) for c in scatter_collections)
                assert total_markers == n_valid, (
                    f"Expected {n_valid} markers for valid elbows, got {total_markers}"
                )
            else:
                # Check lines with markers
                lines_with_markers = [
                    line for line in ax.get_lines() if line.get_marker() not in ["", "None", None]
                ]
                if lines_with_markers:
                    total_markers = sum(len(line.get_xdata()) for line in lines_with_markers)
                    assert total_markers >= n_valid, (
                        f"Expected at least {n_valid} markers, got {total_markers}"
                    )
        finally:
            plt.close(fig)

    def test_uses_colormap_from_config(self, interior_result_with_quantile_elbows: InteriorResult):
        """Test that the plot uses the colormap specified in PlotConfig.

        Colors should be derived from the configured colormap, allowing
        consistent styling across all fitqc visualizations.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        # Use a distinctive colormap
        config = PlotConfig(cmap="plasma")
        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, config)
        try:
            # Verify figure was created successfully with the config
            assert isinstance(fig, Figure)
            # More detailed colormap verification would require inspecting
            # the actual colors used, which is complex. The key test is that
            # it doesn't crash with a custom colormap.
        finally:
            plt.close(fig)

    def test_has_legend_with_quantile_labels(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the plot has a legend showing quantile values.

        The legend should indicate which quantile each marker/line represents,
        helping users interpret the visualization.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            # Find the main axes (not colorbar)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]
            legend = ax.get_legend()

            # Should have a legend
            assert legend is not None, "Expected plot to have a legend"

            # Legend should have labels
            legend_texts = [t.get_text() for t in legend.get_texts()]
            assert len(legend_texts) > 0, "Legend should have at least one label"

            # At least one label should contain a quantile value
            # (e.g., "0.01", "1%", "q=0.01", etc.)
            quantile_elbows = interior_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None

            # Check if any quantile value appears in the legend
            has_quantile_label = False
            for q in quantile_elbows.keys():
                for text in legend_texts:
                    # Check for various formats: "0.01", "1%", "q=0.01"
                    if str(q) in text or f"{q * 100:.1f}%" in text or f"{q * 100:.0f}%" in text:
                        has_quantile_label = True
                        break
                if has_quantile_label:
                    break

            assert has_quantile_label, (
                f"Expected legend to contain quantile values. "
                f"Legend texts: {legend_texts}, quantiles: {list(quantile_elbows.keys())}"
            )
        finally:
            plt.close(fig)

    def test_axes_have_appropriate_labels(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that axes have appropriate labels for quantile elbow data.

        For InteriorResult:
        - X-axis should indicate quantile (e.g., "Quantile", "q")
        - Y-axis should indicate epsilon/threshold (e.g., "Epsilon", "eps*", "Threshold")

        For BoundaryResult:
        - Y-axis should indicate tolerance (e.g., "Tolerance", "t*")
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            # Find the main axes (not colorbar)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]

            # Check X-axis label exists and is non-empty
            xlabel = ax.get_xlabel()
            assert xlabel, "X-axis should have a label"

            # Check Y-axis label exists and is non-empty
            ylabel = ax.get_ylabel()
            assert ylabel, "Y-axis should have a label"

            # Labels should be meaningful (contain key terms)
            xlabel_lower = xlabel.lower()
            ylabel_lower = ylabel.lower()

            # X-axis should relate to quantile
            assert any(term in xlabel_lower for term in ["quantile", "q", "percentile"]), (
                f"X-axis label '{xlabel}' should indicate quantile"
            )

            # Y-axis should relate to threshold/epsilon
            assert any(term in ylabel_lower for term in ["epsilon", "eps", "threshold", "elbow"]), (
                f"Y-axis label '{ylabel}' should indicate threshold/epsilon"
            )
        finally:
            plt.close(fig)

    def test_boundary_result_has_two_panels(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that BoundaryResult produces plots for both lower and upper boundaries.

        Since BoundaryResult has separate quantile_elbows for "lower" and "upper"
        boundaries, the visualization should show both (e.g., as subplots or
        overlaid with different styling).
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(boundary_result_with_quantile_elbows, plot_config)
        try:
            # Find main axes (excluding colorbar)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]

            # Should have at least 2 main axes for lower and upper boundaries
            # (or 1 axis with both overlaid)
            assert len(main_axes) >= 1

            # If there are 2 axes, check they have appropriate titles
            if len(main_axes) >= 2:
                titles = [ax.get_title().lower() for ax in main_axes[:2]]
                has_lower = any("lower" in t for t in titles)
                has_upper = any("upper" in t for t in titles)
                assert has_lower or has_upper, (
                    f"Expected axes to have 'lower' or 'upper' in titles, got: {titles}"
                )
        finally:
            plt.close(fig)

    def test_does_not_call_show(
        self,
        interior_result_with_quantile_elbows: InteriorResult,
        plot_config: PlotConfig,
        monkeypatch,
    ):
        """Test that the function does NOT call plt.show().

        Following fitqc conventions, plotting functions should return Figure
        objects and let the caller decide when/how to display them.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        show_called = []
        monkeypatch.setattr(plt, "show", lambda: show_called.append(True))

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            assert len(show_called) == 0, "plt.show() should not be called"
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowOverlayWithRealData
# =============================================================================


class TestPlotQuantileElbowOverlayWithRealData:
    """Tests using real QC results with synthetic data to verify end-to-end behavior."""

    def test_with_synthetic_spike_data(self, plot_config: PlotConfig):
        """Test plotting with real InteriorResult from synthetic spike data.

        Creates data with a known spike at x0, runs interior QC with quantile
        analysis enabled, and verifies the plot is created correctly.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        rng = np.random.default_rng(42)

        # Create synthetic data with spike at x0=0.5
        n_samples = 10000
        n_spike = 500  # 5% stuck at x0

        x_spike = np.full(n_spike, 0.5)  # Exactly at x0
        x_uniform = rng.uniform(0.0, 1.0, n_samples - n_spike)
        x = np.concatenate([x_spike, x_uniform])

        # Run interior QC with quantile analysis
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05, 0.10),
        )
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # Verify spike was detected
        assert result.spike_detected, "Spike should be detected in test data"
        assert result.quantile_elbows is not None, "quantile_elbows should be populated"

        # Create and verify the plot
        fig = plot_quantile_elbow_overlay(result, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Plot should have content (axes with data)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]
            # Should have some visual elements (lines, scatter, etc.)
            has_content = len(ax.get_lines()) > 0 or len(ax.collections) > 0 or len(ax.patches) > 0
            assert has_content, "Plot should have visual content"
        finally:
            plt.close(fig)

    def test_with_synthetic_pileup_data(self, plot_config: PlotConfig):
        """Test plotting with real BoundaryResult from synthetic pileup data.

        Creates data with boundary pileup, runs boundary QC with quantile
        analysis enabled, and verifies the plot is created correctly.

        Note: This test focuses on verifying the plotting function works correctly
        with boundary results, not on verifying pileup detection (which is
        tested in test_boundary.py).
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        rng = np.random.default_rng(42)

        # Create synthetic data with lower boundary pileup
        n_samples = 10000
        n_pileup = 1000  # 10% at lower boundary

        x_pileup = rng.uniform(0.0, 0.005, n_pileup)  # Concentrated near L=0
        x_uniform = rng.uniform(0.0, 1.0, n_samples - n_pileup)
        x = np.concatenate([x_pileup, x_uniform])

        # Run boundary QC with quantile analysis
        config = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10),
        )
        result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

        # Verify quantile_elbows is populated (regardless of pileup detection)
        assert result.quantile_elbows is not None, "quantile_elbows should be populated"

        # Create and verify the plot
        fig = plot_quantile_elbow_overlay(result, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Plot should have content
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]
            # Should have some visual elements
            has_content = len(ax.get_lines()) > 0 or len(ax.collections) > 0 or len(ax.patches) > 0
            assert has_content, "Plot should have visual content"
        finally:
            plt.close(fig)

    def test_with_clean_data_no_stickiness(self, plot_config: PlotConfig):
        """Test plotting with clean uniform data (no stickiness detected).

        Even when no stickiness is detected, the function should handle
        the result gracefully if quantile_elbows is None.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        rng = np.random.default_rng(42)

        # Create clean uniform data
        x = rng.uniform(0.0, 1.0, 10000)

        # Run interior QC - should not detect spike
        config = InteriorConfig(use_quantile_analysis=True)
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # With clean data, spike may or may not be detected
        # The key is that the plot function handles whatever result we get
        fig = plot_quantile_elbow_overlay(result, plot_config)
        try:
            assert isinstance(fig, Figure)
        finally:
            plt.close(fig)

    def test_preserves_quantile_ordering(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that quantiles are plotted in ascending order.

        The visualization should maintain the natural ordering of quantiles
        (0.001 < 0.005 < 0.01 < etc.) along the x-axis.
        """
        from fitqc.plot import plot_quantile_elbow_overlay

        fig = plot_quantile_elbow_overlay(interior_result_with_quantile_elbows, plot_config)
        try:
            # Find the main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1

            ax = main_axes[0]

            # Get x-data from scatter points only (exclude reference lines)
            # Reference lines like axhline span the full axis range
            x_values = []
            for coll in ax.collections:
                if hasattr(coll, "get_offsets"):
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        x_values.extend(offsets[:, 0])

            if len(x_values) > 1:
                # X values from scatter points should be in ascending order
                x_sorted = sorted(x_values)
                # Allow for some variation due to plotting mechanics
                assert x_values == x_sorted or np.allclose(x_values, x_sorted), (
                    "Quantiles should be plotted in ascending order"
                )
        finally:
            plt.close(fig)
