"""QC report generation and JSON serialization.

This module provides the high-level API for running QC on multiple parameters
and serializing results to JSON for downstream analysis.

Why This Module Exists
----------------------
Scientists often fit many parameters simultaneously (e.g., physics model with
10+ parameters). After fitting thousands of bootstrap/MC samples, they need to:

1. Run QC on ALL parameters efficiently
2. Get a single report summarizing issues across all parameters
3. Build masks to filter out "bad" samples for downstream analysis
4. Serialize results to JSON for reproducibility and sharing

The `run_qc` function provides a one-call API that handles all of this.

Design Decisions
----------------
1. **Dataclass for QCReport**: Simple, typed, introspectable. Scientists can
   access `report.interior_results["param_name"]` directly.

2. **NumpyEncoder for JSON**: NumPy arrays don't serialize to JSON by default.
   We convert arrays to lists and NumPy scalars to Python types for portability.

3. **Mask as boolean array**: The mask indicates "good" samples (True = keep).
   This follows NumPy/pandas convention where masks are used for filtering:
   `good_samples = params["x"][mask]`

4. **Separate interior and boundary results**: These are conceptually different
   failure modes. Interior stickiness (at x0) indicates optimizer failure.
   Boundary stickiness indicates constraint saturation or bad bounds.
"""

import dataclasses
import json
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from fitqc.boundary import BoundaryResult, compute_u, run_boundary_qc
from fitqc.config import BoundaryConfig, InteriorConfig, PrecisionConfig, QCSpec
from fitqc.interior import InteriorResult, compute_z, run_interior_qc


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles NumPy arrays and scalars.

    Why This Exists
    ---------------
    Standard JSON doesn't understand NumPy types. When serializing QC results,
    we have arrays (eps_grid, mass_curve) and NumPy scalars (float64, int64).
    This encoder converts them to Python-native types that JSON understands.

    Conversions:
    - np.ndarray -> list (recursive, handles nested arrays)
    - np.floating (float32, float64, etc.) -> Python float
    - np.integer (int32, int64, etc.) -> Python int
    - np.bool_ -> Python bool

    Usage:
        json.dumps(data, cls=NumpyEncoder)
    """

    def default(self, obj: Any) -> Any:
        """Convert NumPy types to JSON-serializable Python types."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


@dataclass
class QCReport:
    """Aggregated QC results for multiple parameters.

    This dataclass holds the complete QC analysis results for a multi-parameter
    fit. It provides methods to convert to dictionary and JSON for storage
    and downstream analysis.

    Attributes
    ----------
    interior_results : dict[str, InteriorResult]
        Results of x0 stickiness analysis for each parameter.
        Keys are parameter names from spec.param_names.

    boundary_results : dict[str, BoundaryResult]
        Results of boundary pileup analysis for each parameter.
        Keys are parameter names from spec.param_names.

    spec : QCSpec
        The specification used for this QC run, containing param_names,
        x0 values, and bounds. Stored for reproducibility.

    Example
    -------
    ```python
    report, masks = run_qc(params, spec, ...)

    # Check if any parameter has issues
    for name in spec.param_names:
        if report.interior_results[name].spike_detected:
            print(f"{name}: x0 stickiness detected!")
        if report.boundary_results[name].lower_pileup_detected:
            print(f"{name}: lower bound pileup detected!")

    # Save to JSON
    with open("qc_report.json", "w") as f:
        f.write(report.to_json())
    ```
    """

    interior_results: dict[str, InteriorResult]
    boundary_results: dict[str, BoundaryResult]
    spec: QCSpec

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a nested dictionary.

        This uses dataclasses.asdict() for recursive conversion. All nested
        dataclasses (InteriorResult, BoundaryResult, QCSpec) are also converted.

        Returns
        -------
        dict
            Dictionary representation of the report, suitable for further
            processing or conversion to other formats.
        """
        return dataclasses.asdict(self)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize the report to a JSON string.

        Uses NumpyEncoder to handle NumPy arrays and scalars.

        Parameters
        ----------
        indent : int | None, optional
            If provided, pretty-print with this indentation level.
            Default is None (compact output).

        Returns
        -------
        str
            JSON string representation of the report.
        """
        return json.dumps(self.to_dict(), cls=NumpyEncoder, indent=indent)


def run_qc(
    params: dict[str, NDArray[np.floating]],
    spec: QCSpec,
    interior_config: InteriorConfig | None,
    boundary_config: BoundaryConfig | None,
    precision_config: PrecisionConfig | None,
) -> tuple[QCReport, dict[str, NDArray[np.bool_]]]:
    """Run QC analysis on multiple parameters.

    This is the high-level API for running QC on a multi-parameter fit.
    For each parameter, it runs both interior (x0 stickiness) and boundary
    (pileup) analysis, then builds masks indicating "good" samples.

    Parameters
    ----------
    params : dict[str, NDArray[np.floating]]
        Dictionary mapping parameter names to arrays of fitted values.
        Each array should have shape (n_samples,).

    spec : QCSpec
        Specification containing param_names, x0 values, and bounds.
        All keys in params must be in spec.param_names.

    interior_config : InteriorConfig | None
        Configuration for interior QC. If None, uses default InteriorConfig.

    boundary_config : BoundaryConfig | None
        Configuration for boundary QC. If None, uses default BoundaryConfig.

    precision_config : PrecisionConfig | None
        Configuration for floating-point precision. Currently reserved for
        future use in mask computation. If None, uses default behavior.

    Returns
    -------
    tuple[QCReport, dict[str, NDArray[np.bool_]]]
        - QCReport: Aggregated results for all parameters
        - masks: Dictionary mapping parameter names to boolean arrays.
          True = "good" sample (not stuck at x0 or boundary).
          False = "bad" sample (stuck at x0 or boundary).

    Example
    -------
    ```python
    spec = QCSpec(
        param_names=["alpha", "beta"],
        x0={"alpha": 1.0, "beta": 2.0},
        bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},
    )
    params = {"alpha": alpha_samples, "beta": beta_samples}

    report, masks = run_qc(params, spec, None, None, None)

    # Filter to good samples only
    combined_mask = masks["alpha"] & masks["beta"]
    good_alpha = params["alpha"][combined_mask]
    good_beta = params["beta"][combined_mask]
    ```
    """
    # Use default configs if not provided
    if interior_config is None:
        interior_config = InteriorConfig()
    if boundary_config is None:
        boundary_config = BoundaryConfig()

    interior_results: dict[str, InteriorResult] = {}
    boundary_results: dict[str, BoundaryResult] = {}
    masks: dict[str, NDArray[np.bool_]] = {}

    for name in spec.param_names:
        x = params[name]
        x0 = spec.x0[name]
        L, U = spec.bounds[name]

        # Run interior QC (x0 stickiness)
        interior_result = run_interior_qc(
            x=x,
            x0=x0,
            L=L,
            U=U,
            config=interior_config,
        )
        interior_results[name] = interior_result

        # Run boundary QC (pileup detection)
        boundary_result = run_boundary_qc(
            x=x,
            L=L,
            U=U,
            config=boundary_config,
        )
        boundary_results[name] = boundary_result

        # Build mask: True = good sample, False = bad (stuck) sample
        mask = _build_mask(
            x=x,
            x0=x0,
            L=L,
            U=U,
            interior_result=interior_result,
            boundary_result=boundary_result,
        )
        masks[name] = mask

    report = QCReport(
        interior_results=interior_results,
        boundary_results=boundary_results,
        spec=spec,
    )

    return report, masks


def _build_mask(
    x: NDArray[np.floating],
    x0: float,
    L: float,
    U: float,
    interior_result: InteriorResult,
    boundary_result: BoundaryResult,
) -> NDArray[np.bool_]:
    """Build a boolean mask indicating "good" samples.

    A sample is marked as "bad" (False) if:
    1. x0 stickiness detected AND sample is within eps_star of x0
    2. Lower boundary pileup detected AND sample is within t_lo_star of L
    3. Upper boundary pileup detected AND sample is within t_hi_star of U

    Parameters
    ----------
    x : NDArray[np.floating]
        Array of fitted parameter values.
    x0 : float
        Initial guess value.
    L : float
        Lower bound.
    U : float
        Upper bound.
    interior_result : InteriorResult
        Result from interior QC analysis.
    boundary_result : BoundaryResult
        Result from boundary QC analysis.

    Returns
    -------
    NDArray[np.bool_]
        Boolean mask where True = good sample, False = stuck sample.
    """
    n = len(x)
    mask = np.ones(n, dtype=np.bool_)

    # Mark samples stuck at x0
    if interior_result.spike_detected and interior_result.eps_star is not None:
        # Compute z = normalized distance from x0
        z = compute_z(x, x0, L, U)
        stuck_at_x0 = z < interior_result.eps_star
        mask = mask & ~stuck_at_x0

    # Mark samples stuck at lower boundary
    if boundary_result.lower_pileup_detected and boundary_result.t_lo_star is not None:
        # Compute u = normalized position in range
        u = compute_u(x, L, U)
        stuck_at_lower = u < boundary_result.t_lo_star
        mask = mask & ~stuck_at_lower

    # Mark samples stuck at upper boundary
    if boundary_result.upper_pileup_detected and boundary_result.t_hi_star is not None:
        # Compute u = normalized position in range
        u = compute_u(x, L, U)
        stuck_at_upper = (1 - u) < boundary_result.t_hi_star
        mask = mask & ~stuck_at_upper

    return mask
