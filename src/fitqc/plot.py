"""Diagnostic plotting for fitqc.

This module provides visualization functions for interior and boundary QC results.
All plotting functions return Figure objects and NEVER call plt.show(), allowing
users to control when and how figures are displayed or saved.

Key Design Decisions:
- Return Figure, never call plt.show()
- Use non-interactive backend by default (Agg)
- Support configurable colormaps, DPI, and figure sizes
- Include log-scale panels when appropriate for multi-scale data
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from fitqc.config import PlotConfig
from fitqc.stickiness import BoundaryResult, InteriorResult

# Use non-interactive backend to avoid display issues
matplotlib.use("Agg")


def plot_interior_diagnostics(result: InteriorResult, config: PlotConfig) -> Figure:
    """Create diagnostic plots for interior (x0 stickiness) QC results.

    Creates a figure with multiple subplots:
    1. Histogram of z-values (distance from x0) with spike location marked
    2. Mass curve P(z < eps) vs eps showing cumulative mass near x0
    3. Log-scale mass curve (eps on log scale) with elbow point marked

    Args:
        result: InteriorResult from run_interior_qc.
        config: PlotConfig with plotting parameters.

    Returns:
        matplotlib Figure object. Caller is responsible for displaying or saving.
    """
    fig, axes = plt.subplots(1, 3, figsize=config.figsize_interior, dpi=config.dpi)

    cmap = plt.get_cmap(config.cmap)

    # Panel 1: Histogram of z-values
    ax1 = axes[0]
    bin_centers = (result.hist_edges[:-1] + result.hist_edges[1:]) / 2
    ax1.bar(
        bin_centers,
        result.hist_counts,
        width=result.hist_edges[1] - result.hist_edges[0],
        color=cmap(0.3),
        edgecolor="none",
        alpha=0.7,
    )
    ax1.set_xlabel("z (normalized distance from x0)")
    ax1.set_ylabel("Count")
    ax1.set_title("Distribution of z-values")

    # Mark spike location if detected
    if result.spike_detected and result.spike_z_loc is not None:
        ax1.axvline(
            result.spike_z_loc,
            color=cmap(0.8),
            linestyle="--",
            linewidth=2,
            label=f"Spike at z={result.spike_z_loc:.4f}",
        )
        ax1.legend(loc="upper right")

    # Panel 2: Mass curve (linear scale)
    ax2 = axes[1]
    ax2.plot(result.eps_grid, result.mass_curve, color=cmap(0.5), linewidth=2)
    ax2.set_xlabel("epsilon")
    ax2.set_ylabel("P(z < epsilon)")
    ax2.set_title("Mass curve (linear scale)")
    ax2.grid(True, alpha=0.3)

    # Panel 3: Mass curve (log scale for epsilon)
    ax3 = axes[2]
    ax3.semilogx(result.eps_grid, result.mass_curve, color=cmap(0.5), linewidth=2)
    ax3.set_xlabel("epsilon (log scale)")
    ax3.set_ylabel("P(z < epsilon)")
    ax3.set_title("Mass curve (log scale)")
    ax3.grid(True, alpha=0.3)

    # Mark eps_star (elbow point) if detected
    if result.eps_star is not None:
        # Find the mass value at eps_star
        idx = np.searchsorted(result.eps_grid, result.eps_star)
        if idx < len(result.mass_curve):
            mass_at_elbow = result.mass_curve[idx]
        else:
            mass_at_elbow = result.mass_curve[-1]

        ax2.axvline(
            result.eps_star,
            color=cmap(0.9),
            linestyle=":",
            linewidth=2,
            label=f"eps* = {result.eps_star:.2e}",
        )
        ax2.scatter([result.eps_star], [mass_at_elbow], color=cmap(0.9), s=100, zorder=5)
        ax2.legend(loc="lower right")

        ax3.axvline(
            result.eps_star,
            color=cmap(0.9),
            linestyle=":",
            linewidth=2,
            label=f"eps* = {result.eps_star:.2e}",
        )
        ax3.scatter([result.eps_star], [mass_at_elbow], color=cmap(0.9), s=100, zorder=5)
        ax3.legend(loc="lower right")

    fig.tight_layout()

    return fig


def plot_boundary_diagnostics(result: BoundaryResult, config: PlotConfig) -> Figure:
    """Create diagnostic plots for boundary (L/U stickiness) QC results.

    Creates a figure with multiple subplots:
    1. Lower mass curve P(u < tol) with t_lo_star marked
    2. Upper mass curve P(u > 1-tol) with t_hi_star marked
    3. Optional: Log magnitude panel showing both curves on log scale

    Includes a colorbar to show the tolerance gradient.

    Args:
        result: BoundaryResult from run_boundary_qc.
        config: PlotConfig with plotting parameters.

    Returns:
        matplotlib Figure object. Caller is responsible for displaying or saving.
    """
    n_panels = 3 if config.include_log_abs_panel else 2

    fig, axes = plt.subplots(1, n_panels, figsize=config.figsize_boundary, dpi=config.dpi)
    if n_panels == 1:
        axes = [axes]

    cmap = plt.get_cmap(config.cmap)

    # Create a normalization for the colorbar based on tolerance range
    norm = Normalize(vmin=result.tol_grid[0], vmax=result.tol_grid[-1])

    # Panel 1: Lower boundary mass curve
    ax1 = axes[0]
    colors_lower = [cmap(norm(t)) for t in result.tol_grid]
    for i in range(len(result.tol_grid) - 1):
        ax1.plot(
            result.tol_grid[i : i + 2],
            result.lower_mass_curve[i : i + 2],
            color=colors_lower[i],
            linewidth=2,
        )

    ax1.set_xlabel("Tolerance (tol)")
    ax1.set_ylabel("P(u < tol)")
    ax1.set_title("Lower boundary mass curve")
    ax1.grid(True, alpha=0.3)

    # Plot reference line for uniform distribution (P = tol)
    ax1.plot(
        result.tol_grid,
        result.tol_grid,
        "k--",
        alpha=0.5,
        linewidth=1,
        label="Uniform (P = tol)",
    )

    # Mark t_lo_star if detected
    if result.t_lo_star is not None:
        idx = np.searchsorted(result.tol_grid, result.t_lo_star)
        if idx < len(result.lower_mass_curve):
            mass_at_elbow = result.lower_mass_curve[idx]
        else:
            mass_at_elbow = result.lower_mass_curve[-1]

        ax1.axvline(
            result.t_lo_star,
            color="red",
            linestyle=":",
            linewidth=2,
            label=f"t_lo* = {result.t_lo_star:.4f}",
        )
        ax1.scatter([result.t_lo_star], [mass_at_elbow], color="red", s=100, zorder=5)

    ax1.legend(loc="lower right")

    # Panel 2: Upper boundary mass curve
    ax2 = axes[1]
    colors_upper = [cmap(norm(t)) for t in result.tol_grid]
    for i in range(len(result.tol_grid) - 1):
        ax2.plot(
            result.tol_grid[i : i + 2],
            result.upper_mass_curve[i : i + 2],
            color=colors_upper[i],
            linewidth=2,
        )

    ax2.set_xlabel("Tolerance (tol)")
    ax2.set_ylabel("P(u > 1-tol)")
    ax2.set_title("Upper boundary mass curve")
    ax2.grid(True, alpha=0.3)

    # Plot reference line for uniform distribution
    ax2.plot(
        result.tol_grid,
        result.tol_grid,
        "k--",
        alpha=0.5,
        linewidth=1,
        label="Uniform (P = tol)",
    )

    # Mark t_hi_star if detected
    if result.t_hi_star is not None:
        idx = np.searchsorted(result.tol_grid, result.t_hi_star)
        if idx < len(result.upper_mass_curve):
            mass_at_elbow = result.upper_mass_curve[idx]
        else:
            mass_at_elbow = result.upper_mass_curve[-1]

        ax2.axvline(
            result.t_hi_star,
            color="red",
            linestyle=":",
            linewidth=2,
            label=f"t_hi* = {result.t_hi_star:.4f}",
        )
        ax2.scatter([result.t_hi_star], [mass_at_elbow], color="red", s=100, zorder=5)

    ax2.legend(loc="lower right")

    # Panel 3: Log magnitude panel (optional)
    if config.include_log_abs_panel:
        ax3 = axes[2]

        # Use log scale on y-axis to see small differences better
        # Add small offset to avoid log(0)
        lower_safe = np.maximum(result.lower_mass_curve, 1e-10)
        upper_safe = np.maximum(result.upper_mass_curve, 1e-10)

        ax3.semilogy(
            result.tol_grid,
            lower_safe,
            color=cmap(0.3),
            linewidth=2,
            label="Lower boundary",
        )
        ax3.semilogy(
            result.tol_grid,
            upper_safe,
            color=cmap(0.7),
            linewidth=2,
            label="Upper boundary",
        )

        # Reference line for uniform
        uniform_safe = np.maximum(result.tol_grid, 1e-10)
        ax3.semilogy(
            result.tol_grid,
            uniform_safe,
            "k--",
            alpha=0.5,
            linewidth=1,
            label="Uniform",
        )

        ax3.set_xlabel("Tolerance (tol)")
        ax3.set_ylabel("Mass (log scale)")
        ax3.set_title("Log magnitude comparison")
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc="lower right")

    # Apply tight_layout before adding colorbar to avoid compatibility issues
    fig.tight_layout()

    # Colorbar Design Decision
    # -------------------------
    # We add the colorbar manually with fig.add_axes() instead of using the
    # standard fig.colorbar(sm, ax=axes) approach for these reasons:
    #
    # 1. tight_layout() conflicts: The standard colorbar placement with
    #    tight_layout() often causes the colorbar to overlap with plot content
    #    or creates excessive whitespace. Manual positioning avoids this.
    #
    # 2. Consistent placement: With add_axes([left, bottom, width, height]),
    #    the colorbar is always at [0.92, 0.15, 0.02, 0.7] (right edge, narrow,
    #    spanning most of the vertical height). This is predictable across
    #    different subplot configurations.
    #
    # 3. No colorbar stealing space: The standard approach "steals" space from
    #    existing axes. Manual placement with subplots_adjust(right=0.9) gives
    #    us explicit control over the space allocation.
    #
    # Alternative approaches considered:
    # - constrained_layout=True: Cleaner API but less predictable with our
    #   multi-panel layout and can have compatibility issues with older matplotlib
    # - GridSpec with colorbar column: More complex setup for simple use case
    #
    # The trade-off is that this approach requires explicit coordinate tuning,
    # but provides the most reliable cross-version behavior.

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cbar.set_label("Tolerance")

    # Adjust subplot positions to make room for colorbar
    fig.subplots_adjust(right=0.9)

    return fig
