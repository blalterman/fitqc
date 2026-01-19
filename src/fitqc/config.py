"""Configuration dataclasses for fitqc.

This module contains all configuration dataclasses used throughout the package.
No logic, only data definitions.

Overview: What fitqc Detects
----------------------------
fitqc detects two types of "optimizer stickiness" in fitted parameters:

1. **Boundary Stickiness**: Samples stuck at parameter bounds (L or U).
   When an optimizer hits a bound, it can't move further. If many fits end up
   at bounds, something is wrong (bad bounds, bad model, or pathological data).

   Detection: Compute u = (x - L) / (U - L) ∈ [0, 1]. Samples stuck at L have
   u ≈ 0; stuck at U have u ≈ 1. Look for "pileup" (excess mass) near 0 or 1.

2. **Initial-Guess Stickiness**: Samples stuck at the initial guess (x0).
   Some optimizers return x0 when they fail to converge or find a better solution.
   This creates a "spike" in the distribution at exactly x0.

   Detection: Compute z = |x - x0| / max(x0 - L, U - x0) ∈ [0, 1]. Samples at
   x0 have z = 0. Look for a spike (narrow peak with high prominence) at z ≈ 0.

The challenge is distinguishing real stickiness from natural variation:
- A normal distribution centered at 0 naturally has mass near 0
- Uniform data naturally has some samples near bounds
- We use spike detection (prominence + width) and elbow detection to separate
  genuine artifacts from statistical fluctuations.

Configuration Philosophy
------------------------
All tunable parameters are exposed via dataclasses. Defaults are chosen to work
well for typical physics/ML parameter fitting scenarios (thousands of samples,
parameters bounded by physical constraints). Advanced users can tune for their
specific distributions.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PrecisionConfig:
    """Configuration for floating-point precision handling.

    Attributes:
        precision_mode: How to determine comparison dtype.
            - "auto": Infer from input array dtype
            - "float32": Force float32 precision
            - "float64": Force float64 precision
        compare_mode: How to handle value comparison.
            - "quantize_to_storage": Round to storage dtype before comparison
            - "analysis_dtype": Compare in analysis dtype directly
    """

    precision_mode: Literal["auto", "float32", "float64"] = "auto"
    compare_mode: Literal["quantize_to_storage", "analysis_dtype"] = "quantize_to_storage"


@dataclass
class InteriorConfig:
    """Configuration for interior (x0 stickiness) QC.

    The Algorithm
    -------------
    1. Transform x → z = |x - x0| / max(x0 - L, U - x0), so z=0 at x0
    2. For each eps in logspace(eps_log10_min, eps_log10_max, n_eps):
       - Compute P(z < eps) = "fraction of samples within eps of x0"
    3. Build histogram of z-values
    4. Use scipy.signal.find_peaks to detect spikes in the histogram
    5. A spike indicates stickiness if:
       - prominence >= spike_prominence_min (stands out from background)
       - width <= spike_width_max bins (narrow, not a broad distribution)
       - location <= spike_location_max (near z=0, i.e., near x0)
    6. Use elbow detection on the P(z < eps) curve to find eps*

    Why These Defaults
    ------------------
    - eps_log10_min=-12: Below float64 precision at most magnitudes
    - eps_log10_max=-3: 0.1% of range; larger is clearly not "stuck"
    - n_eps=50: Enough resolution for smooth elbow curve
    - n_bins=100: Balance between resolution and noise in histogram
    - spike_prominence_min=10: Peak must be 10 counts above background
    - spike_width_max=15: Max 15% of histogram width (100 bins)
    - spike_location_max=0.1: Spike must be within 10% of x0

    Critical: Avoiding False Positives
    ----------------------------------
    A signed log-normal distribution centered at 0 has natural mass near 0, but
    it's BROAD, not a spike. The width criterion (spike_width_max) prevents this
    from being flagged as stickiness. A true spike is narrow (few bins); natural
    variation is wide (many bins).
    """

    # Epsilon grid for scanning (in log10 space)
    eps_log10_min: float = -12  # ~ULP for float64, ensures we catch precision-limited cases
    eps_log10_max: float = -3  # 0.1% of normalized range
    n_eps: int = 50  # Number of epsilon values to test

    # Histogram parameters for z-distribution
    n_bins: int = 100  # Bins for histogram of z-values

    # Spike detection criteria (scipy.signal.find_peaks parameters)
    spike_prominence_min: float = 10.0  # Min counts above background to be a "spike"
    spike_width_max: float = 15.0  # Max width in bins; wider = broad distribution, not spike
    spike_location_max: float = 0.1  # Spike must be in first 10% of z-range (near x0)


@dataclass
class BoundaryConfig:
    """Configuration for boundary (L/U stickiness) QC.

    The Algorithm
    -------------
    1. Transform x → u = (x - L) / (U - L), so u=0 at L, u=1 at U
    2. For lower boundary: compute P(u < tol) for each tol in linspace(tol_min, tol_max, n_tols)
    3. For upper boundary: compute P(u > 1-tol) similarly
    4. At each quantile in quantile_grid, find the tolerance where that quantile is reached
    5. Use elbow detection on the (tol, cumulative_fraction) curve to find t_lo*, t_hi*

    Why Quantile Grid?
    ------------------
    Instead of just looking at "fraction within tol of boundary", we look at multiple
    quantiles (1%, 5%, 10%, etc.). This gives multiple curves, each potentially showing
    an elbow. The most robust elbow across quantiles determines the optimal tolerance.

    Why These Defaults
    ------------------
    - tol_min=0.0: Start from the boundary itself
    - tol_max=0.05: 5% of range; beyond this, we're not really "at the boundary"
    - n_tols=41: Gives 0.125% resolution in tolerance
    - quantile_grid: Standard quantiles covering tail (1-10%) and body (25-50%)

    Interpreting Results
    --------------------
    - t_lo* > 0.01: More than expected mass within 1% of lower bound → pileup detected
    - t_hi* > 0.01: Similarly for upper bound
    - Asymmetric t_lo* vs t_hi*: One-sided constraint hitting (common in physics)
    """

    # Tolerance grid for scanning (in normalized [0,1] space)
    tol_min: float = 0.0  # Start from boundary
    tol_max: float = 0.05  # 5% of range is max "boundary region"
    n_tols: int = 41  # Number of tolerance values (0.0, 0.00125, ..., 0.05)

    # Quantiles to track for elbow detection
    quantile_grid: tuple[float, ...] = field(default_factory=lambda: (0.01, 0.05, 0.10, 0.25, 0.50))


@dataclass
class PlotConfig:
    """Configuration for diagnostic plots.

    Attributes:
        cmap: Matplotlib colormap name.
        dpi: Figure resolution.
        include_log_abs_panel: Whether to include log-magnitude panel in boundary plots.
        figsize_interior: Figure size for interior diagnostics.
        figsize_boundary: Figure size for boundary diagnostics.
    """

    cmap: str = "Spectral_r"
    dpi: int = 300
    include_log_abs_panel: bool = True
    figsize_interior: tuple[float, float] = (12, 8)
    figsize_boundary: tuple[float, float] = (14, 10)


@dataclass
class QCSpec:
    """Specification for a multi-parameter QC run.

    Attributes:
        param_names: List of parameter names to analyze.
        x0: Initial guess values for each parameter.
        bounds: (lower, upper) bounds for each parameter.
    """

    param_names: list[str]
    x0: dict[str, float]
    bounds: dict[str, tuple[float, float]]

    def __post_init__(self) -> None:
        """Validate that x0 and bounds contain all param_names."""
        for name in self.param_names:
            if name not in self.x0:
                raise ValueError(f"Missing x0 for parameter: {name}")
            if name not in self.bounds:
                raise ValueError(f"Missing bounds for parameter: {name}")
