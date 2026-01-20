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

from fitqc.boundary import BoundaryResult
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult

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


def plot_quantile_spacing_overlays(
    x_sorted: np.ndarray,
    L: float | None = None,
    U: float | None = None,
    tols: np.ndarray | None = None,
    n_tols: int = 11,
    q_max: float = 0.1,
    n_quantiles: int = 100,
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
    alphas = np.linspace(0.2, 0.7, len(tols))

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
    ax.set_ylabel("Spacing (dq)")
    ax.set_title("Quantile spacing near lower tail")
    ax.grid(True, alpha=0.3)

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
    config: PlotConfig | None = None,
) -> Figure:
    """Plot ECDF near boundaries with tolerance-colored overlays.

    Shows how the empirical CDF changes as samples near boundaries are removed.

    Args:
        u: Normalized positions in [0, 1] where u = (x - L) / (U - L).
        tols: Array of tolerance values. If None, uses linspace(0, 0.05, n_tols).
        n_tols: Number of tolerances if tols is None.
        side: Which boundary to visualize ("lower", "upper", or "both").
        config: PlotConfig for styling.

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
    alphas = np.linspace(0.2, 0.7, len(tols))

    # Plot lower boundary ECDF
    if side in ["lower", "both"]:
        ax_idx = 0
        ax = axes[ax_idx]

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

        # Add reference line for uniform ECDF (y = x)
        ax.plot([0, 0.1], [0, 0.1], "k--", alpha=0.5, linewidth=1, label="Uniform (y=x)")

        ax.set_xlabel("u (normalized position)")
        ax.set_ylabel("ECDF")
        ax.set_title("ECDF near lower boundary")
        ax.set_xlim(0, 0.1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="lower right")

    # Plot upper boundary ECDF
    if side in ["upper", "both"]:
        ax_idx = 1 if side == "both" else 0
        ax = axes[ax_idx]

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

        # Add reference line for uniform ECDF (y = x)
        # For the upper boundary plot, the x range is [0.9, 1.0]
        # The reference line should still be y = x
        ax.plot([0.9, 1.0], [0.9, 1.0], "k--", alpha=0.5, linewidth=1, label="Uniform (y=x)")

        ax.set_xlabel("u (normalized position)")
        ax.set_ylabel("ECDF")
        ax.set_title("ECDF near upper boundary")
        ax.set_xlim(0.9, 1.0)
        ax.grid(True, alpha=0.3)
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
    config: PlotConfig | None = None,
) -> Figure:
    """Plot histogram overlays showing effect of boundary tolerance cuts.

    For each tolerance t, shows histogram of data kept after applying:
    - Lower cut: x > L + t*(U-L)
    - Upper cut: x < U - t*(U-L)

    Histograms are colored by tolerance using a colormap with colorbar.
    Higher tolerances (stricter cuts) have higher zorder (drawn on top).
    Uses varying alpha: low tolerance = faint (alpha=0.2), high tolerance = opaque (alpha=0.7).

    Args:
        x: Array of parameter values.
        L: Lower bound.
        U: Upper bound.
        tols: Array of tolerance values to plot. If None, uses linspace(0, 0.05, n_tols).
        n_tols: Number of tolerances if tols is None.
        bins: Number of histogram bins.
        config: PlotConfig for styling. Uses defaults if None.

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

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=config.figsize_tolerance, dpi=config.dpi)

    # Get colormap and create normalization
    cmap = plt.get_cmap(config.cmap)
    norm = Normalize(vmin=tols[0], vmax=tols[-1])

    # Compute fixed bin edges
    bin_edges = np.linspace(L, U, bins + 1)

    # Compute alphas
    alphas = np.linspace(0.2, 0.7, len(tols))

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
        boundary_name="Lower",
        cmap=cmap,
    )

    # Plot upper boundary
    ax_upper = axes[1]
    _plot_boundary_panel(
        ax=ax_upper,
        elbows=quantile_elbows.get("upper", {}),
        t_star=result.t_hi_star,
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
) -> None:
    """Plot a single boundary panel for quantile elbow visualization."""
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
        ax.set_ylabel("Tolerance (elbow threshold)")
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

    # Plot scatter with colors
    for i, (q, tol) in enumerate(zip(x_vals, y_vals, strict=True)):
        ax.scatter(
            [q],
            [tol],
            c=[colors[i]],
            s=100,
            zorder=2,
            label=f"q={q:.3f}: tol={tol:.4f}",
        )

    # Mark t_star if available
    if t_star is not None:
        ax.axhline(
            t_star,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=f"t* (median) = {t_star:.4f}",
        )

    # Labels and title
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Tolerance (elbow threshold)")
    ax.set_title(f"Quantile Elbow Analysis - {boundary_name} Boundary")
    ax.grid(True, alpha=0.3)

    # Add legend (limit entries)
    if len(sorted_quantiles) <= 8:
        ax.legend(loc="best", fontsize=8)
    else:
        handles, labels = ax.get_legend_handles_labels()
        t_star_idx = [i for i, label in enumerate(labels) if "t*" in label]
        if t_star_idx:
            ax.legend([handles[t_star_idx[0]]], [labels[t_star_idx[0]]], loc="best")


def plot_kneedle_internals(
    x: np.ndarray,
    y: np.ndarray,
    curve: str = "concave",
    direction: str = "increasing",
    log_x: bool = False,
    config: PlotConfig | None = None,
) -> Figure:
    """Visualize Kneedle algorithm internal state for elbow detection.

    Creates a 4-panel figure showing the internal steps of the Kneedle algorithm:
    1. Original curve with detected elbow marked
    2. Normalized curve (both x and y normalized to [0,1])
    3. Difference curve showing curvature (where max indicates elbow)
    4. Summary panel with annotations

    This visualization helps diagnose elbow detection behavior and understand
    why a particular point was chosen (or why no elbow was detected).

    Args:
        x: X-values (must be monotonic).
        y: Y-values corresponding to x.
        curve: Curve shape. Either "concave" or "convex".
        direction: Data direction. Either "increasing" or "decreasing".
        log_x: If True, algorithm works in log10(x) space internally but displays
            in original space with log scale on x-axis.
        config: PlotConfig for styling. If None, uses defaults.

    Returns:
        matplotlib Figure object with 4 panels showing algorithm internals.

    Note:
        Accesses KneeLocator private attributes (_y_normalized, _y_diff) defensively
        using try/except. If these internals are unavailable, shows informative
        message instead of crashing.

    Example:
        >>> import numpy as np
        >>> from fitqc.plot import plot_kneedle_internals
        >>> from fitqc.config import PlotConfig
        >>>
        >>> # Create sample data with elbow
        >>> x = np.linspace(1, 100, 50)
        >>> y = 1 / x + 0.1  # Hyperbolic decay
        >>>
        >>> fig = plot_kneedle_internals(x, y, log_x=True)
        >>> fig.savefig("kneedle_internals.png")
    """
    # Handle config defaults
    if config is None:
        config = PlotConfig()

    # Prepare x-axis (handle log_x)
    if log_x:
        x_work = np.log10(x)
    else:
        x_work = x

    # Run KneeLocator to get elbow and internals
    from kneed import KneeLocator

    kl = KneeLocator(
        x_work,
        y,
        curve=curve,
        direction=direction,
        online=True,
    )

    elbow_x = kl.knee  # This is in x_work space
    if elbow_x is not None and log_x:
        elbow_x = 10**elbow_x  # Convert back to original space

    # Defensively access internals
    try:
        x_normalized = kl.x_normalized
    except AttributeError:
        x_normalized = None

    try:
        y_normalized = kl.y_normalized
    except AttributeError:
        y_normalized = None

    try:
        y_diff = kl.y_difference
    except AttributeError:
        # Try alternative name
        try:
            y_diff = kl.Ds_y
        except AttributeError:
            y_diff = None

    # Create 4-panel figure
    fig, axes = plt.subplots(2, 2, figsize=config.figsize_elbow_internals, dpi=config.dpi)
    axes = axes.flatten()

    cmap = plt.get_cmap(config.cmap)

    # Panel 1: Original curve
    ax1 = axes[0]
    ax1.plot(x, y, "o-", linewidth=2, markersize=4, alpha=0.7, color=cmap(0.3))
    if elbow_x is not None:
        # Find y-value at elbow
        elbow_idx = np.argmin(np.abs(x - elbow_x))
        elbow_y = y[elbow_idx]
        ax1.scatter(
            [elbow_x],
            [elbow_y],
            s=200,
            c="red",
            zorder=5,
            marker="*",
            edgecolors="black",
            linewidths=1.5,
        )
        ax1.axvline(elbow_x, color="red", linestyle="--", alpha=0.5, linewidth=2)
        ax1.legend([f"Elbow at x={elbow_x:.4g}"], loc="best")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("Original Curve")
    ax1.grid(True, alpha=0.3)

    # Panel 2: Normalized curve
    ax2 = axes[1]
    if y_normalized is not None and x_normalized is not None:
        ax2.plot(
            x_normalized, y_normalized, "o-", linewidth=2, markersize=4, alpha=0.7, color=cmap(0.5)
        )
        if elbow_x is not None:
            # Find elbow in normalized coordinates
            elbow_idx = np.argmin(np.abs(x - elbow_x))
            elbow_x_norm = x_normalized[elbow_idx]
            ax2.scatter(
                [elbow_x_norm],
                [y_normalized[elbow_idx]],
                s=200,
                c="red",
                zorder=5,
                marker="*",
                edgecolors="black",
                linewidths=1.5,
            )
        ax2.set_title("Normalized Curve")
    else:
        ax2.text(
            0.5,
            0.5,
            "Normalized data unavailable\n(KneeLocator internals)",
            ha="center",
            va="center",
            transform=ax2.transAxes,
            fontsize=10,
        )
        ax2.set_title("Normalized Curve (N/A)")
    ax2.set_xlabel("Normalized x")
    ax2.set_ylabel("Normalized y")
    ax2.grid(True, alpha=0.3)

    # Panel 3: Difference curve
    ax3 = axes[2]
    if y_diff is not None:
        # Use original x values for consistency with Panel 1
        # y_diff should have same length as x
        x_diff = x[: len(y_diff)]
        ax3.plot(x_diff, y_diff, "o-", linewidth=2, markersize=4, alpha=0.7, color=cmap(0.7))
        # Mark maximum (this indicates the elbow)
        max_idx = np.argmax(y_diff)
        ax3.scatter(
            [x_diff[max_idx]],
            [y_diff[max_idx]],
            s=200,
            c="green",
            zorder=5,
            marker="^",
            edgecolors="black",
            linewidths=1.5,
        )
        ax3.axvline(x_diff[max_idx], color="green", linestyle="--", alpha=0.5)
        ax3.set_title("Difference Curve (Curvature)")
    else:
        ax3.text(
            0.5,
            0.5,
            "Difference curve unavailable\n(KneeLocator internals)",
            ha="center",
            va="center",
            transform=ax3.transAxes,
            fontsize=10,
        )
        ax3.set_title("Difference Curve (N/A)")
    ax3.set_xlabel("x")
    ax3.set_ylabel("Difference")
    ax3.grid(True, alpha=0.3)

    # Panel 4: Summary with annotation
    ax4 = axes[3]
    ax4.plot(x, y, "o-", linewidth=2, markersize=4, alpha=0.7, color=cmap(0.3))
    if elbow_x is not None:
        elbow_idx = np.argmin(np.abs(x - elbow_x))
        elbow_y = y[elbow_idx]
        ax4.scatter(
            [elbow_x],
            [elbow_y],
            s=200,
            c="red",
            zorder=5,
            marker="*",
            edgecolors="black",
            linewidths=1.5,
        )
        ax4.axvline(elbow_x, color="red", linestyle="--", alpha=0.5, linewidth=2)
        # Add text annotation
        ax4.annotate(
            f"Elbow\n({elbow_x:.4g}, {elbow_y:.4g})",
            xy=(elbow_x, elbow_y),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.7),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )
        ax4.set_title("Elbow Detection Summary")
    else:
        ax4.text(
            0.5,
            0.5,
            "No elbow detected\n(linear or insufficient curvature)",
            ha="center",
            va="center",
            transform=ax4.transAxes,
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        ax4.set_title("Elbow Detection Summary - No Elbow")
    ax4.set_xlabel("x")
    ax4.set_ylabel("y")
    ax4.grid(True, alpha=0.3)

    # Apply log scale if requested
    if log_x:
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_xscale("log")

    fig.tight_layout()
    return fig


def plot_quantile_elbows_detailed(
    result: InteriorResult | BoundaryResult,
    config: PlotConfig | None = None,
) -> Figure:
    """Visualize quantile elbow points before aggregation.

    Creates scatter plots showing the relationship between quantile values and their
    corresponding detected elbow thresholds. This visualization helps diagnose the
    multi-curve threshold estimation used in quantile-based stickiness detection.

    For InteriorResult:
        - Single panel with quantile (x-axis) vs epsilon threshold (y-axis, log scale)
        - Scatter points colored by quantile value using colormap gradient
        - Horizontal reference line at eps_star (aggregated median threshold)
        - Filters out None values (quantiles where no elbow was detected)

    For BoundaryResult:
        - Two panels (lower and upper boundaries)
        - Each panel: quantile (x-axis) vs tolerance threshold (y-axis, linear scale)
        - Separate scatter plots for lower_elbows and upper_elbows
        - Horizontal reference lines at t_lo_star and t_hi_star

    Args:
        result: InteriorResult or BoundaryResult with quantile_elbows populated.
        config: PlotConfig for styling. If None, uses defaults.

    Returns:
        matplotlib Figure object. Caller is responsible for displaying or saving.

    Note:
        If result.quantile_elbows is None or empty, returns a figure with an
        informative message explaining that quantile analysis is not available.

    Example:
        >>> from fitqc import run_interior_qc, InteriorConfig, PlotConfig
        >>> from fitqc.plot import plot_quantile_elbows_detailed
        >>>
        >>> config = InteriorConfig(use_quantile_analysis=True)
        >>> result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)
        >>> fig = plot_quantile_elbows_detailed(result, PlotConfig())
        >>> fig.savefig("quantile_elbows_detailed.png")
    """
    # Handle config
    if config is None:
        config = PlotConfig()

    # Determine result type
    is_interior = isinstance(result, InteriorResult)

    # Handle None or empty quantile_elbows
    if result.quantile_elbows is None or (
        isinstance(result.quantile_elbows, dict) and len(result.quantile_elbows) == 0
    ):
        # Create empty figure with message
        fig, ax = plt.subplots(figsize=config.figsize_tolerance, dpi=config.dpi)
        ax.text(
            0.5,
            0.5,
            "No quantile analysis data available\n\n"
            "Enable quantile analysis in config:\n"
            f"config = {'InteriorConfig' if is_interior else 'BoundaryConfig'}(use_quantile_analysis=True)",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        ax.set_title("Quantile Elbow Analysis - No Data")
        ax.axis("off")
        return fig

    # Branch based on result type
    if is_interior:
        return _plot_interior_quantile_elbows_detailed(result, config)
    else:
        return _plot_boundary_quantile_elbows_detailed(result, config)


def _plot_interior_quantile_elbows_detailed(result: InteriorResult, config: PlotConfig) -> Figure:
    """Plot quantile elbows for InteriorResult (detailed view)."""
    fig, ax = plt.subplots(figsize=config.figsize_tolerance, dpi=config.dpi)
    cmap = plt.get_cmap(config.cmap)

    # Filter valid elbows (non-None)
    quantile_elbows = result.quantile_elbows
    valid_data = {q: eps for q, eps in quantile_elbows.items() if eps is not None}

    if len(valid_data) == 0:
        # All None - show message
        ax.text(
            0.5,
            0.5,
            "All quantile elbows are None\n(no elbows detected for any quantile)",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        ax.set_title("Interior Quantile Elbows - All None")
        ax.axis("off")
        return fig

    # Extract x, y for scatter
    quantiles = list(valid_data.keys())
    epsilons = list(valid_data.values())

    # Sort by quantile for consistent ordering
    sorted_indices = np.argsort(quantiles)
    quantiles = np.array(quantiles)[sorted_indices]
    epsilons = np.array(epsilons)[sorted_indices]

    # Colormap colors
    norm = Normalize(vmin=quantiles.min(), vmax=quantiles.max())
    colors = [cmap(norm(q)) for q in quantiles]

    # Scatter plot - single scatter call with all points for proper collection handling
    ax.scatter(
        quantiles,
        epsilons,
        c=colors,
        s=100,
        zorder=3,
        edgecolors="black",
        linewidths=0.5,
    )

    # Add individual labels (for legend, if needed)
    for q, eps in zip(quantiles, epsilons, strict=True):
        # Only add to legend if few enough points
        if len(quantiles) <= 8:
            ax.plot([], [], "o", color=cmap(norm(q)), label=f"q={q:.3f}: eps={eps:.2e}")

    # Reference line at eps_star (median aggregation)
    if result.eps_star is not None:
        ax.axhline(
            result.eps_star,
            color="red",
            linestyle="--",
            linewidth=2,
            alpha=0.7,
            label=f"eps* (median) = {result.eps_star:.2e}",
        )

    # Labels and formatting
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Epsilon (elbow threshold)")
    ax.set_yscale("log")  # Epsilon spans orders of magnitude
    ax.set_title("Interior Quantile Elbow Analysis")
    ax.grid(True, alpha=0.3)

    # Legend (limit if many points)
    if len(quantiles) <= 8:
        ax.legend(loc="best", fontsize=8)
    else:
        # Just show eps_star line
        handles, labels = ax.get_legend_handles_labels()
        eps_star_idx = [i for i, label in enumerate(labels) if "eps*" in label]
        if eps_star_idx:
            ax.legend([handles[eps_star_idx[0]]], [labels[eps_star_idx[0]]], loc="best")

    fig.tight_layout()
    return fig


def _plot_boundary_quantile_elbows_detailed(result: BoundaryResult, config: PlotConfig) -> Figure:
    """Plot quantile elbows for BoundaryResult (2 panels)."""
    fig, axes = plt.subplots(1, 2, figsize=config.figsize_tolerance, dpi=config.dpi)
    cmap = plt.get_cmap(config.cmap)

    quantile_elbows = result.quantile_elbows

    # Process lower boundary
    if "lower" in quantile_elbows:
        ax_lower = axes[0]
        lower_elbows = quantile_elbows["lower"]
        valid_lower = {q: tol for q, tol in lower_elbows.items() if tol is not None}

        if len(valid_lower) > 0:
            quantiles_l = np.array(sorted(valid_lower.keys()))
            tolerances_l = np.array([valid_lower[q] for q in quantiles_l])

            norm = Normalize(vmin=quantiles_l.min(), vmax=quantiles_l.max())
            colors = [cmap(norm(q)) for q in quantiles_l]

            # Single scatter call with all points
            ax_lower.scatter(
                quantiles_l,
                tolerances_l,
                c=colors,
                s=100,
                zorder=3,
                edgecolors="black",
                linewidths=0.5,
            )

            if result.t_lo_star is not None:
                ax_lower.axhline(
                    result.t_lo_star,
                    color="red",
                    linestyle="--",
                    linewidth=2,
                    alpha=0.7,
                    label=f"t_lo* = {result.t_lo_star:.4f}",
                )
                ax_lower.legend(loc="best")

        ax_lower.set_xlabel("Quantile")
        ax_lower.set_ylabel("Tolerance (elbow threshold)")
        ax_lower.set_title("Lower Boundary Quantile Elbows")
        ax_lower.grid(True, alpha=0.3)

    # Process upper boundary
    if "upper" in quantile_elbows:
        ax_upper = axes[1]
        upper_elbows = quantile_elbows["upper"]
        valid_upper = {q: tol for q, tol in upper_elbows.items() if tol is not None}

        if len(valid_upper) > 0:
            quantiles_u = np.array(sorted(valid_upper.keys()))
            tolerances_u = np.array([valid_upper[q] for q in quantiles_u])

            norm = Normalize(vmin=quantiles_u.min(), vmax=quantiles_u.max())
            colors = [cmap(norm(q)) for q in quantiles_u]

            # Single scatter call with all points
            ax_upper.scatter(
                quantiles_u,
                tolerances_u,
                c=colors,
                s=100,
                zorder=3,
                edgecolors="black",
                linewidths=0.5,
            )

            if result.t_hi_star is not None:
                ax_upper.axhline(
                    result.t_hi_star,
                    color="red",
                    linestyle="--",
                    linewidth=2,
                    alpha=0.7,
                    label=f"t_hi* = {result.t_hi_star:.4f}",
                )
                ax_upper.legend(loc="best")

        ax_upper.set_xlabel("Quantile")
        ax_upper.set_ylabel("Tolerance (elbow threshold)")
        ax_upper.set_title("Upper Boundary Quantile Elbows")
        ax_upper.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig
