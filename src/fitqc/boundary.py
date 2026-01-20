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

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fitqc._quantile_utils import _aggregate_elbows_median
from fitqc.config import BoundaryConfig
from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass


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
    # For pileup data: tolerance << quantile initially (many samples in small tol),
    #                  then tolerance ≈ quantile (back to uniform)
    # The elbow is where this transition occurs
    elbow_overall = select_elbow(
        quantile_grid, tol_at_quantile, curve="concave", direction="increasing"
    )

    # Return list with single elbow (will be aggregated across lower/upper boundaries)
    elbows_per_quantile = [elbow_overall]

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
    quantile_grid: np.ndarray,
    elbow_quantile: float,
    n_points: int = 15
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
    convergence_tol: float = 1e-6
) -> tuple[float | None, np.ndarray]:
    """Iteratively refine quantile grid to improve elbow detection.

    Args:
        u_sorted: Sorted normalized parameter values.
        tol_grid: Tolerance grid for computing mass curves.
        quantile_grid: Initial quantile grid.
        max_iterations: Maximum refinement iterations.
        convergence_tol: Elbow change threshold for convergence.

    Returns:
        Tuple of (final_elbow, final_quantile_grid).
    """
    current_grid = quantile_grid.copy()
    previous_elbow = None
    tol_max = tol_grid[-1]
    # Reject elbows within 1% of tol_max (likely boundary artifacts)
    tol_max_threshold = tol_max * 0.99

    for iteration in range(max_iterations):
        # Compute quantile curves with current grid
        tol_at_quantile, elbows = _compute_quantile_curves_boundary(
            u_sorted, tol_grid, current_grid
        )

        # Filter out elbows that are too close to tol_max (boundary artifacts)
        filtered_elbows = [
            e if (e is not None and e < tol_max_threshold) else None
            for e in elbows
        ]

        # Aggregate elbows
        from fitqc._quantile_utils import _aggregate_elbows_median
        current_elbow = _aggregate_elbows_median(filtered_elbows, min_agreement_frac=0.5)

        # If no elbow found, stop iteration
        if current_elbow is None:
            return None, current_grid

        # Check convergence
        if previous_elbow is not None:
            if abs(current_elbow - previous_elbow) < convergence_tol:
                # Converged
                return current_elbow, current_grid

        # Refine grid around current elbow
        # Find which quantile corresponds to this tolerance
        # We need to find q such that tol_at_quantile[q] ≈ current_elbow
        idx = np.argmin(np.abs(tol_at_quantile - current_elbow))
        elbow_quantile = current_grid[idx]

        # Refine grid
        current_grid = _refine_quantile_grid_around_elbow(
            current_grid, elbow_quantile, n_points=15
        )

        previous_elbow = current_elbow

    # Max iterations reached - return last result
    return current_elbow, current_grid


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

    # Build tolerance grid based on grid_mode
    tol_grid = _build_tolerance_grid(config)

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

    # Choose detection method based on config
    if config.use_quantile_analysis:
        # Multi-curve quantile analysis
        quantile_grid_arr = np.array(config.quantile_grid)

        if config.refine_transition:
            # Iterative refinement mode
            t_lo_raw, quantile_grid_refined_lower = _refine_elbow_iteratively(
                u_sorted, tol_grid, quantile_grid_arr, max_iterations=5
            )
            t_hi_raw, quantile_grid_refined_upper = _refine_elbow_iteratively(
                one_minus_u_sorted, tol_grid, quantile_grid_arr, max_iterations=5
            )

            # Compute final quantile curves with refined grids for diagnostics
            if quantile_grid_refined_lower is not None:
                tol_at_quantile_lower, elbows_lower = _compute_quantile_curves_boundary(
                    u_sorted, tol_grid, quantile_grid_refined_lower
                )
            else:
                tol_at_quantile_lower = np.array([])
                elbows_lower = []

            if quantile_grid_refined_upper is not None:
                tol_at_quantile_upper, elbows_upper = _compute_quantile_curves_boundary(
                    one_minus_u_sorted, tol_grid, quantile_grid_refined_upper
                )
            else:
                tol_at_quantile_upper = np.array([])
                elbows_upper = []
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

        # Store quantile elbows for diagnostics (use refined grid if available)
        grid_for_diagnostics_lower = quantile_grid_refined_lower if quantile_grid_refined_lower is not None else quantile_grid_arr
        grid_for_diagnostics_upper = quantile_grid_refined_upper if quantile_grid_refined_upper is not None else quantile_grid_arr

        quantile_elbows_result = {
            "lower": {
                float(q): float(tol)
                for q, tol in zip(grid_for_diagnostics_lower, tol_at_quantile_lower, strict=True)
            },
            "upper": {
                float(q): float(tol)
                for q, tol in zip(grid_for_diagnostics_upper, tol_at_quantile_upper, strict=True)
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

    # Detect pileup based on whether elbow shows excess mass
    # For uniform data, we expect P(u < tol) ≈ tol
    # Pileup means observed mass >> expected mass at the elbow
    # We use a ratio threshold: mass / tol > excess_ratio indicates pileup
    pileup_threshold = config.pileup_threshold
    excess_ratio = config.excess_ratio

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
        quantile_elbows=quantile_elbows_result,
        quantile_grid_refined_lower=quantile_grid_refined_lower,
        quantile_grid_refined_upper=quantile_grid_refined_upper,
    )
