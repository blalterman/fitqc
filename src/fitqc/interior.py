"""Interior QC: Detect initial-guess stickiness (x0 stickiness) via distance from x0.

This module detects when optimization results are "stuck" at the initial guess (x0),
which often indicates failed convergence or poor optimizer behavior.

Why This Module Exists
----------------------
Optimizers sometimes return x0 when they fail to converge or find a better solution.
This creates a "spike" in the distribution at exactly x0. By transforming to
z-space (distance from x0), we can detect this spike as an anomalous concentration
of samples near z=0.

The Algorithm
-------------
**Single-Curve Mode (default):**

1. Transform x -> z = ``|x - x0| / max(x0 - L, U - x0)``, so z=0 at x0
2. For each eps in logspace(eps_log10_min, eps_log10_max, n_eps):
   - Compute P(z < eps) = "fraction of samples within eps of x0"
3. Build histogram of z-values
4. Use scipy.signal.find_peaks to detect spikes in the histogram
5. A spike indicates stickiness if:
   - prominence >= spike_prominence_min (stands out from background)
   - width <= spike_width_max bins (narrow, not a broad distribution)
   - location <= spike_location_max (near z=0, i.e., near x0)
6. Use elbow detection on the P(z < eps) curve to find eps*

**Multi-Curve Mode (use_quantile_analysis=True):**

For more robust threshold estimation across multiple samples:

1. Transform to z-space (same as single-curve)
2. For each quantile q in quantile_grid, find epsilon where P(z < eps) = q
3. Detect elbows in the (quantile, epsilon) relationship for each quantile
4. Aggregate across quantiles using median to get final eps*

IMPORTANT: Spike detection and threshold estimation are INDEPENDENT:
- Spike detection (histogram-based) determines IF stickiness exists
- Threshold estimation (elbow-based) determines HOW WIDE the stickiness is
- Multi-curve analysis only affects eps*, not spike_detected

This multi-curve approach provides:
- Better accuracy for very tight spikes (< 1e-8 width)
- Robustness via median aggregation across quantiles
- Diagnostic information via quantile_elbows field in results

IMPORTANT: Two Different Uses of "Log" (Don't Confuse Them!)
------------------------------------------------------------
1. **Log-spaced epsilon SEARCH grid**: We search for the stickiness threshold
   across many orders of magnitude (10^-12 to 10^-3). Using np.logspace ensures
   we sample each decade evenly. This is purely an algorithmic choice about
   how to efficiently search—it has NOTHING to do with the data distribution.
   The actual data `x` is NEVER transformed to log space.

2. **Log-normal TEST data**: We test against signed log-normal distributions
   to ensure we don't falsely flag their natural clustering near zero as
   "stickiness." This is about validating the algorithm against a specific
   data distribution—it has NOTHING to do with the log-spaced search grid.

The elbow detection uses `log_x=True` because the epsilon grid is log-spaced,
so kneed needs to work in log space to find elbows correctly. This still
doesn't transform the actual data—only the threshold search coordinates.

Critical: Avoiding False Positives
----------------------------------
A signed log-normal distribution centered at 0 has natural mass near 0, but
it's BROAD, not a spike. The width criterion (spike_width_max) prevents this
from being flagged as stickiness. A true spike is narrow (few bins); natural
variation is wide (many bins).

Examples
--------
Single-curve detection (default behavior):

>>> from fitqc.interior import run_interior_qc
>>> from fitqc.config import InteriorConfig
>>> import numpy as np
>>>
>>> # Generate data with x0 spike
>>> x = np.concatenate([
...     np.full(300, 0.5),                    # 300 stuck at x0
...     np.random.uniform(0.0, 1.0, 9700)     # 9700 uniform
... ])
>>>
>>> result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0)
>>> print(f"Spike detected: {result.spike_detected}")
>>> print(f"Threshold eps*: {result.eps_star}")

Multi-curve detection for tight spikes:

>>> config = InteriorConfig(
...     use_quantile_analysis=True,
...     quantile_grid=(0.001, 0.01, 0.05)
... )
>>> result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)
>>> print(f"Spike detected: {result.spike_detected}")
>>> print(f"Threshold eps*: {result.eps_star}")
>>> if result.quantile_elbows:
...     print(f"Quantile elbows: {result.quantile_elbows}")
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.signal import find_peaks, peak_widths

from fitqc.config import InteriorConfig
from fitqc.selection import select_elbow
from fitqc.sortedops import tail_mass


def compute_z(x: NDArray[np.floating], x0: float, L: float, U: float) -> NDArray[np.floating]:
    """Compute normalized distance from the initial guess x0.

    Formula: ``z = |x - x0| / max(x0 - L, U - x0)``

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

        Without max(), using (U - L) = 10::

            At x = 10: z = |10 - 1| / 10 = 0.9  (seems OK)
            At x = 0:  z = |0 - 1| / 10 = 0.1   (WRONG! This is at a bound!)

        With max() = 9::

            At x = 10: z = |10 - 1| / 9 = 1.0   (correct: at furthest bound)
            At x = 0:  z = |0 - 1| / 9 = 0.11   (correct: close to x0)

    Compare to compute_u (boundary.py), which measures position in range:
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
    """Result of interior QC analysis."""

    #: Whether a spike at x0 was detected via histogram analysis.
    spike_detected: bool
    #: Z-location of the spike (if detected). Should be near 0 for true stickiness.
    spike_z_loc: float | None
    #: Optimal epsilon threshold from elbow detection (if detected).
    eps_star: float | None
    #: Array of epsilon values tested in the mass curve analysis.
    eps_grid: NDArray[np.floating]
    #: P(z < eps) for each eps in eps_grid.
    mass_curve: NDArray[np.floating]
    #: Histogram counts of z-values.
    hist_counts: NDArray[np.floating]
    #: Histogram bin edges for z-values.
    hist_edges: NDArray[np.floating]
    #: Optional quantile elbow information (multi-curve mode only)
    quantile_elbows: dict[float, float | None] | None = None


def _compute_quantile_curves_interior(
    z_sorted: NDArray[np.floating],
    eps_grid: NDArray[np.floating],
    quantile_grid: NDArray[np.floating],
) -> tuple[NDArray[np.floating], list[float | None]]:
    """Compute epsilon at each quantile via inverse CDF in log-space.

    This function implements the multi-curve quantile analysis for interior detection.
    For each quantile q, it finds the epsilon value where P(z < eps) = q.

    CRITICAL: Interpolation must be done in LOG-SPACE because the epsilon grid
    is log-spaced (spans 10^-12 to 10^-3). Interpolating in linear space would
    give incorrect results for log-distributed data.

    Args:
        z_sorted: Pre-sorted z-values (distance from x0) in ascending order.
        eps_grid: Log-spaced epsilon grid (from np.logspace).
        quantile_grid: Quantile values to compute thresholds for, in [0, 1].

    Returns:
        A tuple containing:
        - eps_at_quantile: Array of epsilon values achieving each quantile.
            Shape matches quantile_grid. eps_at_quantile[i] is the epsilon
            where P(z < eps) = quantile_grid[i].
        - elbows_per_quantile: List of epsilon estimates (one per quantile).
            Each quantile's epsilon is treated as an independent threshold estimate.
            These are aggregated via median to get the final robust eps_star.

    Examples:
        >>> import numpy as np
        >>> # Generate uniform z-distribution
        >>> z = np.sort(np.random.uniform(0, 1e-3, 1000))
        >>> eps_grid = np.logspace(-12, -3, 50)
        >>> quantile_grid = np.array([0.01, 0.05, 0.10])
        >>>
        >>> eps_at_q, elbows = _compute_quantile_curves_interior(z, eps_grid, quantile_grid)
        >>> # For uniform data, relationship should be approximately linear in log-space
        >>> assert len(eps_at_q) == len(quantile_grid)
        >>> assert len(elbows) == len(quantile_grid)

        >>> # Generate spike data: tight concentration near 0
        >>> z_spike = np.concatenate([
        ...     np.random.uniform(0, 1e-9, 50),    # 5% in tight spike
        ...     np.random.uniform(1e-9, 1e-3, 950)  # 95% elsewhere
        ... ])
        >>> z_spike = np.sort(z_spike)
        >>> eps_at_q, elbows = _compute_quantile_curves_interior(z_spike, eps_grid, quantile_grid)
        >>> # First quantile (1%) should need tiny epsilon
        >>> assert eps_at_q[0] < 1e-8, "1% quantile should be in spike region"
        >>> # Later quantiles should need larger epsilon
        >>> assert eps_at_q[2] > 1e-8, "10% quantile should be beyond spike"
    """
    # Step 1: Compute mass curve P(z < eps) for each epsilon
    # This is the cumulative distribution function of z evaluated at each eps
    z_mass_curve = np.array([np.mean(z_sorted < eps) for eps in eps_grid])

    # Step 2: For each quantile, find epsilon where P(z < eps) = quantile
    # CRITICAL: Interpolate in LOG-SPACE because eps_grid is log-spaced
    # Using linear interpolation in log-space maintains the log-scale relationship
    log_eps_at_quantile = np.interp(
        quantile_grid,  # x values (quantiles we want)
        z_mass_curve,  # y values (cumulative probabilities)
        np.log(eps_grid),  # x values (log of epsilon grid)
    )
    eps_at_quantile = np.exp(log_eps_at_quantile)

    # Step 3: Treat each quantile's epsilon as an independent threshold estimate
    # The median aggregation (done by caller) will combine these robustly
    # Filter out any NaN or infinite values
    elbows_per_quantile = [float(eps) if np.isfinite(eps) else None for eps in eps_at_quantile]

    return eps_at_quantile, elbows_per_quantile


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
    # CRITICAL: Spike detection (above) is INDEPENDENT of threshold estimation (below)
    # - spike_detected tells us IF there's stickiness (binary classification)
    # - eps_star tells us HOW WIDE the stickiness is (threshold estimation)
    # - Multi-curve analysis only affects eps_star, NOT spike_detected

    eps_star = None
    quantile_elbows = None

    if spike_detected:
        if config.use_quantile_analysis:
            # Multi-curve mode: Use quantile analysis for robust threshold estimation
            from fitqc._quantile_utils import _aggregate_elbows_median

            quantile_grid = np.array(config.quantile_grid)
            _, elbows = _compute_quantile_curves_interior(z_sorted, eps_grid, quantile_grid)

            # Aggregate elbows via median for robust estimate
            eps_star = _aggregate_elbows_median(elbows, config.min_quantile_agreement)

            # Store quantile elbow information for diagnostics
            quantile_elbows = {
                float(q): (float(eps) if eps is not None else None)
                for q, eps in zip(quantile_grid, elbows, strict=True)
            }
        else:
            # Single-curve mode (default): Original elbow detection
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
        quantile_elbows=quantile_elbows,
    )
