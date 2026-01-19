# Stickiness Wrapper Implementation Plan

## Executive Summary

Add a thin wrapper `detect_stickiness()` function that provides a unified API over the existing `run_interior_qc()` and `run_boundary_qc()` functions. The existing modules remain unchanged.

**Branch:** Create fresh from `main`
**Approach:** Test-first development
**Risk level:** Low (additive change, no modifications to existing code)

---

## Design Decisions (Approved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Extract to util.py | No | Commonalities already factored into `sortedops.py` and `selection.py` |
| Unified StickinessResult | No | Keep `InteriorResult` and `BoundaryResult`; return union type |
| Wrap compute_z/compute_u | No | Keep in original modules; wrapper provides detection only |
| Primary API | Yes | `detect_stickiness()` is primary; existing functions are "advanced" |
| Mode options | `"interior"`, `"lower"`, `"upper"`, `"all"` | Full flexibility |
| Scale options | `float \| "std" \| "iqr" \| "range"` | User choice for unbounded parameters |

---

## File Changes

| File | Action | Lines (est.) |
|------|--------|--------------|
| `src/fitqc/stickiness.py` | CREATE | ~200 |
| `src/fitqc/__init__.py` | MODIFY | +2 |
| `tests/test_stickiness.py` | CREATE | ~600 |

**Files NOT modified:**
- `src/fitqc/interior.py` — unchanged
- `src/fitqc/boundary.py` — unchanged
- `tests/test_interior.py` — unchanged
- `tests/test_boundary.py` — unchanged
- All other existing files — unchanged

---

## API Specification

### Function Signature

```python
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
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `x` | `NDArray[np.floating]` | Fitted parameter values from optimization runs |
| `ref` | `float` | Reference point (x0 for interior, L for lower, U for upper) |
| `L` | `float \| None` | Lower bound; None if unbounded below |
| `U` | `float \| None` | Upper bound; None if unbounded above |
| `mode` | `Literal[...]` | Which stickiness check: `"interior"`, `"lower"`, `"upper"`, `"all"` |
| `scale` | `float \| str \| None` | Normalization scale for unbounded parameters |
| `interior_config` | `InteriorConfig \| None` | Config for interior detection |
| `boundary_config` | `BoundaryConfig \| None` | Config for boundary detection |

### Return Types by Mode

| Mode | Return Type | Description |
|------|-------------|-------------|
| `"interior"` | `InteriorResult` | x0 stickiness detection result |
| `"lower"` | `BoundaryResult` | Lower boundary result (upper fields None) |
| `"upper"` | `BoundaryResult` | Upper boundary result (lower fields None) |
| `"all"` | `tuple[InteriorResult, BoundaryResult]` | Both results |

### Scale Parameter Behavior

| Condition | Scale Behavior |
|-----------|----------------|
| Both L and U provided | Scale parameter ignored; uses `max(ref - L, U - ref)` |
| Either L or U is None | Scale parameter **required** |
| `scale=float` | Uses provided value directly |
| `scale="std"` | Uses `np.std(x)` |
| `scale="iqr"` | Uses `np.percentile(x, 75) - np.percentile(x, 25)` |
| `scale="range"` | Uses `np.max(x) - np.min(x)` |

### Validation Rules

| Condition | Error |
|-----------|-------|
| `mode="interior"` and (L is None or U is None) and scale is None | `ValueError` |
| `mode="lower"` and L is None | `ValueError` |
| `mode="upper"` and U is None | `ValueError` |
| `scale <= 0` | `ValueError` |
| `scale` is invalid string | `ValueError` |
| `mode` is invalid | `ValueError` |

---

## Implementation Structure

### `src/fitqc/stickiness.py`

```python
"""Unified stickiness detection API.

This module provides detect_stickiness(), a single entry point for detecting
optimizer stickiness at reference points (initial guess x0, lower bound L,
upper bound U).

The function wraps:
- run_interior_qc() from fitqc.interior
- run_boundary_qc() from fitqc.boundary

These underlying modules remain unchanged and available for advanced use.
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
    """Compute normalization scale for distance calculations."""
    # Implementation details in test file


def _validate_mode_bounds(
    mode: str,
    L: float | None,
    U: float | None,
    scale: float | str | None,
) -> None:
    """Validate mode is compatible with provided bounds."""
    # Implementation details in test file


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

    [Full docstring - see test file for expected behavior]
    """
    # 1. Validate mode
    # 2. Validate bounds for mode
    # 3. Dispatch based on mode
    # 4. For lower/upper, filter BoundaryResult fields
    # 5. Return appropriate type
```

### `src/fitqc/__init__.py` Changes

Add to imports:
```python
from fitqc.stickiness import detect_stickiness
```

Add to `__all__`:
```python
"detect_stickiness",
```

---

## Execution Order

1. **Create branch from main**
2. **Write tests** (`tests/test_stickiness.py`)
3. **User approves tests**
4. **Implement** (`src/fitqc/stickiness.py`)
5. **Update exports** (`src/fitqc/__init__.py`)
6. **Run all tests** — new tests pass, existing tests still pass
7. **Run ruff** — fix linting issues
8. **Commit and push**

---

## Verification Criteria

```bash
# All tests pass (101 existing + ~59 new)
pytest -v

# Linting passes
ruff check .
ruff format --check .

# Example still works
python examples/run_array_qc.py

# New function importable
python -c "from fitqc import detect_stickiness; print(detect_stickiness)"
```

---

## Propositions Reference

See conversation history for detailed For/Against/Decision propositions on:
- Question 0: Extract to util.py
- Question 1: Unified StickinessResult
- Question 2: Wrap compute_z/compute_u
- Question 3: Primary API
- Question 4: Mode options
- Question 5: Unbounded handling
- Question 5b: Scale options
