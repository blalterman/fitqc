"""Configuration dataclasses for fitqc.

This module contains all configuration dataclasses used throughout the package.
No logic, only data definitions.
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

    Attributes:
        eps_log10_min: Minimum log10(eps) for grid search.
        eps_log10_max: Maximum log10(eps) for grid search.
        n_eps: Number of epsilon values in grid.
        n_bins: Number of histogram bins for z-distribution.
        spike_prominence_min: Minimum prominence for spike detection.
        spike_width_max: Maximum width (in bins) for a spike (vs broad distribution).
        spike_location_max: Maximum z-location for a spike to be considered near x0.
    """

    eps_log10_min: float = -12
    eps_log10_max: float = -3
    n_eps: int = 50
    n_bins: int = 100
    spike_prominence_min: float = 10.0
    spike_width_max: float = 15.0
    spike_location_max: float = 0.1


@dataclass
class BoundaryConfig:
    """Configuration for boundary (L/U stickiness) QC.

    Attributes:
        tol_min: Minimum tolerance for boundary detection.
        tol_max: Maximum tolerance for boundary detection.
        n_tols: Number of tolerance values in grid.
        quantile_grid: Quantile values for elbow detection curves.
    """

    tol_min: float = 0.0
    tol_max: float = 0.05
    n_tols: int = 41
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
