"""Shared utilities for quantile-based stickiness detection.

This module contains functions shared between boundary and interior detection
when using the multi-curve quantile analysis approach.
"""

import numpy as np


def _aggregate_elbows_median(
    elbows: list[float | None],
    min_agreement_frac: float = 0.5
) -> float | None:
    """Aggregate multiple elbow estimates via median.

    This function takes elbow estimates from multiple quantile curves and
    returns a robust central estimate. It works for both boundary tolerances
    (linear scale) and interior epsilons (log scale).

    Args:
        elbows: List of elbow estimates, where None indicates no elbow was found
            for that quantile curve.
        min_agreement_frac: Minimum fraction of non-None elbows required for
            a valid aggregate. If fewer than this fraction of elbows are valid,
            returns None.

    Returns:
        The median of valid elbows if sufficient agreement exists, otherwise None.

    Examples:
        >>> # Good agreement across 5 quantile curves
        >>> elbows = [0.010, 0.011, 0.009, 0.010, 0.011]
        >>> _aggregate_elbows_median(elbows)
        0.010

        >>> # Some quantiles didn't find elbows, but enough did
        >>> elbows = [0.010, None, 0.009, 0.010, None]
        >>> _aggregate_elbows_median(elbows, min_agreement_frac=0.5)
        0.010

        >>> # Insufficient agreement - too many None values
        >>> elbows = [0.010, None, None, None, 0.011]
        >>> _aggregate_elbows_median(elbows, min_agreement_frac=0.5)
        None

        >>> # All None - no elbows found
        >>> elbows = [None, None, None]
        >>> _aggregate_elbows_median(elbows)
        None
    """
    # Filter out None values to get valid elbows
    valid_elbows = [e for e in elbows if e is not None]

    # Check if we have sufficient agreement
    if len(valid_elbows) < min_agreement_frac * len(elbows):
        return None  # Insufficient agreement

    # Return median of valid elbows
    return float(np.median(valid_elbows))
