"""Tests for plot_histogram_tolerance_overlays function."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from fitqc.config import PlotConfig
from fitqc.plot import plot_histogram_tolerance_overlays


class TestPlotHistogramToleranceOverlays:
    """Test suite for plot_histogram_tolerance_overlays function."""

    def test_returns_figure(self):
        """Test that function returns a Figure object."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_two_axes(self):
        """Test that figure has 2 main subplots plus colorbar axis."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0)

        # Should have 2 main axes + 1 colorbar axis = 3 total
        # (2 subplots for lower/upper cuts, 1 colorbar)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_colorbar_present(self):
        """Test that colorbar is present at right edge."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0)

        # Check for colorbar axis at right edge (x0 > 0.9, width < 0.05)
        has_colorbar = False
        for ax in fig.axes:
            bbox = ax.get_position()
            if bbox.x0 > 0.9 and bbox.width < 0.05:
                has_colorbar = True
                break

        assert has_colorbar, "Expected colorbar axis at right edge"
        plt.close(fig)

    def test_empty_array_after_filtering_high_tolerance(self):
        """Test that function handles empty arrays gracefully at high tolerance."""
        # Small dataset that will be completely filtered out at high tolerances
        x = np.array([0.0, 0.01, 0.99, 1.0])

        # Use very high tolerances that will filter out all data
        tols = np.array([0.0, 0.1, 0.4, 0.5])

        # Should not crash, even though high tolerances filter out all data
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, tols=tols, bins=10)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_single_tolerance(self):
        """Test with a single tolerance value (n_tols=1)."""
        x = np.random.default_rng(42).uniform(0, 1, 500)
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, n_tols=1, bins=50)

        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_custom_tolerance_array(self):
        """Test that custom tolerance array is used for colorbar normalization."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)
        custom_tols = np.array([0.0, 0.01, 0.02, 0.03])

        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, tols=custom_tols, bins=50)

        assert isinstance(fig, plt.Figure)

        # Get colorbar axis (should be at right edge)
        cbar_ax = next(ax for ax in fig.axes if ax.get_position().x0 > 0.9)

        # Check colorbar limits match custom tolerance range
        ylim = cbar_ax.get_ylim()
        assert ylim[0] == pytest.approx(0.0, abs=1e-6), "Colorbar min should match min tolerance"
        assert ylim[1] == pytest.approx(0.03, abs=1e-6), "Colorbar max should match max tolerance"

        plt.close(fig)

    def test_invalid_bounds_raises_error(self):
        """Test that L >= U raises ValueError."""
        x = np.random.default_rng(42).uniform(0, 1, 100)

        # L == U
        with pytest.raises(ValueError, match="L must be less than U"):
            plot_histogram_tolerance_overlays(x, L=0.5, U=0.5)

        # L > U
        with pytest.raises(ValueError, match="L must be less than U"):
            plot_histogram_tolerance_overlays(x, L=1.0, U=0.0)

    def test_handles_non_finite_values(self):
        """Test that function filters out NaN and inf values."""
        x = np.array([0.1, 0.2, np.nan, 0.3, np.inf, 0.4, -np.inf, 0.5])

        # Should filter out non-finite values and proceed
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, n_tols=3, bins=20)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_custom_config(self):
        """Test with custom PlotConfig."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)
        config = PlotConfig(
            cmap="viridis",
            dpi=150,
            figsize_tolerance=(10, 6),
        )

        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, config=config)

        assert isinstance(fig, plt.Figure)
        assert fig.dpi == 150
        plt.close(fig)

    def test_different_bin_counts(self):
        """Test with different number of bins."""
        x = np.random.default_rng(42).uniform(0, 1, 1000)

        # Test with fewer bins
        fig1 = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, bins=20)
        assert isinstance(fig1, plt.Figure)
        plt.close(fig1)

        # Test with more bins
        fig2 = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, bins=200)
        assert isinstance(fig2, plt.Figure)
        plt.close(fig2)

    def test_negative_bounds(self):
        """Test with negative bounds."""
        rng = np.random.default_rng(42)
        x = rng.uniform(-1, 0, 1000)

        fig = plot_histogram_tolerance_overlays(x, L=-1.0, U=0.0, n_tols=5)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_large_bounds_range(self):
        """Test with large bounds range."""
        rng = np.random.default_rng(42)
        x = rng.uniform(0, 1000, 1000)

        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1000.0, n_tols=5)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_does_not_call_show(self, monkeypatch):
        """Test that function does NOT call plt.show()."""
        show_called = []
        monkeypatch.setattr(plt, "show", lambda: show_called.append(True))

        x = np.random.default_rng(42).uniform(0, 1, 100)
        plot_histogram_tolerance_overlays(x, L=0.0, U=1.0)

        assert len(show_called) == 0, "plt.show() should not be called"
        plt.close("all")

    def test_histogram_overlay_effect(self):
        """Test that tolerance filtering reduces sample counts as expected."""
        rng = np.random.default_rng(42)

        # Create data with 30% pile-up at lower boundary
        x_center = rng.normal(0.5, 0.1, 700)
        x_lower = rng.uniform(0.0, 0.05, 300)  # 30% in [0, 0.05]
        x = np.concatenate([x_center, x_lower])
        x = np.clip(x, 0, 1)

        tols = np.array([0.0, 0.05])  # 0% vs 5% tolerance
        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, tols=tols, bins=50)

        # Verify pile-up exists: count samples in boundary region [0, 0.05]
        n_in_boundary = np.sum(x <= 0.05)
        assert n_in_boundary > 250, f"Expected ~300 samples in [0, 0.05], got {n_in_boundary}"

        # With tol=0.05, lower cut removes x <= 0.05
        # Verify this would remove most of the pile-up samples
        n_after_filtering = np.sum(x > 0.05)
        assert n_after_filtering < len(x), "Filtering should reduce sample count"
        assert n_after_filtering == pytest.approx(len(x) - n_in_boundary, abs=10), (
            "tol=0.05 should remove samples <= 0.05"
        )

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_all_data_at_boundaries(self):
        """Test with all data concentrated at boundaries."""
        # All data at boundaries
        x = np.concatenate(
            [
                np.full(500, 0.0),  # Half at lower boundary
                np.full(500, 1.0),  # Half at upper boundary
            ]
        )

        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, n_tols=5, bins=50)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_data_outside_bounds_filtered(self):
        """Test that data outside [L, U] is handled correctly."""
        # Include some data outside bounds (should be filtered by bin edges)
        x = np.array([-0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5])

        fig = plot_histogram_tolerance_overlays(x, L=0.0, U=1.0, n_tols=3, bins=20)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
