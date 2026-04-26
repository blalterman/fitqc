Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent. Do not read feedback or dispatch documents yet --
partial reads will distort context before we have a plan. Once I approve your
plan, then execute.

---

**Read:** `dispatches/dispatch-viz-fixes-real-data-2026-04-15.md`

## Prerequisites

```bash
python -m pytest tests/test_boundary_seams.py -v
python -c "from fitqc.boundary import BoundaryResult; assert hasattr(BoundaryResult, 'kneedle_elbows_lower')"
```

## Scope

Fix boundary elbow overlay plot: keep CDF-inverse curve dots (relabel as
"tolerance at quantile"), add elbow marker on the curve (interpolate `t_lo_raw`),
add two horizontal lines (raw threshold and validated threshold). Fix color
contrast in diagnostics plots. Generate all diagnostic figures for real PPA12 data.

Key data model fact: Kneedle runs ONCE on the (quantile, tolerance) curve and
produces ONE elbow. `kneedle_elbows_lower` is a 1-element list.
`quantile_elbows["lower"]` contains per-quantile CDF-inverse values (the curve
Kneedle operated on). The dispatch has a "Data Model Context" section with full
details.

Do NOT remove CDF-inverse dots, change detection logic, or change PlotConfig
defaults.

## Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check
- Use pyarrow (not pandas) for reading parquet
- Do NOT commit generated PNG files

## Verification

```bash
python examples/quantile_viz_workflow.py
python generate_quantile_diagnostics.py
ls figures/A_He/ figures/np2/ figures/w_const/
python -m pytest tests/ -x -q
```
