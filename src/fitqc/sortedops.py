"""O(log n) operations on sorted arrays.

This module provides efficient binary search operations for tail mass computation,
quantile extraction, and range slicing on pre-sorted arrays.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def tail_mass(x_sorted: NDArray[np.floating], threshold: float) -> float:
    """Compute P(x <= threshold) via binary search.

    Args:
        x_sorted: Pre-sorted array of values (ascending order).
        threshold: Value to compute cumulative probability up to.

    Returns:
        Fraction of values less than or equal to threshold.
    """
    n = len(x_sorted)
    if n == 0:
        return 0.0
    count = np.searchsorted(x_sorted, threshold, side="right")
    return count / n


def quantile_by_index(
    x_sorted: NDArray[np.floating], q: float | ArrayLike
) -> float | NDArray[np.floating]:
    """Get quantile value(s) by index interpolation.

    Uses floor-based indexing: index = floor(q * (n-1)).

    Args:
        x_sorted: Pre-sorted array of values (ascending order).
        q: Quantile(s) to compute, in range [0, 1]. Can be scalar or array.

    Returns:
        Quantile value(s) from the sorted array. Shape matches input q.
    """
    n = len(x_sorted)
    q_arr = np.asarray(q)
    scalar_input = q_arr.ndim == 0

    # Compute indices: q * (n-1), then floor to get integer index
    indices = np.floor(q_arr * (n - 1)).astype(int)

    # Clip to valid range
    indices = np.clip(indices, 0, n - 1)

    result = x_sorted[indices]

    if scalar_input:
        return float(result)
    return result


def slice_by_range(x_sorted: NDArray[np.floating], lo: float, hi: float) -> tuple[int, int]:
    """Return (lo_idx, hi_idx) for open interval (lo, hi).

    The returned indices can be used for slicing: x_sorted[lo_idx:hi_idx]
    will contain all values strictly between lo and hi.

    Args:
        x_sorted: Pre-sorted array of values (ascending order).
        lo: Lower bound (exclusive).
        hi: Upper bound (exclusive).

    Returns:
        Tuple of (lo_idx, hi_idx) for slicing the array.
    """
    # Find first index > lo (start of open interval)
    lo_idx = int(np.searchsorted(x_sorted, lo, side="right"))

    # Find first index >= hi (end of open interval)
    hi_idx = int(np.searchsorted(x_sorted, hi, side="left"))

    return lo_idx, hi_idx
