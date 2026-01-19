"""Boundary stickiness detection via proximity to parameter bounds.

This module detects whether fitted parameters are "stuck" at their bounds
(L or U). When an optimizer hits a bound constraint, samples pile up at the
boundary, creating detectable excess mass in the distribution.

The Algorithm
-------------
1. Transform x -> u = (x - L) / (U - L), so u=0 at L, u=1 at U
2. For lower boundary: compute P(u < tol) for each tol in linspace(tol_min, tol_max, n_tols)
3. For upper boundary: compute P(u > 1-tol) = P(1-u < tol) similarly
4. Use elbow detection on the mass curves to find t_lo*, t_hi*
5. Pileup is detected if the elbow tolerance exceeds a threshold

The mass curve P(u < tol) vs tol shows:
- For uniform data: linear growth (P ~ tol)
- For boundary pileup: sharp initial rise then slower growth (elbow indicates pileup region)

Why Elbow Detection?
-------------------
The elbow point indicates where "stuck" samples end and "natural" samples begin.
If no elbow is found, there's no boundary pileup - the distribution is uniform
near the boundary.
"""

from dataclasses import dataclass

import numpy as np

from fitqc.config import BoundaryConfig
from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass


def compute_u(x: np.ndarray, L: float, U: float) -> np.ndarray:
    """Compute normalized position in [L, U].

    u = (x - L) / (U - L)

    So u=0 at L, u=1 at U, u=0.5 at midpoint.

    Args:
        x: Array of parameter values.
        L: Lower bound.
        U: Upper bound.

    Returns:
        Normalized positions in [0, 1] for values within [L, U].
        Values outside [L, U] will be outside [0, 1].
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
