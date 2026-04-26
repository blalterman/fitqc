# Dispatch: Prototype derivative-based t_star refinement

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** prototype + analysis
**CPM task:** `calibration-derivative-refine` (new; depends on
`calibration-grid-resolution`)

## Scope

On the refined tolerance grid from `calibration-grid-resolution`,
compute `dM/dt` numerically on each parameter's boundary mass
curves. Find the `dM/dt → 1` crossing as a candidate `t_star`
refinement. Compare against Kneedle's `t_star` from B/C1. Report a
dialectic decision among:
(a) Leave Kneedle in place.
(b) Replace Kneedle with the derivative method.
(c) Use derivative as a diagnostic flag (warn when Kneedle's
    `t_star` has `dM/dt` far from 1).

## Motivation

User proposed derivative-based detection. Reasoning showed
derivatives inherit grid-resolution problems, so this task is gated
on `calibration-grid-resolution` landing. Once the grid resolves
pileup widths 1e-7 to 5e-4, `dM/dt` is a well-defined signal:
uniform data has `dM/dt = 1`; pileup regions have `dM/dt > 1`; the
transition is principled rather than heuristic.

## Prerequisites (verify before starting)

- [ ] `calibration-grid-resolution` committed; `analyze_overrides.py`
      regenerated with the new grid; TP=24/24 preserved. If not,
      STOP and escalate.

## Read First

1. `dispatches/override_review_results.md` — post-C1 `t_star` values
   from Kneedle on the refined grid.
2. `src/fitqc/boundary.py:_compute_quantile_curves_boundary` —
   produces the mass curve used for derivative computation.
3. `dispatches/boundary-fn-diagnostics-2026-04-17.md` — true pileup
   widths (reference truth for magnitude comparison).
4. `dispatches/ground_truth_validation.csv` — scale hints.
5. `dispatches/tolerance-validation-2026-04-XX.md` (if Task C
   committed) — per-parameter magnitude classifications.

## Investigation protocol

1. **Prototype script** `dispatches/prototype_dmdt_t_star.py`:
   - Run `run_boundary_qc` on all 12 parameters under current
     production config.
   - Extract the mass curve and grid from `BoundaryResult`.
   - Compute `dM/dt` via central differences in log(t) space, with
     an optional Gaussian smoothing kernel (CLI flag, default
     σ=0.1 in log10(t)).
   - Find the first `dM/dt ≤ 1 + tol_eps` crossing (moving from
     high density to uniform); report as `t_star_deriv`.
2. **Comparison table** per (parameter, side):
   `t_star_kneedle` vs `t_star_deriv` vs CSV scale, with log-delta
   and "closer-to-truth" winner.
3. **Sensitivity sweep** on smoothing kernel σ (e.g. 0.05, 0.1, 0.2).
   Report how the winner count shifts.
4. **Dialectic** per CLAUDE.md: Leave | Replace | Diagnostic, with
   FOR/AGAINST/COUNTEREXAMPLE tied to the table.
5. **Results doc** `dispatches/derivative-refinement-results-2026-04-XX.md`.
6. If dialectic concludes Replace or Diagnostic, scope a follow-up
   task (do not execute here).

## Acceptance Criteria

- [ ] Prototype script committed; runnable via
      `python dispatches/prototype_dmdt_t_star.py`.
- [ ] Per-parameter comparison table in results doc with
      `t_star_kneedle`, `t_star_deriv`, CSV scale, log-delta, winner.
- [ ] Sensitivity sweep reported for ≥3 smoothing kernel values.
- [ ] Dialectic decision recorded; follow-up task scoped if needed.
- [ ] No changes to `src/fitqc/boundary.py`. Prototype only.
- [ ] `python -m pytest tests/ -q` unchanged from the C1 baseline.

## Anti-Patterns

- Do NOT change production detection logic. This is prototype only.
- Do NOT start before `calibration-grid-resolution` lands; derivative
  on a coarse grid is uninformative.
- Do NOT tune the smoothing kernel width to match CSV magnitudes.
  Report the sensitivity; don't fit to the target.
- Do NOT commit the results doc and the prototype script in separate
  commits — the results must be paired with the script version that
  produced them.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
python dispatches/prototype_dmdt_t_star.py
test -f dispatches/derivative-refinement-results-2026-04-*.md
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
```

## Out of Scope

- Production detection changes (scoped separately if dialectic
  recommends it).
- Interior derivative-based detection (separate investigation).
- Changes to boundary config defaults.

## Open Items

- PROPOSED: smoothing kernel width (Gaussian σ in log10(t) space).
  Sweep during prototype; dialectic selects.
- PROPOSED: derivative threshold (`dM/dt ≤ 1 + tol_eps`). Start with
  tol_eps = 0.2; sensitivity sweep.
