"""Tests for plot_quantile_spacing_overlays function."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from fitqc.config import PlotConfig
from fitqc.plot import plot_quantile_spacing_overlays


class TestPlotQuantileSpacingOverlaysSmoke:
    """Smoke tests for basic functionality."""

    def test_returns_figure(self):
        """Test that function returns a Figure object."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_one_axis(self):
        """Test that figure has exactly 1 main axis plus colorbar."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x)

        # Should have at least 2 axes (main plot + colorbar)
        assert len(fig.axes) >= 2
        plt.close(fig)

    def test_colorbar_present(self):
        """Test that colorbar is present at right edge."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x)

        # Check for colorbar axis at right edge (left > 0.9, narrow width)
        has_colorbar = False
        for ax in fig.axes:
            bbox = ax.get_position()
            if bbox.x0 > 0.9 and bbox.width < 0.05:
                has_colorbar = True
                break

        assert has_colorbar, "Expected colorbar axis at right edge"
        plt.close(fig)

    def test_works_without_bounds(self):
        """Test that function works without L/U (no tolerance filtering)."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_works_with_bounds(self):
        """Test that function works with L/U (tolerance filtering enabled)."""
        x = np.sort(np.random.default_rng(42).random(1000))
        L, U = 0.0, 1.0
        fig = plot_quantile_spacing_overlays(x, L=L, U=U)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_custom_config(self):
        """Test that custom PlotConfig is respected."""
        x = np.sort(np.random.default_rng(42).random(1000))
        config = PlotConfig(dpi=100, cmap="viridis", figsize_tolerance=(10, 6))
        fig = plot_quantile_spacing_overlays(x, config=config)

        assert fig.dpi == 100
        plt.close(fig)

    def test_custom_tolerances(self):
        """Test that custom tolerance array is used for colorbar normalization."""
        x = np.sort(np.random.default_rng(42).random(1000))
        tols = np.array([0.0, 0.01, 0.02, 0.05])
        fig = plot_quantile_spacing_overlays(x, L=0.0, U=1.0, tols=tols)

        assert isinstance(fig, plt.Figure)

        # Get colorbar axis (should be at right edge)
        cbar_ax = [ax for ax in fig.axes if ax.get_position().x0 > 0.9][0]

        # Check colorbar limits match custom tolerance range
        ylim = cbar_ax.get_ylim()
        assert ylim[0] == pytest.approx(0.0, abs=1e-6), "Colorbar min should match min tolerance"
        assert ylim[1] == pytest.approx(0.05, abs=1e-6), "Colorbar max should match max tolerance"

        plt.close(fig)


class TestPlotQuantileSpacingOverlaysDataDriven:
    """Data-driven tests for spacing behavior."""

    def test_uniform_data_constant_spacing(self):
        """Test that uniform data produces roughly constant spacing."""
        # Uniform data should have roughly constant quantile spacing
        x = np.sort(np.linspace(0, 1, 10000))
        fig = plot_quantile_spacing_overlays(x, q_max=0.5, n_quantiles=50)

        # Get the main axis (not colorbar)
        main_ax = fig.axes[0]

        # Check that lines were plotted
        assert len(main_ax.lines) > 0, "Expected spacing curves to be plotted"

        # For uniform data, spacing should be relatively constant
        # Check first plotted line (tol=0)
        line = main_ax.lines[0]
        ydata = line.get_ydata()

        # Spacing should have low coefficient of variation for uniform data
        cv = np.std(ydata) / np.mean(ydata)
        assert cv < 0.5, f"Expected constant spacing for uniform data, got CV={cv}"

        plt.close(fig)

    def test_pileup_shows_compressed_spacing(self):
        """Test that data with pile-up near zero shows compressed spacing initially."""
        rng = np.random.default_rng(42)

        # Create data with extreme pile-up at lower boundary
        # 90% of data concentrated in first 1% of range, rest spread across 99%
        pileup = rng.uniform(0, 0.01, 900)
        normal = rng.uniform(0.01, 1.0, 100)
        x = np.sort(np.concatenate([pileup, normal]))

        # Look at first 20% of data to see the pile-up region
        fig = plot_quantile_spacing_overlays(x, L=0.0, U=1.0, q_max=0.2, n_quantiles=100)

        # Get the main axis
        main_ax = fig.axes[0]
        assert len(main_ax.lines) > 0

        # For tol=0 (first line), spacing within pile-up should be small
        # compared to spacing after pile-up
        line = main_ax.lines[0]
        ydata = line.get_ydata()

        # Within pile-up region (first 80% of the first 20% of data)
        # vs transition region (last 20% of the first 20% of data)
        pile_region = np.mean(ydata[:80])
        transition_region = np.mean(ydata[-20:])

        # Pile-up region should have much smaller spacing
        assert pile_region < transition_region, (
            f"Expected smaller spacing in pile-up region, got pile={pile_region}, trans={transition_region}"
        )

        plt.close(fig)

    def test_higher_tolerance_removes_pileup(self):
        """Test that higher tolerance removes pile-up, producing more uniform spacing."""
        rng = np.random.default_rng(42)

        # Create data with strong pile-up at lower boundary
        pileup = rng.uniform(0, 0.01, 700)
        normal = rng.uniform(0.01, 1.0, 300)
        x = np.sort(np.concatenate([pileup, normal]))

        # Use specific tolerances - high tolerance should remove pile-up region
        tols = np.array([0.0, 0.015])  # Second tolerance removes pile-up region

        fig = plot_quantile_spacing_overlays(x, L=0.0, U=1.0, tols=tols, q_max=0.5, n_quantiles=50)

        main_ax = fig.axes[0]
        assert len(main_ax.lines) >= 2

        # After filtering with tol=0.015, the data should be more uniform
        # Check that the mean spacing increases (fewer samples in small region)
        line_tol0 = main_ax.lines[0]
        line_tol015 = main_ax.lines[1]

        mean_tol0 = np.mean(line_tol0.get_ydata())
        mean_tol015 = np.mean(line_tol015.get_ydata())

        # After removing pile-up region, mean spacing should increase
        assert mean_tol015 > mean_tol0 * 1.5, (
            f"Expected larger spacing after filtering, got mean0={mean_tol0}, mean015={mean_tol015}"
        )

        plt.close(fig)

    def test_spacing_always_nonnegative(self):
        """Test that spacing is always non-negative (since input is sorted)."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x, q_max=0.5, n_quantiles=100)

        main_ax = fig.axes[0]

        # Check all plotted curves have non-negative y-values
        # Skip the reference line (horizontal line with constant y-value)
        for line in main_ax.lines:
            ydata = line.get_ydata()
            # Convert to array if it's a list
            ydata_array = np.array(ydata)

            # Skip horizontal reference lines (constant y-value)
            if len(ydata_array) > 1 and np.std(ydata_array) > 0:
                assert np.all(ydata_array >= 0), "Spacing should be non-negative"

        plt.close(fig)


class TestPlotQuantileSpacingOverlaysEdgeCases:
    """Edge case tests."""

    def test_small_array(self):
        """Test with array smaller than n_quantiles."""
        x = np.array([0.0, 0.1, 0.2, 0.3, 0.4])  # Only 5 elements
        fig = plot_quantile_spacing_overlays(x, n_quantiles=100)

        # Should still produce a figure, but with fewer points
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_single_tolerance(self):
        """Test with single tolerance value."""
        x = np.sort(np.random.default_rng(42).random(1000))
        tols = np.array([0.0])

        fig = plot_quantile_spacing_overlays(x, tols=tols)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_unsorted_input_raises(self):
        """Test that non-sorted input raises assertion error."""
        x = np.random.default_rng(42).random(100)  # Not sorted

        with pytest.raises(AssertionError, match="x_sorted must be sorted"):
            plot_quantile_spacing_overlays(x)

    def test_empty_after_filtering(self):
        """Test behavior when filtering removes all data."""
        # Small array, high tolerance
        x = np.array([0.5])

        # Tolerance that removes everything
        tols = np.array([0.6])

        fig = plot_quantile_spacing_overlays(x, L=0.0, U=1.0, tols=tols)

        # Should still return a figure, just with no curves
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_array_with_inf_nan(self):
        """Test handling of non-finite values."""
        x = np.array([0.0, 0.1, np.nan, 0.3, np.inf, 0.5, 0.7])
        x_sorted = np.sort(x)

        # Should handle non-finite values gracefully
        fig = plot_quantile_spacing_overlays(x_sorted)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_very_small_q_max(self):
        """Test with very small q_max."""
        x = np.sort(np.random.default_rng(42).random(1000))
        fig = plot_quantile_spacing_overlays(x, q_max=0.01, n_quantiles=10)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_duplicate_values(self):
        """Test with duplicate values (zero spacing)."""
        # Array with many duplicates
        x = np.sort(np.array([0.0] * 100 + [0.5] * 100 + [1.0] * 100))

        fig = plot_quantile_spacing_overlays(x, q_max=0.5, n_quantiles=50)

        # Should handle zero spacings
        assert isinstance(fig, plt.Figure)

        # Check that some spacings are zero
        main_ax = fig.axes[0]
        if len(main_ax.lines) > 0:
            ydata = main_ax.lines[0].get_ydata()
            assert np.any(ydata == 0), "Expected some zero spacings with duplicates"

        plt.close(fig)


class TestPlotQuantileSpacingOverlaysValidation:
    """Validation tests for input requirements."""

    def test_sorted_with_duplicates_accepted(self):
        """Test that sorted array with duplicates is accepted."""
        x = np.array([0.0, 0.1, 0.1, 0.2, 0.3, 0.3, 0.3, 0.5])
        fig = plot_quantile_spacing_overlays(x)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_descending_raises(self):
        """Test that descending array raises assertion error."""
        x = np.array([1.0, 0.9, 0.8, 0.7])

        with pytest.raises(AssertionError, match="x_sorted must be sorted"):
            plot_quantile_spacing_overlays(x)

    def test_partially_sorted_raises(self):
        """Test that partially sorted array raises assertion error."""
        x = np.array([0.0, 0.2, 0.1, 0.3])  # Not fully sorted

        with pytest.raises(AssertionError, match="x_sorted must be sorted"):
            plot_quantile_spacing_overlays(x)

    def test_bounds_filtering_reduces_data(self):
        """Test that providing bounds with tolerance actually filters data."""
        rng = np.random.default_rng(42)
        x = np.sort(rng.uniform(0, 1, 1000))

        # With high tolerance, should remove data near boundaries
        tols = np.array([0.0, 0.1])  # 10% tolerance
        fig = plot_quantile_spacing_overlays(x, L=0.0, U=1.0, tols=tols, q_max=0.5, n_quantiles=100)

        main_ax = fig.axes[0]

        # With tolerance filtering, curves should differ
        # (tol=0.1 should have different spacing pattern than tol=0)
        if len(main_ax.lines) >= 2:
            line0 = main_ax.lines[0].get_ydata()
            line1 = main_ax.lines[1].get_ydata()

            # Lines should be different due to filtering
            # (though both arrays might have different lengths, compare means)
            mean0 = np.mean(line0)
            mean1 = np.mean(line1)

            # With 10% tolerance removing boundary data, mean spacing should change
            assert not np.allclose(mean0, mean1, rtol=0.01), (
                "Expected different spacing patterns with tolerance filtering"
            )

        plt.close(fig)
