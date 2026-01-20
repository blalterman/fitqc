"""Tests for plot_kneedle_internals function.

All tests verify specific properties: type, dtype, shape, or numeric content.
No trivial assertions allowed.
"""

import matplotlib.pyplot as plt
import numpy as np

from fitqc.config import PlotConfig
from fitqc.plot import plot_kneedle_internals


class TestPlotKneedleInternalsStructure:
    """Tests verifying subplot structure and panel counts."""

    def test_creates_exactly_four_panels(self):
        """Creates exactly 4 panels: original, normalized, difference, annotated."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        # Exact count, not ">=3"
        assert len(fig.axes) == 4, (
            f"Expected exactly 4 panels, got {len(fig.axes)}. "
            f"Panels should be: original curve, normalized curve, difference curve, annotated curve"
        )
        plt.close(fig)

    def test_figure_has_correct_dpi(self):
        """Figure DPI matches PlotConfig.dpi."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        config = PlotConfig(dpi=200)
        fig = plot_kneedle_internals(x, y, config=config)

        # Type check
        assert isinstance(fig.dpi, (int, float))
        # Exact value check
        assert fig.dpi == 200, f"Expected DPI=200, got {fig.dpi}"
        plt.close(fig)

    def test_figure_has_correct_size(self):
        """Figure size matches PlotConfig.figsize_elbow_internals."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        config = PlotConfig(figsize_elbow_internals=(18, 12))
        fig = plot_kneedle_internals(x, y, config=config)

        # Get actual size in inches
        actual_size = fig.get_size_inches()

        # Type check
        assert isinstance(actual_size, np.ndarray)
        # Shape check
        assert actual_size.shape == (2,), f"Expected shape (2,), got {actual_size.shape}"
        # Dtype check
        assert actual_size.dtype == np.float64
        # Value check
        np.testing.assert_allclose(actual_size, [18, 12], rtol=1e-10)
        plt.close(fig)

    def test_all_axes_have_non_empty_labels(self):
        """Every axis has both xlabel and ylabel with non-empty strings."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        for i, ax in enumerate(fig.axes):
            xlabel = ax.get_xlabel()
            ylabel = ax.get_ylabel()

            # Type checks
            assert isinstance(xlabel, str), f"Axis {i} xlabel is not str, got {type(xlabel)}"
            assert isinstance(ylabel, str), f"Axis {i} ylabel is not str, got {type(ylabel)}"

            # Length checks (non-empty)
            assert len(xlabel) > 0, f"Axis {i} xlabel is empty"
            assert len(ylabel) > 0, f"Axis {i} ylabel is empty"

        plt.close(fig)

    def test_all_axes_have_titles(self):
        """Every axis has a title with at least 3 characters."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        for i, ax in enumerate(fig.axes):
            title = ax.get_title()

            # Type check
            assert isinstance(title, str), f"Axis {i} title is not str, got {type(title)}"

            # Minimum length check (substantive title, not just "A")
            assert len(title) >= 3, (
                f"Axis {i} title too short: '{title}'. "
                f"Expected descriptive title like 'Original Curve' or 'Normalized'"
            )

        plt.close(fig)


class TestPlotKneedleInternalsOriginalCurvePanel:
    """Tests verifying original curve panel shows exact input data."""

    def test_original_panel_plots_exact_x_data(self):
        """Original curve panel plots exact x values from input."""
        x = np.array([0.0, 2.5, 5.0, 7.5, 10.0])
        y = np.array([0.0, 0.918, 0.993, 0.9994, 0.99995])
        fig = plot_kneedle_internals(x, y)

        # Panel 0 should be original curve
        ax = fig.axes[0]
        lines = ax.get_lines()

        # Should have at least one line
        assert len(lines) >= 1, "Original panel should have at least one line"

        # Get line data
        line = lines[0]
        xdata = line.get_xdata()

        # Type checks
        assert isinstance(xdata, np.ndarray), f"Expected ndarray, got {type(xdata)}"

        # Shape check
        assert xdata.shape == (5,), f"Expected shape (5,), got {xdata.shape}"

        # Content check - exact values
        np.testing.assert_allclose(xdata, x, rtol=1e-10, atol=1e-14)

        plt.close(fig)

    def test_original_panel_plots_exact_y_data(self):
        """Original curve panel plots exact y values from input."""
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[0]
        lines = ax.get_lines()
        assert len(lines) >= 1

        line = lines[0]
        ydata = line.get_ydata()

        # Type check
        assert isinstance(ydata, np.ndarray)

        # Shape check
        assert ydata.shape == (50,), f"Expected shape (50,), got {ydata.shape}"

        # Dtype check
        assert ydata.dtype in [np.float32, np.float64], f"Expected float dtype, got {ydata.dtype}"

        # Content check
        np.testing.assert_allclose(ydata, y, rtol=1e-10, atol=1e-14)

        plt.close(fig)

    def test_original_panel_preserves_data_range(self):
        """Original curve panel preserves the exact data range."""
        x = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
        y = np.array([1.0, 1.5, 1.8, 1.95, 1.99])
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[0]
        lines = ax.get_lines()
        line = lines[0]

        xdata = line.get_xdata()
        ydata = line.get_ydata()

        # Check x range exactly
        x_min, x_max = xdata.min(), xdata.max()
        np.testing.assert_allclose([x_min, x_max], [100.0, 500.0], rtol=1e-10)

        # Check y range exactly
        y_min, y_max = ydata.min(), ydata.max()
        np.testing.assert_allclose([y_min, y_max], [1.0, 1.99], rtol=1e-10)

        plt.close(fig)


class TestPlotKneedleInternalsNormalizedCurvePanel:
    """Tests verifying normalized curve panel scales data to [0,1]."""

    def test_normalized_panel_x_in_zero_one_range(self):
        """Normalized curve has x values in [0, 1] range."""
        x = np.array([5.0, 10.0, 15.0, 20.0, 25.0])
        y = 1 - np.exp(-x / 10)
        fig = plot_kneedle_internals(x, y)

        # Panel 1 should be normalized curve
        ax = fig.axes[1]
        lines = ax.get_lines()
        assert len(lines) >= 1, "Normalized panel should have at least one line"

        line = lines[0]
        xdata = line.get_xdata()

        # Type and shape
        assert isinstance(xdata, np.ndarray)
        assert xdata.shape == (5,), f"Expected shape (5,), got {xdata.shape}"

        # Content - must be in [0, 1]
        assert xdata.min() >= 0.0, f"Normalized x min should be >= 0, got {xdata.min()}"
        assert xdata.max() <= 1.0, f"Normalized x max should be <= 1, got {xdata.max()}"

        # Check exact endpoints
        np.testing.assert_allclose(xdata[0], 0.0, atol=1e-10)
        np.testing.assert_allclose(xdata[-1], 1.0, atol=1e-10)

        plt.close(fig)

    def test_normalized_panel_y_in_zero_one_range(self):
        """Normalized curve has y values in [0, 1] range."""
        x = np.linspace(0, 5, 30)
        y = x**2  # Range [0, 25]
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[1]
        lines = ax.get_lines()
        line = lines[0]
        ydata = line.get_ydata()

        # Type and shape
        assert isinstance(ydata, np.ndarray)
        assert ydata.shape == (30,), f"Expected shape (30,), got {ydata.shape}"

        # Content - must be in [0, 1]
        assert ydata.min() >= 0.0, f"Normalized y min should be >= 0, got {ydata.min()}"
        assert ydata.max() <= 1.0, f"Normalized y max should be <= 1, got {ydata.max()}"

        # Check exact endpoints
        np.testing.assert_allclose(ydata[0], 0.0, atol=1e-10)
        np.testing.assert_allclose(ydata[-1], 1.0, atol=1e-10)

        plt.close(fig)

    def test_normalized_panel_preserves_monotonicity(self):
        """Normalized curve preserves monotonic ordering from input."""
        x = np.array([1.0, 3.0, 5.0, 7.0, 9.0])
        y = np.array([0.5, 0.7, 0.85, 0.95, 0.99])  # Monotonically increasing
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[1]
        lines = ax.get_lines()
        line = lines[0]
        ydata = line.get_ydata()

        # Check monotonicity: y[i+1] >= y[i]
        diffs = np.diff(ydata)

        # Type check
        assert isinstance(diffs, np.ndarray)

        # Shape check
        assert diffs.shape == (4,), f"Expected shape (4,), got {diffs.shape}"

        # Content check - all diffs should be >= 0
        assert np.all(diffs >= -1e-10), (
            f"Normalized curve should be monotonically increasing. "
            f"Found negative diffs: {diffs[diffs < -1e-10]}"
        )

        plt.close(fig)


class TestPlotKneedleInternalsDifferenceCurvePanel:
    """Tests verifying difference curve panel shows curvature."""

    def test_difference_panel_has_correct_length(self):
        """Difference curve has same length as input data."""
        x = np.linspace(0, 8, 40)
        y = np.log1p(x)
        fig = plot_kneedle_internals(x, y)

        # Panel 2 should be difference curve
        ax = fig.axes[2]
        lines = ax.get_lines()
        assert len(lines) >= 1, "Difference panel should have at least one line"

        line = lines[0]
        ydata = line.get_ydata()

        # Shape check
        assert ydata.shape == (40,), f"Expected shape (40,), got {ydata.shape}"

        plt.close(fig)

    def test_difference_panel_has_positive_maximum(self):
        """Difference curve has a positive maximum for concave increasing curve."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)  # Concave increasing
        fig = plot_kneedle_internals(x, y, curve="concave", direction="increasing")

        ax = fig.axes[2]
        lines = ax.get_lines()
        line = lines[0]
        ydata = line.get_ydata()

        # Type check
        assert isinstance(ydata, np.ndarray)

        # Content check - max should be positive
        max_val = ydata.max()
        assert isinstance(max_val, (float, np.floating)), f"Expected float, got {type(max_val)}"
        assert max_val > 0, f"Difference curve max should be > 0, got {max_val}"

        plt.close(fig)

    def test_difference_panel_maximum_location(self):
        """Difference curve maximum occurs in middle region for typical elbow."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[2]
        lines = ax.get_lines()
        line = lines[0]
        ydata = line.get_ydata()

        # Find argmax
        max_idx = np.argmax(ydata)

        # Type check
        assert isinstance(max_idx, (int, np.integer)), f"Expected int, got {type(max_idx)}"

        # Content check - should be in middle region (not at edges)
        # For typical elbow curve, max difference is in [10%, 90%] of the data
        assert 10 <= max_idx <= 90, (
            f"Difference curve maximum should be in middle region [10, 90], got index {max_idx}"
        )

        plt.close(fig)


class TestPlotKneedleInternalsElbowMarking:
    """Tests verifying elbow point is marked on annotated panel."""

    def test_annotated_panel_has_scatter_points(self):
        """Annotated panel has scatter points marking the elbow."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        # Panel 3 should be annotated curve
        ax = fig.axes[3]
        collections = ax.collections

        # Should have at least one collection (scatter plot)
        assert len(collections) >= 1, (
            f"Annotated panel should have scatter points for elbow marking, "
            f"found {len(collections)} collections"
        )

        # Get first collection
        coll = collections[0]

        # Check it has offsets (scatter plot)
        offsets = coll.get_offsets()
        assert isinstance(offsets, np.ndarray), f"Expected ndarray, got {type(offsets)}"

        # Shape check - should be (n, 2) for n points
        assert offsets.ndim == 2, f"Expected 2D array, got {offsets.ndim}D"
        assert offsets.shape[1] == 2, f"Expected 2 columns (x, y), got {offsets.shape[1]}"

        # Should have at least 1 point
        assert offsets.shape[0] >= 1, f"Expected >= 1 scatter points, got {offsets.shape[0]}"

        plt.close(fig)

    def test_scatter_points_have_nonzero_size(self):
        """Scatter points have nonzero marker size."""
        x = np.linspace(0, 10, 100)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        ax = fig.axes[3]
        collections = ax.collections
        assert len(collections) >= 1

        coll = collections[0]
        sizes = coll.get_sizes()

        # Type check
        assert isinstance(sizes, np.ndarray), f"Expected ndarray, got {type(sizes)}"

        # Content check - all sizes should be > 0
        assert np.all(sizes > 0), f"Scatter point sizes should be > 0, got {sizes}"

        plt.close(fig)


class TestPlotKneedleInternalsLogScale:
    """Tests verifying log scale when log_x=True."""

    def test_log_scale_applied_to_original_panel(self):
        """When log_x=True, original panel uses log scale on x-axis."""
        x = np.logspace(-12, -3, 50)
        y = np.linspace(0.001, 0.5, 50)
        fig = plot_kneedle_internals(x, y, log_x=True)

        # Original panel (panel 0) should have log x scale
        ax = fig.axes[0]
        xscale = ax.get_xscale()

        # Type check
        assert isinstance(xscale, str), f"Expected str, got {type(xscale)}"

        # Content check
        assert xscale == "log", f"Expected log scale, got {xscale}"

        plt.close(fig)

    def test_log_scale_not_applied_when_false(self):
        """When log_x=False, original panel uses linear scale."""
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y, log_x=False)

        # Original panel should have linear scale
        ax = fig.axes[0]
        xscale = ax.get_xscale()

        # Type check
        assert isinstance(xscale, str)

        # Content check
        assert xscale == "linear", f"Expected linear scale, got {xscale}"

        plt.close(fig)


class TestPlotKneedleInternalsEdgeCases:
    """Tests verifying edge case handling."""

    def test_handles_linear_data(self):
        """Handles perfectly linear data without crashing."""
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        fig = plot_kneedle_internals(x, y)

        # Should still create 4 panels
        assert len(fig.axes) == 4

        # Each panel should have content
        for i, ax in enumerate(fig.axes):
            has_content = len(ax.get_lines()) > 0 or len(ax.collections) > 0
            assert has_content, f"Panel {i} should have visual content"

        plt.close(fig)

    def test_handles_minimum_array_size(self):
        """Handles minimum array size (2 points)."""
        x = np.array([0.0, 1.0])
        y = np.array([0.0, 1.0])
        fig = plot_kneedle_internals(x, y)

        # Should create 4 panels
        assert len(fig.axes) == 4

        # Original panel should plot both points
        ax = fig.axes[0]
        lines = ax.get_lines()
        assert len(lines) >= 1

        line = lines[0]
        xdata = line.get_xdata()

        # Shape check
        assert xdata.shape == (2,), f"Expected shape (2,), got {xdata.shape}"

        plt.close(fig)

    def test_handles_noisy_data(self):
        """Handles noisy data with local fluctuations."""
        rng = np.random.default_rng(42)
        x = np.linspace(0, 10, 100)
        y = (1 - np.exp(-x)) + rng.normal(0, 0.05, 100)
        fig = plot_kneedle_internals(x, y)

        # Should create all panels
        assert len(fig.axes) == 4

        # Check data is actually plotted in original panel
        ax = fig.axes[0]
        lines = ax.get_lines()
        assert len(lines) >= 1

        line = lines[0]
        ydata = line.get_ydata()

        # Shape check
        assert ydata.shape == (100,), f"Expected shape (100,), got {ydata.shape}"

        # Content check - should have noise variance
        std_dev = np.std(np.diff(ydata))
        assert std_dev > 0.01, f"Expected noisy data, got std={std_dev}"

        plt.close(fig)

    def test_handles_step_function(self):
        """Handles step function data."""
        x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        fig = plot_kneedle_internals(x, y)

        # Should create 4 panels
        assert len(fig.axes) == 4

        # Normalized panel should still be in [0, 1]
        ax = fig.axes[1]
        lines = ax.get_lines()
        line = lines[0]
        ydata = line.get_ydata()

        # Content check
        assert ydata.min() >= -1e-10, f"Normalized y min should be >= 0, got {ydata.min()}"
        assert ydata.max() <= 1 + 1e-10, f"Normalized y max should be <= 1, got {ydata.max()}"

        plt.close(fig)


class TestPlotKneedleInternalsConfiguration:
    """Tests verifying PlotConfig integration."""

    def test_uses_custom_figsize(self):
        """Uses custom figsize from PlotConfig."""
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        config = PlotConfig(figsize_elbow_internals=(20, 10))
        fig = plot_kneedle_internals(x, y, config=config)

        actual_size = fig.get_size_inches()

        # Type and shape
        assert isinstance(actual_size, np.ndarray)
        assert actual_size.shape == (2,)

        # Content - exact values
        np.testing.assert_allclose(actual_size, [20, 10], rtol=1e-10)

        plt.close(fig)

    def test_uses_custom_dpi(self):
        """Uses custom DPI from PlotConfig."""
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        config = PlotConfig(dpi=150)
        fig = plot_kneedle_internals(x, y, config=config)

        # Type check
        assert isinstance(fig.dpi, (int, float))

        # Content check
        assert fig.dpi == 150, f"Expected DPI=150, got {fig.dpi}"

        plt.close(fig)

    def test_none_config_uses_defaults(self):
        """When config=None, uses default PlotConfig values."""
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y, config=None)

        # Should use default DPI (300)
        default_config = PlotConfig()
        assert fig.dpi == default_config.dpi

        # Should still create 4 panels
        assert len(fig.axes) == 4

        plt.close(fig)
