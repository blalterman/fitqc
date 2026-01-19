"""Stickiness detection: detect optimizer stickiness at reference points.

This module consolidates interior (x0) and boundary (L/U) stickiness detection.
Both algorithms detect when optimization results are "stuck" at a reference point
by looking for anomalous mass concentration near the reference.

Why This Module Exists
----------------------
Optimizers can get stuck in three ways:
1. **At x0 (initial guess)**: Optimizer fails to move from starting point
2. **At L (lower bound)**: Optimizer hits lower constraint
3. **At U (upper bound)**: Optimizer hits upper constraint

All three are detected using the same conceptual approach:
- Transform to normalized distance from reference point
- Look for excess mass near z=0 (the reference point)

The implementations differ in details:
- Interior (x0): Uses histogram + spike detection with prominence/width criteria
- Boundary (L/U): Uses mass curve + excess ratio check

Core Algorithm Pattern
----------------------
1. Transform x -> z (normalized distance from reference)
   - Interior: z = |x - x0| / max(x0 - L, U - x0)
   - Boundary: u = (x - L) / (U - L), then check u < tol or (1-u) < tol

2. Build mass curve: P(z < eps) for various eps values

3. Detect stickiness:
   - Interior: Find histogram spike near z=0 using scipy.signal.find_peaks
   - Boundary: Find elbow in mass curve, check for excess mass

4. Return threshold (eps* or t*) that separates "stuck" from "normal" samples

IMPORTANT: Two Different Uses of "Log" (Don't Confuse Them!)
------------------------------------------------------------
1. **Log-spaced epsilon SEARCH grid** (interior): We search for the stickiness
   threshold across many orders of magnitude (10^-12 to 10^-3). Using np.logspace
   ensures we sample each decade evenly.

2. **Linear tolerance grid** (boundary): We search tolerances from 0 to 0.05
   (5% of range) linearly, since boundary pileup typically occurs at larger scales.

The choice of grid spacing is algorithm-specific, not a fundamental difference.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks, peak_widths

from fitqc.config import BoundaryConfig, InteriorConfig
from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass

# =============================================================================
# Interior (x0 stickiness) Detection
# =============================================================================


def compute_z(x: NDArray[np.floating], x0: float, L: float, U: float) -> NDArray[np.floating]:
    """Compute normalized distance from the initial guess x0.

    Formula: z = |x - x0| / max(x0 - L, U - x0)

    This gives:
        z = 0 when x equals x0 (sample is at the initial guess)
        z = 1 when x is at the furthest bound from x0

    Why max() in the denominator (unlike compute_u)?
    ------------------------------------------------
    The initial guess x0 can be ANYWHERE in the range [L, U], not just the center.
    We need z to always be in [0, 1] so our spike detection thresholds work
    consistently regardless of where x0 is placed.

    Example: Parameter range [0, 10] with x0 = 1 (near the lower bound)
        - Distance from x0 to L: 1 - 0 = 1
        - Distance from x0 to U: 10 - 1 = 9
        - max() = 9 (the furthest you can get from x0)

        Without max(), using (U - L) = 10:
            At x = 10: z = |10 - 1| / 10 = 0.9  (seems OK)
            At x = 0:  z = |0 - 1| / 10 = 0.1   (WRONG! This is at a bound!)

        With max() = 9:
            At x = 10: z = |10 - 1| / 9 = 1.0   (correct: at furthest bound)
            At x = 0:  z = |0 - 1| / 9 = 0.11   (correct: close to x0)

    Compare to compute_u (boundary detection), which measures position in range:
    - u uses (U - L) because we're mapping the fixed range [L, U] to [0, 1]
    - There's no off-center reference point, just a linear rescaling

    Args:
        x: Array of fitted parameter values from your optimization runs.
        x0: The initial guess you provided to the optimizer.
        L: Lower bound of the parameter (the constraint minimum).
        U: Upper bound of the parameter (the constraint maximum).

    Returns:
        Array of z-values in [0, 1]. z=0 means "at x0", z=1 means "at furthest bound".
    """
    # The furthest any sample can be from x0 is to whichever bound is farther away
    max_dist = max(x0 - L, U - x0)

    # Compute normalized distance: 0 at x0, 1 at furthest bound
    z = np.abs(x - x0) / max_dist

    return z


@dataclass
class InteriorResult:
    """Result of interior QC analysis.

    Attributes:
        spike_detected: Whether a spike at x0 was detected.
        spike_z_loc: Z-location of the spike (if detected), i.e., the normalized
            distance from x0 where the spike occurs. Should be near 0 for true stickiness.
        eps_star: Optimal epsilon threshold from elbow detection (if detected).
            This represents the "radius" around x0 where stuck samples cluster.
        eps_grid: Array of epsilon values tested in the mass curve analysis.
        mass_curve: P(z < eps) for each eps in eps_grid. Shows cumulative
            fraction of samples within each epsilon of x0.
        hist_counts: Histogram counts of z-values.
        hist_edges: Histogram bin edges for z-values.
    """

    spike_detected: bool
    spike_z_loc: float | None
    eps_star: float | None
    eps_grid: NDArray[np.floating]
    mass_curve: NDArray[np.floating]
    hist_counts: NDArray[np.floating]
    hist_edges: NDArray[np.floating]


def run_interior_qc(
    x: NDArray[np.floating],
    x0: float,
    L: float,
    U: float,
    config: InteriorConfig | None = None,
) -> InteriorResult:
    """Run interior QC analysis to detect x0 stickiness.

    This function detects whether optimization results are stuck at the initial
    guess x0 by looking for a narrow spike in the z-distribution (distance from x0).

    Args:
        x: Array of fitted parameter values.
        x0: Initial guess value.
        L: Lower bound of the parameter range.
        U: Upper bound of the parameter range.
        config: Configuration for the analysis. If None, uses default InteriorConfig.

    Returns:
        InteriorResult containing detection results and diagnostic data.
    """
    if config is None:
        config = InteriorConfig()

    # Step 1: Transform to z-space
    z = compute_z(x, x0, L, U)

    # Step 2: Build epsilon grid and compute mass curve P(z < eps)
    eps_grid = np.logspace(config.eps_log10_min, config.eps_log10_max, config.n_eps)

    # Sort z for efficient tail_mass computation
    z_sorted = np.sort(z)

    # Compute mass curve: P(z < eps) for each eps
    mass_curve = np.array([tail_mass(z_sorted, eps) for eps in eps_grid])

    # Step 3: Build histogram of z-values
    # Clip z to [0, 1] range for histogram (values outside are edge cases)
    z_clipped = np.clip(z, 0, 1)
    hist_counts, hist_edges = np.histogram(z_clipped, bins=config.n_bins, range=(0, 1))

    # Convert to float for consistency
    hist_counts = hist_counts.astype(np.float64)

    # Early check: A true spike at z=0 requires significant mass at tiny epsilon.
    # If mass_curve[0] is essentially zero, there's no spike, just noise.
    # This is critical for avoiding false positives on uniform data.
    min_mass_for_spike = 0.001  # At least 0.1% of samples must be at tiny epsilon
    if mass_curve[0] < min_mass_for_spike:
        return InteriorResult(
            spike_detected=False,
            spike_z_loc=None,
            eps_star=None,
            eps_grid=eps_grid,
            mass_curve=mass_curve,
            hist_counts=hist_counts,
            hist_edges=hist_edges,
        )

    # Step 4: Use find_peaks to detect spikes in the histogram
    # Pad histogram with zeros so find_peaks can detect peaks at boundaries (index 0)
    # scipy.signal.find_peaks doesn't detect peaks at array edges by default
    hist_padded = np.concatenate([[0], hist_counts, [0]])
    peaks, _peak_properties = find_peaks(
        hist_padded,
        prominence=config.spike_prominence_min,
    )
    # Convert peak indices from padded array back to original histogram indices.
    # The padding added one element at the start, so padded_index = original_index + 1.
    # Therefore: original_index = padded_index - 1.
    peaks = peaks - 1

    # After subtracting 1, peaks that were at padded index 0 become -1 (invalid).
    # This shouldn't happen since we padded with zeros (no peak there), but we
    # filter defensively to avoid index errors.
    peaks = peaks[(peaks >= 0) & (peaks < len(hist_counts))]

    # Step 5: Check spike criteria
    spike_detected = False
    spike_z_loc = None

    if len(peaks) > 0:
        # Get peak widths on padded histogram, then filter
        hist_padded_peaks = peaks + 1  # Convert back to padded indices for width calc
        widths, _, _, _ = peak_widths(hist_padded, hist_padded_peaks, rel_height=0.5)

        # Check each peak against criteria
        for i, peak_idx in enumerate(peaks):
            # Get z-location of this peak (center of the bin)
            bin_width = hist_edges[1] - hist_edges[0]
            peak_z = hist_edges[peak_idx] + bin_width / 2

            # Check if peak meets all criteria:
            # 1. Near z=0 (location criterion)
            # 2. Narrow (width criterion) - CRITICAL for avoiding false positives
            # 3. Has sufficient prominence (already filtered by find_peaks)
            if peak_z <= config.spike_location_max and widths[i] <= config.spike_width_max:
                spike_detected = True
                spike_z_loc = peak_z
                break  # Found a valid spike, no need to check more

    # Step 6: Use elbow detection on the mass curve to find eps*
    eps_star = None
    if spike_detected:
        eps_star = select_elbow(
            eps_grid,
            mass_curve,
            curve="concave",
            direction="increasing",
            log_x=True,
        )

    return InteriorResult(
        spike_detected=spike_detected,
        spike_z_loc=spike_z_loc,
        eps_star=eps_star,
        eps_grid=eps_grid,
        mass_curve=mass_curve,
        hist_counts=hist_counts,
        hist_edges=hist_edges,
    )


# =============================================================================
# Boundary (L/U stickiness) Detection
# =============================================================================


def compute_u(x: np.ndarray, L: float, U: float) -> np.ndarray:
    """Compute normalized position in the parameter range [L, U].

    Formula: u = (x - L) / (U - L)

    This gives:
        u = 0   when x is at the lower bound L
        u = 1   when x is at the upper bound U
        u = 0.5 when x is at the midpoint

    Why no max() in the denominator (unlike compute_z)?
    ---------------------------------------------------
    Here we measure WHERE a value sits in the range, not how far it is from
    some reference point. The range [L, U] is fixed and symmetric—every value
    maps linearly to [0, 1]. There's no "reference point" that could be off-center.

    Compare to compute_z (interior detection), which measures distance from x0:
    - z uses max(x0 - L, U - x0) because x0 might be near one bound
    - If x0 = 1 with L = 0, U = 10: max distance is 9 (to U), not 1 (to L)
    - Without max(), z would exceed 1 for some values

    Here, u always stays in [0, 1] for values in [L, U] because we're just
    rescaling the range, not measuring distance from an off-center point.

    Args:
        x: Array of fitted parameter values from your optimization runs.
        L: Lower bound of the parameter (the constraint minimum).
        U: Upper bound of the parameter (the constraint maximum).

    Returns:
        Array of normalized positions. Values in [L, U] map to [0, 1].
        Values outside bounds will be outside [0, 1] (rare in practice).
    """
    return (x - L) / (U - L)


@dataclass
class BoundaryResult:
    """Result of boundary QC analysis.

    Attributes:
        lower_pileup_detected: Whether excess mass was detected near lower bound.
        upper_pileup_detected: Whether excess mass was detected near upper bound.
        t_lo_star: Optimal lower tolerance (elbow point), or None if no elbow.
        t_hi_star: Optimal upper tolerance (elbow point), or None if no elbow.
        tol_grid: Array of tolerance values tested.
        lower_mass_curve: P(u < tol) for each tolerance.
        upper_mass_curve: P(u > 1-tol) for each tolerance.
    """

    lower_pileup_detected: bool
    upper_pileup_detected: bool
    t_lo_star: float | None
    t_hi_star: float | None
    tol_grid: np.ndarray
    lower_mass_curve: np.ndarray
    upper_mass_curve: np.ndarray


def run_boundary_qc(
    x: np.ndarray,
    L: float,
    U: float,
    config: BoundaryConfig | None = None,
) -> BoundaryResult:
    """Run boundary QC analysis.

    Detects pileup at lower and upper parameter bounds by computing the
    fraction of samples within increasing tolerances of each boundary,
    then using elbow detection to find where the "stuck" region ends.

    Args:
        x: Array of parameter values to analyze.
        L: Lower bound of the parameter.
        U: Upper bound of the parameter.
        config: Configuration for boundary analysis. Uses defaults if None.

    Returns:
        BoundaryResult with detection flags, optimal tolerances, and mass curves.
    """
    if config is None:
        config = BoundaryConfig()

    # Transform to normalized coordinates
    u = compute_u(x, L, U)

    # Build tolerance grid
    tol_grid = np.linspace(config.tol_min, config.tol_max, config.n_tols)

    # Sort u for efficient tail_mass computation
    u_sorted = np.sort(u)

    # Compute lower mass curve: P(u < tol) for each tol
    lower_mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

    # For upper boundary: P(u > 1-tol) = P(1-u < tol)
    # We need to compute this by working with 1-u
    one_minus_u_sorted = np.sort(1 - u)
    upper_mass_curve = np.array([tail_mass(one_minus_u_sorted, tol) for tol in tol_grid])

    # Use elbow detection to find optimal tolerances
    # The mass curve is concave and increasing when there's pileup
    # Skip tol=0 for elbow detection (avoid singularities)
    if tol_grid[0] == 0.0 and len(tol_grid) > 1:
        elbow_tols = tol_grid[1:]
        elbow_lower_mass = lower_mass_curve[1:]
        elbow_upper_mass = upper_mass_curve[1:]
    else:
        elbow_tols = tol_grid
        elbow_lower_mass = lower_mass_curve
        elbow_upper_mass = upper_mass_curve

    t_lo_raw = select_elbow(elbow_tols, elbow_lower_mass, curve="concave", direction="increasing")
    t_hi_raw = select_elbow(elbow_tols, elbow_upper_mass, curve="concave", direction="increasing")

    # Detect pileup based on whether elbow shows excess mass
    # For uniform data, we expect P(u < tol) ≈ tol
    # Pileup means observed mass >> expected mass at the elbow
    # We use a ratio threshold: mass / tol > excess_ratio indicates pileup
    pileup_threshold = 0.005  # minimum tolerance to consider
    excess_ratio = 1.5  # mass must be at least 1.5x expected

    def check_excess_mass(
        t_star: float | None, mass_curve: np.ndarray
    ) -> tuple[bool, float | None]:
        """Check if there's excess mass at the elbow tolerance.

        Returns:
            Tuple of (has_pileup, validated_tolerance).
            If no excess mass, tolerance is set to None.
        """
        if t_star is None or t_star < pileup_threshold:
            return False, None
        # Find the mass at t_star by interpolation
        idx = np.searchsorted(tol_grid, t_star)
        if idx >= len(mass_curve):
            idx = len(mass_curve) - 1
        mass_at_elbow = mass_curve[idx]
        # For uniform data, expected mass = t_star
        # Pileup if observed >> expected
        has_pileup = mass_at_elbow > t_star * excess_ratio
        # Only return tolerance if there's genuine pileup
        return has_pileup, float(t_star) if has_pileup else None

    lower_pileup_detected, t_lo_star = check_excess_mass(t_lo_raw, lower_mass_curve)
    upper_pileup_detected, t_hi_star = check_excess_mass(t_hi_raw, upper_mass_curve)

    return BoundaryResult(
        lower_pileup_detected=bool(lower_pileup_detected),
        upper_pileup_detected=bool(upper_pileup_detected),
        t_lo_star=t_lo_star,
        t_hi_star=t_hi_star,
        tol_grid=tol_grid,
        lower_mass_curve=lower_mass_curve,
        upper_mass_curve=upper_mass_curve,
    )
