# Dispatch: Validate t_star magnitudes against raw histograms

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** analysis
**CPM task:** `calibration-tolerance-mags` (depends on `calibration-boundary-fns`)

## Scope

For each of the 24 (parameter, side) detected boundary pileups in the
post-B factorial output, overlay the computed `t_star` on the raw
parameter histogram and validate the cut location is physically
reasonable. Compare against CSV-documented scale hints. Flag any case
where `t_star` is more than ±1 decade off from the visual pileup scale.

## Motivation

Commit `44447a0` raised detection to TP=24/24 on the CSV ground truth,
but "detected" does not imply "cutting at the right place." If `t_star`
is off by a decade, `_build_mask` either cuts too aggressively (clean
samples removed) or too conservatively (pileup leaks through). C is the
bridge between detection correctness (B) and end-to-end mask validity
(E) on real PPA12 data.

## Read First

1. `dispatches/override_review_results.md` — `t_lo_star` / `t_hi_star`
   for all 24 cases under the `all-on` config.
2. `dispatches/ground_truth_validation.csv` — the `note` column has
   scale hints per parameter (e.g., `e_dv_ap` "noise for |x| < 1e-2",
   `vx` "5-12 km/s inward from U=-200"). These are the visual-inspection
   targets.
3. `dispatches/boundary_inspection.pdf` — raw histograms that produced
   the CSV (one page per parameter).
4. `dispatches/boundary-fn-diagnostics-2026-04-17.md` — the per-FN
   "true scale" column (at tol≈1e-3 / 1e-5 / 1e-7) is an independent
   check on where the pileup lives.
5. `src/fitqc/boundary.py` — production of `t_star`
   (`_check_excess_mass` L455-523 and the M3 refinement block).

## Investigation protocol

For each (parameter, side) with `t_star != None`:

1. Read `t_star` from `override_review_results.md`.
2. Read the CSV `note` column for that side (and the row's scale hint
   if one exists).
3. Overlay `t_star` on the raw histogram — either by reading the
   corresponding page of `boundary_inspection.pdf`, or by running an
   ad-hoc plotting script against the PPA12 data the CSV was built from.
4. Classify:
   - **WITHIN** ±1 decade of documented scale → OK.
   - **OFF** by more than ±1 decade → flag with written reason.
   - **NO HINT** (CSV has no scale note for that side) → justify based
     on the visual histogram; document the reasoning explicitly.
5. Record `(parameter, side, t_star, scale_hint, verdict, justification)`
   in a results markdown.

## Acceptance Criteria

- [ ] Results table committed as
      `dispatches/tolerance-validation-2026-04-XX.md` covering every
      (parameter, side) with `t_star != None`.
- [ ] Every case labeled WITHIN / OFF / NO HINT.
- [ ] OFF cases each have a written justification or a hand-off note
      that names the downstream task expected to resolve it.
- [ ] Zero changes to `dispatches/ground_truth_validation.csv`.
- [ ] Zero changes to `src/fitqc/boundary.py` or any production code.
- [ ] `python -m pytest tests/ -q` passes with same count as pre-work
      baseline (422 after B's fix, with the 3 quantile-test deselects).

## Anti-Patterns

- Do NOT adjust config (`pileup_threshold`, `excess_ratio`) to push
  `t_star` toward the target scale. Any production change belongs in a
  separate task with its own dialectic.
- Do NOT modify the ground truth CSV.
- Do NOT widen the ±1 decade criterion silently when a case is close.
  If the threshold is too strict, flag it as an open question; don't
  move the goalposts mid-task.

## Verification

Reproduce current state:

```bash
cd /Users/balterma/observatories/code/fitqc
grep -c "t_lo_star\|t_hi_star" dispatches/override_review_results.md
# Expected: nonzero; 24 t_star values exist in the all-on section.
```

On completion:

```bash
test -f dispatches/tolerance-validation-2026-04-*.md && echo "results: OK"

python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
# Expected: 422 passed
```

## Out of Scope

- Fixing any flagged OFF cases in production code (follow-up task).
- Interior stickiness detection (Task D: `calibration-interior-det`).
- End-to-end mask application (Task E: `calibration-end-to-end`).

## Open Items

- POSSIBLY STALE: plan L98 says "14 current + new ones from B". Post-B
  the count is 24; scale the results table accordingly.
- PROPOSED: If ±1 decade flags an unexpectedly large fraction of cases,
  stop and surface the distribution for user review rather than
  adjusting the threshold.
