"""Floating-point precision utilities for comparing fit values at appropriate resolution.

This module provides tools to handle floating-point precision when comparing
fitted parameter values, particularly for detecting optimizer stickiness.

Why This Module Exists
----------------------
When detecting if fitted parameters are "stuck" at initial guesses (x0), we need
to define what "equal to x0" means. This is surprisingly subtle:

1. **Storage vs Analysis Precision**: Data might be stored as float32 (common in
   HDF5, parquet) but analyzed as float64. A value that looks "exactly equal" to
   x0 in float32 might differ by ~1e-7 in float64. We must compare at the
   appropriate precision.

2. **Magnitude-Dependent Resolution**: Floating-point spacing (ULP) varies with
   magnitude. Near 1.0, float64 can distinguish values ~2e-16 apart. Near 1e6,
   only ~1e-10 apart. Our "stickiness threshold" must account for this.

3. **Never Hardcode Epsilon**: Machine epsilon (2.2e-16 for float64, 1.2e-7 for
   float32) should ALWAYS come from `np.finfo(dtype).eps`. Hardcoding breaks
   when dtypes change or on non-standard platforms.

Key Concepts
------------
- **ULP (Unit in Last Place)**: The spacing between adjacent floating-point
  numbers at a given value. `ulp_at(1.0, float64) = eps ≈ 2.2e-16`.
  `ulp_at(1e6, float64) ≈ 1.2e-10`. Use `np.spacing()` to compute.

- **Effective dtype**: The dtype to use for comparisons. "auto" uses the array's
  native dtype. Override when you know data was originally a different precision.

- **eps_from_ulp**: Converts ULP at x0 to a relative threshold in [0,1] space
  (normalized by parameter range U-L). This is the minimum distinguishable
  distance from x0 in normalized coordinates.

Example
-------
If x0=1000.0, L=0, U=2000, and data is float32:
- ULP at 1000 in float32 ≈ 6e-5
- eps = ulp / (U-L) = 6e-5 / 2000 = 3e-8
- Any sample within 3e-8 (normalized) of x0 could be "stuck" due to precision
"""

from typing import Literal

import numpy as np
from numpy.typing import DTypeLike, NDArray

PrecisionMode = Literal["auto", "float32", "float64"]


def effective_dtype(x: NDArray[np.floating], precision_mode: PrecisionMode) -> type[np.floating]:
    """Determine the comparison dtype based on array dtype and precision mode.

    Parameters
    ----------
    x : NDArray[np.floating]
        Input array to determine dtype from.
    precision_mode : PrecisionMode
        Mode for precision selection:
        - "auto": Use the array's native dtype
        - "float32": Force float32 precision
        - "float64": Force float64 precision

    Returns
    -------
    type[np.floating]
        The effective dtype to use for comparisons (np.float32 or np.float64).
    """
    if precision_mode == "auto":
        return x.dtype.type
    elif precision_mode == "float32":
        return np.float32
    elif precision_mode == "float64":
        return np.float64
    else:
        msg = f"Invalid precision_mode: {precision_mode}. Must be 'auto', 'float32', or 'float64'."
        raise ValueError(msg)


def ulp_at(val: float, dtype: DTypeLike) -> float:
    """Compute the unit in last place (ULP) at a given value.

    The ULP is the spacing between adjacent floating-point numbers at the
    given value. This uses np.spacing() which returns the distance to the
    next larger representable floating-point value.

    Parameters
    ----------
    val : float
        The value at which to compute the ULP.
    dtype : DTypeLike
        The floating-point dtype (np.float32 or np.float64).

    Returns
    -------
    float
        The ULP at the given value for the specified dtype.
    """
    # Convert to the target dtype to get spacing at that precision
    val_typed = np.array(val, dtype=dtype)
    return float(np.spacing(val_typed))


def quantize_scalar(val: float, dtype: DTypeLike) -> float:
    """Round a scalar value to the precision of the specified dtype.

    This function casts the value to the target dtype and back to float64,
    effectively quantizing it to the representable values of that dtype.

    Parameters
    ----------
    val : float
        The value to quantize.
    dtype : DTypeLike
        The target dtype for quantization (np.float32 or np.float64).

    Returns
    -------
    float
        The quantized value (as float64).
    """
    return float(np.array(val, dtype=dtype))


def eps_from_ulp(x0: float, L: float, U: float, dtype: DTypeLike, mult: int = 1) -> float:
    """Compute an epsilon threshold from ULP scaled by the parameter range.

    This computes a relative tolerance based on the ULP at x0, normalized
    by the parameter range (U - L), and optionally scaled by a multiplier.

    Parameters
    ----------
    x0 : float
        The reference value (typically initial guess or center point).
    L : float
        Lower bound of the parameter range.
    U : float
        Upper bound of the parameter range.
    dtype : DTypeLike
        The floating-point dtype for ULP calculation.
    mult : int, optional
        Multiplier for the epsilon (default: 1).

    Returns
    -------
    float
        The computed epsilon threshold: ulp_at(x0, dtype) / (U - L) * mult
    """
    ulp = ulp_at(x0, dtype)
    param_range = U - L
    return ulp / param_range * mult
