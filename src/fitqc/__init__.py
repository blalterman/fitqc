"""fitqc: Fit QC diagnostics for detecting optimizer stickiness.

This package provides tools to detect two types of optimizer stickiness in fitted parameters:
1. Boundary stickiness - samples stuck near parameter bounds (L/U)
2. Initial-guess stickiness - samples stuck near x0 (optimizer fallback)

Quick Start
-----------
::

    from fitqc import run_qc, QCSpec

    # Define your parameter specification
    spec = QCSpec(
        param_names=["alpha", "beta"],
        x0={"alpha": 1.0, "beta": 2.0},
        bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},
    )

    # Run QC on your fitted samples
    params = {"alpha": alpha_samples, "beta": beta_samples}
    report, masks = run_qc(params, spec)

    # Filter to good samples
    combined_mask = masks["alpha"] & masks["beta"]
    clean_alpha = params["alpha"][combined_mask]

Modules
-------
config : Dataclass configurations for QC algorithms
interior : Interior QC (x0 stickiness detection)
boundary : Boundary QC (pileup detection)
report : High-level API and JSON serialization
plot : Diagnostic plotting functions
synth : Synthetic data generators for testing
"""

__version__ = "0.1.0"

# Configuration dataclasses
# Core functions
# Result dataclasses
from fitqc.boundary import BoundaryResult, compute_u, run_boundary_qc
from fitqc.config import (
    BoundaryConfig,
    InteriorConfig,
    PlotConfig,
    PrecisionConfig,
    QCSpec,
)
from fitqc.interior import InteriorResult, compute_z, run_interior_qc

# Plotting
from fitqc.plot import plot_boundary_diagnostics, plot_interior_diagnostics

# High-level API
from fitqc.report import QCReport, run_qc

# Synthetic data generators
from fitqc.synth import (
    generate_lognormal,
    generate_normal,
    generate_signed_lognormal,
    generate_uniform,
    generate_with_boundary_pileup,
    generate_with_x0_spike,
)

__all__ = [
    # Configuration
    "BoundaryConfig",
    # Results
    "BoundaryResult",
    "InteriorConfig",
    "InteriorResult",
    "PlotConfig",
    "PrecisionConfig",
    "QCReport",
    "QCSpec",
    # Version
    "__version__",
    # Core functions
    "compute_u",
    "compute_z",
    # Synthetic data
    "generate_lognormal",
    "generate_normal",
    "generate_signed_lognormal",
    "generate_uniform",
    "generate_with_boundary_pileup",
    "generate_with_x0_spike",
    # Plotting
    "plot_boundary_diagnostics",
    "plot_interior_diagnostics",
    "run_boundary_qc",
    "run_interior_qc",
    # High-level API
    "run_qc",
]
