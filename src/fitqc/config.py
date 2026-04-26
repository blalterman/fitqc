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

   Detection: Compute ``z = |x - x0| / max(x0 - L, U - x0)`` ∈ [0, 1]. Samples at
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
    **Single-Curve Mode (default):**

    1. Transform x → z = ``|x - x0| / max(x0 - L, U - x0)``, so z=0 at x0
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

    When analyzing multiple curves simultaneously (e.g., from different fits),
    the algorithm computes P(z < eps) for each quantile in quantile_grid.
    The optimal threshold eps* is then determined by finding the median elbow
    across all quantiles, providing a more robust estimate.

    - Spike detection remains INDEPENDENT of quantile analysis
    - Only the threshold estimation (eps*) uses multi-curve median aggregation
    - Requires min_quantile_agreement fraction of quantiles to have valid elbows

    Why These Defaults
    ------------------
    - eps_log10_min=-12: Below float64 precision at most magnitudes
    - eps_log10_max=-3: 0.1% of range; larger is clearly not "stuck"
    - n_eps=50: Enough resolution for smooth elbow curve
    - n_bins=100: Balance between resolution and noise in histogram
    - spike_prominence_min=10: Peak must be 10 counts above background
    - spike_width_max=15: Max 15% of histogram width (100 bins)
    - spike_location_max=0.1: Spike must be within 10% of x0
    - use_quantile_analysis=False: Opt-in for multi-curve analysis
    - quantile_grid: Standard quantiles from 0.1% to 10%
    - min_quantile_agreement=0.5: At least half the quantiles must agree

    Critical: Avoiding False Positives
    ----------------------------------
    A signed log-normal distribution centered at 0 has natural mass near 0, but
    it's BROAD, not a spike. The width criterion (spike_width_max) prevents this
    from being flagged as stickiness. A true spike is narrow (few bins); natural
    variation is wide (many bins).
    """

    # Epsilon grid for scanning (in log10 space)
    eps_log10_min: float = -12  # ~ULP for float64, ensures we catch precision-limited cases
    # e_w_p2 exhibits an upstream float32-precision artifact at eps ~ 1e-8;
    # see dispatches/e-w-p2-precision-note-2026-04-17.md.
    eps_log10_max: float = -3  # 0.1% of normalized range
    n_eps: int = 50  # Number of epsilon values to test

    # Histogram parameters for z-distribution
    n_bins: int = 100  # Bins for histogram of z-values

    # Spike detection criteria (scipy.signal.find_peaks parameters)
    spike_prominence_min: float = 10.0  # Min counts above background to be a "spike"
    spike_width_max: float = 15.0  # Max width in bins; wider = broad distribution, not spike
    spike_location_max: float = 0.1  # Spike must be in first 10% of z-range (near x0)

    # Multi-curve quantile analysis (opt-in)
    use_quantile_analysis: bool = False  # Enable multi-curve robust threshold estimation
    quantile_grid: tuple[float, ...] = field(
        default_factory=lambda: (0.001, 0.005, 0.01, 0.02, 0.05, 0.10)
    )  # Quantiles to analyze for threshold detection
    min_quantile_agreement: float = 0.5  # Minimum fraction of quantiles that must agree


@dataclass
class BoundaryConfig:
    """Configuration for boundary (L/U stickiness) QC.

    The Algorithm
    -------------
    **Single-Curve Mode (default):**
    1. Transform x → u = (x - L) / (U - L), so u=0 at L, u=1 at U
    2. For lower boundary: compute P(u < tol) for each tol in linspace(tol_min, tol_max, n_tols)
    3. For upper boundary: compute P(u > 1-tol) similarly
    4. Use elbow detection on the (tol, cumulative_fraction) curve to find t_lo*, t_hi*

    **Multi-Curve Mode (use_quantile_analysis=True):**
    When analyzing multiple curves simultaneously, the algorithm computes the tolerance
    at which each quantile in quantile_grid is reached. The optimal threshold is then
    determined by finding the median elbow across all quantiles, providing a more robust
    estimate for tight pileups.

    - Median aggregation provides robustness against outlier quantiles
    - Requires min_quantile_agreement fraction of quantiles to have valid elbows
    - Particularly useful for very tight pileups (< 0.5% of range)

    Grid Mode Options
    -----------------
    **uniform** (default): Linear spacing from tol_min to tol_max
    - Good for general-purpose detection
    - Equal resolution across entire tolerance range

    **progressive**: Denser spacing near boundaries, coarser farther out
    - Better for detecting very tight pileups (< 1% of range)
    - Concentrates sampling resolution where pileups typically occur
    - Recommended when you expect tight boundary constraints

    **progressive_log**: Progressive grid plus three log-spaced points
    (1e-7, 1e-6, 1e-5) prepended below the progressive floor of 1e-4.
    - Produces readable log-y mass-curve plots at fine tolerances where
      real pileup widths often live (1e-7 to 5e-4 per PPA12 diagnostics).
    - Superset of "progressive": every progressive tol is present, plus
      three sub-1e-4 points. Does not alter detection for cases the
      progressive grid already handled (verified on the 12 PPA12
      datasets: TP=24/24 preserved).
    - Opt-in, not the default; select when generating diagnostics that
      need fine-scale structure to be visible on log-y.

    Why These Defaults
    ------------------
    - tol_min=0.0: Start from the boundary itself
    - tol_max=0.05: 5% of range; beyond this, we're not really "at the boundary"
    - n_tols=41: Gives 0.125% resolution in tolerance
    - grid_mode="uniform": Works well for most cases
    - use_quantile_analysis=False: Opt-in for multi-curve analysis
    - quantile_grid: Quantiles from 1e-5 up to 0.25. The 1e-5 floor lets
      Kneedle see pileups whose fractional mass is below 5e-4 (np2, vx
      lower, np1 upper). See dispatch-grid-resolution-2026-04-17.md.
    - min_quantile_agreement=0.5: At least half the quantiles must agree

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

    # Grid mode selection
    grid_mode: str = "uniform"  # "uniform", "progressive", or "progressive_log"

    # Multi-curve quantile analysis (opt-in)
    use_quantile_analysis: bool = False  # Enable multi-curve robust threshold estimation
    quantile_grid: tuple[float, ...] = field(
        default_factory=lambda: (
            # 1e-5 .. 5e-4: Sparse pileups below prior floor.
            # Needed so Kneedle can see pileups whose fractional mass is
            # below 5e-4 (e.g. np2 ~3e-5, vx lower ~8e-5, np1 ~5e-5).
            # Without these, tol_at_quantile[0] == tol_grid[0] for sparse
            # pileups and Kneedle misses the transition entirely.
            1e-5,
            3e-5,
            1e-4,
            3e-4,
            # 5e-4 .. 1% of range: Very tight pileups (precision artifacts)
            0.0005,
            0.001,
            0.0015,
            0.002,
            0.0025,
            0.003,
            0.004,
            0.005,
            0.007,
            0.01,
            # 1-2%: A_He transition zone - CRITICAL, dense coverage
            0.011,
            0.012,
            0.013,
            0.015,
            0.017,
            0.02,
            # 2-5%: Moderate pileups
            0.025,
            0.03,
            0.04,
            0.05,
            # 5-25%: Broad distribution tail
            0.06,
            0.08,
            0.10,
            0.15,
            0.20,
            0.25,
        )
    )  # Quantiles for threshold detection (30 points; extends below 5e-4 for sparse pileups)
    min_quantile_agreement: float = 0.5  # Minimum fraction of quantiles that must agree

    # Detection thresholds (Fix 4: Make these configurable)
    pileup_threshold: float = 0.005  # Minimum tolerance to consider as pileup (0.5% of range)
    excess_ratio: float = 1.5  # Mass must be at least N times expected for uniform

    # Iterative refinement (Fix 5)
    refine_transition: bool = False  # Enable iterative Kneedle refinement

    # Sub-grid excess-mass fallback tolerances. Tried in ascending order when
    # the primary Kneedle + check_excess_mass path returns no detection. The
    # smallest tol whose mass exceeds tol * excess_ratio is reported as t_star,
    # so downstream filters apply the tightest cut consistent with the data.
    subgrid_fallback_tols: tuple[float, ...] = field(
        default_factory=lambda: (1e-7, 1e-6, 1e-5, 3e-5, 1e-4, 3e-4)
    )

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        # Validate pileup_threshold
        if not (0.0 <= self.pileup_threshold <= 0.1):
            raise ValueError(f"pileup_threshold must be in [0, 0.1], got {self.pileup_threshold}")

        # Validate excess_ratio
        if self.excess_ratio < 1.0:
            raise ValueError(
                f"excess_ratio must be >= 1.0 (1.0 = uniform baseline), got {self.excess_ratio}"
            )


@dataclass
class PlotConfig:
    """Configuration for diagnostic plots.

    Attributes:
        cmap: Matplotlib colormap name.
        dpi: Figure resolution.
        include_log_abs_panel: Whether to include log-magnitude panel in boundary plots.
        figsize_interior: Figure size for interior diagnostics.
        figsize_boundary: Figure size for boundary diagnostics.
        figsize_tolerance: Figure size for tolerance overlay visualizations.
    """

    cmap: str = "Spectral_r"
    dpi: int = 300
    include_log_abs_panel: bool = True
    figsize_interior: tuple[float, float] = (12, 8)
    figsize_boundary: tuple[float, float] = (14, 10)
    figsize_tolerance: tuple[float, float] = (12, 8)


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
