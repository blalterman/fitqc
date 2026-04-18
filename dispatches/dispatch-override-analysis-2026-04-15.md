Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

# Dispatch: Analyze Boundary QC With All Overrides Disabled

**Generated:** 2026-04-15
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Work type:** analysis

## Scope

Write and run `analyze_overrides.py` — a standalone analysis script that
compares boundary QC detection across 12 PPA12 datasets with the M1/M2/M3
override mechanisms enabled vs disabled. The primary comparison is all
overrides ON (current behavior) vs all overrides OFF. Supplementary
per-override traces identify which mechanism fires on which dataset.

**Do NOT modify any source code.** This is analysis-only. The script lives
at repo root and is not committed to the package.

## Motivation

`run_boundary_qc` has three override mechanisms (M1, M2, M3) that modify
detection values between the core pipeline stages (iterative Kneedle elbow
detection and `_check_excess_mass` validation). The commit that introduced
them (`7f8d7a7`) documents 5 datasets with remaining detection problems:

- e_dv_ap: lower bound not detected
- e_dv_pp: over-filtering on boundary
- np1: upper bound not caught
- w_const: over-trims lower boundary
- np2: over-trims lower boundary (removes half the skewed distribution)

This analysis determines whether the core pipeline handles the data without
the overrides, and whether each override improves or degrades detection.

## Read First

1. `src/fitqc/boundary.py:682-739` -- M1 (spread-pileup propagation) and M3
   (broad-pileup fallback). Both modify `t_lo_raw`/`t_hi_raw` before
   `_check_excess_mass`. M1 can cascade into M3.
2. `src/fitqc/boundary.py:857-906` -- M2 (delta-function propagation).
   Modifies `t_lo_star`/`t_hi_star` after `_check_excess_mass`.
3. `src/fitqc/boundary.py:455-523` -- `_check_excess_mass`. The validation
   step between raw elbows and final thresholds. Predates the overrides.
4. `src/fitqc/report.py:309-320` -- downstream consumption. `t_lo_star`
   controls the filtering mask: `stuck_at_lower = u < t_lo_star`.
5. `tests/conftest.py:338-360` -- `all_ppa12_test_cases` fixture. The 12
   dataset names and loading pattern.

## Key Decisions

- DECIDED: Comparison must use `refine_transition=True` throughout.
  `refine_transition=False` disables overrides but ALSO changes the elbow
  detection algorithm (single-pass vs iterative Kneedle), invalidating the
  comparison.
- DECIDED: Correctness judged against empirical pileup fractions computed
  from the raw data distributions, NOT against test metadata
  (`fitqc_test.expected_*_stickiness`), which may have been calibrated with
  overrides enabled.
- DECIDED: Analysis-only. No production code changes.
- PROPOSED: Disable overrides via source-line excision
  (`inspect.getsource` + block removal by comment markers + `exec`). This
  is one approach — the executing session may choose a different mechanism
  if it finds a cleaner way.

## Technical Context

### Override locations and cascade

The overrides are inline blocks within `run_boundary_qc`, not separate
functions. They fire only when `refine_transition=True` and
`use_quantile_analysis=True`.

```
_refine_elbow_iteratively() -> t_lo_raw, q_lo_elbow
    |
[M1] if t_raw < 0.005 AND q_ref > 0.005 AND mass(0) < 1e-10 AND t < 0.2*q
     -> t_raw := max(q_ref/2, 0.005)
    |  (M1 can enable M3 by raising t_raw above 0.005)
[M3] if t_raw >= 0.005 AND mass_ratio < 3.0 AND t_broad > 3*t_raw
     -> t_raw := t_broad
    |
_check_excess_mass(t_raw_modified) -> detected, t_star
    |
[M2] if detected AND t_star < 0.005 AND t_raw < 1e-10 AND mass(0) > 0.01
     -> t_star := mass(0)
```

M1 and M2 are mutually exclusive (M1 guard: mass(0) < 1e-10; M2 guard:
mass(0) > 0.01).

Interior QC (`run_interior_qc`) has zero imports from the boundary module
and is not affected by these overrides.

### Source-line excision block boundaries

If using `inspect.getsource` approach, block boundaries relative to the
function source:

| Block | Start marker | End marker |
|-------|-------------|------------|
| M1 | `"# Mechanism 1 \u2014"` | Line before `"# Mechanism 3 \u2014"` |
| M3 | `"# Mechanism 3 \u2014"` | Line before first `"kneedle_elbows_lower = elbows_lower"` |
| M2 | `"# Mechanism 2 \u2014"` | Line before last `"return BoundaryResult("` |

Removing blocks is safe: M1/M3 only modify `t_lo_raw`/`t_hi_raw` (already
set by `_refine_elbow_iteratively`), M2 only modifies `t_lo_star`/`t_hi_star`
(already set by `_check_excess_mass`). No variable declarations are lost.

### Configurations

| Config | Label | Blocks removed |
|--------|-------|----------------|
| 1 | `all_on` | None (current behavior) |
| 2 | `no_m1` | M1 only |
| 3 | `no_m3` | M3 only |
| 4 | `no_m2` | M2 only |
| 5 | `all_off` | M1 + M3 + M2 |

### Data loading

- Parquet: `pq.read_table(path)["values"].to_numpy()` (pyarrow, NOT pandas)
- Metadata: `json.load()` for L, U, name
- Pattern: `tests/conftest.py:338-360`
- Config: `BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')`
- Datasets: `A_He`, `e_dv_ap`, `e_dv_pp`, `np1`, `np2`, `vx`, `vy`, `vz`,
  `w_const`, `e_w_p1`, `e_w_p2`, `e_w_a`

### Empirical ground truth

For each dataset, compute from raw data (not metadata):
- `u = (x - L) / (U - L)` (normalized positions)
- Lower delta fraction: `np.mean(u < 1e-10)`
- Upper delta fraction: `np.mean(u > 1 - 1e-10)`
- Mass curves from `BoundaryResult` (identical across configs)

## Acceptance Criteria

- [ ] `analyze_overrides.py` runs without error on all 12 datasets x 5 configs
- [ ] Per-dataset trace shows: empirical pileup fractions, all 5 configs' values
      (`t_lo_raw`, `t_lo_star`, `t_hi_raw`, `t_hi_star`, detection booleans)
- [ ] Trace identifies which overrides fire on which datasets with before/after values
- [ ] Summary compares all_on vs all_off: which datasets change, direction of change
- [ ] Verdict per override: improved, degraded, or neutral vs empirical truth
- [ ] Report saved to `~/Documents/Obsidian-Vault/fitqc/reports/override-analysis-2026-04-15.md`
- [ ] No files in `src/` modified
- [ ] Existing tests pass

## Anti-Patterns

- Do NOT modify `boundary.py` or any source code -- analysis-only
- Do NOT use `refine_transition=False` as baseline -- changes the detection
  algorithm, not just the overrides
- Do NOT trust test metadata `fitqc_test.expected_*_stickiness` as ground
  truth -- may be calibrated with overrides enabled (circular)
- Do NOT use pandas for parquet reading -- use pyarrow (`pq.read_table`)

## Verification

```bash
# Prerequisites — expected output: "Prerequisites OK"
python -c "
from fitqc import run_boundary_qc, BoundaryConfig
import numpy as np
rng = np.random.default_rng(42)
x = np.concatenate([rng.uniform(0, 0.01, 500), rng.uniform(0, 10, 9500)])
config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')
result = run_boundary_qc(x, 0.0, 10.0, config)
assert result.t_lo_raw is not None
assert result.kneedle_elbows_lower is not None
print('Prerequisites OK')
"

# Analysis script runs — expected output: per-dataset traces + summary table
python analyze_overrides.py

# No source changes — expected output: empty (no lines printed)
git diff --name-only src/

# Tests pass — expected output: "N passed" with exit code 0
python -m pytest tests/ -x -q
```
