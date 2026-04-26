Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent. Do not read feedback or dispatch documents yet --
partial reads will distort context before we have a plan. Once I approve your
plan, then execute.

---

# Dispatch: Boundary Pipeline Seam Tests and Data Structure Fixes

**Generated:** 2026-04-15
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Work type:** software

## Scope

The boundary QC detection pipeline (`run_boundary_qc` in `boundary.py`) has 10
integration seams where data is handed off between stages. Most are untested.
Three changes:

1. **Extract `check_excess_mass()`** from inline closure (boundary.py:762) to
   module-level `_check_excess_mass()` with explicit parameters. No behavior change.
   This makes the function independently testable.

2. **Store raw Kneedle elbows in `BoundaryResult`** (boundary.py:420). The raw
   elbows and raw median are currently computed and discarded. Add fields:
   `kneedle_elbows_lower`, `kneedle_elbows_upper`, `t_lo_raw`, `t_hi_raw`,
   `kneedle_quantile_grid`. All optional with `None` default.

3. **Write ~30 integration seam tests** in `tests/test_boundary_seams.py` covering
   all 10 pipeline seams. Test specifications are in the plan file.

## Motivation

The boundary pipeline computes raw Kneedle elbows, aggregates them via median,
then passes the median through `check_excess_mass()` which can silently replace
it with a near-zero grid point for any median < 0.005. Three override mechanisms
(M1, M2, M3) can further transform the value. The raw elbows and raw median are
discarded -- never stored in the result object.

The `quantile_elbows` field in `BoundaryResult` stores CDF-inverse interpolations,
not the actual Kneedle elbows used for detection.

Without raw elbows stored and without seam tests, it is impossible to verify that
the pipeline preserves or intentionally transforms detection values, and impossible
to calibrate data cut thresholds.

## Read First

1. `~/.claude/plans/effervescent-exploring-whale.md` -- complete seam map, per-seam
   test specifications, and execution order
2. `src/fitqc/boundary.py:420-443` -- `BoundaryResult` dataclass (add new fields)
3. `src/fitqc/boundary.py:762-812` -- `check_excess_mass` closure (extract this)
4. `src/fitqc/boundary.py:598-655` -- M1 and M3 override mechanisms (untested)
5. `src/fitqc/boundary.py:823-866` -- M2 override mechanism (untested)
6. `src/fitqc/boundary.py:668-670` -- where raw median is computed and discarded
7. `src/fitqc/boundary.py:148-218` -- `_compute_quantile_curves_boundary` (returns
   single-element elbows list despite "multi-curve" naming)
8. `src/fitqc/_quantile_utils.py:10-67` -- `_aggregate_elbows_median` (no-op on
   length-1 list, special case at line 55)

## Acceptance Criteria

### Extract check_excess_mass
- [ ] `_check_excess_mass` is a module-level function in `boundary.py` with explicit
      parameters: `t_star`, `mass_curve`, `tol_grid`, `pileup_threshold`, `excess_ratio`
- [ ] `run_boundary_qc` calls the extracted function (no behavior change)
- [ ] Full test suite passes

### Store raw elbows in BoundaryResult
- [ ] `BoundaryResult` has new fields: `kneedle_elbows_lower`, `kneedle_elbows_upper`,
      `t_lo_raw`, `t_hi_raw`, `kneedle_quantile_grid`
- [ ] All new fields are optional with `None` default (backward compatible)
- [ ] `run_boundary_qc` populates these fields from the actual elbows computed at
      lines 586-596 (refine path) and 659-665 (non-refine path)
- [ ] Full test suite passes

### Integration seam tests
- [ ] New file `tests/test_boundary_seams.py` with ~30 tests
- [ ] Coverage for all 10 seams per the plan's seam map
- [ ] All new tests pass
- [ ] No regressions in existing tests

## Anti-Patterns

- Do NOT change detection logic or override mechanisms -- this dispatch is about
  observability and testability, not behavior changes
- Do NOT modify `InteriorResult` or `run_interior_qc` -- the interior pipeline is
  structurally clean
- Do NOT modify plot functions -- visualization fixes are a separate dispatch
- Do NOT add fields to `BoundaryResult` beyond what's specified

## Verification

```bash
# Extraction preserved behavior
python -m pytest tests/ -x -q

# New fields populated
python -c "
from fitqc import run_boundary_qc, BoundaryConfig
import numpy as np
rng = np.random.default_rng(42)
x = np.concatenate([rng.uniform(0, 0.01, 500), rng.uniform(0, 10, 9500)])
config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')
result = run_boundary_qc(x, 0.0, 10.0, config)
print(f't_lo_raw: {result.t_lo_raw}')
print(f't_lo_star: {result.t_lo_star}')
print(f'kneedle_elbows_lower: {result.kneedle_elbows_lower}')
print(f'kneedle_quantile_grid: {result.kneedle_quantile_grid}')
assert result.t_lo_raw is not None, 'raw median not stored'
assert result.kneedle_elbows_lower is not None, 'raw elbows not stored'
print('PASS')
"

# Seam tests
python -m pytest tests/test_boundary_seams.py -v

# Full regression
python -m pytest tests/ -x -q
```
