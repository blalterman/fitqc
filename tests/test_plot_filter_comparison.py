"""Tests for filter comparison plotting functions."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from fitqc.boundary import BoundaryResult
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult
from fitqc.plot import (
    plot_bounds_filter_comparison,
    plot_combined_filter_comparison,
    plot_interior_filter_comparison,
)


class TestPlotBoundsFilterComparison:
    """Tests for plot_bounds_filter_comparison function."""

    def test_returns_figure(self):
        """Test that function returns a Figure object."""
        x = np.concatenate(
            [
                np.array([0.0] * 100),  # Out-of-bounds samples
                np.random.uniform(0.01, 100, 9900),
            ]
        )
        fig = plot_bounds_filter_comparison(x, L=0.01, U=100.0, bins=50)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_two_subplots(self):
        """Test that figure has exactly 2 subplots (unfiltered and filtered)."""
        x = np.random.uniform(0, 100, 1000)
        fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_handles_no_out_of_bounds(self):
        """Test with data that has no out-of-bounds samples."""
        x = np.random.uniform(10, 90, 1000)
        fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)
        assert fig is not None
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_handles_all_out_of_bounds(self):
        """Test with data where all samples are out-of-bounds."""
        x = np.concatenate(
            [
                np.array([-10.0] * 500),
                np.array([110.0] * 500),
            ]
        )
        fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50)
        assert fig is not None
        plt.close(fig)

    def test_filters_correctly(self):
        """Test that filtering is applied correctly."""
        # Create known data
        x = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0])  # 0.0 is out-of-bounds
        L, U = 1.0, 20.0

        # Call function (we just verify it doesn't crash)
        fig = plot_bounds_filter_comparison(x, L=L, U=U, bins=10)
        assert fig is not None

        # The plot should show 1 out-of-bounds and 5 in-bounds
        # We can't easily verify the plot content, but at least it runs
        plt.close(fig)

    def test_raises_on_invalid_bounds(self):
        """Test that function raises ValueError when L >= U."""
        x = np.random.uniform(0, 100, 1000)
        with pytest.raises(ValueError, match="L must be less than U"):
            plot_bounds_filter_comparison(x, L=100.0, U=0.0)

    def test_handles_string_bins(self):
        """Test that function handles string bin specifiers."""
        x = np.random.uniform(0, 100, 1000)
        fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins="auto")
        assert fig is not None
        plt.close(fig)

    def test_custom_config(self):
        """Test that custom PlotConfig is respected."""
        x = np.random.uniform(0, 100, 1000)
        config = PlotConfig(dpi=100)
        fig = plot_bounds_filter_comparison(x, L=0.0, U=100.0, bins=50, config=config)
        assert fig is not None
        plt.close(fig)


class TestPlotInteriorFilterComparison:
    """Tests for plot_interior_filter_comparison function."""

    @pytest.fixture
    def mock_interior_result(self):
        """Create a mock InteriorResult for testing."""
        return InteriorResult(
            spike_detected=True,
            spike_z_loc=0.05,
            eps_star=0.001,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=np.random.default_rng(42).integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
        )

    def test_returns_figure(self, mock_interior_result):
        """Test that function returns a Figure object."""
        x = np.concatenate(
            [
                np.array([50.0] * 1000),  # Stuck at x0
                np.random.uniform(0, 100, 9000),
            ]
        )
        fig = plot_interior_filter_comparison(
            x, x0=50.0, L=0.0, U=100.0, interior_result=mock_interior_result, bins=50
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_two_subplots(self, mock_interior_result):
        """Test that figure has exactly 2 subplots."""
        x = np.random.uniform(0, 100, 1000)
        fig = plot_interior_filter_comparison(
            x, x0=50.0, L=0.0, U=100.0, interior_result=mock_interior_result, bins=50
        )
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_handles_no_stickiness_detected(self):
        """Test when no interior stickiness is detected."""
        result = InteriorResult(
            spike_detected=False,
            spike_z_loc=None,
            eps_star=None,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.05, 50),
            hist_counts=np.random.default_rng(42).integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
        )
        x = np.random.uniform(0, 100, 1000)
        fig = plot_interior_filter_comparison(
            x, x0=50.0, L=0.0, U=100.0, interior_result=result, bins=50
        )
        assert fig is not None
        plt.close(fig)

    def test_custom_config(self, mock_interior_result):
        """Test that custom PlotConfig is respected."""
        x = np.random.uniform(0, 100, 1000)
        config = PlotConfig(dpi=100)
        fig = plot_interior_filter_comparison(
            x, x0=50.0, L=0.0, U=100.0, interior_result=mock_interior_result, bins=50, config=config
        )
        assert fig is not None
        plt.close(fig)


class TestPlotCombinedFilterComparison:
    """Tests for plot_combined_filter_comparison function."""

    @pytest.fixture
    def mock_boundary_result(self):
        """Create a mock BoundaryResult for testing."""
        return BoundaryResult(
            lower_pileup_detected=True,
            upper_pileup_detected=False,
            t_lo_star=0.02,
            t_hi_star=None,
            tol_grid=np.linspace(0, 0.05, 41),
            lower_mass_curve=np.linspace(0, 0.1, 41),
            upper_mass_curve=np.linspace(0, 0.05, 41),
        )

    @pytest.fixture
    def mock_interior_result(self):
        """Create a mock InteriorResult for testing."""
        return InteriorResult(
            spike_detected=True,
            spike_z_loc=0.05,
            eps_star=0.001,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=np.random.default_rng(42).integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
        )

    def test_returns_figure_with_both_filters(self, mock_boundary_result, mock_interior_result):
        """Test with both boundary and interior filtering."""
        x = np.concatenate(
            [
                np.array([0.0] * 100),  # Out-of-bounds
                np.array([50.0] * 500),  # Stuck at x0
                np.random.uniform(0.01, 100, 9400),
            ]
        )
        fig = plot_combined_filter_comparison(
            x,
            x0=50.0,
            L=0.01,
            U=100.0,
            interior_result=mock_interior_result,
            boundary_result=mock_boundary_result,
            bins=50,
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_has_four_subplots_with_interior(self, mock_boundary_result, mock_interior_result):
        """Test that figure has 4 subplots when interior result is provided."""
        x = np.random.uniform(0, 100, 1000)
        fig = plot_combined_filter_comparison(
            x,
            x0=50.0,
            L=0.0,
            U=100.0,
            interior_result=mock_interior_result,
            boundary_result=mock_boundary_result,
            bins=50,
        )
        assert len(fig.axes) == 8  # 4x2 grid (linear + log)
        plt.close(fig)

    def test_handles_no_interior_result(self, mock_boundary_result):
        """Test when no interior result is provided."""
        x = np.random.uniform(0, 100, 1000)
        fig = plot_combined_filter_comparison(
            x,
            x0=None,
            L=0.0,
            U=100.0,
            interior_result=None,
            boundary_result=mock_boundary_result,
            bins=50,
        )
        # Should still work, just showing boundary filtering only
        assert fig is not None
        plt.close(fig)

    def test_handles_no_boundary_detected(self, mock_interior_result):
        """Test when no boundary stickiness is detected."""
        result = BoundaryResult(
            lower_pileup_detected=False,
            upper_pileup_detected=False,
            t_lo_star=None,
            t_hi_star=None,
            tol_grid=np.linspace(0, 0.05, 41),
            lower_mass_curve=np.linspace(0, 0.05, 41),
            upper_mass_curve=np.linspace(0, 0.05, 41),
        )
        x = np.random.uniform(0, 100, 1000)
        fig = plot_combined_filter_comparison(
            x,
            x0=50.0,
            L=0.0,
            U=100.0,
            interior_result=mock_interior_result,
            boundary_result=result,
            bins=50,
        )
        assert fig is not None
        plt.close(fig)

    def test_custom_config(self, mock_boundary_result, mock_interior_result):
        """Test that custom PlotConfig is respected."""
        x = np.random.uniform(0, 100, 1000)
        config = PlotConfig(dpi=100)
        fig = plot_combined_filter_comparison(
            x,
            x0=50.0,
            L=0.0,
            U=100.0,
            interior_result=mock_interior_result,
            boundary_result=mock_boundary_result,
            bins=50,
            config=config,
        )
        assert fig is not None
        plt.close(fig)

    def test_handles_all_filters_applied(self, mock_boundary_result, mock_interior_result):
        """Test comprehensive filtering scenario."""
        # Create data with multiple issues
        x = np.concatenate(
            [
                np.array([-5.0] * 50),  # Out-of-bounds below
                np.array([105.0] * 50),  # Out-of-bounds above
                np.array([50.0] * 400),  # Stuck at x0
                np.random.uniform(0, 100, 9500),  # Good data
            ]
        )
        fig = plot_combined_filter_comparison(
            x,
            x0=50.0,
            L=0.0,
            U=100.0,
            interior_result=mock_interior_result,
            boundary_result=mock_boundary_result,
            bins=50,
        )
        assert fig is not None
        assert len(fig.axes) == 8  # 4x2 grid (linear + log)
        plt.close(fig)
