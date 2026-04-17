"""Tests covering the B1-B8 plot improvements.

Exercises:
- B2b boundary auto-zoom
- B3a/B3b histogram overlay log-y + interior cuts
- B4a ECDF t_star markers
- B6 interior z-histogram symlog
- B7 plot_parameter_overview (populated and interior_result=None paths)
"""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from fitqc.boundary import BoundaryResult
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult
from fitqc.plot import (
    plot_boundary_diagnostics,
    plot_ecdf_tolerance_overlays,
    plot_histogram_tolerance_overlays,
    plot_interior_diagnostics,
    plot_parameter_overview,
)


def _mock_boundary_result(
    *,
    t_lo_star: float | None = 0.005,
    t_hi_star: float | None = 0.005,
    pileup_threshold: float = 0.005,
) -> BoundaryResult:
    tol_grid = np.linspace(0, 0.05, 41)
    return BoundaryResult(
        lower_pileup_detected=t_lo_star is not None,
        upper_pileup_detected=t_hi_star is not None,
        t_lo_star=t_lo_star,
        t_hi_star=t_hi_star,
        tol_grid=tol_grid,
        lower_mass_curve=np.linspace(0, 0.1, 41),
        upper_mass_curve=np.linspace(0, 0.1, 41),
        pileup_threshold=pileup_threshold,
    )


def _mock_interior_result(*, spike: bool = True, eps_star: float | None = 0.01) -> InteriorResult:
    rng = np.random.default_rng(0)
    return InteriorResult(
        spike_detected=spike,
        spike_z_loc=0.05 if spike else None,
        eps_star=eps_star,
        eps_grid=np.logspace(-6, -1, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
    )


def test_boundary_diagnostics_zooms_to_pileup_region():
    """B2b: with small t_star the linear panels zoom to ~pileup_threshold*4."""
    result = _mock_boundary_result(t_lo_star=0.005, t_hi_star=0.005, pileup_threshold=0.005)
    fig = plot_boundary_diagnostics(result, PlotConfig())
    # axes[0] and axes[1] are the two linear mass-curve panels
    x0, x1 = fig.axes[0].get_xlim()
    assert x0 == pytest.approx(0.0)
    # Expect x_max = max(t_lo_star*4, pileup_threshold*4) = 0.02
    assert x1 < 0.05, f"expected zoomed xlim to be < 0.05, got {x1}"
    assert x1 == pytest.approx(0.02, rel=1e-6)
    plt.close(fig)


def test_histogram_overlays_log_y_and_interior_cuts():
    """B3a/B3b: log-y is always applied; interior cuts drop samples."""
    rng = np.random.default_rng(1)
    x = np.concatenate([rng.uniform(0, 1, size=900), np.zeros(100)])  # spike at x0=0
    L, U = 0.0, 1.0

    # Baseline: no interior cut
    fig_base = plot_histogram_tolerance_overlays(x=x, L=L, U=U, bins=50)
    ax_lo_base, ax_up_base = fig_base.axes[0], fig_base.axes[1]
    assert ax_lo_base.get_yscale() == "log"
    assert ax_up_base.get_yscale() == "log"
    plt.close(fig_base)

    # With x0/eps_star: interior cut applied. Use a very wide cut to ensure
    # it removes something visible.
    fig_cut = plot_histogram_tolerance_overlays(
        x=x, L=L, U=U, bins=50, x0=0.0, eps_star=0.1, t_lo_star=0.05
    )
    # t_lo_star axvline should appear on the lower panel
    ax_lo_cut = fig_cut.axes[0]
    axvline_xs = [
        line.get_xdata()[0]
        for line in ax_lo_cut.lines
        if len(line.get_xdata()) == 2 and line.get_xdata()[0] == line.get_xdata()[1]
    ]
    assert any(abs(x - (L + 0.05 * (U - L))) < 1e-9 for x in axvline_xs), (
        f"expected axvline at L + t_lo_star*(U-L)=0.05, got {axvline_xs}"
    )
    plt.close(fig_cut)


def test_ecdf_overlays_marks_t_star():
    """B4a: axvline drawn at t_lo_star when supplied."""
    rng = np.random.default_rng(2)
    u = rng.uniform(0, 1, size=500)
    fig = plot_ecdf_tolerance_overlays(u=u, side="lower", t_lo_star=0.02)
    ax = fig.axes[0]
    axvline_xs = [
        line.get_xdata()[0]
        for line in ax.lines
        if len(line.get_xdata()) == 2 and line.get_xdata()[0] == line.get_xdata()[1]
    ]
    assert any(abs(x - 0.02) < 1e-9 for x in axvline_xs), (
        f"expected axvline at 0.02, got {axvline_xs}"
    )
    plt.close(fig)


def test_interior_diagnostics_uses_symlog_on_z():
    """B6: z-histogram panel uses symlog y-scale."""
    result = _mock_interior_result()
    fig = plot_interior_diagnostics(result, PlotConfig())
    assert fig.axes[0].get_yscale() == "symlog"
    plt.close(fig)


def test_parameter_overview_smoke():
    """B7: 3x2 overview renders for both interior_result paths."""
    rng = np.random.default_rng(3)
    L, U = 0.0, 1.0
    x0 = 0.0
    x = np.concatenate([rng.uniform(L, U, size=900), np.zeros(100)])

    br = _mock_boundary_result(t_lo_star=0.01, t_hi_star=0.01)
    ir = _mock_interior_result()

    fig_populated = plot_parameter_overview(
        param_name="synthetic",
        x=x,
        x0=x0,
        L=L,
        U=U,
        interior_result=ir,
        boundary_result=br,
        config=PlotConfig(),
        tp_fn_status="lower: TP | upper: TP",
    )
    assert len(fig_populated.axes) == 6
    plt.close(fig_populated)

    fig_none = plot_parameter_overview(
        param_name="synthetic_no_interior",
        x=x,
        x0=None,
        L=L,
        U=U,
        interior_result=None,
        boundary_result=br,
        config=PlotConfig(),
    )
    assert len(fig_none.axes) == 6
    plt.close(fig_none)
