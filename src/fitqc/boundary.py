"""Boundary stickiness detection via proximity to parameter bounds.

This module detects whether fitted parameters are "stuck" at their bounds
(L or U). When an optimizer hits a bound constraint, samples pile up at the
boundary, creating detectable excess mass in the distribution.

The Algorithm
-------------
**Single-Curve Mode (default):**

1. Transform x -> u = (x - L) / (U - L), so u=0 at L, u=1 at U
2. For lower boundary: compute P(u < tol) for each tol in linspace(tol_min, tol_max, n_tols)
3. For upper boundary: compute P(u > 1-tol) = P(1-u < tol) similarly
4. Use elbow detection on the mass curves to find t_lo*, t_hi*
5. Pileup is detected if the elbow tolerance exceeds a threshold

The mass curve P(u < tol) vs tol shows:
- For uniform data: linear growth (P ~ tol)
- For boundary pileup: sharp initial rise then slower growth (elbow indicates pileup region)

**Multi-Curve Mode (use_quantile_analysis=True):**

For more robust threshold estimation, especially for tight pileups:

1. Compute the same u-transformation
2. For each quantile q in quantile_grid, find the tolerance tol where P(u < tol) = q
3. Detect elbows in the (quantile, tolerance) relationship for each quantile
4. Aggregate across quantiles using median to get final t_lo*, t_hi*

This multi-curve approach provides:
- Better accuracy for very tight pileups (< 0.5% of range)
- Robustness via median aggregation across quantiles
- Diagnostic information via quantile_elbows field in results

Grid Modes
----------
**uniform**: Standard linear spacing from tol_min to tol_max
**progressive**: Denser spacing near boundaries (0-1%), coarser farther out

Progressive mode is recommended for detecting very tight pileups where most
concentration occurs within 1% of the boundary.

Why Elbow Detection?
--------------------
The elbow point indicates where "stuck" samples end and "natural" samples begin.
If no elbow is found, there's no boundary pileup - the distribution is uniform
near the boundary.

Examples
--------
Single-curve detection (default behavior):

>>> from fitqc.boundary import run_boundary_qc
>>> from fitqc.config import BoundaryConfig
>>> import numpy as np
>>>
>>> # Generate data with lower boundary pileup
>>> x = np.concatenate([
...     np.random.uniform(0.0, 0.01, 500),   # 500 stuck at lower bound
...     np.random.uniform(0.0, 1.0, 9500)     # 9500 uniform
... ])
>>>
>>> result = run_boundary_qc(x, L=0.0, U=1.0)
>>> print(f"Lower pileup detected: {result.lower_pileup_detected}")
>>> print(f"Threshold t_lo*: {result.t_lo_star}")

Multi-curve detection with progressive grid:

>>> config = BoundaryConfig(
...     grid_mode="progressive",
...     use_quantile_analysis=True,
...     quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05)
... )
>>> result = run_boundary_qc(x, L=0.0, U=1.0, config=config)
>>> print(f"Lower pileup detected: {result.lower_pileup_detected}")
>>> print(f"Threshold t_lo*: {result.t_lo_star}")
>>> if result.quantile_elbows:
...     print(f"Quantile elbows: {result.quantile_elbows['lower']}")
"""

import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fitqc._quantile_utils import _aggregate_elbows_median
from fitqc.config import BoundaryConfig
from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass

logger = logging.getLogger(__name__)


def _build_tolerance_grid(config: BoundaryConfig) -> NDArray[np.floating]:
    """Build tolerance grid for boundary detection.

    Supports both uniform and progressive grid modes. Progressive mode concentrates
    resolution near the boundary (where tight pileups occur) and uses coarser
    spacing farther out.

    Args:
        config: BoundaryConfig specifying grid mode and parameters.

    Returns:
        Array of tolerance values in [tol_min, tol_max].

    Examples:
        >>> # Uniform grid (default)
        >>> config = BoundaryConfig(tol_min=0.0, tol_max=0.05, n_tols=41, grid_mode="uniform")
        >>> grid = _build_tolerance_grid(config)
        >>> len(grid)
        41
        >>> grid[0], grid[-1]
        (0.0, 0.05)

        >>> # Progressive grid (denser near 0)
        >>> config = BoundaryConfig(grid_mode="progressive")
        >>> grid = _build_tolerance_grid(config)
        >>> spacing_near_zero = grid[1] - grid[0]
        >>> spacing_far = grid[-1] - grid[-2]
        >>> spacing_far > spacing_near_zero  # Coarser farther out
        True
    """
    if config.grid_mode == "uniform":
        return np.linspace(config.tol_min, config.tol_max, config.n_tols)
    elif config.grid_mode == "progressive":
        # Progressive grid: denser near 0, coarser farther out
        # Breakpoints based on empirical pileup distributions
        # Most stickiness is in [0, 0.001] (0-0.1% of range)
        # Some stickiness extends to [0.001, 0.005] (0.1-0.5%)
        # Broad pileups can reach [0.005, 0.02] (0.5-2%)
        # Beyond 0.02 (2%) is rarely stickiness
        return np.concatenate(
            [
                np.linspace(0.0000, 0.0010, 11),  # [0, 0.1%]:   11 points, 0.01% spacing
                np.linspace(0.0010, 0.0050, 17)[1:],  # [0.1%, 0.5%]: 16 points, 0.025% spacing
                np.linspace(0.0050, 0.0200, 13)[1:],  # [0.5%, 2%]:   12 points, 0.125% spacing
                np.linspace(0.0200, 0.0500, 7)[1:],  # [2%, 5%]:      6 points, 0.75% spacing
            ]
        )
    else:
        raise ValueError(
            f"Unknown grid_mode: {config.grid_mode}. Must be 'uniform' or 'progressive'."
        )


def _compute_quantile_curves_boundary(
    u_sorted: NDArray[np.floating],
    tol_grid: NDArray[np.floating],
    quantile_grid: NDArray[np.floating],
) -> tuple[NDArray[np.floating], list[float | None]]:
    """Compute quantile-based threshold curves for boundary detection.

    For each quantile q, finds the tolerance where P(u < tol) = q via inverse CDF.
    Then detects elbow in the (quantile, tolerance) relationship, which shows where
    pileup transitions to natural variation.

    Args:
        u_sorted: Sorted array of normalized parameter values in [0, 1].
        tol_grid: Array of tolerance values to evaluate.
        quantile_grid: Array of quantiles in (0, 1) to analyze.

    Returns:
        Tuple of:
            - tol_at_quantile: Array of tolerance values achieving each quantile.
              Shape matches quantile_grid. tol_at_quantile[i] is the tolerance
              where P(u < tol) = quantile_grid[i].
            - elbows_per_quantile: List of elbow points detected, one per quantile.
              Currently returns [elbow_overall] where elbow_overall is detected
              in the (quantile, tolerance) space.

    Examples:
        >>> # Uniform data: tol should be proportional to quantile
        >>> u = np.sort(np.random.uniform(0, 1, 1000))
        >>> tol_grid = np.linspace(0, 0.15, 151)
        >>> quantile_grid = np.array([0.01, 0.05, 0.10])
        >>> tol_at_q, elbows = _compute_quantile_curves_boundary(u, tol_grid, quantile_grid)
        >>> # For uniform data, ratio tol/q should be ~1
        >>> ratio = tol_at_q / quantile_grid
        >>> np.allclose(ratio, 1.0, atol=0.1)
        True

        >>> # Data with pileup: elbow appears at pileup fraction
        >>> u_pileup = np.concatenate([np.zeros(50), np.random.uniform(0, 1, 950)])
        >>> u_pileup = np.sort(u_pileup)
        >>> tol_at_q, elbows = _compute_quantile_curves_boundary(u_pileup, tol_grid, quantile_grid)
        >>> # Should detect elbow (not None)
        >>> elbows[0] is not None
        True
    """
    # Compute mass curve: P(u < tol) for each tolerance
    mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

    # For each quantile, find tolerance where mass = quantile (inverse CDF)
    # Use linear interpolation
    tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)

    # Detect elbow in (quantile, tolerance) relationship
    # For uniform data: tolerance ≈ quantile (linear)
    # For pileup data: tolerance ≈ 0 initially (delta function at boundary),
    #                  then tolerance starts rising (back to uniform)
    # The curve transitions from flat (t≈0) to rising, which is convex
    elbow_quantile = select_elbow(
        quantile_grid, tol_at_quantile, curve="convex", direction="increasing"
    )

    # Convert elbow from quantile-space to tolerance-space
    if elbow_quantile is not None:
        # Look up the tolerance value at the detected elbow quantile
        elbow_tol = np.interp(elbow_quantile, quantile_grid, tol_at_quantile)
    else:
        elbow_tol = None

    # Return list with single elbow (will be aggregated across lower/upper boundaries)
    elbows_per_quantile = [elbow_tol]

    return tol_at_quantile, elbows_per_quantile


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

    Compare to compute_z (interior.py), which measures distance from x0:
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


def _refine_quantile_grid_around_elbow(
    quantile_grid: np.ndarray, elbow_quantile: float, n_points: int = 15
) -> np.ndarray:
    """Add intermediate points around an elbow for better resolution.

    Args:
        quantile_grid: Current quantile grid.
        elbow_quantile: The quantile value where the elbow was detected.
        n_points: Number of points to add around the elbow.

    Returns:
        Refined quantile grid with additional points near the elbow.

    Strategy:
        1. Find the two grid points bracketing the elbow
        2. Add n_points evenly spaced between them
        3. Merge with original grid and sort
        4. Remove duplicates
    """
    # Find bracketing indices
    idx = np.searchsorted(quantile_grid, elbow_quantile)

    # Edge case: elbow at first quantile (idx == 0)
    if idx == 0:
        # Add points between grid[0] and grid[1]
        if len(quantile_grid) > 1:
            q_left = quantile_grid[0]
            q_right = quantile_grid[1]
        else:
            # Single-point grid - can't refine
            return quantile_grid
    # Edge case: elbow at or beyond last quantile
    elif idx >= len(quantile_grid):
        # Add points between grid[-2] and grid[-1]
        if len(quantile_grid) > 1:
            q_left = quantile_grid[-2]
            q_right = quantile_grid[-1]
        else:
            return quantile_grid
    # Normal case: elbow between two points
    else:
        q_left = quantile_grid[idx - 1]
        q_right = quantile_grid[idx]

    # Generate intermediate points
    # Use linspace to get n_points BETWEEN the brackets (exclude endpoints)
    new_points = np.linspace(q_left, q_right, n_points + 2)[1:-1]

    # Merge with original grid
    refined_grid = np.concatenate([quantile_grid, new_points])

    # Sort and remove duplicates
    refined_grid = np.unique(refined_grid)

    return refined_grid


def _refine_elbow_iteratively(
    u_sorted: np.ndarray,
    tol_grid: np.ndarray,
    quantile_grid: np.ndarray,
    max_iterations: int = 5,
    convergence_tol: float = 1e-6,
) -> tuple[float | None, np.ndarray, float | None, np.ndarray, list]:
    """Iteratively refine quantile grid to improve elbow detection.

    Args:
        u_sorted: Sorted normalized parameter values.
        tol_grid: Tolerance grid for computing mass curves.
        quantile_grid: Initial quantile grid.
        max_iterations: Maximum refinement iterations.
        convergence_tol: Elbow change threshold for convergence.

    Returns:
        Tuple of (final_tol_elbow, final_quantile_grid, final_quantile_elbow,
        tol_at_quantile, elbows_list).  The last two are from the final
        iteration and can be reused for diagnostics.
    """
    from fitqc._quantile_utils import _aggregate_elbows_median

    current_grid = quantile_grid.copy()
    previous_elbow = None
    first_elbow = None
    first_quantile_elbow = None
    _delta_origin = False  # Set when iter 0 detects a delta function
    _delta_quantile = None
    # Keep last iteration's diagnostic data for caller reuse
    last_tol_at_quantile: np.ndarray = np.array([])
    last_elbows: list[float | None] = []

    for _iteration in range(max_iterations):
        # Compute quantile curves with current grid
        tol_at_quantile, elbows = _compute_quantile_curves_boundary(
            u_sorted, tol_grid, current_grid
        )
        last_tol_at_quantile = tol_at_quantile
        last_elbows = elbows

        # Aggregate elbows (no hard artifact filter — let check_excess_mass validate)
        current_elbow = _aggregate_elbows_median(elbows, min_agreement_frac=0.5)

        # If no elbow found, stop iteration
        if current_elbow is None:
            return None, current_grid, None, tol_at_quantile, elbows

        # Map tolerance-space elbow to quantile-space via interpolation.
        # tol_at_quantile is monotonically non-decreasing (CDF inverse).
        # For delta functions (current_elbow ≈ 0), np.interp returns the first
        # grid point — a small value that signals "delta" to the caller.
        # The actual pileup fraction is recovered downstream via mass(0).
        elbow_quantile = float(np.interp(current_elbow, tol_at_quantile, current_grid))

        # Track first-iteration elbow for stability guard
        if first_elbow is None:
            first_elbow = current_elbow
            first_quantile_elbow = elbow_quantile

        # If we're returning from a delta-continue (iter 0 was a delta,
        # we refined the grid, now on iter 1): return with the delta
        # values but the grown grid and refreshed tol_at_quantile.
        if _delta_origin:
            return 0.0, current_grid, _delta_quantile, tol_at_quantile, elbows

        # Special case: elbow at t≈0 (delta function at boundary).
        # Refine once around the quantile elbow before returning so that the
        # grid actually grows (needed for grid-resolution diagnostics).
        if current_elbow < 1e-10:
            if _iteration == 0 and elbow_quantile is not None:
                _delta_origin = True
                _delta_quantile = elbow_quantile
                current_grid = _refine_quantile_grid_around_elbow(
                    current_grid, elbow_quantile, n_points=15
                )
                previous_elbow = current_elbow
                continue
            return current_elbow, current_grid, elbow_quantile, tol_at_quantile, elbows

        # Stability guard: if refinement degraded significantly, revert to first
        if previous_elbow is not None and current_elbow < first_elbow * 0.3:
            return (
                first_elbow,
                current_grid,
                first_quantile_elbow,
                tol_at_quantile,
                elbows,
            )

        # Check convergence (relative tolerance)
        if previous_elbow is not None:
            rel_tol = max(convergence_tol, 0.03 * abs(current_elbow))
            if abs(current_elbow - previous_elbow) < rel_tol:
                return current_elbow, current_grid, elbow_quantile, tol_at_quantile, elbows

        # Refine grid around current elbow quantile
        current_grid = _refine_quantile_grid_around_elbow(current_grid, elbow_quantile, n_points=15)

        previous_elbow = current_elbow

    # Max iterations reached - return last result
    return current_elbow, current_grid, elbow_quantile, last_tol_at_quantile, last_elbows


@dataclass
class BoundaryResult:
    """Result of boundary QC analysis."""

    #: Whether excess mass was detected near lower bound.
    lower_pileup_detected: bool
    #: Whether excess mass was detected near upper bound.
    upper_pileup_detected: bool
    #: Optimal lower tolerance (elbow point), or None if no elbow.
    t_lo_star: float | None
    #: Optimal upper tolerance (elbow point), or None if no elbow.
    t_hi_star: float | None
    #: Array of tolerance values tested.
    tol_grid: np.ndarray
    #: P(u < tol) for each tolerance.
    lower_mass_curve: np.ndarray
    #: P(u > 1-tol) for each tolerance.
    upper_mass_curve: np.ndarray
    #: Quantile elbow data (only with use_quantile_analysis=True).
    quantile_elbows: dict[str, dict[float, float | None]] | None = None
    #: Refined quantile grid for lower boundary (only with refine_transition=True).
    quantile_grid_refined_lower: np.ndarray | None = None
    #: Refined quantile grid for upper boundary (only with refine_transition=True).
    quantile_grid_refined_upper: np.ndarray | None = None
    #: Raw Kneedle elbows for lower boundary (per-iteration list from refinement).
    kneedle_elbows_lower: list[float | None] | None = None
    #: Raw Kneedle elbows for upper boundary (per-iteration list from refinement).
    kneedle_elbows_upper: list[float | None] | None = None
    #: Raw aggregated tolerance for lower boundary (before check_excess_mass).
    t_lo_raw: float | None = None
    #: Raw aggregated tolerance for upper boundary (before check_excess_mass).
    t_hi_raw: float | None = None
    #: Quantile grid used for Kneedle detection.
    kneedle_quantile_grid: tuple[float, ...] | None = None


def _check_excess_mass(
    t_star: float | None,
    mass_curve: np.ndarray,
    tol_grid: np.ndarray,
    pileup_threshold: float,
    excess_ratio: float,
) -> tuple[bool, float | None]:
    """Check if there's excess mass at the elbow tolerance.

    Special handling for t≈0 (delta function at exact boundary):
    When elbow is detected at t≈0, this indicates samples concentrated
    exactly at the boundary (e.g., optimizer stuck at L=0). We measure
    the pileup using the first measurable non-zero tolerance point.

    Parameters
    ----------
    t_star : float or None
        Raw elbow tolerance to validate.
    mass_curve : np.ndarray
        Tail-mass curve (P(u < tol) or P(u > 1-tol)).
    tol_grid : np.ndarray
        Array of tolerance values corresponding to mass_curve.
    pileup_threshold : float
        Threshold below which elbows are treated as delta-function candidates.
    excess_ratio : float
        Minimum mass/tol ratio to declare pileup.

    Returns
    -------
    tuple[bool, float | None]
        (has_pileup, validated_tolerance). If no excess mass, tolerance is None.
    """
    if t_star is None:
        return False, None

    # Special case: elbow at very small t indicates delta function at boundary
    # This happens when optimizer gets stuck exactly at L or U
    # Example: A_He PPA12 has 1.64% samples at exactly L=0
    # After iterative refinement and aggregation, the median elbow might be
    # slightly above zero (e.g., 0.0003) even when many individual elbows are at 0
    # Use pileup_threshold as the cutoff: elbows smaller than this need special handling
    if t_star < pileup_threshold:
        # Check if this small elbow represents a genuine delta function pileup
        # Find first non-zero tolerance point to measure the pileup
        # Skip tol_grid[0] which is often exactly 0
        for idx in range(1, min(5, len(tol_grid))):  # Check first few points
            t_check = tol_grid[idx]
            if t_check > 1e-10:  # Found measurable tolerance
                mass_check = mass_curve[idx]
                # For delta function, mass should be nearly constant up to pileup width
                # Check if mass >> uniform expectation at this tolerance
                if mass_check > t_check * excess_ratio:
                    # Valid pileup detected
                    # Return the measurement tolerance (not the elbow value)
                    return True, float(t_check)
        # No measurable pileup found - elbow is small but no excess mass
        return False, None

    # Normal case: elbow at measurable tolerance (t_star >= pileup_threshold)
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


def run_boundary_qc(
    x: np.ndarray,
    L: float,
    U: float,
    config: BoundaryConfig | None = None,
) -> BoundaryResult:
    """Detect boundary stickiness (pileup near parameter bounds L and U).

    This function DETECTS when samples cluster too close to the parameter
    bounds L or U, which indicates the optimizer got stuck at constraints.
    It does NOT filter the data - filtering is performed separately using
    the returned detection thresholds.

    Important Distinctions:

    - **Boundary stickiness** (detected here): Samples AT or NEAR L/U (valid but
      suspicious). Example: For L=0, U=25, samples at x=0.001 are boundary-sticky.
    - **Out-of-bounds** (NOT detected here): Samples with x < L or x > U (invalid).
      Example: For L=0, samples at x=-0.5 are out-of-bounds.

    Note: If out-of-bounds samples are present, they are excluded from the
    boundary stickiness analysis and a warning is logged. To remove out-of-bounds
    samples from your data, use the bounds filter in plot_bounds_filter_comparison().

    The detection works by:
    1. Normalizing positions: u = (x - L) / (U - L)
    2. Computing cumulative mass near boundaries at increasing tolerances
    3. Using elbow detection to find where "stuck" region ends
    4. Returning detection thresholds (t_lo_star for lower, t_hi_star for upper)

    These thresholds can be used to filter boundary-sticky samples:
    - Lower boundary filter: keep samples with u > t_lo_star
    - Upper boundary filter: keep samples with u < t_hi_star

    Args:
        x: Array of parameter values to analyze.
        L: Lower bound of the parameter.
        U: Upper bound of the parameter.
        config: Configuration for boundary analysis. Uses defaults if None.

    Returns:
        BoundaryResult with:
        - lower_pileup_detected: True if samples pile up near L
        - upper_pileup_detected: True if samples pile up near U
        - t_lo_star: Threshold for lower boundary (None if not detected)
        - t_hi_star: Threshold for upper boundary (None if not detected)
        - Mass curves and tolerance grids for visualization

    Examples:
        >>> # Detect boundary stickiness
        >>> result = run_boundary_qc(x, L=0.0, U=25.0)
        >>> if result.lower_pileup_detected:
        ...     print(f"Lower boundary stickiness detected at u < {result.t_lo_star:.4f}")
        ...     # Filter: keep x[u > result.t_lo_star]
    """
    if config is None:
        config = BoundaryConfig()

    # Transform to normalized coordinates
    u = compute_u(x, L, U)

    # Validate that samples are within parameter bounds
    # Samples outside [L, U] create u < 0 or u > 1, which violate algorithm assumptions
    n_total = len(u)
    out_of_bounds_mask = (u < 0) | (u > 1)
    n_out_of_bounds = np.sum(out_of_bounds_mask)

    if n_out_of_bounds > 0:
        frac_out_of_bounds = n_out_of_bounds / n_total
        n_below = np.sum(u < 0)
        n_above = np.sum(u > 1)

        logger.warning(
            f"Boundary QC: {n_out_of_bounds} samples ({frac_out_of_bounds:.2%}) "
            f"are outside parameter bounds [L={L}, U={U}]. "
            f"Below L: {n_below} ({n_below / n_total:.2%}), "
            f"Above U: {n_above} ({n_above / n_total:.2%}). "
            f"These samples will be excluded from boundary stickiness analysis. "
            f"Note: Samples outside bounds may indicate fit failures or data quality issues."
        )

        # Filter to only valid samples
        u = u[~out_of_bounds_mask]

        # If all samples are out of bounds, return no detection
        if len(u) == 0:
            logger.error(
                "Boundary QC: All samples are outside parameter bounds. "
                "Cannot perform boundary stickiness analysis."
            )
            return BoundaryResult(
                lower_pileup_detected=False,
                upper_pileup_detected=False,
                t_lo_star=None,
                t_hi_star=None,
                tol_grid=np.array([]),
                lower_mass_curve=np.array([]),
                upper_mass_curve=np.array([]),
                quantile_elbows=None,
            )

    # Build tolerance grid based on grid_mode
    tol_grid = _build_tolerance_grid(config)

    # Extend tolerance grid when refinement is enabled so that broad pileups
    # (elbows at tol > tol_max) can be detected.
    if config.refine_transition:
        tol_max_extended = max(config.quantile_grid)
        if tol_max_extended > tol_grid[-1]:
            n_ext = max(20, int((tol_max_extended - tol_grid[-1]) / 0.005))
            extension = np.linspace(tol_grid[-1], tol_max_extended, n_ext + 1)[1:]
            tol_grid = np.concatenate([tol_grid, extension])

    # Sort u for efficient tail_mass computation
    u_sorted = np.sort(u)

    # Compute lower mass curve: P(u < tol) for each tol
    lower_mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])

    # For upper boundary: P(u > 1-tol) = P(1-u < tol)
    # We need to compute this by working with 1-u
    one_minus_u_sorted = np.sort(1 - u)
    upper_mass_curve = np.array([tail_mass(one_minus_u_sorted, tol) for tol in tol_grid])

    # Initialize quantile_elbows as None (will be populated if multi-curve enabled)
    quantile_elbows_result = None
    quantile_grid_refined_lower = None
    quantile_grid_refined_upper = None
    kneedle_elbows_lower = None
    kneedle_elbows_upper = None
    kneedle_quantile_grid = None

    # Choose detection method based on config
    if config.use_quantile_analysis:
        # Multi-curve quantile analysis
        quantile_grid_arr = np.array(config.quantile_grid)

        if config.refine_transition:
            # Iterative refinement mode
            (
                t_lo_raw,
                quantile_grid_refined_lower,
                q_lo_elbow,
                tol_at_quantile_lower,
                elbows_lower,
            ) = _refine_elbow_iteratively(u_sorted, tol_grid, quantile_grid_arr, max_iterations=5)
            (
                t_hi_raw,
                quantile_grid_refined_upper,
                q_hi_elbow,
                tol_at_quantile_upper,
                elbows_upper,
            ) = _refine_elbow_iteratively(
                one_minus_u_sorted, tol_grid, quantile_grid_arr, max_iterations=5
            )

            # Mechanism 1 — spread-pileup propagation:
            # For concentrated (but non-delta) pileups the tolerance elbow is
            # very small because the CDF-inverse at the pileup fraction maps
            # to a tiny tolerance.  Override with half the quantile elbow
            # (≈ pileup width, not fraction) so check_excess_mass's normal
            # case validates instead of the delta branch.
            # Guards:
            #  - mass(0) < 1e-10: excludes delta functions where samples sit
            #    at the exact boundary (those are handled by Mechanism 2)
            #  - t < 0.2*q: excludes very narrow pileups where the tolerance
            #    elbow IS a reasonable estimate of the pileup width
            for _side_label, q_ref in [
                ("lower", q_lo_elbow),
                ("upper", q_hi_elbow),
            ]:
                t_val = t_lo_raw if _side_label == "lower" else t_hi_raw
                mass_at_zero = (
                    lower_mass_curve[0] if _side_label == "lower" else upper_mass_curve[0]
                )
                if (
                    t_val is not None
                    and t_val < config.pileup_threshold
                    and q_ref is not None
                    and q_ref > config.pileup_threshold
                    and mass_at_zero < 1e-10
                    and t_val < 0.2 * q_ref
                ):
                    override = max(q_ref / 2, config.pileup_threshold)
                    if _side_label == "lower":
                        t_lo_raw = override
                    else:
                        t_hi_raw = override

            # Mechanism 3 — broad-pileup fallback:
            # When the quantile analysis finds only a weak elbow (mass ratio
            # barely above excess_ratio), the pileup may extend well beyond
            # the detected tolerance.  Search the mass curve for the largest
            # tolerance that still shows excess mass.
            for _side_label in ["lower", "upper"]:
                t_raw = t_lo_raw if _side_label == "lower" else t_hi_raw
                mc = lower_mass_curve if _side_label == "lower" else upper_mass_curve
                if t_raw is None or t_raw < config.pileup_threshold:
                    continue
                idx_t = min(int(np.searchsorted(tol_grid, t_raw)), len(mc) - 1)
                mass_ratio = mc[idx_t] / t_raw if t_raw > 0 else 0
                if mass_ratio >= 2.0 * config.excess_ratio:
                    continue  # Strong excess — quantile result is reliable
                # Weak excess: search backward for the true pileup extent
                t_broad = t_raw
                for j in range(len(tol_grid) - 1, idx_t, -1):
                    if tol_grid[j] > 0 and mc[j] / tol_grid[j] > config.excess_ratio:
                        t_broad = float(tol_grid[j])
                        break
                if t_broad > t_raw * 3:
                    if _side_label == "lower":
                        t_lo_raw = t_broad
                    else:
                        t_hi_raw = t_broad

            kneedle_elbows_lower = elbows_lower
            kneedle_elbows_upper = elbows_upper
            kneedle_quantile_grid = tuple(float(q) for q in quantile_grid_arr)
        else:
            # Single-pass quantile analysis (no refinement)
            # Compute quantile curves for lower boundary
            tol_at_quantile_lower, elbows_lower = _compute_quantile_curves_boundary(
                u_sorted, tol_grid, quantile_grid_arr
            )

            # Compute quantile curves for upper boundary
            tol_at_quantile_upper, elbows_upper = _compute_quantile_curves_boundary(
                one_minus_u_sorted, tol_grid, quantile_grid_arr
            )

            # Aggregate elbows via median
            t_lo_raw = _aggregate_elbows_median(elbows_lower, config.min_quantile_agreement)
            t_hi_raw = _aggregate_elbows_median(elbows_upper, config.min_quantile_agreement)

            kneedle_elbows_lower = elbows_lower
            kneedle_elbows_upper = elbows_upper
            kneedle_quantile_grid = tuple(float(q) for q in quantile_grid_arr)

        # Store quantile elbows for diagnostics.
        # Use a diagnostic tol_grid capped at pileup_threshold for CDF-inverse
        # computation so high-quantile entries don't inflate the diagnostic dict.
        # Add extra low-quantile points for resolution below pileup_threshold.

        grid_for_diagnostics_lower = (
            quantile_grid_refined_lower
            if quantile_grid_refined_lower is not None
            else quantile_grid_arr
        )
        grid_for_diagnostics_upper = (
            quantile_grid_refined_upper
            if quantile_grid_refined_upper is not None
            else quantile_grid_arr
        )

        if config.refine_transition:
            # Recompute CDF-inverse with a diagnostic tol_grid capped at
            # pileup_threshold.  This clamps high-quantile tol values so
            # the diagnostic dict doesn't report inflated tolerances from
            # the extended grid.  Add extra low-quantile resolution so
            # most entries fall below the pileup threshold for non-pileup data.
            diag_tol_max = config.pileup_threshold
            diag_n = max(11, config.n_tols // 4)
            diag_tol_grid = np.linspace(config.tol_min, diag_tol_max, diag_n)
            diag_low_q = np.linspace(0.0001, config.pileup_threshold, 30)
            diag_grid_lo = np.sort(
                np.unique(np.concatenate([grid_for_diagnostics_lower, diag_low_q]))
            )
            diag_grid_hi = np.sort(
                np.unique(np.concatenate([grid_for_diagnostics_upper, diag_low_q]))
            )
            base_mass_lo = np.array([tail_mass(u_sorted, t) for t in diag_tol_grid])
            base_mass_hi = np.array([tail_mass(one_minus_u_sorted, t) for t in diag_tol_grid])
            tol_at_q_diag_lo = np.interp(diag_grid_lo, base_mass_lo, diag_tol_grid)
            tol_at_q_diag_hi = np.interp(diag_grid_hi, base_mass_hi, diag_tol_grid)
            quantile_elbows_result = {
                "lower": {
                    float(q): float(tol)
                    for q, tol in zip(diag_grid_lo, tol_at_q_diag_lo, strict=True)
                },
                "upper": {
                    float(q): float(tol)
                    for q, tol in zip(diag_grid_hi, tol_at_q_diag_hi, strict=True)
                },
            }
            # Update grid references for result
            grid_for_diagnostics_lower = diag_grid_lo
            grid_for_diagnostics_upper = diag_grid_hi
        else:
            quantile_elbows_result = {
                "lower": {
                    float(q): float(tol)
                    for q, tol in zip(
                        grid_for_diagnostics_lower, tol_at_quantile_lower, strict=True
                    )
                },
                "upper": {
                    float(q): float(tol)
                    for q, tol in zip(
                        grid_for_diagnostics_upper, tol_at_quantile_upper, strict=True
                    )
                },
            }
    else:
        # Single-curve elbow detection (original method)
        # Skip tol=0 for elbow detection (avoid singularities)
        if tol_grid[0] == 0.0 and len(tol_grid) > 1:
            elbow_tols = tol_grid[1:]
            elbow_lower_mass = lower_mass_curve[1:]
            elbow_upper_mass = upper_mass_curve[1:]
        else:
            elbow_tols = tol_grid
            elbow_lower_mass = lower_mass_curve
            elbow_upper_mass = upper_mass_curve

        t_lo_raw = select_elbow(
            elbow_tols, elbow_lower_mass, curve="concave", direction="increasing"
        )
        t_hi_raw = select_elbow(
            elbow_tols, elbow_upper_mass, curve="concave", direction="increasing"
        )

    pileup_threshold = config.pileup_threshold
    excess_ratio = config.excess_ratio

    lower_pileup_detected, t_lo_star = _check_excess_mass(
        t_lo_raw, lower_mass_curve, tol_grid, pileup_threshold, excess_ratio
    )
    upper_pileup_detected, t_hi_star = _check_excess_mass(
        t_hi_raw, upper_mass_curve, tol_grid, pileup_threshold, excess_ratio
    )

    # Mechanism 2 — delta-function propagation (refine_transition only):
    # For delta-function pileups (t_raw ≈ 0), check_excess_mass returns a very
    # small t_star (first measurable tol point).  When the pileup fraction is
    # large enough (mass(0) >> pileup_threshold) AND the quantile grid has
    # sufficient resolution around the pileup fraction, override t_star with
    # mass(0) — the exact pileup fraction.
    if config.use_quantile_analysis and config.refine_transition:
        for side, mass_curve_side, _refined_grid, t_raw, detected, t_star_val in [
            (
                "lower",
                lower_mass_curve,
                quantile_grid_refined_lower,
                t_lo_raw,
                lower_pileup_detected,
                t_lo_star,
            ),
            (
                "upper",
                upper_mass_curve,
                quantile_grid_refined_upper,
                t_hi_raw,
                upper_pileup_detected,
                t_hi_star,
            ),
        ]:
            if not (
                detected
                and t_star_val is not None
                and t_star_val < config.pileup_threshold
                and t_raw is not None
                and t_raw < 1e-10
                and mass_curve_side[0] > 2 * config.pileup_threshold
            ):
                continue
            pileup_frac = float(mass_curve_side[0])
            # Grid resolution guard: ensure the quantile grid has at least 2
            # points near the pileup fraction for a reliable estimate.
            # Use the initial (unrefined) grid when checking — the delta-continue
            # in _refine_elbow_iteratively grows the grid for diagnostics, not
            # to signal that M2 resolution is adequate.
            grid_to_check = quantile_grid_arr
            nearby = grid_to_check[
                (grid_to_check > 0.5 * pileup_frac) & (grid_to_check < 1.5 * pileup_frac)
            ]
            if len(nearby) < 2:
                continue
            if side == "lower":
                t_lo_star = pileup_frac
            else:
                t_hi_star = pileup_frac

    return BoundaryResult(
        lower_pileup_detected=bool(lower_pileup_detected),
        upper_pileup_detected=bool(upper_pileup_detected),
        t_lo_star=t_lo_star,
        t_hi_star=t_hi_star,
        tol_grid=tol_grid,
        lower_mass_curve=lower_mass_curve,
        upper_mass_curve=upper_mass_curve,
        quantile_elbows=quantile_elbows_result,
        quantile_grid_refined_lower=quantile_grid_refined_lower,
        quantile_grid_refined_upper=quantile_grid_refined_upper,
        kneedle_elbows_lower=kneedle_elbows_lower,
        kneedle_elbows_upper=kneedle_elbows_upper,
        t_lo_raw=t_lo_raw,
        t_hi_raw=t_hi_raw,
        kneedle_quantile_grid=kneedle_quantile_grid,
    )
