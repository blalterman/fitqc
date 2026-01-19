# Stickiness Wrapper Implementation Prompt

## Task

Implement a thin wrapper `detect_stickiness()` function that provides a unified API over the existing `run_interior_qc()` and `run_boundary_qc()` functions.

**Key constraint:** Do NOT modify existing modules. This is an additive change only.

---

## Context

Read these files before starting:
- `plans/stickiness-wrapper-plan.md` — Implementation plan and API specification
- `plans/stickiness-wrapper-tests.md` — Complete test specifications

---

## Execution Steps

### Step 1: Create Branch

```bash
git checkout main
git pull origin main
git checkout -b claude/stickiness-wrapper-<session-id>
```

### Step 2: Write Tests First

Create `tests/test_stickiness.py` with ALL tests from `plans/stickiness-wrapper-tests.md`.

**Test requirements:**
- Non-trivial assertions (verify type, shape, dtype, values)
- No `assert X is not None` without additional checks
- Use `np.testing.assert_array_equal` for array comparisons
- Use `pytest.approx` for float comparisons
- Use `pytest.raises` for error testing

**Test file structure:**
```python
"""Tests for the detect_stickiness unified API."""

import numpy as np
import pytest

# Import after implementation exists
# from fitqc.stickiness import detect_stickiness
# from fitqc.interior import InteriorResult, run_interior_qc
# from fitqc.boundary import BoundaryResult, run_boundary_qc
# from fitqc.config import InteriorConfig, BoundaryConfig


class TestStickinessModuleStructure:
    """Verify module exports and function signatures."""
    ...

class TestModeDispatch:
    """Verify correct function is called for each mode."""
    ...

# Continue with all test classes from test plan
```

**STOP after writing tests. Get user approval before proceeding.**

### Step 3: Implement Wrapper

Create `src/fitqc/stickiness.py`:

```python
"""Unified stickiness detection API.

This module provides detect_stickiness(), a single entry point for detecting
optimizer stickiness at reference points (initial guess x0, lower bound L,
upper bound U).

The function wraps:
- run_interior_qc() from fitqc.interior
- run_boundary_qc() from fitqc.boundary

These underlying modules remain unchanged and available for advanced use.

Design Decisions
----------------
1. Thin wrapper: Delegates to existing functions, no duplicate logic
2. Union return type: Returns InteriorResult | BoundaryResult, not unified type
3. Scale parameter: Enables unbounded parameter analysis
4. Mode parameter: Provides granular control (interior/lower/upper/all)
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import NDArray

from fitqc.boundary import BoundaryResult, run_boundary_qc
from fitqc.config import BoundaryConfig, InteriorConfig
from fitqc.interior import InteriorResult, run_interior_qc


def _compute_effective_scale(
    x: NDArray[np.floating],
    ref: float,
    L: float | None,
    U: float | None,
    scale: float | Literal["std", "iqr", "range"] | None,
) -> float:
    """Compute normalization scale for distance calculations.

    When bounds are available, uses max(ref - L, U - ref).
    When bounds are missing, uses the scale parameter.

    Parameters
    ----------
    x : array
        Data values (used for data-driven scales)
    ref : float
        Reference point
    L, U : float or None
        Bounds
    scale : float, str, or None
        Scale specification

    Returns
    -------
    float
        Positive scale value

    Raises
    ------
    ValueError
        If scale is required but not provided, or invalid
    """
    # If both bounds available, use bounds-derived scale
    if L is not None and U is not None:
        return max(ref - L, U - ref)

    # Otherwise, scale is required
    if scale is None:
        raise ValueError(
            "scale parameter required when L or U is None. "
            "Use scale='std', 'iqr', 'range', or provide a positive float."
        )

    # Handle numeric scale
    if isinstance(scale, (int, float)):
        if scale <= 0:
            raise ValueError(f"scale must be positive, got {scale}")
        return float(scale)

    # Handle string scale methods
    if scale == "std":
        s = float(np.std(x))
    elif scale == "iqr":
        q75, q25 = np.percentile(x, [75, 25])
        s = float(q75 - q25)
    elif scale == "range":
        s = float(np.max(x) - np.min(x))
    else:
        raise ValueError(
            f"Unknown scale method: '{scale}'. "
            "Use 'std', 'iqr', 'range', or a positive float."
        )

    if s <= 0:
        raise ValueError(
            f"Computed scale is non-positive ({s}). "
            "Data may be constant or scale method inappropriate."
        )

    return s


def _validate_mode_bounds(
    mode: str,
    L: float | None,
    U: float | None,
    scale: float | str | None,
) -> None:
    """Validate mode is compatible with provided bounds.

    Raises
    ------
    ValueError
        If mode requires bounds that are not provided
    """
    if mode == "interior":
        if (L is None or U is None) and scale is None:
            raise ValueError(
                "mode='interior' requires both L and U, or scale parameter. "
                "For unbounded parameters, provide scale='std', 'iqr', 'range', or a float."
            )
    elif mode == "lower":
        if L is None:
            raise ValueError("mode='lower' requires L to be specified.")
    elif mode == "upper":
        if U is None:
            raise ValueError("mode='upper' requires U to be specified.")
    elif mode == "all":
        # All mode needs at least partial bounds for boundary checks
        if L is None and U is None:
            if scale is None:
                raise ValueError(
                    "mode='all' requires at least one bound (L or U), "
                    "or scale parameter for interior check."
                )
    elif mode not in ("interior", "lower", "upper", "all"):
        raise ValueError(
            f"Invalid mode: '{mode}'. "
            "Use 'interior', 'lower', 'upper', or 'all'."
        )


def detect_stickiness(
    x: NDArray[np.floating],
    ref: float,
    L: float | None,
    U: float | None,
    mode: Literal["interior", "lower", "upper", "all"] = "all",
    scale: float | Literal["std", "iqr", "range"] | None = None,
    interior_config: InteriorConfig | None = None,
    boundary_config: BoundaryConfig | None = None,
) -> InteriorResult | BoundaryResult | tuple[InteriorResult, BoundaryResult]:
    """
    Detect optimizer stickiness at reference points.

    This is the primary API for stickiness detection. It wraps run_interior_qc()
    and run_boundary_qc() with a unified interface.

    Parameters
    ----------
    x : NDArray[np.floating]
        Fitted parameter values from optimization runs.
    ref : float
        Reference point to check for stickiness.
        - For mode='interior': the initial guess x0
        - For mode='lower': typically L (the lower bound)
        - For mode='upper': typically U (the upper bound)
    L : float or None
        Lower bound of parameter range. None if unbounded below.
    U : float or None
        Upper bound of parameter range. None if unbounded above.
    mode : {'interior', 'lower', 'upper', 'all'}, default 'all'
        Which stickiness check to perform:
        - 'interior': Check for stickiness at x0 (initial guess)
        - 'lower': Check for pileup at lower bound
        - 'upper': Check for pileup at upper bound
        - 'all': Perform all checks
    scale : float or {'std', 'iqr', 'range'} or None, default None
        Normalization scale for unbounded parameters.
        - Required when L or U is None for interior mode
        - float: Use this value directly
        - 'std': Use np.std(x)
        - 'iqr': Use interquartile range
        - 'range': Use max(x) - min(x)
        - None: Use bounds-derived scale (requires both L and U)
    interior_config : InteriorConfig or None
        Configuration for interior detection. Uses defaults if None.
    boundary_config : BoundaryConfig or None
        Configuration for boundary detection. Uses defaults if None.

    Returns
    -------
    InteriorResult or BoundaryResult or tuple[InteriorResult, BoundaryResult]
        - mode='interior': InteriorResult
        - mode='lower' or 'upper': BoundaryResult (with other direction's fields as None)
        - mode='all': tuple of (InteriorResult, BoundaryResult)

    Raises
    ------
    ValueError
        If mode is invalid, or required bounds/scale are missing.

    Examples
    --------
    Basic usage with bounds:

    >>> x = np.random.uniform(0, 10, size=1000)
    >>> result = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="interior")
    >>> result.spike_detected
    False

    All checks at once:

    >>> interior, boundary = detect_stickiness(x, ref=5.0, L=0.0, U=10.0, mode="all")

    Unbounded parameter with scale:

    >>> result = detect_stickiness(x, ref=5.0, L=None, U=None, mode="interior", scale="std")
    """
    # Validate mode and bounds
    _validate_mode_bounds(mode, L, U, scale)

    # Dispatch based on mode
    if mode == "interior":
        return _run_interior(x, ref, L, U, scale, interior_config)
    elif mode == "lower":
        return _run_lower(x, L, U, boundary_config)
    elif mode == "upper":
        return _run_upper(x, L, U, boundary_config)
    elif mode == "all":
        return _run_all(x, ref, L, U, scale, interior_config, boundary_config)
    else:
        # Should not reach here due to validation, but be defensive
        raise ValueError(f"Invalid mode: {mode}")


def _run_interior(
    x: NDArray[np.floating],
    ref: float,
    L: float | None,
    U: float | None,
    scale: float | str | None,
    config: InteriorConfig | None,
) -> InteriorResult:
    """Run interior (x0 stickiness) check."""
    # Compute effective scale
    effective_scale = _compute_effective_scale(x, ref, L, U, scale)

    # If bounds are missing, we need to create synthetic bounds for run_interior_qc
    # The scale determines the effective range
    if L is None or U is None:
        # Create symmetric bounds around ref based on scale
        effective_L = ref - effective_scale
        effective_U = ref + effective_scale
    else:
        effective_L = L
        effective_U = U

    return run_interior_qc(x, x0=ref, L=effective_L, U=effective_U, config=config)


def _run_lower(
    x: NDArray[np.floating],
    L: float,
    U: float | None,
    config: BoundaryConfig | None,
) -> BoundaryResult:
    """Run lower boundary check only."""
    # If U is None, use a large value that won't affect lower boundary detection
    effective_U = U if U is not None else float(np.max(x) + np.std(x))

    full_result = run_boundary_qc(x, L=L, U=effective_U, config=config)

    # Return result with upper fields nulled
    return BoundaryResult(
        lower_pileup_detected=full_result.lower_pileup_detected,
        upper_pileup_detected=False,
        t_lo_star=full_result.t_lo_star,
        t_hi_star=None,
        tol_grid=full_result.tol_grid,
        lower_mass_curve=full_result.lower_mass_curve,
        upper_mass_curve=None,
    )


def _run_upper(
    x: NDArray[np.floating],
    L: float | None,
    U: float,
    config: BoundaryConfig | None,
) -> BoundaryResult:
    """Run upper boundary check only."""
    # If L is None, use a small value that won't affect upper boundary detection
    effective_L = L if L is not None else float(np.min(x) - np.std(x))

    full_result = run_boundary_qc(x, L=effective_L, U=U, config=config)

    # Return result with lower fields nulled
    return BoundaryResult(
        lower_pileup_detected=False,
        upper_pileup_detected=full_result.upper_pileup_detected,
        t_lo_star=None,
        t_hi_star=full_result.t_hi_star,
        tol_grid=full_result.tol_grid,
        lower_mass_curve=None,
        upper_mass_curve=full_result.upper_mass_curve,
    )


def _run_all(
    x: NDArray[np.floating],
    ref: float,
    L: float | None,
    U: float | None,
    scale: float | str | None,
    interior_config: InteriorConfig | None,
    boundary_config: BoundaryConfig | None,
) -> tuple[InteriorResult, BoundaryResult]:
    """Run all stickiness checks."""
    # Run interior check
    interior_result = _run_interior(x, ref, L, U, scale, interior_config)

    # Run boundary check (need at least one bound)
    if L is not None or U is not None:
        effective_L = L if L is not None else float(np.min(x) - np.std(x))
        effective_U = U if U is not None else float(np.max(x) + np.std(x))
        boundary_result = run_boundary_qc(x, L=effective_L, U=effective_U, config=boundary_config)
    else:
        # No bounds at all - can't do meaningful boundary check
        # Create a placeholder result
        boundary_result = BoundaryResult(
            lower_pileup_detected=False,
            upper_pileup_detected=False,
            t_lo_star=None,
            t_hi_star=None,
            tol_grid=np.array([]),
            lower_mass_curve=np.array([]),
            upper_mass_curve=np.array([]),
        )

    return (interior_result, boundary_result)
```

### Step 4: Update Exports

Edit `src/fitqc/__init__.py`:

Add to imports:
```python
from fitqc.stickiness import detect_stickiness
```

Add to `__all__`:
```python
"detect_stickiness",
```

### Step 5: Verify

```bash
# Run all tests
pytest -v

# Check linting
ruff check .
ruff format --check .

# Verify example still works
python examples/run_array_qc.py

# Verify new function importable
python -c "from fitqc import detect_stickiness; print(detect_stickiness)"
```

### Step 6: Commit

```bash
git add tests/test_stickiness.py
git commit -m "test(stickiness): add tests for detect_stickiness unified API

Add comprehensive tests for the new detect_stickiness() wrapper function.
Tests cover: mode dispatch, scale handling, validation errors, detection
correctness, array properties, and edge cases.

Co-Authored-By: Claude <noreply@anthropic.com>"

git add src/fitqc/stickiness.py src/fitqc/__init__.py
git commit -m "feat(stickiness): add detect_stickiness unified API

Add thin wrapper providing unified interface for stickiness detection:
- Mode parameter: 'interior', 'lower', 'upper', 'all'
- Scale parameter: enables unbounded parameter analysis
- Returns union type: InteriorResult | BoundaryResult

Existing interior.py and boundary.py modules unchanged.

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin claude/stickiness-wrapper-<session-id>
```

---

## Verification Checklist

- [ ] All 101 existing tests still pass
- [ ] All ~51 new tests pass
- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] `python examples/run_array_qc.py` works
- [ ] `from fitqc import detect_stickiness` works
- [ ] No modifications to `interior.py` or `boundary.py`
- [ ] No modifications to existing test files

---

## Design Propositions Summary

The following decisions were made with For/Against analysis:

| Decision | Choice | Key Rationale |
|----------|--------|---------------|
| Extract to util.py | No | Already factored into sortedops.py, selection.py |
| Unified StickinessResult | No | Preserves type safety, domain semantics |
| Wrap compute_z/compute_u | No | Implementation details, not public API |
| Primary API | Yes | Simpler onboarding for new users |
| Mode options | 4 modes | Granular control, symmetric API |
| Scale options | 4 methods | User choice based on data characteristics |

See conversation history for detailed propositions.
