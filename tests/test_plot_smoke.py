"""Smoke tests for the plot module."""

import matplotlib.pyplot as plt
import numpy as np

from fitqc.boundary import BoundaryResult
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult
from fitqc.plot import plot_boundary_diagnostics, plot_interior_diagnostics


def create_mock_interior_result() -> InteriorResult:
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


def create_mock_boundary_result() -> BoundaryResult:
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


class TestPlotSmoke:
    """Smoke tests for plotting functions."""

    def test_interior_plot_has_expected_axes(self):
        """Test that interior plot has at least 3 axes."""
        result = create_mock_interior_result()
        fig = plot_interior_diagnostics(result, PlotConfig())
        assert len(fig.axes) >= 3
        plt.close(fig)

    def test_boundary_plot_has_colorbar(self):
        """Test that boundary plot has a colorbar axis.

        The boundary plot creates a colorbar using fig.add_axes() with dimensions
        [0.92, 0.15, 0.02, 0.7]. We verify this by checking for an axis positioned
        at the right edge (left > 0.9) with narrow width (width < 0.05).
        """
        result = create_mock_boundary_result()
        fig = plot_boundary_diagnostics(result, PlotConfig())

        # Colorbar is added at position [0.92, 0.15, 0.02, 0.7]
        # We look for an axis with these characteristics:
        # - Positioned at right edge (left > 0.9)
        # - Narrow width (< 0.05)
        has_colorbar = False
        for ax in fig.axes:
            bbox = ax.get_position()
            # Check for colorbar characteristics: narrow, at right edge
            if bbox.x0 > 0.9 and bbox.width < 0.05:
                has_colorbar = True
                break

        assert has_colorbar, "Expected boundary plot to have a colorbar axis at right edge"
        plt.close(fig)

    def test_log_magnitude_panel_present(self):
        """Test that log magnitude panel is present when configured."""
        config = PlotConfig(include_log_abs_panel=True)
        result = create_mock_boundary_result()
        fig = plot_boundary_diagnostics(result, config)
        # Check if any axis has log scale
        has_log = any(ax.get_xscale() == "log" or ax.get_yscale() == "log" for ax in fig.axes)
        assert has_log
        plt.close(fig)

    def test_plot_returns_figure_not_none(self):
        """Test that plot functions return Figure objects."""
        fig = plot_interior_diagnostics(create_mock_interior_result(), PlotConfig())
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_does_not_call_show(self, monkeypatch):
        """Test that plot functions do NOT call plt.show()."""
        show_called = []
        monkeypatch.setattr(plt, "show", lambda: show_called.append(True))
        plot_interior_diagnostics(create_mock_interior_result(), PlotConfig())
        plot_boundary_diagnostics(create_mock_boundary_result(), PlotConfig())
        assert len(show_called) == 0
        plt.close("all")

    def test_kneedle_internals_runs_without_crash(self):
        """Smoke test: plot_kneedle_internals executes without exceptions."""
        from fitqc.plot import plot_kneedle_internals

        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        fig = plot_kneedle_internals(x, y)

        # Minimal check - just verify figure created
        assert len(fig.axes) >= 3, "Should create at least 3 panels"
        plt.close(fig)

    def test_quantile_elbows_detailed_runs_without_crash(self):
        """Smoke test: plot_quantile_elbows_detailed executes without exceptions."""
        from fitqc.plot import plot_quantile_elbows_detailed

        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=np.random.default_rng(42).integers(0, 100, 100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={0.01: 1e-7, 0.05: 5e-7},
        )
        fig = plot_quantile_elbows_detailed(result)

        assert len(fig.axes) >= 1, "Should create at least 1 panel"
        plt.close(fig)

    def test_new_plots_do_not_call_show(self, monkeypatch):
        """Test that new plot functions do NOT call plt.show()."""
        from fitqc.plot import plot_kneedle_internals, plot_quantile_elbows_detailed

        show_called = []
        monkeypatch.setattr(plt, "show", lambda: show_called.append(True))

        # Test plot_kneedle_internals
        x = np.linspace(0, 10, 50)
        y = 1 - np.exp(-x)
        fig1 = plot_kneedle_internals(x, y)
        plt.close(fig1)

        # Test plot_quantile_elbows_detailed
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=np.random.default_rng(42).integers(0, 100, 100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={0.01: 1e-7},
        )
        fig2 = plot_quantile_elbows_detailed(result)
        plt.close(fig2)

        assert len(show_called) == 0, "plt.show() should not be called"
