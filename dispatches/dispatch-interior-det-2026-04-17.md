# Dispatch: Evaluate interior detection against CSV ground truth

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** code + analysis
**CPM task:** `calibration-interior-det` (parallel to B/C; no internal predecessor)

## Scope

Run `src/fitqc/interior.py` detection on all 12 PPA12 parameters and
tabulate results against the `interior` column of
`dispatches/ground_truth_validation.csv`. Produce an interior
factorial-style verdict table. For each disagreement between detection
and CSV, decide whether to update the CSV note (if re-inspection
confirms detection) or flag it as an algorithmic false
negative/positive for a follow-up fix task.

## Motivation

The boundary path (B + C + E) only catches pileups at bounds.
Interior stickiness (e.g., `vy` at `x0=0`, `e_dv_pp` at `x0=0`) requires
the interior path. The plan flagged 8 parameters with interior
stickiness in the CSV, four marked "my guess"
(`vy`/`vz`/`e_w_p1`/`e_w_p2`). Commit `14595de` already confirmed `vy`
has an interior sticky at `x0=0`, so the CSV state may differ from what
the plan described — read it fresh.

## Read First

1. `dispatches/ground_truth_validation.csv` — the `interior` column.
   Read it **fresh**; the "my guess" annotations in the `note` column
   may have been updated since commit `519f8cd` (plan) as of
   `14595de` and possibly later.
2. `src/fitqc/interior.py` — the detection code under evaluation.
3. `src/fitqc/config.py` — `InteriorConfig` defaults (relevant
   thresholds / windows).
4. `dispatches/boundary_inspection.pdf` — contains histograms of all
   12 parameters; useful for visual re-inspection of "my guess"
   disagreements.
5. `analyze_overrides.py` — pattern reference for how the boundary
   factorial was structured (D does not need ablation; just
   detection vs CSV on all 12 parameters).

## Investigation protocol

1. **Harness**: write a diagnostic script (placed in `dispatches/`, e.g.
   `dispatches/diagnose_interior_12.py`) that runs `interior.py`
   detection on each of the 12 PPA12 parameters using production config
   and records `(parameter, interior_detected, x0_detected,
   tolerance_detected)`.
2. **Tabulate** against CSV `interior` column:
   - CSV value numeric + detection says interior → TP
   - CSV value numeric + detection says no interior → FN
   - CSV value None + detection says interior → FP
   - CSV value None + detection says no interior → TN
3. **For each disagreement**:
   - If CSV entry is tagged "my guess", re-inspect the histogram in
     `boundary_inspection.pdf`. If the histogram supports detection,
     update the CSV note (and only the note; do not flip the numeric
     value without user confirmation). If the histogram supports the
     CSV, flag detection as an algorithmic miss.
   - If CSV entry is NOT tagged "my guess", flag the disagreement as a
     suspected algorithmic FN/FP and record it for a follow-up fix task.
4. **Results table** committed as
   `dispatches/interior-validation-2026-04-XX.md` with verdict per
   parameter.

## Acceptance Criteria

- [ ] Diagnostic script committed at
      `dispatches/diagnose_interior_12.py` and runnable (`python
      dispatches/diagnose_interior_12.py` produces the 12-row table to
      stdout).
- [ ] Results table committed at
      `dispatches/interior-validation-2026-04-XX.md` with TP/FN/FP/TN
      counts and per-parameter verdict.
- [ ] Every "my guess" entry in the CSV `interior` column either:
      (a) confirmed (note remains or is sharpened), or
      (b) flagged as a suspected algorithmic FN requiring follow-up.
- [ ] CSV numeric values in the `interior` column are **not** modified
      without explicit user approval; only the `note` column may be
      sharpened.
- [ ] No changes to `src/fitqc/interior.py` or config as part of this
      task (D evaluates; fixes are separate).
- [ ] `python -m pytest tests/ -q` passes with same count as pre-work
      baseline (422 with the 3 quantile-test deselects).

## Anti-Patterns

- Do NOT flip a "my guess" CSV interior value (numeric ↔ None) without
  explicit user approval after visual re-inspection. The note is
  editable; the numeric value is not.
- Do NOT tune `interior.py` thresholds to match CSV. Any production
  change belongs in a separate task with dialectic.
- Do NOT assume the "my guess" set is still
  `{vy, vz, e_w_p1, e_w_p2}` — read the CSV fresh; commit `14595de`
  and later may have changed that set.
- Do NOT compute interior detection using boundary code paths
  (`_compute_quantile_curves_boundary`, `_check_excess_mass`). Use
  `interior.py` only.

## Verification

Pre-work:

```bash
cd /Users/balterma/observatories/code/fitqc
python -c "import pandas as pd; df = pd.read_csv('dispatches/ground_truth_validation.csv'); print(df[['parameter','interior','note']].to_string())"
# Expected: 12 parameters; note current 'my guess' entries and any
# interior numeric values.
```

On completion:

```bash
test -f dispatches/diagnose_interior_12.py && echo "script: OK"
test -f dispatches/interior-validation-2026-04-*.md && echo "results: OK"
python dispatches/diagnose_interior_12.py | head -20
# Expected: 12 rows; interior_detected / x0_detected / tolerance_detected

python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
# Expected: 422 passed
```

## Out of Scope

- Fixing any algorithmic FN/FP in `interior.py` (separate follow-up).
- Boundary `t_star` validation (C: `calibration-tolerance-mags`).
- End-to-end mask application (E: `calibration-end-to-end`).

## Open Items

- POSSIBLY STALE: plan L120 enumerates "my guess" as
  `{vy, vz, e_w_p1, e_w_p2}`. Commit `14595de` removed at least `vy`
  from that set. Treat the CSV as authoritative.
- PROPOSED: The diagnostic script can reuse patterns from
  `dispatches/diagnose_boundary_24.py` (B's diagnostic tool, already in
  the tree). Adapt rather than reinvent.
