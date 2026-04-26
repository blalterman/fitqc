Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent. Do not read feedback or dispatch documents yet --
partial reads will distort context before we have a plan. Once I approve your
plan, then execute.

---

# Dispatch: Visualization Fixes and Real Data Diagnostics

**Generated:** 2026-04-15
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Work type:** software

## Prerequisites

These must pass before starting:
```bash
python -m pytest tests/test_boundary_seams.py -v
python -c "from fitqc.boundary import BoundaryResult; assert hasattr(BoundaryResult, 'kneedle_elbows_lower')"
```

## Data Model Context

The boundary Kneedle algorithm runs ONCE on the (quantile, tolerance) curve and
finds ONE elbow point in quantile-space, which maps to one tolerance value.

- `result.kneedle_elbows_lower` — **1-element list** (one tolerance value)
- `result.kneedle_quantile_grid` — **26-element tuple** (the quantile levels)
- `result.quantile_elbows["lower"]` — **dict of {quantile: tolerance}** with one
  entry per quantile level. These are CDF-inverse values (the curve Kneedle
  operated on), not per-quantile Kneedle elbows.
- `result.t_lo_raw` — raw detection result (single Kneedle elbow tolerance,
  possibly overridden by M1/M3 before `check_excess_mass`)
- `result.t_lo_star` — validated threshold (after `check_excess_mass` + M2)

## Scope

Three changes to the visualization layer:

1. **Fix boundary elbow overlay plot** (`src/fitqc/plot.py`, `_plot_boundary_panel`):
   - **Dots:** CDF-inverse curve from `result.quantile_elbows["lower"]`, labeled
     "tolerance at quantile"
   - **Elbow marker:** distinct marker on the curve where Kneedle found the elbow.
     Derive quantile position: `q = np.interp(t_lo_raw, tol_values, quantile_keys)`
   - **Horizontal line for `t_lo_raw`** labeled "raw threshold"
   - **Horizontal line for `t_lo_star`** labeled "validated threshold", distinct
     color/style from raw line
   - Backward compat: if `t_lo_raw` is None, fall back to current single-line
     behavior with a warning label

2. **Fix color contrast** (`src/fitqc/plot.py`):
   - `plot_interior_diagnostics` (line 30): mass curve `"#2166ac"`, elbow `"#d62728"`,
     spike `"#ff7f0e"` — replacing `cmap(0.5)`/`cmap(0.8)`/`cmap(0.9)`
   - `plot_boundary_diagnostics` (line 125): colormap normalization floor 0.0 → 0.15

3. **Generate diagnostics for real PPA12 data** (new `generate_quantile_diagnostics.py`):
   - 6 datasets: A_He, e_dv_pp, e_dv_ap, np1, np2, w_const
   - Data: `tests/data/{name}_test_sample.parquet` + `{name}_test_metadata.json`
   - Config: `BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode="progressive")`
   - 7 figure types per dataset to `figures/{name}/`
   - Console output: raw threshold vs validated threshold per boundary
   - Patterns: `plot_ppa12_interior_combined.py` (data loading), `examples/quantile_viz_workflow.py` (plot calls)

## Motivation

Boundary elbow plots show CDF-inverse values labeled as Kneedle elbows, with
the validated threshold labeled as the median. The raw detection threshold is
not shown. Mass curve lines in diagnostics plots are invisible (pale yellow on
white). No diagnostic plots exist for real PPA12 data.

## Read First

1. `src/fitqc/plot.py:1660-1728` -- `_plot_boundary_panel` (main fix target)
2. `src/fitqc/plot.py:30-122` -- `plot_interior_diagnostics` (color fix)
3. `src/fitqc/plot.py:125-322` -- `plot_boundary_diagnostics` (color fix)
4. `src/fitqc/boundary.py:440-452` -- `BoundaryResult` fields
5. `examples/quantile_viz_workflow.py` -- pattern for calling diagnostic plot functions
6. `plot_ppa12_interior_combined.py` -- pattern for loading PPA12 data

## Acceptance Criteria

### Fix boundary elbow overlay plot
- [ ] Dots show CDF-inverse curve from `result.quantile_elbows["lower"/"upper"]`,
      labeled "tolerance at quantile"
- [ ] Distinct marker on the curve at the Kneedle elbow location
- [ ] Horizontal line for `t_lo_raw` labeled "raw threshold"
- [ ] Horizontal line for `t_lo_star` labeled "validated threshold"
- [ ] Backward compatible when `t_lo_raw` is None
- [ ] Existing plot tests pass

### Fix color contrast
- [ ] `plot_interior_diagnostics` uses explicit hex colors, not `cmap()` calls
- [ ] `plot_boundary_diagnostics` colormap floor at 0.15
- [ ] Regenerated `quantile_viz_interior_diagnostics.png` has visible mass curve line

### Real data diagnostics
- [ ] `generate_quantile_diagnostics.py` at repo root
- [ ] 7 figure types for each of 6 datasets in `figures/{name}/`
- [ ] Console output shows raw threshold vs validated threshold per boundary
- [ ] No blank panels or crashes

## Anti-Patterns

- Do NOT change detection logic in `boundary.py` or `interior.py`
- Do NOT change PlotConfig defaults -- use explicit colors in plot functions
- Do NOT commit generated PNG files

## Verification

```bash
# Prerequisites
python -m pytest tests/test_boundary_seams.py -v
python -c "from fitqc.boundary import BoundaryResult; assert hasattr(BoundaryResult, 'kneedle_elbows_lower')"

# Regenerate synthetic example
python examples/quantile_viz_workflow.py
# Inspect: quantile_viz_interior_diagnostics.png (blue mass curve line visible?)
# Inspect: quantile_viz_boundary_elbows.png (CDF-inverse curve with elbow marker, two horizontal lines?)

# Generate real data diagnostics
python generate_quantile_diagnostics.py
ls figures/A_He/ figures/np2/ figures/w_const/
# Inspect: figures/A_He/A_He_boundary_elbows.png
# Inspect: figures/np2/np2_histogram_overlays.png

# Regression
python -m pytest tests/ -x -q
```
