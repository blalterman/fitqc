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

from typing import Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

from fitqc.boundary import BoundaryResult, compute_u
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult, compute_z

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

    # Panel 1: Histogram of z-values, before/after interior cut.
    ax1 = axes[0]
    bin_centers = (result.hist_edges[:-1] + result.hist_edges[1:]) / 2
    bin_width = result.hist_edges[1] - result.hist_edges[0]
    ax1.bar(
        bin_centers,
        result.hist_counts,
        width=bin_width,
        color="#808080",
        edgecolor="none",
        alpha=0.6,
        label="Before cut",
    )
    if result.eps_star is not None:
        after_counts = np.where(bin_centers >= result.eps_star, result.hist_counts, 0)
        ax1.bar(
            bin_centers,
            after_counts,
            width=bin_width,
            color=cmap(0.3),
            edgecolor="none",
            alpha=0.85,
            label=f"After cut (z >= eps*={result.eps_star:.2e})",
        )
    ax1.set_xlabel("z (normalized distance from x0)")
    ax1.set_ylabel("Count")
    ax1.set_title("Distribution of z-values")
    ax1.set_yscale("symlog", linthresh=1)

    # Mark spike location if detected
    if result.spike_detected and result.spike_z_loc is not None:
        ax1.axvline(
            result.spike_z_loc,
            color="#ff7f0e",
            linestyle="--",
            linewidth=2,
            label=f"Spike at z={result.spike_z_loc:.4f}",
        )
    ax1.legend(loc="upper right", fontsize=8)

    # Panel 2: Mass curve (linear scale)
    ax2 = axes[1]
    ax2.plot(result.eps_grid, result.mass_curve, color="#2166ac", linewidth=2)
    ax2.set_xlabel("epsilon")
    ax2.set_ylabel("P(z < epsilon)")
    ax2.set_title("Mass curve (linear scale)")
    ax2.grid(True, alpha=0.3)

    # Panel 3: Mass curve (log scale for epsilon)
    ax3 = axes[2]
    ax3.semilogx(result.eps_grid, result.mass_curve, color="#2166ac", linewidth=2)
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
            color="#d62728",
            linestyle=":",
            linewidth=2,
            label=f"eps* = {result.eps_star:.2e}",
        )
        ax2.scatter([result.eps_star], [mass_at_elbow], color="#d62728", s=100, zorder=5)
        ax2.legend(loc="lower right")

        ax3.axvline(
            result.eps_star,
            color="#d62728",
            linestyle=":",
            linewidth=2,
            label=f"eps* = {result.eps_star:.2e}",
        )
        ax3.scatter([result.eps_star], [mass_at_elbow], color="#d62728", s=100, zorder=5)
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
    colors_lower = [cmap(0.15 + 0.85 * norm(t)) for t in result.tol_grid]
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

    t_lo_for_zoom = result.t_lo_star if result.t_lo_star is not None else 0.0
    x_max_lo = max(t_lo_for_zoom * 4, result.pileup_threshold * 4)
    if x_max_lo > 0 and len(result.tol_grid) > 0:
        in_range = result.tol_grid <= x_max_lo
        if in_range.any():
            mass_in = result.lower_mass_curve[in_range]
            uniform_in = result.tol_grid[in_range]
            y_max_lo = 1.2 * max(float(mass_in.max()), 1.5 * float(uniform_in.max()))
            ax1.set_xlim(0, x_max_lo)
            ax1.set_ylim(0, y_max_lo)

    # Panel 2: Upper boundary mass curve
    ax2 = axes[1]
    colors_upper = [cmap(0.15 + 0.85 * norm(t)) for t in result.tol_grid]
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

    t_hi_for_zoom = result.t_hi_star if result.t_hi_star is not None else 0.0
    x_max_hi = max(t_hi_for_zoom * 4, result.pileup_threshold * 4)
    if x_max_hi > 0 and len(result.tol_grid) > 0:
        in_range = result.tol_grid <= x_max_hi
        if in_range.any():
            mass_in = result.upper_mass_curve[in_range]
            uniform_in = result.tol_grid[in_range]
            y_max_hi = 1.2 * max(float(mass_in.max()), 1.5 * float(uniform_in.max()))
            ax2.set_xlim(0, x_max_hi)
            ax2.set_ylim(0, y_max_hi)

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

    trunc_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "trunc", [cmap(x) for x in np.linspace(0.15, 1.0, 256)]
    )
    sm = plt.cm.ScalarMappable(cmap=trunc_cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cbar.set_label("Tolerance")

    # Adjust subplot positions to make room for colorbar
    fig.subplots_adjust(right=0.9)

    return fig


def plot_quantile_spacing_overlays(
    x_sorted: np.ndarray,
    L: float | None = None,
    U: float | None = None,
    tols: np.ndarray | None = None,
    n_tols: int = 11,
    q_max: float = 0.1,
    n_quantiles: int = 100,
    use_alpha: bool = True,
    config: PlotConfig | None = None,
) -> Figure:
    """Plot quantile spacing near zero with tolerance overlays.

    Shows dq (spacing between consecutive quantiles) vs quantile index.
    Compression in spacing indicates pile-up; expansion indicates gaps.

    This function visualizes how quantile spacing changes when different tolerance
    levels are applied to filter data near boundaries. When L and U are provided,
    each tolerance level filters the data by removing samples within
    tol*(U-L) of the boundaries. This helps diagnose boundary pile-up effects.

    Args:
        x_sorted: Pre-sorted array of values (must be sorted in ascending order).
        L: Lower bound for tolerance filtering (optional).
        U: Upper bound for tolerance filtering (optional).
        tols: Tolerance values for filtering. If None, uses linspace(0, 0.05, n_tols).
        n_tols: Number of tolerances if tols is None.
        q_max: Maximum quantile to show (0.1 = first 10%).
        n_quantiles: Number of quantile points.
        use_alpha: If True, use alpha gradient (base=1.0, top=0.3). If False, all layers use alpha=1.0 (fully opaque).
        config: PlotConfig for styling. If None, uses PlotConfig().

    Returns:
        Figure with spacing curves colored by tolerance.

    Note:
        L and U are optional. If provided, tolerance filtering is applied by
        removing samples within tol*(U-L) of each boundary. If not provided,
        the same data is plotted at all tolerance levels (useful for comparing
        pre-filtered datasets or when working with normalized z-scores).

    Raises:
        AssertionError: If x_sorted is not sorted in ascending order.
    """
    # Filter non-finite values first
    x_finite = x_sorted[np.isfinite(x_sorted)]

    # Validate input is sorted (after removing non-finite values)
    if len(x_finite) > 1:
        assert np.all(np.diff(x_finite) >= 0), "x_sorted must be sorted in ascending order"

    # Set defaults
    if config is None:
        config = PlotConfig()

    if tols is None:
        tols = np.linspace(0, 0.05, n_tols)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=config.figsize_tolerance, dpi=config.dpi)

    # Get colormap
    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tols[0], vmax=tols[-1])

    # Create alpha gradient for visibility
    if use_alpha:
        alphas = np.linspace(1.0, 0.3, len(tols))
    else:
        alphas = np.ones(len(tols))

    # Track median spacing for tol=0 (for reference line)
    median_spacing_ref = None

    # Plot spacing for each tolerance
    for i, tol in enumerate(tols):
        # Use the already cleaned data
        x_clean = x_finite

        # Apply tolerance filtering if bounds are provided
        if L is not None and U is not None:
            # Filter based on tolerance: keep samples outside tol*(U-L) from boundaries
            margin = tol * (U - L)
            x_filt = x_clean[(x_clean > L + margin) & (x_clean < U - margin)]
        else:
            # No filtering, use all data
            x_filt = x_clean

        # Skip if filtered array is too small
        if len(x_filt) < 2:
            continue

        # Compute quantile indices from 0 to q_max
        n_filt = len(x_filt)
        max_idx = int(q_max * n_filt)

        # Ensure we have enough points
        if max_idx < 2:
            continue

        # Adjust n_quantiles if it exceeds available data
        n_q = min(n_quantiles, max_idx)
        q_indices = np.linspace(0, max_idx - 1, n_q).astype(int)
        q_indices = np.clip(q_indices, 0, n_filt - 1)

        # Extract quantile values
        quantiles = x_filt[q_indices]

        # Compute spacing
        dq = np.diff(quantiles)

        # Skip if no spacing to plot
        if len(dq) == 0:
            continue

        # Store median spacing for tol=0
        if i == 0 and median_spacing_ref is None:
            median_spacing_ref = np.median(dq)

        # Plot with color and alpha
        color = cmap(norm(tol))
        ax.plot(
            np.arange(len(dq)),
            dq,
            color=color,
            alpha=alphas[i],
            linewidth=2,
            zorder=i,
        )

    # Add reference line for median spacing (if available)
    if median_spacing_ref is not None:
        ax.axhline(
            median_spacing_ref,
            color="gray",
            linestyle="--",
            linewidth=1,
            alpha=0.5,
            label=f"Median spacing (tol=0): {median_spacing_ref:.2e}",
        )
        ax.legend(loc="upper right")

    # Labels and title
    ax.set_xlabel("Quantile index")
    ax.set_ylabel("Spacing dq = |x[i+1] - x[i]|")
    ax.set_title(f"Spacing dq between adjacent samples in the lowest q={q_max:.2g} of values")
    ax.grid(True, alpha=0.3)
    ax.annotate(
        "Compression (smaller dq) = pileup; Expansion (larger dq) = gap",
        xy=(0.98, 0.98),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
    )

    # Apply tight_layout before adding colorbar
    fig.tight_layout()

    # Add colorbar (following the same pattern as plot_boundary_diagnostics)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cbar.set_label("Tolerance")

    # Adjust subplot positions to make room for colorbar
    fig.subplots_adjust(right=0.9)

    return fig


def plot_ecdf_tolerance_overlays(
    u: np.ndarray,
    tols: np.ndarray | None = None,
    n_tols: int = 11,
    side: Literal["lower", "upper", "both"] = "lower",
    use_alpha: bool = True,
    config: PlotConfig | None = None,
    t_lo_star: float | None = None,
    t_hi_star: float | None = None,
) -> Figure:
    """Plot ECDF near boundaries with tolerance-colored overlays.

    Shows how the empirical CDF changes as samples near boundaries are removed.

    When ``t_lo_star`` or ``t_hi_star`` is supplied, a vertical red marker
    is drawn at the detected cut position on the corresponding panel.

    Args:
        u: Normalized positions in [0, 1] where u = (x - L) / (U - L).
        tols: Array of tolerance values. If None, uses linspace(0, 0.05, n_tols).
        n_tols: Number of tolerances if tols is None.
        side: Which boundary to visualize ("lower", "upper", or "both").
        use_alpha: If True, use alpha gradient (base=1.0, top=0.3). If False, all layers use alpha=1.0 (fully opaque).
        config: PlotConfig for styling.
        t_lo_star: Optional detected lower cut; drawn as a vertical marker.
        t_hi_star: Optional detected upper cut; drawn as a vertical marker (placed at ``1 - t_hi_star``).

    Returns:
        Figure with ECDF curves colored by tolerance.
    """
    # Validate side parameter
    if side not in ["lower", "upper", "both"]:
        raise ValueError(f"side must be 'lower', 'upper', or 'both', got {side}")

    # Set default config
    if config is None:
        config = PlotConfig()

    # Set default tolerances
    if tols is None:
        tols = np.linspace(0, 0.05, n_tols)

    # Filter non-finite values
    u_clean = u[np.isfinite(u)]

    # Helper function to compute ECDF
    def _compute_ecdf(u_filtered):
        if len(u_filtered) == 0:
            return np.array([]), np.array([])
        u_sorted = np.sort(u_filtered)
        n = len(u_sorted)
        y = np.arange(1, n + 1) / n
        return u_sorted, y

    # Setup figure
    n_panels = 2 if side == "both" else 1
    fig, axes = plt.subplots(1, n_panels, figsize=config.figsize_tolerance, dpi=config.dpi)
    if n_panels == 1:
        axes = [axes]

    # Setup colormap
    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tols[0], vmax=tols[-1])

    # Setup alpha values (varying transparency)
    if use_alpha:
        alphas = np.linspace(1.0, 0.3, len(tols))
    else:
        alphas = np.ones(len(tols))

    # Plot lower boundary ECDF
    if side in ["lower", "both"]:
        ax_idx = 0
        ax = axes[ax_idx]

        ecdf_y_in_view: list[float] = []
        for i, tol in enumerate(tols):
            # Filter data
            u_filt = u_clean[u_clean > tol]

            # Compute ECDF
            u_sorted, ecdf_vals = _compute_ecdf(u_filt)

            # Skip if empty
            if len(u_sorted) == 0:
                continue

            # Get color
            color = cmap(norm(tol))

            # Plot ECDF
            ax.plot(u_sorted, ecdf_vals, color=color, alpha=alphas[i], linewidth=2, zorder=i)

            in_view = (u_sorted >= 0) & (u_sorted <= 0.1)
            if in_view.any():
                ecdf_y_in_view.append(float(ecdf_vals[in_view].min()))
                ecdf_y_in_view.append(float(ecdf_vals[in_view].max()))

        # Add reference line for uniform ECDF (y = x)
        ax.plot([0, 0.1], [0, 0.1], "k--", alpha=0.5, linewidth=1, label="Uniform (y=x)")

        ax.set_xlabel("u (normalized position)")
        ax.set_ylabel("ECDF")
        ax.set_title("ECDF near lower boundary")
        ax.set_xlim(0, 0.1)
        ax.grid(True, alpha=0.3)

        if ecdf_y_in_view:
            y_min = min(ecdf_y_in_view)
            y_max = max(ecdf_y_in_view)
            if y_max - y_min < 0.05:
                ax.set_ylim(y_min - 0.005, y_max + 0.005)

        if t_lo_star is not None:
            ax.axvline(
                t_lo_star,
                color="red",
                lw=2,
                label=f"t_lo* = {t_lo_star:.4f}",
            )

        ax.legend(loc="lower right")

    # Plot upper boundary ECDF
    if side in ["upper", "both"]:
        ax_idx = 1 if side == "both" else 0
        ax = axes[ax_idx]

        ecdf_y_in_view_upper: list[float] = []
        for i, tol in enumerate(tols):
            # Filter data
            u_filt = u_clean[u_clean < 1 - tol]

            # Compute ECDF
            u_sorted, ecdf_vals = _compute_ecdf(u_filt)

            # Skip if empty
            if len(u_sorted) == 0:
                continue

            # Get color
            color = cmap(norm(tol))

            # Plot ECDF
            ax.plot(u_sorted, ecdf_vals, color=color, alpha=alphas[i], linewidth=2, zorder=i)

            in_view = (u_sorted >= 0.9) & (u_sorted <= 1.0)
            if in_view.any():
                ecdf_y_in_view_upper.append(float(ecdf_vals[in_view].min()))
                ecdf_y_in_view_upper.append(float(ecdf_vals[in_view].max()))

        # Add reference line for uniform ECDF (y = x)
        # For the upper boundary plot, the x range is [0.9, 1.0]
        # The reference line should still be y = x
        ax.plot([0.9, 1.0], [0.9, 1.0], "k--", alpha=0.5, linewidth=1, label="Uniform (y=x)")

        ax.set_xlabel("u (normalized position)")
        ax.set_ylabel("ECDF")
        ax.set_title("ECDF near upper boundary")
        ax.set_xlim(0.9, 1.0)
        ax.grid(True, alpha=0.3)

        if ecdf_y_in_view_upper:
            y_min = min(ecdf_y_in_view_upper)
            y_max = max(ecdf_y_in_view_upper)
            if y_max - y_min < 0.05:
                ax.set_ylim(y_min - 0.005, y_max + 0.005)

        if t_hi_star is not None:
            ax.axvline(
                1 - t_hi_star,
                color="red",
                lw=2,
                label=f"t_hi* = {t_hi_star:.4f}",
            )

        ax.legend(loc="lower right")

    # Apply tight_layout before adding colorbar
    fig.tight_layout()

    # Add colorbar (same pattern as boundary diagnostics)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cbar.set_label("Tolerance")

    # Adjust subplot positions to make room for colorbar
    fig.subplots_adjust(right=0.9)

    return fig


def plot_histogram_tolerance_overlays(
    x: np.ndarray,
    L: float,
    U: float,
    tols: np.ndarray | None = None,
    n_tols: int = 11,
    bins: int = 100,
    use_alpha: bool = True,
    config: PlotConfig | None = None,
    x0: float | None = None,
    eps_star: float | None = None,
    t_lo_star: float | None = None,
    t_hi_star: float | None = None,
) -> Figure:
    """Plot histogram overlays showing effect of boundary tolerance cuts.

    For each tolerance t, shows histogram of data kept after applying:
    - Lower cut: x > L + t*(U-L)
    - Upper cut: x < U - t*(U-L)

    Histograms are colored by tolerance using a colormap with colorbar.
    Higher tolerances (stricter cuts) have higher zorder (drawn on top).
    By default, uses varying alpha: low tolerance = opaque (alpha=1.0), high tolerance = transparent (alpha=0.3).

    When ``x0`` and ``eps_star`` are both supplied, samples within the
    interior stickiness cut (``|x - x0| < eps_star * max(x0 - L, U - x0)``)
    are additionally removed from every tolerance layer. This matches the
    ``_build_mask`` semantics in ``fitqc.report``.

    When ``t_lo_star`` or ``t_hi_star`` is supplied, a vertical red marker
    is drawn at the corresponding detected cut position.

    Args:
        x: Array of parameter values.
        L: Lower bound.
        U: Upper bound.
        tols: Array of tolerance values to plot. If None, uses linspace(0, 0.05, n_tols).
        n_tols: Number of tolerances if tols is None.
        bins: Number of histogram bins.
        use_alpha: If True, use alpha gradient (base=1.0, top=0.3). If False, all layers use alpha=1.0 (fully opaque).
        config: PlotConfig for styling. Uses defaults if None.
        x0: Optional interior stickiness center. Used with eps_star.
        eps_star: Optional interior stickiness radius (normalized). Used with x0.
        t_lo_star: Optional lower-boundary detected cut; drawn as a vertical marker.
        t_hi_star: Optional upper-boundary detected cut; drawn as a vertical marker.

    Returns:
        Figure with two subplots (lower cuts, upper cuts) and colorbar.
    """
    # Validate inputs
    if L >= U:
        raise ValueError(f"L must be less than U, got L={L}, U={U}")

    # Handle defaults
    if config is None:
        config = PlotConfig()

    if tols is None:
        tols = np.linspace(0, 0.05, n_tols)

    # Filter non-finite values
    x = x[np.isfinite(x)]

    if x0 is not None and eps_star is not None and len(x) > 0:
        z = compute_z(x, x0, L, U)
        x = x[z >= eps_star]

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=config.figsize_tolerance, dpi=config.dpi)

    # Get colormap and create normalization
    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tols[0], vmax=tols[-1])

    # Compute fixed bin edges
    bin_edges = np.linspace(L, U, bins + 1)

    # Compute alphas
    if use_alpha:
        alphas = np.linspace(1.0, 0.3, len(tols))
    else:
        alphas = np.ones(len(tols))

    # Get colors for each tolerance
    colors = [cmap(norm(t)) for t in tols]

    # Left subplot: lower cuts
    ax_lower = axes[0]
    for i, tol in enumerate(tols):
        # Filter: x > L + tol*(U-L)
        x_filt = x[x > L + tol * (U - L)]

        # Skip if empty
        if len(x_filt) == 0:
            continue

        # Plot histogram
        ax_lower.hist(
            x_filt,
            bins=bin_edges,
            histtype="stepfilled",
            alpha=alphas[i],
            color=colors[i],
            zorder=i,
        )

    ax_lower.set_xlabel("Parameter value")
    ax_lower.set_ylabel("Count")
    ax_lower.set_title("Lower cuts: x > L + tol*(U-L)")
    ax_lower.grid(True, alpha=0.3)
    ax_lower.set_yscale("log")

    if t_lo_star is not None:
        ax_lower.axvline(
            L + t_lo_star * (U - L),
            color="red",
            lw=2,
            label=f"t_lo* = {t_lo_star:.4f}",
        )
        ax_lower.legend(loc="upper right")

    # Right subplot: upper cuts
    ax_upper = axes[1]
    for i, tol in enumerate(tols):
        # Filter: x < U - tol*(U-L)
        x_filt = x[x < U - tol * (U - L)]

        # Skip if empty
        if len(x_filt) == 0:
            continue

        # Plot histogram
        ax_upper.hist(
            x_filt,
            bins=bin_edges,
            histtype="stepfilled",
            alpha=alphas[i],
            color=colors[i],
            zorder=i,
        )

    ax_upper.set_xlabel("Parameter value")
    ax_upper.set_ylabel("Count")
    ax_upper.set_title("Upper cuts: x < U - tol*(U-L)")
    ax_upper.grid(True, alpha=0.3)
    ax_upper.set_yscale("log")

    if t_hi_star is not None:
        ax_upper.axvline(
            U - t_hi_star * (U - L),
            color="red",
            lw=2,
            label=f"t_hi* = {t_hi_star:.4f}",
        )
        ax_upper.legend(loc="upper left")

    # Apply tight_layout before adding colorbar
    fig.tight_layout()

    # Add colorbar (following pattern from plot_boundary_diagnostics)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cbar.set_label("Tolerance")
    fig.subplots_adjust(right=0.9)

    return fig


def plot_histogram_tolerance_overlays_combined(
    x: np.ndarray,
    L: float,
    U: float,
    tols: np.ndarray | None = None,
    n_tols: int = 11,
    bins: int = 100,
    use_alpha: bool = True,
    config: PlotConfig | None = None,
    x0: float | None = None,
    eps_star: float | None = None,
    t_lo_star: float | None = None,
    t_hi_star: float | None = None,
    ax: "plt.Axes | None" = None,
    with_colorbar: bool = True,
) -> Figure:
    """Single-panel histogram overlays with symmetric tolerance cuts.

    For each tolerance ``t``, shows the histogram of samples that satisfy
    BOTH lower and upper cuts simultaneously:
        ``L + t*(U-L) <= x <= U - t*(U-L)``

    Colored by tolerance via the configured colormap with a vertical
    colorbar. Log-y. When ``t_lo_star`` / ``t_hi_star`` are supplied,
    vertical red markers are drawn at the detected cut positions on the
    same panel (legend laid out in two columns).

    When ``x0`` and ``eps_star`` are supplied, samples within the interior
    stickiness cut are removed first (matches the two-panel version's
    semantics).

    Args:
        x, L, U: sample array and bounds.
        tols: tolerance grid. Defaults to ``linspace(0, 0.05, n_tols)``.
        n_tols, bins, use_alpha, config: as for
            ``plot_histogram_tolerance_overlays``.
        x0, eps_star: optional interior cut.
        t_lo_star, t_hi_star: optional detected cut markers.
        ax: optional existing Axes to draw on. When supplied, the returned
            Figure is ``ax.figure``.
        with_colorbar: if True (default), a tolerance colorbar is attached.
            When ``ax`` is None, the colorbar is placed at the figure's
            right edge. When ``ax`` is supplied, the colorbar is appended
            next to ``ax`` via ``make_axes_locatable`` so the surrounding
            gridspec layout is not disrupted. Set to False to skip the
            colorbar entirely (e.g., when the caller manages its own).

    Returns:
        The Figure containing (or owning) the drawn Axes.
    """
    if L >= U:
        raise ValueError(f"L must be less than U, got L={L}, U={U}")

    if config is None:
        config = PlotConfig()

    if tols is None:
        tols = np.linspace(0, 0.05, n_tols)

    x = x[np.isfinite(x)]
    if x0 is not None and eps_star is not None and len(x) > 0:
        z = compute_z(x, x0, L, U)
        x = x[z >= eps_star]

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=config.figsize_tolerance, dpi=config.dpi)
        own_fig = True
    else:
        fig = ax.figure
        own_fig = False

    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tols[0], vmax=tols[-1])
    bin_edges = np.linspace(L, U, bins + 1)
    alphas = np.linspace(1.0, 0.3, len(tols)) if use_alpha else np.ones(len(tols))
    colors = [cmap(norm(t)) for t in tols]

    for i, tol in enumerate(tols):
        margin = tol * (U - L)
        x_filt = x[(x >= L + margin) & (x <= U - margin)]
        if len(x_filt) == 0:
            continue
        ax.hist(
            x_filt,
            bins=bin_edges,
            histtype="stepfilled",
            alpha=alphas[i],
            color=colors[i],
            zorder=i,
        )

    ax.set_xlabel("Parameter value")
    ax.set_ylabel("Count")
    ax.set_title("Histogram at increasing symmetric tolerance cuts")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3)

    if t_lo_star is not None:
        ax.axvline(
            L + t_lo_star * (U - L),
            color="red",
            lw=2,
            label=f"t_lo* = {t_lo_star:.4f}",
        )
    if t_hi_star is not None:
        ax.axvline(
            U - t_hi_star * (U - L),
            color="red",
            lw=2,
            ls="--",
            label=f"t_hi* = {t_hi_star:.4f}",
        )
    if t_lo_star is not None or t_hi_star is not None:
        ax.legend(loc="best", fontsize=8, ncol=2)

    if with_colorbar:
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        if own_fig:
            fig.tight_layout()
            cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
            cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
            cbar.set_label("Tolerance")
            fig.subplots_adjust(right=0.9)
        else:
            from mpl_toolkits.axes_grid1 import make_axes_locatable

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="3%", pad=0.05)
            cbar = fig.colorbar(sm, cax=cax, orientation="vertical")
            cbar.set_label("Tolerance")
        # Show each sampled tolerance as a tick mark on the colorbar so the
        # viewer can map between discrete histogram layers and the color ramp.
        cbar.set_ticks(list(tols))
        cbar.ax.tick_params(labelsize=7)

    return fig


def plot_bounds_filter_comparison(
    x: np.ndarray,
    L: float,
    U: float,
    bins: int | str = "auto",
    config: PlotConfig | None = None,
    show_detail: bool = True,
) -> Figure:
    """Visualize removal of out-of-bounds samples (x < L or x > U).

    IMPORTANT: Despite the name "bounds filter", this visualization shows removal
    of OUT-OF-BOUNDS samples (x < L or x > U), NOT boundary-sticky samples (too
    close to L or U). For boundary stickiness filtering, see plot_combined_filter_comparison().

    Creates histograms showing:
    - Original data (including any out-of-bounds samples)
    - Filtered data (only samples within [L, U])
    - Out-of-bounds detail panel (if show_detail=True and out-of-bounds exist)

    When out-of-bounds samples exist, the third panel zooms in to show the
    filtered region clearly, making the impact visible even when out-of-bounds
    samples are spatially compressed.

    What gets removed:
    - x < L (below lower bound) - typically from failed fits
    - x > U (above upper bound) - typically from failed fits

    What does NOT get removed:
    - Samples AT the boundaries (x = L or x = U) - these are valid
    - Samples NEAR the boundaries - use combined filter for this

    Args:
        x: Array of parameter values (unfiltered).
        L: Lower bound of the parameter.
        U: Upper bound of the parameter.
        bins: Number of bins or binning strategy. Default is 'auto'.
        config: PlotConfig for styling. Uses defaults if None.
        show_detail: If True and out-of-bounds samples exist, adds a detail panel.

    Returns:
        Figure with 2-3 subplots showing unfiltered and filtered distributions.

    Examples:
        >>> # Dataset with failed fits at x=0 (out-of-bounds for L=0.01)
        >>> x = np.concatenate([
        ...     np.zeros(100),  # Out-of-bounds (x < L)
        ...     np.random.uniform(0.01, 100, 9900)  # Valid data
        ... ])
        >>> fig = plot_bounds_filter_comparison(x, L=0.01, U=100.0)
        >>> # Panel 1: Shows all 10,000 samples including spike at x=0
        >>> # Panel 2: Shows 9,900 samples (out-of-bounds removed)
        >>> # Panel 3: Zoomed view of [0, 0.01] region showing the removal
    """
    # Validate inputs
    if L >= U:
        raise ValueError(f"L must be less than U, got L={L}, U={U}")

    # Handle defaults
    if config is None:
        config = PlotConfig()

    # Filter non-finite values
    x = x[np.isfinite(x)]

    # Create filtered version
    x_filtered = x[(x >= L) & (x <= U)]

    # Count out-of-bounds samples
    n_total = len(x)
    n_below = np.sum(x < L)
    n_above = np.sum(x > U)
    n_out_of_bounds = n_below + n_above
    n_filtered = len(x_filtered)

    # Determine if we need a detail panel
    has_out_of_bounds = n_out_of_bounds > 0
    n_panels = 3 if (show_detail and has_out_of_bounds) else 2

    # Create figure with subplots (vertical layout for easier comparison)
    figsize = (10, 12) if n_panels == 3 else (10, 8)
    fig, axes = plt.subplots(n_panels, 1, figsize=figsize, dpi=config.dpi)

    # Determine bin edges from full data range for consistent binning
    # Extend slightly beyond [L, U] to capture out-of-bounds samples
    x_min = min(x.min(), L)
    x_max = max(x.max(), U)

    # Create bins
    if isinstance(bins, str):
        # Use numpy's histogram to determine bin edges
        _, bin_edges = np.histogram(x, bins=bins, range=(x_min, x_max))
    else:
        bin_edges = np.linspace(x_min, x_max, bins + 1)

    # Top subplot: Original (unfiltered) data
    ax_unfiltered = axes[0]
    counts_unfiltered, _, _ = ax_unfiltered.hist(
        x,
        bins=bin_edges,
        histtype="stepfilled",
        alpha=0.7,
        color="steelblue",
        edgecolor="black",
        linewidth=0.5,
    )

    # Add vertical lines at bounds
    ax_unfiltered.axvline(L, color="red", linestyle="--", linewidth=1.5, label=f"L={L}", alpha=0.7)
    ax_unfiltered.axvline(U, color="red", linestyle="--", linewidth=1.5, label=f"U={U}", alpha=0.7)

    # Add shading for out-of-bounds regions
    if n_below > 0:
        ax_unfiltered.axvspan(
            x_min, L, alpha=0.2, color="red", label=f"Out-of-bounds (below L): {n_below}"
        )
    if n_above > 0:
        ax_unfiltered.axvspan(
            U, x_max, alpha=0.2, color="red", label=f"Out-of-bounds (above U): {n_above}"
        )

    ax_unfiltered.set_xlabel("Parameter value")
    ax_unfiltered.set_ylabel("Count")
    ax_unfiltered.set_title(
        f"Original Data (n={n_total:,}, out-of-bounds={n_out_of_bounds:,} [{n_out_of_bounds / n_total:.2%}])"
    )
    ax_unfiltered.grid(True, alpha=0.3)
    ax_unfiltered.legend(loc="best", fontsize=8)

    # Bottom subplot: Filtered data
    ax_filtered = axes[1]
    counts_filtered, _, _ = ax_filtered.hist(
        x_filtered,
        bins=bin_edges,
        histtype="stepfilled",
        alpha=0.7,
        color="mediumseagreen",
        edgecolor="black",
        linewidth=0.5,
    )

    # Add vertical lines at bounds
    ax_filtered.axvline(L, color="green", linestyle="--", linewidth=1.5, label=f"L={L}", alpha=0.7)
    ax_filtered.axvline(U, color="green", linestyle="--", linewidth=1.5, label=f"U={U}", alpha=0.7)

    ax_filtered.set_xlabel("Parameter value")
    ax_filtered.set_ylabel("Count")
    ax_filtered.set_title(f"Filtered Data (n={n_filtered:,}, retained={n_filtered / n_total:.2%})")
    ax_filtered.grid(True, alpha=0.3)
    ax_filtered.legend(loc="best", fontsize=8)

    # Match y-axis scales for direct comparison
    y_max_overall = max(counts_unfiltered.max(), counts_filtered.max()) * 1.1
    ax_unfiltered.set_ylim(0, y_max_overall)
    ax_filtered.set_ylim(0, y_max_overall)

    # Third panel: Out-of-bounds detail (if needed)
    if n_panels == 3:
        ax_detail = axes[2]

        # Determine zoom range based on where out-of-bounds samples are
        valid_range = U - L
        margin = valid_range * 0.05  # 5% of valid range as margin

        if n_below > 0 and n_above > 0:
            # Out-of-bounds on both sides - show both regions
            zoom_label = "Out-of-Bounds Detail (Both Regions)"
            zoom_x_min = x_min
            zoom_x_max = x_max
        elif n_below > 0:
            # Out-of-bounds below L - zoom to that region
            zoom_x_min = x_min
            zoom_x_max = min(L + margin, U)
            zoom_label = f"Out-of-Bounds Detail (Below L: [{x_min:.3g}, {zoom_x_max:.3g}])"
        else:  # n_above > 0
            # Out-of-bounds above U - zoom to that region
            zoom_x_min = max(U - margin, L)
            zoom_x_max = x_max
            zoom_label = f"Out-of-Bounds Detail (Above U: [{zoom_x_min:.3g}, {x_max:.3g}])"

        # Create bins for zoom range
        zoom_range_width = zoom_x_max - zoom_x_min
        if isinstance(bins, str):
            # Use auto binning for zoom region
            _, zoom_bin_edges = np.histogram(
                x[(x >= zoom_x_min) & (x <= zoom_x_max)], bins=bins, range=(zoom_x_min, zoom_x_max)
            )
        else:
            # Use same bin density as main plot
            main_range_width = x_max - x_min
            zoom_bin_count = max(int(bins * zoom_range_width / main_range_width), 20)
            zoom_bin_edges = np.linspace(zoom_x_min, zoom_x_max, zoom_bin_count + 1)

        # Plot original data in zoom range
        x_zoom_original = x[(x >= zoom_x_min) & (x <= zoom_x_max)]
        _, _, _ = ax_detail.hist(
            x_zoom_original,
            bins=zoom_bin_edges,
            histtype="stepfilled",
            alpha=0.5,
            color="steelblue",
            edgecolor="black",
            linewidth=0.5,
            label=f"Original (n={len(x_zoom_original):,})",
        )

        # Plot filtered data in zoom range (should be much less or zero in out-of-bounds)
        x_zoom_filtered = x_filtered[(x_filtered >= zoom_x_min) & (x_filtered <= zoom_x_max)]
        _, _, _ = ax_detail.hist(
            x_zoom_filtered,
            bins=zoom_bin_edges,
            histtype="stepfilled",
            alpha=0.5,
            color="mediumseagreen",
            edgecolor="black",
            linewidth=0.5,
            label=f"Filtered (n={len(x_zoom_filtered):,})",
        )

        # Add vertical lines at bounds
        if zoom_x_min < L < zoom_x_max:
            ax_detail.axvline(
                L, color="red", linestyle="--", linewidth=1.5, label=f"L={L}", alpha=0.7
            )
        if zoom_x_min < U < zoom_x_max:
            ax_detail.axvline(
                U, color="red", linestyle="--", linewidth=1.5, label=f"U={U}", alpha=0.7
            )

        # Shade out-of-bounds regions
        if n_below > 0 and zoom_x_min < L:
            ax_detail.axvspan(zoom_x_min, min(L, zoom_x_max), alpha=0.2, color="red")
        if n_above > 0 and zoom_x_max > U:
            ax_detail.axvspan(max(U, zoom_x_min), zoom_x_max, alpha=0.2, color="red")

        ax_detail.set_xlabel("Parameter value")
        ax_detail.set_ylabel("Count")
        ax_detail.set_title(
            f"{zoom_label}\nRemoved: {n_out_of_bounds:,} samples ({n_out_of_bounds / n_total:.2%})"
        )
        ax_detail.grid(True, alpha=0.3)
        ax_detail.legend(loc="best", fontsize=8)
        ax_detail.set_xlim(zoom_x_min, zoom_x_max)

    fig.tight_layout()

    return fig


def plot_interior_filter_comparison(
    x: np.ndarray,
    x0: float,
    L: float,
    U: float,
    interior_result: InteriorResult,
    bins: int | str = "auto",
    config: PlotConfig | None = None,
) -> Figure:
    """Visualize removal of x0-sticky samples (initial guess stickiness).

    IMPORTANT TERMINOLOGY NOTE:
    Despite the name "interior filter", this shows removal of samples stuck
    at the INITIAL GUESS x0, NOT samples in the "interior region" of parameter
    space. The term "interior" refers to x0 as an interior point (i.e., not at
    the boundaries L or U).

    Better mental model: "x0 stickiness filter" or "initial guess filter"

    What gets removed:
    - Samples too close to x0 (``|x - x0| / (U - L) < eps_star``)
    - Indicates optimizer failed to explore away from initial guess

    What does NOT get removed:
    - Samples far from boundaries (these are valid, high-quality fits)
    - Samples near x0 if no stickiness is detected (threshold not exceeded)

    See Also:
    - run_interior_qc(): Detection function that identifies x0-sticky samples
    - plot_combined_filter_comparison(): Shows ALL THREE filter types together
    - README.md: "Understanding Filter Terminology" section

    Args:
        x: Array of parameter values (unfiltered).
        x0: Initial guess value for the parameter.
        L: Lower bound of the parameter.
        U: Upper bound of the parameter.
        interior_result: Result from run_interior_qc containing detection info.
        bins: Number of bins or binning strategy ('auto', 'fd', 'sturges', etc.).
        config: PlotConfig for styling. Uses defaults if None.

    Returns:
        Figure with two subplots:
        - Panel 1: Original data (including x0-stuck samples)
        - Panel 2: Filtered data (x0-sticky samples removed)

    Examples:
        >>> from fitqc import run_interior_qc, plot_interior_filter_comparison
        >>> # Run interior QC to detect x0 stickiness
        >>> result = run_interior_qc(x, x0=1.0, L=0.0, U=10.0)
        >>> # Visualize x0-sticky sample removal
        >>> fig = plot_interior_filter_comparison(x, 1.0, 0.0, 10.0, result)
        >>> fig.savefig("interior_filter.png")
    """
    # Validate inputs
    if L >= U:
        raise ValueError(f"L must be less than U, got L={L}, U={U}")

    # Handle defaults
    if config is None:
        config = PlotConfig()

    # Filter non-finite values
    x = x[np.isfinite(x)]

    # Create filtered version based on interior result
    if interior_result.spike_detected and interior_result.eps_star is not None:
        # Filter out samples within eps_star of x0
        z = np.abs(x - x0) / (U - L)
        x_filtered = x[z > interior_result.eps_star]
    else:
        # No detection, all samples pass
        x_filtered = x.copy()

    # Count stuck samples
    n_total = len(x)
    n_stuck = n_total - len(x_filtered)
    n_filtered = len(x_filtered)

    # Create figure with two subplots (vertical layout)
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), dpi=config.dpi)

    # Determine bin edges
    if isinstance(bins, str):
        _, bin_edges = np.histogram(x, bins=bins, range=(L, U))
    else:
        bin_edges = np.linspace(L, U, bins + 1)

    # Top subplot: Original (unfiltered) data
    ax_unfiltered = axes[0]
    counts_unfiltered, _, _ = ax_unfiltered.hist(
        x,
        bins=bin_edges,
        histtype="stepfilled",
        alpha=0.7,
        color="steelblue",
        edgecolor="black",
        linewidth=0.5,
    )

    # Add vertical line at x0
    ax_unfiltered.axvline(x0, color="red", linestyle="--", linewidth=2, label=f"x0={x0}", alpha=0.8)

    # Shade region around x0 if spike detected
    if interior_result.spike_detected and interior_result.eps_star is not None:
        eps_star = interior_result.eps_star
        x0_width = eps_star * (U - L)
        ax_unfiltered.axvspan(
            x0 - x0_width,
            x0 + x0_width,
            alpha=0.2,
            color="red",
            label=f"Stuck region (ε*={eps_star:.4f}): {n_stuck} samples",
        )

    ax_unfiltered.set_xlabel("Parameter value")
    ax_unfiltered.set_ylabel("Count")
    title_str = f"Original Data (n={n_total:,}"
    if interior_result.spike_detected:
        title_str += f", stuck={n_stuck:,} [{n_stuck / n_total:.2%}])"
    else:
        title_str += ", no x0 stickiness detected)"
    ax_unfiltered.set_title(title_str)
    ax_unfiltered.grid(True, alpha=0.3)
    ax_unfiltered.legend(loc="best", fontsize=8)

    # Bottom subplot: Filtered data
    ax_filtered = axes[1]
    counts_filtered, _, _ = ax_filtered.hist(
        x_filtered,
        bins=bin_edges,
        histtype="stepfilled",
        alpha=0.7,
        color="mediumseagreen",
        edgecolor="black",
        linewidth=0.5,
    )

    # Add vertical line at x0
    ax_filtered.axvline(x0, color="green", linestyle="--", linewidth=2, label=f"x0={x0}", alpha=0.8)

    ax_filtered.set_xlabel("Parameter value")
    ax_filtered.set_ylabel("Count")
    ax_filtered.set_title(f"Filtered Data (n={n_filtered:,}, retained={n_filtered / n_total:.2%})")
    ax_filtered.grid(True, alpha=0.3)
    ax_filtered.legend(loc="best", fontsize=8)

    # Match y-axis scales for direct comparison
    y_max_overall = max(counts_unfiltered.max(), counts_filtered.max()) * 1.1
    ax_unfiltered.set_ylim(0, y_max_overall)
    ax_filtered.set_ylim(0, y_max_overall)

    fig.tight_layout()

    return fig


def plot_combined_filter_comparison(
    x: np.ndarray,
    x0: float | None,
    L: float,
    U: float,
    interior_result: InteriorResult | None,
    boundary_result: BoundaryResult,
    bins: int | str = "auto",
    config: PlotConfig | None = None,
) -> Figure:
    """Visualize removal of ALL THREE filter types: out-of-bounds, boundary-sticky, and x0-sticky.

    IMPORTANT: This is where boundary spikes disappear! Panel 2 ("Boundary Filter Only")
    still shows boundary spikes because it only removes out-of-bounds (x < L or x > U).
    Panel 4 ("Combined Filters") applies BOTH boundary stickiness detection AND
    out-of-bounds filtering, which is why the spikes disappear there.

    Four Progressive Filtering Stages:

    Panel 1: Original Data
    - All samples (unfiltered)
    - Shows out-of-bounds + boundary spikes + x0 spikes (if applicable)

    Panel 2: "Boundary Filter Only"
    - Removes: Out-of-bounds samples (x < L or x > U)
    - Still shows: Boundary spikes (samples AT L or U)
    - Still shows: x0 spikes (if applicable)
    - For datasets with all x ∈ [L, U]: Identical to Panel 1

    Panel 3: "Interior Filter Only" (if x0 provided)
    - Removes: x0-sticky samples (``|x - x0| / (U - L) < eps_star``)
    - Still shows: Out-of-bounds samples
    - Still shows: Boundary spikes
    - Skipped if x0 is None

    Panel 4: "Combined Filters" - FINAL RESULT
    - Removes: out-of-bounds, boundary-sticky, and x0-sticky samples
    - This is where boundary spikes disappear!
    - Represents the cleanest, highest-quality data

    Understanding the Terminology Confusion:
    - "Boundary filter" (Panel 2) only removes out-of-bounds, NOT boundary spikes
    - Boundary spikes are removed by applying boundary_result thresholds in Panel 4
    - The naming reflects implementation modules, not user-facing effects

    See Also:
    - plot_bounds_filter_comparison(): Shows only out-of-bounds removal
    - plot_interior_filter_comparison(): Shows only x0-sticky removal
    - README.md: "Understanding Filter Terminology" section

    Args:
        x: Array of parameter values (unfiltered).
        x0: Initial guess value (None for moment-based parameters).
        L: Lower bound of the parameter.
        U: Upper bound of the parameter.
        interior_result: Result from run_interior_qc (None if no x0).
        boundary_result: Result from run_boundary_qc containing threshold info.
        bins: Number of bins or binning strategy.
        config: PlotConfig for styling. Uses defaults if None.

    Returns:
        Figure with 2x2 grid showing progressive filtering stages.

    Examples:
        >>> from fitqc import run_qc
        >>> report, masks = run_qc(params, spec)
        >>> fig = plot_combined_filter_comparison(
        ...     x, x0=1.0, L=0.0, U=10.0,
        ...     report.interior_results['alpha'],
        ...     report.boundary_results['alpha']
        ... )
    """
    # Validate inputs
    if L >= U:
        raise ValueError(f"L must be less than U, got L={L}, U={U}")

    # Handle defaults
    if config is None:
        config = PlotConfig()

    # Filter non-finite values
    x = x[np.isfinite(x)]
    n_total = len(x)

    # Apply boundary filter: out-of-bounds removal + stickiness thresholds
    u = (x - L) / (U - L)
    boundary_mask = (u >= 0) & (u <= 1)
    if boundary_result.lower_pileup_detected and boundary_result.t_lo_star is not None:
        boundary_mask &= u > boundary_result.t_lo_star
    if boundary_result.upper_pileup_detected and boundary_result.t_hi_star is not None:
        boundary_mask &= u < (1 - boundary_result.t_hi_star)
    x_boundary_only = x[boundary_mask]

    # Apply interior filter (if applicable)
    if interior_result is not None and x0 is not None:
        if interior_result.spike_detected and interior_result.eps_star is not None:
            z = np.abs(x - x0) / (U - L)
            interior_mask = z > interior_result.eps_star
            x_interior_only = x[interior_mask]
        else:
            interior_mask = np.ones(len(x), dtype=bool)
            x_interior_only = x.copy()
    else:
        interior_mask = np.ones(len(x), dtype=bool)
        x_interior_only = x.copy()

    # Apply both filters
    combined_mask = boundary_mask & interior_mask
    x_combined = x[combined_mask]

    # Count samples at each stage
    n_boundary = len(x_boundary_only)
    n_interior = len(x_interior_only)
    n_combined = len(x_combined)

    # Create figure with 4x2 grid: linear (top) and log (bottom)
    fig, axes = plt.subplots(4, 2, figsize=(16, 22), dpi=config.dpi)

    # Determine bin edges
    if isinstance(bins, str):
        _, bin_edges = np.histogram(x, bins=bins, range=(L, U))
    else:
        bin_edges = np.linspace(L, U, bins + 1)

    # Colors: high-contrast pair for original vs filtered overlay
    color_original = "#888888"  # Gray for original (background)
    color_filtered = "#d62728"  # Red for filtered (foreground)

    # --- Helper to plot a single panel ---
    def _plot_panel(
        ax,
        data,
        color,
        edgecolor,
        alpha,
        title,
        show_bounds=True,
        bounds_color="red",
        overlay_original=False,
    ):
        if overlay_original:
            ax.hist(
                x,
                bins=bin_edges,
                histtype="stepfilled",
                alpha=0.5,
                color=color_original,
                edgecolor="none",
                label="Original",
                zorder=1,
            )
            counts, _, _ = ax.hist(
                data,
                bins=bin_edges,
                histtype="stepfilled",
                alpha=0.85,
                color=color_filtered,
                edgecolor="black",
                linewidth=0.3,
                label="Filtered",
                zorder=2,
            )
            ax.legend(fontsize=8, loc="upper right")
        else:
            counts, _, _ = ax.hist(
                data,
                bins=bin_edges,
                histtype="stepfilled",
                alpha=alpha,
                color=color,
                edgecolor=edgecolor,
                linewidth=0.5,
            )
        if show_bounds:
            ax.axvline(L, color=bounds_color, linestyle="--", linewidth=1, alpha=0.5)
            ax.axvline(U, color=bounds_color, linestyle="--", linewidth=1, alpha=0.5)
        if x0 is not None:
            ax.axvline(x0, color="orange", linestyle="--", linewidth=1.5, alpha=0.7)
        ax.set_xlabel("Parameter value")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        return counts

    # --- Row 0: Linear scale panels ---
    counts_original = _plot_panel(
        axes[0, 0], x, "steelblue", "black", 0.7, f"1. Original (n={n_total:,})"
    )
    axes[0, 0].set_ylabel("Count")

    removed_boundary = n_total - n_boundary
    counts_boundary = _plot_panel(
        axes[0, 1],
        x_boundary_only,
        "coral",
        "black",
        0.7,
        f"2. Boundary Filter (n={n_boundary:,}, "
        f"removed={removed_boundary:,} [{removed_boundary / n_total:.2%}])",
        bounds_color="green",
    )
    axes[0, 1].set_ylabel("Count")

    removed_interior = n_total - n_interior
    title_int = "3. Interior Filter"
    if interior_result is not None and interior_result.spike_detected:
        title_int += (
            f" (n={n_interior:,}, removed={removed_interior:,} [{removed_interior / n_total:.2%}])"
        )
    else:
        title_int += f" (n={n_interior:,}, no x0 stickiness)"
    counts_interior = _plot_panel(axes[1, 0], x_interior_only, "plum", "black", 0.7, title_int)
    axes[1, 0].set_ylabel("Count")

    removed_combined = n_total - n_combined
    counts_combined = _plot_panel(
        axes[1, 1],
        x_combined,
        None,
        None,
        None,
        f"4. Combined (n={n_combined:,}, removed={removed_combined:,} "
        f"[{removed_combined / n_total:.2%}])",
        bounds_color="green",
        overlay_original=True,
    )
    axes[1, 1].set_ylabel("Count")

    # Match y-axis for linear panels (rows 0-1)
    y_max_linear = (
        max(
            counts_original.max(),
            counts_boundary.max(),
            counts_interior.max(),
            counts_combined.max(),
        )
        * 1.1
    )
    for ax in axes[:2].flat:
        ax.set_ylim(0, y_max_linear)

    # --- Row 2-3: Log scale panels (same layout, log y-axis) ---
    _plot_panel(
        axes[2, 0], x, "steelblue", "black", 0.7, f"5. Original \u2014 log scale (n={n_total:,})"
    )
    axes[2, 0].set_ylabel("Count (log)")
    axes[2, 0].set_yscale("log")

    _plot_panel(
        axes[2, 1],
        x_boundary_only,
        "coral",
        "black",
        0.7,
        "6. Boundary Filter \u2014 log scale",
        bounds_color="green",
    )
    axes[2, 1].set_ylabel("Count (log)")
    axes[2, 1].set_yscale("log")

    _plot_panel(
        axes[3, 0], x_interior_only, "plum", "black", 0.7, "7. Interior Filter \u2014 log scale"
    )
    axes[3, 0].set_ylabel("Count (log)")
    axes[3, 0].set_yscale("log")

    _plot_panel(
        axes[3, 1],
        x_combined,
        None,
        None,
        None,
        "8. Combined \u2014 log scale",
        bounds_color="green",
        overlay_original=True,
    )
    axes[3, 1].set_ylabel("Count (log)")
    axes[3, 1].set_yscale("log")

    fig.tight_layout()

    return fig


def plot_quantile_elbow_overlay(
    result: InteriorResult | BoundaryResult,
    config: PlotConfig | None = None,
) -> Figure:
    """Plot quantile elbow thresholds from multi-curve detection results.

    Visualizes the relationship between quantile levels and their detected elbow
    thresholds, providing insight into the multi-curve threshold estimation used
    in quantile-based stickiness detection.

    For InteriorResult:

    - X-axis: Quantile values (e.g., 0.001, 0.01, 0.05)
    - Y-axis: Detected epsilon thresholds (log scale)
    - Single panel showing quantile vs eps relationship

    For BoundaryResult:

    - Two panels: one for lower boundary, one for upper boundary
    - X-axis: Quantile values
    - Y-axis: Detected tolerance thresholds

    Args:
        result: InteriorResult or BoundaryResult with quantile_elbows field.
        config: PlotConfig for styling. Uses defaults if None.

    Returns:
        matplotlib Figure object. Caller is responsible for displaying or saving.

    Note:
        If result.quantile_elbows is None or empty, returns a figure with a
        message indicating no quantile data is available.

    Example:
        >>> from fitqc import run_interior_qc, InteriorConfig, PlotConfig
        >>> from fitqc.plot import plot_quantile_elbow_overlay
        >>>
        >>> config = InteriorConfig(use_quantile_analysis=True)
        >>> result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)
        >>> fig = plot_quantile_elbow_overlay(result, PlotConfig())
        >>> fig.savefig("quantile_elbows.png")
    """
    # Set default config
    if config is None:
        config = PlotConfig()

    # Determine result type and extract quantile_elbows
    is_boundary = isinstance(result, BoundaryResult)

    # Handle None or empty quantile_elbows
    if result.quantile_elbows is None:
        return _plot_no_quantile_data(config, is_boundary)

    if isinstance(result.quantile_elbows, dict) and len(result.quantile_elbows) == 0:
        return _plot_no_quantile_data(config, is_boundary)

    # Create figure based on result type
    if is_boundary:
        return _plot_boundary_quantile_elbows(result, config)
    else:
        return _plot_interior_quantile_elbows(result, config)


def _plot_no_quantile_data(config: PlotConfig, is_boundary: bool) -> Figure:
    """Create a placeholder figure when no quantile data is available."""
    fig, ax = plt.subplots(1, 1, figsize=config.figsize_tolerance, dpi=config.dpi)

    ax.text(
        0.5,
        0.5,
        "No quantile elbow data available.\n\n"
        "Enable quantile analysis with:\n"
        "config = InteriorConfig(use_quantile_analysis=True)"
        if not is_boundary
        else "config = BoundaryConfig(use_quantile_analysis=True)",
        ha="center",
        va="center",
        fontsize=12,
        transform=ax.transAxes,
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
    )

    ax.set_xlabel("Quantile")
    ax.set_ylabel("Elbow Threshold")
    ax.set_title("Quantile Elbow Analysis")

    fig.tight_layout()
    return fig


def _plot_interior_quantile_elbows(result: InteriorResult, config: PlotConfig) -> Figure:
    """Plot quantile elbows for interior (x0 stickiness) results."""
    fig, ax = plt.subplots(1, 1, figsize=config.figsize_tolerance, dpi=config.dpi)

    cmap = plt.get_cmap(config.cmap)
    quantile_elbows = result.quantile_elbows

    # Filter valid (non-None) elbows and sort by quantile
    valid_elbows = {q: e for q, e in quantile_elbows.items() if e is not None}
    sorted_quantiles = sorted(valid_elbows.keys())

    if len(sorted_quantiles) == 0:
        # No valid elbows, show message
        ax.text(
            0.5,
            0.5,
            "No valid elbow thresholds detected.\nAll quantiles returned None.",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.set_xlabel("Quantile")
        ax.set_ylabel("Epsilon (elbow threshold)")
        ax.set_title("Quantile Elbow Analysis - Interior")
        fig.tight_layout()
        return fig

    # Extract data for plotting
    x_vals = np.array(sorted_quantiles)
    y_vals = np.array([valid_elbows[q] for q in sorted_quantiles])

    # Create color normalization
    norm = Normalize(vmin=x_vals.min(), vmax=x_vals.max())

    # Plot each point with color based on quantile
    colors = [cmap(norm(q)) for q in x_vals]

    # Plot line connecting points
    ax.plot(x_vals, y_vals, "k-", alpha=0.3, linewidth=1, zorder=1)

    # Plot scatter with colors and labels
    for i, (q, eps) in enumerate(zip(x_vals, y_vals, strict=True)):
        ax.scatter(
            [q],
            [eps],
            c=[colors[i]],
            s=100,
            zorder=2,
            label=f"q={q:.3f}: eps={eps:.2e}",
        )

    # Mark eps_star if available
    if result.eps_star is not None:
        ax.axhline(
            result.eps_star,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=f"eps* (median) = {result.eps_star:.2e}",
        )

    # Use log scale for y-axis (epsilon values span orders of magnitude)
    ax.set_yscale("log")

    # Labels and title
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Epsilon (elbow threshold)")
    ax.set_title("Quantile Elbow Analysis - Interior (x0 stickiness)")
    ax.grid(True, alpha=0.3)

    # Add legend (limit to reasonable number of entries)
    if len(sorted_quantiles) <= 8:
        ax.legend(loc="best", fontsize=8)
    else:
        # Just show eps_star in legend if too many quantiles
        handles, labels = ax.get_legend_handles_labels()
        # Keep only the eps_star line if present
        eps_star_idx = [i for i, label in enumerate(labels) if "eps*" in label]
        if eps_star_idx:
            ax.legend([handles[eps_star_idx[0]]], [labels[eps_star_idx[0]]], loc="best")

    fig.tight_layout()
    return fig


def _plot_boundary_quantile_elbows(result: BoundaryResult, config: PlotConfig) -> Figure:
    """Plot quantile elbows for boundary (L/U stickiness) results."""
    fig, axes = plt.subplots(1, 2, figsize=config.figsize_tolerance, dpi=config.dpi)

    cmap = plt.get_cmap(config.cmap)
    quantile_elbows = result.quantile_elbows

    # Plot lower boundary
    ax_lower = axes[0]
    _plot_boundary_panel(
        ax=ax_lower,
        elbows=quantile_elbows.get("lower", {}),
        t_star=result.t_lo_star,
        t_raw=result.t_lo_raw,
        boundary_name="Lower",
        cmap=cmap,
    )

    # Plot upper boundary
    ax_upper = axes[1]
    _plot_boundary_panel(
        ax=ax_upper,
        elbows=quantile_elbows.get("upper", {}),
        t_star=result.t_hi_star,
        t_raw=result.t_hi_raw,
        boundary_name="Upper",
        cmap=cmap,
    )

    fig.tight_layout()
    return fig


def _plot_boundary_panel(
    ax,
    elbows: dict[float, float | None],
    t_star: float | None,
    boundary_name: str,
    cmap,
    t_raw: float | None = None,
) -> None:
    """Plot a single boundary panel for quantile elbow visualization.

    Shows the CDF-inverse curve (tolerance at each quantile), the Kneedle
    elbow location, and horizontal lines for raw and validated thresholds.
    """
    # Filter valid (non-None) elbows
    if elbows is None:
        elbows = {}
    valid_elbows = {q: t for q, t in elbows.items() if t is not None}
    sorted_quantiles = sorted(valid_elbows.keys())

    if len(sorted_quantiles) == 0:
        ax.text(
            0.5,
            0.5,
            f"No valid elbow thresholds\nfor {boundary_name.lower()} boundary.",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.set_xlabel("Quantile")
        ax.set_ylabel("Tolerance")
        ax.set_title(f"Quantile Elbow Analysis - {boundary_name} Boundary")
        return

    # Extract data
    x_vals = np.array(sorted_quantiles)
    y_vals = np.array([valid_elbows[q] for q in sorted_quantiles])

    # Create color normalization
    norm = Normalize(vmin=x_vals.min(), vmax=x_vals.max())
    colors = [cmap(norm(q)) for q in x_vals]

    # Plot line connecting points
    ax.plot(x_vals, y_vals, "k-", alpha=0.3, linewidth=1, zorder=1)

    # Plot scatter with colors — single legend entry for the curve
    for i, (q, tol) in enumerate(zip(x_vals, y_vals, strict=True)):
        ax.scatter(
            [q],
            [tol],
            c=[colors[i]],
            s=100,
            zorder=2,
            label="tolerance at quantile" if i == 0 else None,
        )

    # Elbow marker: interpolate the quantile position of t_raw on the curve
    if t_raw is not None:
        q_elbow = np.interp(t_raw, y_vals, x_vals)
        ax.scatter(
            [q_elbow],
            [t_raw],
            marker="D",
            c="#d62728",
            s=150,
            zorder=3,
            edgecolors="black",
            linewidths=0.8,
            label=f"Kneedle elbow = {t_raw:.4f}",
        )

    # Horizontal threshold lines
    if t_raw is not None:
        ax.axhline(
            t_raw,
            color="#2ca02c",
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
            label=f"raw threshold = {t_raw:.4f}",
        )

    if t_star is not None:
        validated_label = f"validated threshold = {t_star:.4f}"
        if t_raw is None:
            validated_label += " (raw unavailable)"
        ax.axhline(
            t_star,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=validated_label,
        )

    # Labels and title
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Tolerance")
    ax.set_title(f"Quantile Elbow Analysis - {boundary_name} Boundary")
    ax.grid(True, alpha=0.3)

    ax.legend(loc="best", fontsize=8)


def _overview_merged_hist(
    ax,
    x_clean: np.ndarray,
    x_filtered: np.ndarray,
    n_total: int,
    n_kept: int,
    x0: float | None,
    L: float,
    U: float,
    tols: np.ndarray,
    boundary_result: BoundaryResult,
    interior_result: InteriorResult | None,
    config: PlotConfig,
) -> None:
    """Info-dense top-left panel merging three visualizations.

    Layers (bottom to top):
    1. Raw histogram as pale gray fill (context).
    2. Tolerance sweep: stepfilled histograms at each sampled tolerance,
       colored via the configured colormap with a colorbar (from
       plot_histogram_tolerance_overlays_combined).
    3. Pipeline-filtered histogram (actual asymmetric mask + interior cut)
       as a thick black step-outline (no fill).
    4. L/U/x0/t*/eps* vertical markers.

    The tolerance sweep is symmetric (same t on both sides); the filtered
    outline is the asymmetric pipeline mask the receiver actually applies.
    Showing both together lets the viewer compare the two cuts at a glance.
    """
    bin_edges = np.linspace(L, U, 101)

    plot_histogram_tolerance_overlays_combined(
        x=x_clean,
        L=L,
        U=U,
        tols=tols,
        bins=100,
        config=config,
        x0=x0,
        eps_star=interior_result.eps_star if interior_result is not None else None,
        t_lo_star=None,
        t_hi_star=None,
        ax=ax,
        with_colorbar=True,
    )

    # Gray semi-transparent overlay on the pipeline-filtered (retained)
    # region: the tolerance sweep below shows what each tolerance layer
    # looks like in full color; the gray overlay highlights what the
    # pipeline actually keeps. Combined with the vertical cut markers
    # below, this lets the viewer see at a glance which region is
    # retained and which is discarded.
    if n_kept > 0:
        ax.hist(
            x_filtered,
            bins=bin_edges,
            color="#555555",
            alpha=0.45,
            edgecolor="none",
            zorder=100,
            label=f"Pipeline filtered (kept {n_kept} of {n_total})",
        )

    ax.axvline(L, color="black", lw=1)
    ax.axvline(U, color="black", lw=1)
    if x0 is not None:
        ax.axvline(x0, color="green", lw=1.5, label=f"x0={x0:.3g}")
    if boundary_result.t_lo_star is not None:
        ax.axvline(
            L + boundary_result.t_lo_star * (U - L),
            color="red",
            lw=2,
            ls=":",
            label=f"t_lo*={boundary_result.t_lo_star:.4f}",
        )
    if boundary_result.t_hi_star is not None:
        ax.axvline(
            U - boundary_result.t_hi_star * (U - L),
            color="red",
            lw=2,
            ls=":",
            label=f"t_hi*={boundary_result.t_hi_star:.4f}",
        )
    if interior_result is not None and interior_result.eps_star is not None and x0 is not None:
        half_width = interior_result.eps_star * max(x0 - L, U - x0)
        ax.axvline(x0 - half_width, color="orange", lw=1.5, ls="--", alpha=0.7)
        ax.axvline(
            x0 + half_width,
            color="orange",
            lw=1.5,
            ls="--",
            alpha=0.7,
            label=f"eps*={interior_result.eps_star:.2e}",
        )

    ax.set_title(f"Raw, tolerance sweep, pipeline-filtered (n={n_total})")
    ax.grid(True, alpha=0.3)
    # Final legend call after all layers + markers so every labeled artist
    # appears (the combined-overlay's internal legend is superseded here).
    ax.legend(loc="best", fontsize=7)


def _overview_boundary_mass_side(
    ax,
    result: BoundaryResult,
    side: Literal["lower", "upper"],
    config: PlotConfig,
) -> None:
    """Single boundary-side mass-curve panel with tolerance-colored segments.

    Draws one side only (lower or upper) with per-segment color encoding
    the tolerance value, a tolerance colorbar appended via
    make_axes_locatable, and t_star marker + zoom logic.
    """
    tol_grid = result.tol_grid
    if side == "lower":
        mass_curve = result.lower_mass_curve
        t_star = result.t_lo_star
        title = "Lower boundary mass curve"
        ylabel = "P(u < tol)"
        marker_label = "t_lo*"
    else:
        mass_curve = result.upper_mass_curve
        t_star = result.t_hi_star
        title = "Upper boundary mass curve"
        ylabel = "P(u > 1-tol)"
        marker_label = "t_hi*"

    if len(tol_grid) == 0:
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "No mass-curve data",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=10,
        )
        return

    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tol_grid[0], vmax=tol_grid[-1])
    seg_colors = [cmap(0.15 + 0.85 * norm(t)) for t in tol_grid]

    for i in range(len(tol_grid) - 1):
        ax.plot(
            tol_grid[i : i + 2],
            mass_curve[i : i + 2],
            color=seg_colors[i],
            linewidth=2,
        )
    ax.plot(
        tol_grid,
        tol_grid,
        "k--",
        alpha=0.4,
        linewidth=1,
        label="Uniform (P = tol)",
    )
    ax.set_xlabel("Tolerance (tol)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if t_star is not None:
        ax.axvline(
            t_star,
            color="red",
            linestyle=":",
            linewidth=2,
            label=f"{marker_label} = {t_star:.4f}",
        )

    t_for_zoom = t_star if t_star is not None else 0.0
    x_max = max(t_for_zoom * 4, result.pileup_threshold * 4)
    if x_max > 0:
        in_range = tol_grid <= x_max
        if in_range.any():
            mass_in = mass_curve[in_range]
            uniform_in = tol_grid[in_range]
            y_max = 1.2 * max(float(mass_in.max()), 1.5 * float(uniform_in.max()))
            ax.set_xlim(0, x_max)
            ax.set_ylim(0, y_max)

    ax.legend(loc="best", fontsize=7)

    from mpl_toolkits.axes_grid1 import make_axes_locatable

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = ax.figure.colorbar(sm, cax=cax, orientation="vertical")
    cbar.set_label("Tolerance")
    cbar.ax.tick_params(labelsize=7)


def _overview_interior_zhist(ax, interior_result: InteriorResult) -> None:
    """Interior z-histogram with before/after overplot."""
    if interior_result.hist_edges is None or len(interior_result.hist_edges) <= 1:
        ax.axis("off")
        ax.text(0.5, 0.5, "No z-histogram", ha="center", va="center", transform=ax.transAxes)
        return
    ihe = interior_result.hist_edges
    bin_centers = (ihe[:-1] + ihe[1:]) / 2
    bin_width = ihe[1] - ihe[0]
    ax.bar(
        bin_centers,
        interior_result.hist_counts,
        width=bin_width,
        color="#808080",
        alpha=0.6,
        edgecolor="none",
        label="Before cut",
    )
    if interior_result.eps_star is not None:
        after_counts = np.where(
            bin_centers >= interior_result.eps_star,
            interior_result.hist_counts,
            0,
        )
        ax.bar(
            bin_centers,
            after_counts,
            width=bin_width,
            color="#2166ac",
            alpha=0.85,
            edgecolor="none",
            label=f"After cut (eps*={interior_result.eps_star:.2e})",
        )
        ax.axvline(interior_result.eps_star, color="red", lw=2, ls=":")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xlabel("z (normalized distance from x0)")
    ax.set_ylabel("Count")
    ax.set_title("Interior z-histogram")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=7)


def _overview_ecdf_side(
    ax,
    u: np.ndarray,
    side: Literal["lower", "upper"],
    tols: np.ndarray,
    t_star: float | None,
    cmap,
) -> None:
    """Simplified ECDF panel with tolerance-colored overlays + t* marker."""
    u = u[np.isfinite(u)]
    norm = Normalize(vmin=tols[0], vmax=tols[-1])
    alphas = np.linspace(1.0, 0.3, len(tols))
    for i, tol in enumerate(tols):
        if side == "lower":
            u_filt = u[u > tol]
        else:
            u_filt = u[u < 1 - tol]
        if len(u_filt) == 0:
            continue
        u_sorted = np.sort(u_filt)
        ecdf_vals = np.arange(1, len(u_sorted) + 1) / len(u_sorted)
        ax.plot(u_sorted, ecdf_vals, color=cmap(norm(tol)), alpha=alphas[i], linewidth=1.5)
    if side == "lower":
        ax.plot([0, 0.1], [0, 0.1], "k--", alpha=0.5, linewidth=1)
        ax.set_xlim(0, 0.1)
        ax.set_xlabel("u")
        ax.set_title("ECDF near lower")
        if t_star is not None:
            ax.axvline(t_star, color="red", lw=2, label=f"t_lo*={t_star:.4f}")
            ax.legend(loc="best", fontsize=7)
    else:
        ax.plot([0.9, 1.0], [0.9, 1.0], "k--", alpha=0.5, linewidth=1)
        ax.set_xlim(0.9, 1.0)
        ax.set_xlabel("u")
        ax.set_title("ECDF near upper")
        if t_star is not None:
            ax.axvline(1 - t_star, color="red", lw=2, label=f"t_hi*={t_star:.4f}")
            ax.legend(loc="best", fontsize=7)
    ax.set_ylabel("ECDF")
    ax.grid(True, alpha=0.3)


def _overview_interior_mass(ax, interior_result: InteriorResult) -> None:
    """Interior mass curve (log-x) with eps* marker."""
    if len(interior_result.eps_grid) == 0:
        ax.axis("off")
        ax.text(0.5, 0.5, "No mass curve", ha="center", va="center", transform=ax.transAxes)
        return
    ax.semilogx(interior_result.eps_grid, interior_result.mass_curve, color="#2166ac", linewidth=2)
    ax.set_xlabel("epsilon (log scale)")
    ax.set_ylabel("P(z < epsilon)")
    ax.set_title("Interior mass curve")
    ax.grid(True, alpha=0.3)
    if interior_result.eps_star is not None:
        ax.axvline(
            interior_result.eps_star,
            color="red",
            lw=2,
            ls=":",
            label=f"eps*={interior_result.eps_star:.2e}",
        )
        ax.legend(loc="best", fontsize=7)


def _overview_spacing(
    ax,
    x_sorted: np.ndarray,
    L: float,
    U: float,
    tols: np.ndarray,
    cmap,
    q_max: float = 0.15,
    n_quantiles: int = 100,
) -> None:
    """Simplified quantile-spacing overlay."""
    norm = Normalize(vmin=tols[0], vmax=tols[-1])
    alphas = np.linspace(1.0, 0.3, len(tols))
    for i, tol in enumerate(tols):
        margin = tol * (U - L)
        x_filt = x_sorted[(x_sorted > L + margin) & (x_sorted < U - margin)]
        n_filt = len(x_filt)
        max_idx = int(q_max * n_filt)
        if max_idx < 2:
            continue
        n_q = min(n_quantiles, max_idx)
        q_indices = np.linspace(0, max_idx - 1, n_q).astype(int)
        quantiles = x_filt[q_indices]
        dq = np.diff(quantiles)
        if len(dq) == 0:
            continue
        ax.plot(np.arange(len(dq)), dq, color=cmap(norm(tol)), alpha=alphas[i], linewidth=1.5)
    ax.set_xlabel("Quantile index")
    ax.set_ylabel("dq")
    ax.set_title(f"Spacing in lowest q={q_max:.2g}")
    ax.grid(True, alpha=0.3)


def _draw_elbow_family(
    ax,
    elbows: dict,
    t_star: float | None,
    t_raw: float | None,
    color: str,
    marker: str,
    label_prefix: str,
) -> bool:
    """Draw one family (lower / upper / interior) on the combined-elbows panel.

    Renders: scatter + connecting line for per-quantile elbows, diamond
    marker at (q_elbow, t_raw) where the Kneedle result intersects the
    curve, axhline at t_raw (dashed, same color), axhline at t_star
    (solid thicker, same color). Mirrors the standalone
    ``*_boundary_elbows.png`` content so no information is lost when the
    overview folds the panel in.

    Returns True if anything was drawn.
    """
    if not elbows:
        return False
    valid = {q: t for q, t in elbows.items() if t is not None}
    if not valid:
        return False

    sorted_q = sorted(valid.keys())
    x_vals = np.array(sorted_q)
    y_vals = np.array([valid[q] for q in sorted_q])
    ax.plot(x_vals, y_vals, color=color, alpha=0.35, linewidth=1)
    ax.scatter(
        x_vals,
        y_vals,
        marker=marker,
        color=color,
        s=40,
        label=f"{label_prefix} tol(q)",
    )

    if t_raw is not None:
        # Interpolate the quantile position where the curve reaches t_raw.
        # When y_vals is not monotonically increasing np.interp still returns
        # a sensible result at the nearest edge; t_raw=0 maps to x_vals[0].
        q_elbow = float(np.interp(t_raw, y_vals, x_vals))
        ax.scatter(
            [q_elbow],
            [t_raw],
            marker="D",
            s=110,
            facecolor=color,
            edgecolor="black",
            linewidth=0.8,
            zorder=5,
            label=f"{label_prefix} Kneedle elbow={t_raw:.4f}",
        )
        ax.axhline(
            t_raw,
            color=color,
            linestyle="--",
            linewidth=1,
            alpha=0.6,
            label=f"{label_prefix} t_raw={t_raw:.4f}",
        )

    if t_star is not None:
        ax.axhline(
            t_star,
            color=color,
            linestyle="-",
            linewidth=1.8,
            alpha=0.9,
            label=f"{label_prefix} t*={t_star:.4f}",
        )
    return True


def _overview_boundary_elbow_side(
    ax,
    boundary_result: BoundaryResult,
    side: Literal["lower", "upper"],
) -> None:
    """Single boundary-side elbow panel.

    One side only (lower or upper), with per-quantile scatter, Kneedle
    diamond, t_raw and t_star axhlines — matches the corresponding
    panel of the standalone *_boundary_elbows.png.
    """
    elbows_dict = boundary_result.quantile_elbows or {}
    if not isinstance(elbows_dict, dict):
        elbows_dict = {}
    if side == "lower":
        elbows = elbows_dict.get("lower", {})
        t_star = boundary_result.t_lo_star
        t_raw = boundary_result.t_lo_raw
        color = "#1f77b4"
        marker = "o"
        label_prefix = "lower"
        title = "Lower boundary quantile elbows"
    else:
        elbows = elbows_dict.get("upper", {})
        t_star = boundary_result.t_hi_star
        t_raw = boundary_result.t_hi_raw
        color = "#d62728"
        marker = "x"
        label_prefix = "upper"
        title = "Upper boundary quantile elbows"

    drawn = _draw_elbow_family(ax, elbows, t_star, t_raw, color, marker, label_prefix)
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Tolerance")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    if drawn:
        ax.legend(loc="best", fontsize=7)
    else:
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            f"No {label_prefix} quantile elbows",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=10,
        )


def _overview_interior_elbows_panel(
    ax,
    interior_result: InteriorResult | None,
) -> None:
    """Interior quantile elbow panel: single family on log y-axis."""
    if (
        interior_result is None
        or interior_result.quantile_elbows is None
        or not interior_result.quantile_elbows
    ):
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "No interior quantile elbows",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=10,
        )
        return

    drawn = _draw_elbow_family(
        ax,
        interior_result.quantile_elbows,
        interior_result.eps_star,
        # InteriorResult has no separate t_raw; the detector emits a
        # single eps_star (median across quantiles) that serves as the
        # validated threshold. No Kneedle-diamond or t_raw axhline is
        # drawn for interior, matching the standalone interior plot.
        None,
        "#2ca02c",
        "s",
        "interior",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Epsilon (log)")
    ax.set_title("Interior quantile elbows")
    ax.grid(True, alpha=0.3)
    if drawn:
        ax.legend(loc="best", fontsize=7)


def plot_parameter_overview(
    param_name: str,
    x: np.ndarray,
    x0: float | None,
    L: float,
    U: float,
    interior_result: InteriorResult | None,
    boundary_result: BoundaryResult,
    config: PlotConfig | None = None,
    tp_fn_status: str | None = None,
    tols: np.ndarray | None = None,
) -> Figure:
    """Single-page 4x3 per-parameter overview.

    Layout:
        Row 1: merged raw+sweep+filtered (spans cols 0-1) / interior z-hist
        Row 2: lower boundary mass / upper boundary mass / interior mass
        Row 3: ECDF lower / ECDF upper / quantile spacing
        Row 4: lower boundary elbows / upper boundary elbows / interior elbows

    Rows 2 and 4 mirror each other: left column = lower boundary, middle =
    upper boundary, right = interior. This "lower/upper/interior" column
    discipline lets the viewer scan vertically to compare related
    visualizations for the same side of the distribution.

    The top-left merged panel folds three visualizations (tolerance sweep
    in full color, pipeline-filtered as gray overlay, cut markers as
    vertical lines) with a colorbar. Each mass-curve and elbow panel
    matches the corresponding standalone figure's content so the overview
    is a complete visual verification surface.

    Args:
        param_name: Display name (appears in title).
        x: Parameter value array.
        x0: Optional interior stickiness center.
        L, U: Parameter bounds.
        interior_result: Optional interior QC result. Interior panels show
            placeholder text when None.
        boundary_result: Boundary QC result (required).
        config: PlotConfig for styling. Uses defaults if None.
        tp_fn_status: Optional free-text status appended to the title
            (e.g. "lower: TP | upper: TP"). Driver supplies after cross-
            referencing ground-truth CSV.
        tols: Tolerance grid for the tolerance-sweep panels (combined
            hist overlay, ECDF, spacing). Defaults to a 12-point
            progressive grid that matches the detection code's
            piecewise-linear emphasis on the [0, 0.005] region where
            most pileups live:
            ``[0, 0.0002, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.008,
            0.01, 0.02, 0.03, 0.05]``.

    Returns:
        Figure sized 16x22. Axes count = 11 grid panels (merged top spans
        two cells = 1 axes) + 3 colorbars (merged top, lower mass, upper
        mass) = 14.
    """
    if config is None:
        config = PlotConfig()
    if tols is None:
        # Progressive grid (denser near 0) matching the detection code's
        # "progressive" grid_mode in src/fitqc/boundary.py:_build_tolerance_grid.
        tols = np.array(
            [0.0, 0.0002, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.008, 0.01, 0.02, 0.03, 0.05]
        )

    x_clean = x[np.isfinite(x)]
    n_total = int(len(x_clean))

    keep = np.ones(n_total, dtype=bool)
    if (
        interior_result is not None
        and interior_result.spike_detected
        and interior_result.eps_star is not None
        and x0 is not None
    ):
        z_all = compute_z(x_clean, x0, L, U)
        keep &= ~(z_all < interior_result.eps_star)
    if boundary_result.lower_pileup_detected and boundary_result.t_lo_star is not None:
        u_all = compute_u(x_clean, L, U)
        keep &= ~(u_all < boundary_result.t_lo_star)
    if boundary_result.upper_pileup_detected and boundary_result.t_hi_star is not None:
        u_all = compute_u(x_clean, L, U)
        keep &= ~((1 - u_all) < boundary_result.t_hi_star)
    n_kept = int(keep.sum())
    x_filtered = x_clean[keep]

    cmap = plt.get_cmap(config.cmap)

    fig = plt.figure(figsize=(16, 22), dpi=config.dpi)
    gs = fig.add_gridspec(4, 3, hspace=0.5, wspace=0.35)

    # Row 1: merged top panel spans cols 0-1; interior z-hist in col 2.
    ax_r1c01 = fig.add_subplot(gs[0, 0:2])
    _overview_merged_hist(
        ax_r1c01,
        x_clean,
        x_filtered,
        n_total,
        n_kept,
        x0,
        L,
        U,
        tols,
        boundary_result,
        interior_result,
        config,
    )

    ax_r1c2 = fig.add_subplot(gs[0, 2])
    if interior_result is not None:
        _overview_interior_zhist(ax_r1c2, interior_result)
    else:
        ax_r1c2.axis("off")
        ax_r1c2.text(
            0.5,
            0.5,
            "No interior result",
            ha="center",
            va="center",
            transform=ax_r1c2.transAxes,
            fontsize=11,
        )

    # Row 2: mass curves - lower boundary, upper boundary, interior.
    ax_r2c1 = fig.add_subplot(gs[1, 0])
    _overview_boundary_mass_side(ax_r2c1, boundary_result, "lower", config)

    ax_r2c2 = fig.add_subplot(gs[1, 1])
    _overview_boundary_mass_side(ax_r2c2, boundary_result, "upper", config)

    ax_r2c3 = fig.add_subplot(gs[1, 2])
    if interior_result is not None:
        _overview_interior_mass(ax_r2c3, interior_result)
    else:
        ax_r2c3.axis("off")
        ax_r2c3.text(
            0.5,
            0.5,
            "No interior result",
            ha="center",
            va="center",
            transform=ax_r2c3.transAxes,
            fontsize=11,
        )

    # Row 3: ECDF lower, ECDF upper, quantile spacing.
    ax_r3c1 = fig.add_subplot(gs[2, 0])
    ax_r3c2 = fig.add_subplot(gs[2, 1])
    if U > L:
        u_values = (x_clean - L) / (U - L)
        _overview_ecdf_side(ax_r3c1, u_values, "lower", tols, boundary_result.t_lo_star, cmap)
        _overview_ecdf_side(ax_r3c2, u_values, "upper", tols, boundary_result.t_hi_star, cmap)

    ax_r3c3 = fig.add_subplot(gs[2, 2])
    if n_total > 0:
        x_sorted = np.sort(x_clean)
        _overview_spacing(ax_r3c3, x_sorted, L, U, tols, cmap)
    else:
        ax_r3c3.axis("off")

    # Row 4: elbows - lower boundary, upper boundary, interior.
    ax_r4c1 = fig.add_subplot(gs[3, 0])
    _overview_boundary_elbow_side(ax_r4c1, boundary_result, "lower")

    ax_r4c2 = fig.add_subplot(gs[3, 1])
    _overview_boundary_elbow_side(ax_r4c2, boundary_result, "upper")

    ax_r4c3 = fig.add_subplot(gs[3, 2])
    _overview_interior_elbows_panel(ax_r4c3, interior_result)

    x0_str = f"{x0:.3g}" if x0 is not None else "None"
    title_parts = [f"{param_name}", f"L={L:.3g}", f"U={U:.3g}", f"x0={x0_str}"]
    if tp_fn_status is not None:
        title_parts.append(tp_fn_status)
    fig.suptitle("   ".join(title_parts), fontsize=14, y=0.995)

    footer_parts = [
        f"t_lo*={boundary_result.t_lo_star}",
        f"t_hi*={boundary_result.t_hi_star}",
        f"lower_pileup_detected={boundary_result.lower_pileup_detected}",
        f"upper_pileup_detected={boundary_result.upper_pileup_detected}",
    ]
    if interior_result is not None:
        footer_parts.append(f"eps*={interior_result.eps_star}")
        footer_parts.append(f"spike_detected={interior_result.spike_detected}")
    fig.text(0.5, 0.005, "   ".join(footer_parts), ha="center", va="bottom", fontsize=9)

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    return fig
