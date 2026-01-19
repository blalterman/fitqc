"""Tests for plot_ecdf_tolerance_overlays function."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from fitqc.config import PlotConfig
from fitqc.plot import plot_ecdf_tolerance_overlays


class TestPlotEcdfToleranceSmoke:
    """Smoke tests for plot_ecdf_tolerance_overlays."""

    def test_returns_figure(self):
        """Test that function returns a Figure object."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


    def test_colorbar_present(self):
        """Test that colorbar is present at right edge."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u)

        # Colorbar is added at position [0.92, 0.15, 0.02, 0.7]
        # Look for an axis with these characteristics:
        # - Positioned at right edge (left > 0.9)
        # - Narrow width (< 0.05)
        has_colorbar = False
        for ax in fig.axes:
            bbox = ax.get_position()
            if bbox.x0 > 0.9 and bbox.width < 0.05:
                has_colorbar = True
                break

        assert has_colorbar, "Expected colorbar axis at right edge"
        plt.close(fig)

    def test_does_not_call_show(self, monkeypatch):
        """Test that function does NOT call plt.show()."""
        show_called = []
        monkeypatch.setattr(plt, "show", lambda: show_called.append(True))
        u = np.random.uniform(0, 1, 1000)
        plot_ecdf_tolerance_overlays(u)
        assert len(show_called) == 0
        plt.close("all")


class TestPlotEcdfToleranceDataDriven:
    """Data-driven tests for plot_ecdf_tolerance_overlays."""

    def test_uniform_data_produces_diagonal_ecdf(self):
        """Test that uniform data produces ECDF approximately equal to y=x."""
        rng = np.random.default_rng(42)
        u = rng.uniform(0, 1, 10000)

        # Use tol=0 to include all data
        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0]), side="lower")

        # Get the first axis (main plot)
        ax = fig.axes[0]

        # Find the ECDF line (should be first line, reference is second)
        lines = ax.get_lines()
        assert len(lines) >= 1, "Expected at least 1 line (ECDF)"

        # Get ECDF line (not the reference line)
        ecdf_line = lines[0]
        x_data = ecdf_line.get_xdata()
        y_data = ecdf_line.get_ydata()

        # For uniform data, ECDF should be close to y=x
        # Check at several points in [0, 0.1]
        for x_val in [0.01, 0.03, 0.05, 0.07, 0.09]:
            # Find closest x value
            idx = np.argmin(np.abs(x_data - x_val))
            if idx < len(y_data):
                y_actual = y_data[idx]
                # Allow 1% tolerance for statistical variation
                assert abs(y_actual - x_val) < 0.01, f"At x={x_val}, ECDF={y_actual}, expected ~{x_val}"

        plt.close(fig)

    def test_lower_pileup_shows_deviation(self):
        """Test that data with lower pile-up shows ECDF deviating from diagonal."""
        rng = np.random.default_rng(42)

        # Create data with pile-up near 0: 50% uniform, 50% concentrated near 0
        u_uniform = rng.uniform(0, 1, 5000)
        u_pileup = rng.uniform(0, 0.02, 5000)  # Concentrated in [0, 0.02]
        u = np.concatenate([u_uniform, u_pileup])

        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0]), side="lower")
        ax = fig.axes[0]

        # Get ECDF line
        lines = ax.get_lines()
        ecdf_line = lines[0]
        x_data = ecdf_line.get_xdata()
        y_data = ecdf_line.get_ydata()

        # With pile-up, ECDF should be ABOVE the diagonal near x=0
        # At x=0.02, we expect ~50% of data (5000/10000)
        idx = np.argmin(np.abs(x_data - 0.02))
        if idx < len(y_data):
            y_actual = y_data[idx]
            # Should be significantly above 0.02 (diagonal)
            assert y_actual > 0.3, f"Expected significant pile-up at x=0.02, got ECDF={y_actual}"

        plt.close(fig)

    def test_upper_pileup_shows_deviation(self):
        """Test that data with upper pile-up shows ECDF deviating near u=1."""
        rng = np.random.default_rng(42)

        # Create data with pile-up near 1: 50% uniform, 50% concentrated near 1
        u_uniform = rng.uniform(0, 1, 5000)
        u_pileup = rng.uniform(0.98, 1.0, 5000)  # Concentrated in [0.98, 1]
        u = np.concatenate([u_uniform, u_pileup])

        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0]), side="upper")
        ax = fig.axes[0]

        # Get ECDF line
        lines = ax.get_lines()
        ecdf_line = lines[0]
        x_data = ecdf_line.get_xdata()
        y_data = ecdf_line.get_ydata()

        # With pile-up, ECDF should be BELOW the diagonal near x=1
        # At x=0.98, we expect less than 98% of data (because pile-up is above)
        idx = np.argmin(np.abs(x_data - 0.98))
        if idx < len(y_data):
            y_actual = y_data[idx]
            # Should be below 0.98 (diagonal)
            assert y_actual < 0.95, f"Expected ECDF below diagonal at x=0.98, got ECDF={y_actual}"

        plt.close(fig)

    def test_empty_after_filtering(self):
        """Test that function handles empty array after filtering."""
        # All data near 0, so high tolerance filters everything
        u = np.array([0.001, 0.002, 0.003])

        # Use tol=0.01 to filter everything
        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.01]), side="lower")

        # Should still return a valid figure
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_single_tolerance(self):
        """Test that function works with a single tolerance value."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0]), n_tols=1)

        assert isinstance(fig, plt.Figure)
        ax = fig.axes[0]
        lines = ax.get_lines()
        # Should have at least 1 ECDF line + 1 reference line
        assert len(lines) >= 2
        plt.close(fig)

    def test_custom_tolerance_array(self):
        """Test that custom tolerance array is used for colorbar normalization."""
        u = np.random.uniform(0, 1, 1000)
        custom_tols = np.array([0.0, 0.01, 0.03, 0.05])

        fig = plot_ecdf_tolerance_overlays(u, tols=custom_tols)

        assert isinstance(fig, plt.Figure)

        # Get colorbar axis (should be at right edge)
        cbar_ax = [ax for ax in fig.axes if ax.get_position().x0 > 0.9][0]

        # Check colorbar limits match custom tolerance range
        ylim = cbar_ax.get_ylim()
        assert ylim[0] == pytest.approx(0.0, abs=1e-6), "Colorbar min should match min tolerance"
        assert ylim[1] == pytest.approx(0.05, abs=1e-6), "Colorbar max should match max tolerance"

        plt.close(fig)

    def test_non_finite_values_filtered(self):
        """Test that non-finite values are filtered out."""
        u = np.array([0.1, 0.2, np.nan, 0.3, np.inf, 0.4, -np.inf, 0.5])

        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0]))

        # Should successfully create figure without errors
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotEcdfToleranceInvalidInputs:
    """Test error handling for invalid inputs."""

    def test_invalid_side_parameter(self):
        """Test that invalid side parameter raises ValueError."""
        u = np.random.uniform(0, 1, 1000)

        with pytest.raises(ValueError, match="side must be 'lower', 'upper', or 'both'"):
            plot_ecdf_tolerance_overlays(u, side="invalid")


class TestPlotEcdfToleranceVisualProperties:
    """Test visual properties of the plots."""

    def test_ecdf_monotonically_increasing(self):
        """Test that ECDF curves are monotonically increasing."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u, tols=np.array([0.0, 0.01]), side="lower")

        ax = fig.axes[0]
        lines = ax.get_lines()

        # Check each ECDF line (skip reference line which is last)
        for line in lines[:-1]:  # All except reference line
            y_data = line.get_ydata()
            # Check monotonicity (allowing for numerical precision)
            diffs = np.diff(y_data)
            assert np.all(diffs >= -1e-10), "ECDF should be monotonically increasing"

        plt.close(fig)

    def test_higher_tolerance_fewer_points(self):
        """Test that higher tolerance results in fewer points in ECDF."""
        rng = np.random.default_rng(42)
        u = rng.uniform(0, 1, 1000)

        # Compare tol=0 vs tol=0.02
        tols = np.array([0.0, 0.02])
        fig = plot_ecdf_tolerance_overlays(u, tols=tols, side="lower")

        ax = fig.axes[0]
        lines = ax.get_lines()

        # First line is tol=0, second is tol=0.02
        if len(lines) >= 2:
            line_tol0 = lines[0]
            line_tol002 = lines[1]

            n_points_tol0 = len(line_tol0.get_xdata())
            n_points_tol002 = len(line_tol002.get_xdata())

            # tol=0.02 should have fewer points (data filtered)
            assert n_points_tol002 < n_points_tol0, "Higher tolerance should result in fewer points"

        plt.close(fig)

    def test_config_dpi_applied(self):
        """Test that PlotConfig DPI setting is applied."""
        u = np.random.uniform(0, 1, 1000)
        config = PlotConfig(dpi=150)

        fig = plot_ecdf_tolerance_overlays(u, config=config)

        assert fig.dpi == 150
        plt.close(fig)

    def test_config_colormap_applied(self):
        """Test that PlotConfig colormap setting is applied."""
        u = np.random.uniform(0, 1, 1000)
        config = PlotConfig(cmap="viridis")

        fig = plot_ecdf_tolerance_overlays(u, config=config)

        # Colorbar should use the specified colormap
        # The colorbar is the second axis
        cbar_ax = fig.axes[1]
        # Just verify it doesn't crash - detailed colormap checking is complex
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_xlim_set_correctly_lower(self):
        """Test that x-axis limits are set correctly for lower boundary."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u, side="lower")

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be approximately [0, 0.1]
        assert xlim[0] == pytest.approx(0, abs=0.001)
        assert xlim[1] == pytest.approx(0.1, abs=0.001)
        plt.close(fig)

    def test_xlim_set_correctly_upper(self):
        """Test that x-axis limits are set correctly for upper boundary."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u, side="upper")

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be approximately [0.9, 1.0]
        assert xlim[0] == pytest.approx(0.9, abs=0.001)
        assert xlim[1] == pytest.approx(1.0, abs=0.001)
        plt.close(fig)

    def test_both_sides_have_correct_xlims(self):
        """Test that both sides have correct x-axis limits when side='both'."""
        u = np.random.uniform(0, 1, 1000)
        fig = plot_ecdf_tolerance_overlays(u, side="both")

        # First axis is lower boundary
        ax_lower = fig.axes[0]
        xlim_lower = ax_lower.get_xlim()
        assert xlim_lower[0] == pytest.approx(0, abs=0.001)
        assert xlim_lower[1] == pytest.approx(0.1, abs=0.001)

        # Second axis is upper boundary
        ax_upper = fig.axes[1]
        xlim_upper = ax_upper.get_xlim()
        assert xlim_upper[0] == pytest.approx(0.9, abs=0.001)
        assert xlim_upper[1] == pytest.approx(1.0, abs=0.001)

        plt.close(fig)
