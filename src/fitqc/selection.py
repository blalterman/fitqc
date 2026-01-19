"""Elbow detection using the kneed library for automatic threshold selection.

Why This Module Exists
----------------------
Both interior and boundary QC need to automatically select optimal thresholds:
- Interior QC: Find eps* where the "spike" near x0 ends
- Boundary QC: Find tol* where boundary pileup becomes negligible

The pattern is the same: we compute a curve (e.g., "fraction of samples within eps
of x0" vs eps) and need to find where it "levels off"—the elbow point.

What is Elbow Detection?
------------------------
Given a curve that rises sharply then plateaus (or vice versa), the "elbow" is
the point of maximum curvature—where the rate of change transitions from steep
to flat. Visually, it's where the curve "bends."

Example: If we plot "fraction within eps of x0" vs eps:
- For small eps: fraction is small (only truly stuck samples)
- At some eps*: fraction jumps (we've captured the spike)
- For large eps: fraction grows slowly (natural variation)
The elbow at eps* tells us the spike's boundary.

Why kneed Library?
------------------
We use the `kneed` library (https://github.com/arvkevi/kneed) because:
1. Implements the "Kneedle" algorithm from Satopaa et al. (2011)
2. Handles noisy data robustly
3. Works for both concave and convex curves
4. Well-tested, published algorithm (not a hand-rolled heuristic)

We set `online=True` for better handling of:
- Step-like functions (common in our use case)
- Edge cases where the elbow is near the boundary

Why log_x Parameter?
--------------------
Epsilon grids are typically log-spaced (e.g., 1e-12 to 1e-3). In linear space,
most points cluster near zero, distorting the elbow detection. By working in
log10(eps) space, points are evenly distributed, giving better elbow detection.

We transform internally so the caller can work in natural units (actual eps values)
while the algorithm sees log-space.

When No Elbow Exists
--------------------
For linear data or curves without clear inflection, `select_elbow` returns `None`.
Callers must handle this case—it typically means the effect being measured
(spike, pileup) is absent or too weak to detect.
"""

import numpy as np
from kneed import KneeLocator


def select_elbow(
    x: np.ndarray,
    y: np.ndarray,
    curve: str = "concave",
    direction: str = "increasing",
    log_x: bool = False,
) -> float | None:
    """Find elbow point using kneed library.

    Args:
        x: X values (must be monotonic)
        y: Y values
        curve: "concave" or "convex"
        direction: "increasing" or "decreasing"
        log_x: If True, work in log-space for x

    Returns:
        Elbow x-value, or None if no elbow found
    """
    if log_x:
        x_work = np.log10(x)
    else:
        x_work = x

    # Use online mode for better handling of step-like functions and edge cases
    kl = KneeLocator(
        x_work,
        y,
        curve=curve,
        direction=direction,
        online=True,
    )

    if kl.knee is None:
        return None

    if log_x:
        return 10**kl.knee
    return kl.knee
