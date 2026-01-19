"""Elbow detection using the kneed library for automatic threshold selection."""

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
