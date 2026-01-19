"""Synthetic data generators for testing fitqc.

This module provides functions to generate synthetic parameter distributions
for testing and demonstrating fitqc's QC capabilities.

Why This Module Exists
----------------------
To properly test QC algorithms, we need:
1. Clean distributions (normal, log-normal) to verify no false positives
2. Distributions with injected artifacts to verify detection works
3. Edge cases like signed log-normal that naturally have mass near zero

The generators use NumPy's random Generator API with explicit seeds for
reproducibility. All functions accept a `seed` parameter for deterministic output.

Generator Types
---------------
1. **Basic distributions**: normal, lognormal, uniform
   - For testing false positive rates (should NOT trigger detection)

2. **Signed log-normal**: Values that can be positive or negative
   - Critical edge case: naturally has mass near zero, but it's BROAD
   - Must NOT trigger false spike detection

3. **Artifact injection**: Add boundary pileup or x0 stickiness
   - For testing true positive rates (SHOULD trigger detection)

Usage
-----
```python
from fitqc.synth import generate_normal, generate_with_x0_spike

# Clean data - should not trigger QC
clean = generate_normal(n=10000, loc=5.0, scale=2.0, seed=42)

# Data with x0 stickiness - should trigger interior QC
sticky = generate_with_x0_spike(n=10000, x0=5.0, spike_frac=0.05, seed=42)
```
"""

import numpy as np
from numpy.typing import NDArray


def generate_normal(
    n: int,
    loc: float = 0.0,
    scale: float = 1.0,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate samples from a normal distribution.

    Args:
        n: Number of samples
        loc: Mean of the distribution
        scale: Standard deviation
        seed: Random seed for reproducibility

    Returns:
        Array of n samples from N(loc, scale²)
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc, scale, size=n)


def generate_lognormal(
    n: int,
    mean: float = 0.0,
    sigma: float = 1.0,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate samples from a log-normal distribution.

    The log-normal distribution is exp(N(mean, sigma²)), so values are always positive.

    Args:
        n: Number of samples
        mean: Mean of the underlying normal distribution (not the log-normal mean)
        sigma: Standard deviation of the underlying normal
        seed: Random seed for reproducibility

    Returns:
        Array of n positive samples
    """
    rng = np.random.default_rng(seed)
    return rng.lognormal(mean, sigma, size=n)


def generate_uniform(
    n: int,
    low: float = 0.0,
    high: float = 1.0,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate samples from a uniform distribution.

    Args:
        n: Number of samples
        low: Lower bound
        high: Upper bound
        seed: Random seed for reproducibility

    Returns:
        Array of n samples from U(low, high)
    """
    rng = np.random.default_rng(seed)
    return rng.uniform(low, high, size=n)


def generate_signed_lognormal(
    n: int,
    mu: float = 0.0,
    sigma: float = 1.0,
    sign_prob: float = 0.5,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate samples from a signed log-normal distribution.

    This distribution has support on (-∞, +∞) and naturally concentrates mass
    near zero (from both sides). It's a critical test case because:
    - It has high density near zero (like x0 stickiness would)
    - But the mass is BROAD, not a narrow spike
    - QC should NOT flag this as stickiness

    The distribution is: sign * exp(N(mu, sigma²)) where sign is ±1 with
    probability sign_prob for positive.

    Args:
        n: Number of samples
        mu: Mean of the underlying normal (controls magnitude scale)
        sigma: Std dev of the underlying normal (controls spread)
        sign_prob: Probability of positive sign (0.5 = symmetric)
        seed: Random seed for reproducibility

    Returns:
        Array of n samples, roughly half positive and half negative
    """
    rng = np.random.default_rng(seed)

    # Generate magnitudes from log-normal
    magnitudes = rng.lognormal(mu, sigma, size=n)

    # Generate random signs
    signs = np.where(rng.random(n) < sign_prob, 1.0, -1.0)

    return signs * magnitudes


def generate_with_x0_spike(
    n: int,
    x0: float,
    L: float,
    U: float,
    spike_frac: float = 0.05,
    base_distribution: str = "uniform",
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate data with an artificial x0 stickiness spike.

    Creates a base distribution with a fraction of samples exactly at x0,
    simulating optimizer stickiness at the initial guess.

    Args:
        n: Total number of samples
        x0: Initial guess value (spike location)
        L: Lower bound for base distribution
        U: Upper bound for base distribution
        spike_frac: Fraction of samples to place at x0 (default 5%)
        base_distribution: "uniform" or "normal" for non-spike samples
        seed: Random seed for reproducibility

    Returns:
        Array with spike_frac of samples at x0, rest from base distribution
    """
    rng = np.random.default_rng(seed)

    # Number of spike samples
    n_spike = int(n * spike_frac)
    n_base = n - n_spike

    # Generate base distribution
    if base_distribution == "uniform":
        base = rng.uniform(L, U, size=n_base)
    elif base_distribution == "normal":
        # Normal centered between bounds
        center = (L + U) / 2
        scale = (U - L) / 6  # ~99.7% within bounds
        base = rng.normal(center, scale, size=n_base)
        base = np.clip(base, L, U)
    else:
        raise ValueError(f"Unknown base_distribution: {base_distribution}")

    # Create spike at x0
    spike = np.full(n_spike, x0)

    # Combine and shuffle
    result = np.concatenate([base, spike])
    rng.shuffle(result)

    return result


def generate_with_boundary_pileup(
    n: int,
    L: float,
    U: float,
    lower_pileup_frac: float = 0.0,
    upper_pileup_frac: float = 0.0,
    pileup_width: float = 0.01,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Generate data with artificial boundary pileup.

    Creates a uniform base distribution with extra mass near the boundaries,
    simulating optimizer stickiness at parameter bounds.

    Args:
        n: Total number of samples
        L: Lower bound
        U: Upper bound
        lower_pileup_frac: Fraction of samples to pile up near L
        upper_pileup_frac: Fraction of samples to pile up near U
        pileup_width: How close to boundary (as fraction of range)
        seed: Random seed for reproducibility

    Returns:
        Array with pileup near boundaries
    """
    rng = np.random.default_rng(seed)

    range_width = U - L

    # Calculate sample counts
    n_lower = int(n * lower_pileup_frac)
    n_upper = int(n * upper_pileup_frac)
    n_base = n - n_lower - n_upper

    # Generate base uniform distribution
    base = rng.uniform(L, U, size=n_base)

    # Generate pileup near lower bound
    lower_pileup = rng.uniform(L, L + range_width * pileup_width, size=n_lower)

    # Generate pileup near upper bound
    upper_pileup = rng.uniform(U - range_width * pileup_width, U, size=n_upper)

    # Combine and shuffle
    result = np.concatenate([base, lower_pileup, upper_pileup])
    rng.shuffle(result)

    return result
