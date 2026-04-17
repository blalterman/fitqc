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
    plot_histogram_tolerance_overlays_combined,
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


def test_interior_diagnostics_overplots_before_after_cut():
    """S2: z-histogram panel shows a gray 'before' and a colored 'after' bar set."""
    # eps_star at ~0.05 so about half the 100 bins (0..1) are above the cut
    result = _mock_interior_result(spike=True, eps_star=0.05)
    fig = plot_interior_diagnostics(result, PlotConfig())
    ax1 = fig.axes[0]
    bar_artists = [patch for patch in ax1.containers]
    # Expect two bar containers: raw (gray) + after-cut (blue)
    assert len(bar_artists) == 2, f"expected two bar containers, got {len(bar_artists)}"
    plt.close(fig)


def test_histogram_tolerance_overlays_combined_single_panel():
    """S3: combined overlay returns a single-panel figure with log-y + markers."""
    rng = np.random.default_rng(5)
    x = np.concatenate([rng.uniform(0, 1, size=900), np.zeros(50), np.ones(50)])
    fig = plot_histogram_tolerance_overlays_combined(
        x=x,
        L=0.0,
        U=1.0,
        bins=50,
        t_lo_star=0.02,
        t_hi_star=0.03,
    )
    # Exactly one main panel (+ one colorbar axes attached by own_fig path)
    main_axes = [ax for ax in fig.axes if ax.get_ylabel() == "Count"]
    assert len(main_axes) == 1, f"expected one main panel, got {len(main_axes)}"
    ax = main_axes[0]
    assert ax.get_yscale() == "log"
    # Both t* markers drawn
    axvline_xs = [
        line.get_xdata()[0]
        for line in ax.lines
        if len(line.get_xdata()) == 2 and line.get_xdata()[0] == line.get_xdata()[1]
    ]
    assert any(abs(x - 0.02) < 1e-9 for x in axvline_xs)
    assert any(abs(x - (1.0 - 0.03)) < 1e-9 for x in axvline_xs)
    plt.close(fig)


def test_histogram_tolerance_overlays_combined_accepts_external_ax():
    """S3/T2: passing an existing Axes draws on that axes.

    With with_colorbar=True (default) a colorbar axes is appended next to
    the main axes via make_axes_locatable. With with_colorbar=False only
    the caller's axes is used.
    """
    rng = np.random.default_rng(6)
    x = rng.uniform(0, 1, size=500)

    fig, ax = plt.subplots(1, 1)
    returned_fig = plot_histogram_tolerance_overlays_combined(x=x, L=0.0, U=1.0, bins=30, ax=ax)
    assert returned_fig is fig
    # Default with_colorbar=True: main axes + colorbar axes = 2
    assert len(fig.axes) == 2
    plt.close(fig)

    fig2, ax2 = plt.subplots(1, 1)
    plot_histogram_tolerance_overlays_combined(
        x=x, L=0.0, U=1.0, bins=30, ax=ax2, with_colorbar=False
    )
    assert len(fig2.axes) == 1
    plt.close(fig2)


def test_parameter_overview_smoke():
    """V2: 4x3 overview renders for all interior_result paths.

    Axes count after the V2 reshuffle:
    - 11 grid panels: merged top spans 2 cells (1 axes), interior z-hist
      (1), 3 mass-curve cells, 3 ECDF/spacing cells, 3 elbow cells.
    - 3 colorbars: merged top panel, lower boundary mass, upper boundary
      mass.
    Total: 14 axes. Stable across all interior_result paths since
    placeholder text still occupies the cell.
    """
    rng = np.random.default_rng(3)
    L, U = 0.0, 1.0
    x0 = 0.0
    x = np.concatenate([rng.uniform(L, U, size=900), np.zeros(100)])

    br = _mock_boundary_result(t_lo_star=0.01, t_hi_star=0.01)
    ir = _mock_interior_result()

    fig_mock_interior = plot_parameter_overview(
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
    assert len(fig_mock_interior.axes) == 14
    assert tuple(fig_mock_interior.get_size_inches()) == (16.0, 22.0)
    plt.close(fig_mock_interior)

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
    assert len(fig_none.axes) == 14
    plt.close(fig_none)

    # Interior with quantile_elbows populated - same count.
    ir_with_elbows = InteriorResult(
        spike_detected=True,
        spike_z_loc=0.05,
        eps_star=0.01,
        eps_grid=np.logspace(-6, -1, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=np.random.default_rng(4).integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows={0.1: 0.01, 0.2: 0.012, 0.3: 0.015},
    )
    br_with_elbows = _mock_boundary_result()
    br_with_elbows.quantile_elbows = {
        "lower": {0.1: 0.01, 0.2: 0.012, 0.3: 0.015},
        "upper": {0.1: 0.008, 0.2: 0.01, 0.3: 0.012},
    }
    fig_full = plot_parameter_overview(
        param_name="full",
        x=x,
        x0=x0,
        L=L,
        U=U,
        interior_result=ir_with_elbows,
        boundary_result=br_with_elbows,
        config=PlotConfig(),
    )
    assert len(fig_full.axes) == 14
    plt.close(fig_full)
