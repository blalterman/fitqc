# Dispatch: Recalibrate tolerance grid for boundary detection

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** code + analysis
**CPM task:** `calibration-grid-resolution` (new; parallel to or following `calibration-tolerance-mags`)

## Scope

Replace or augment the current linear tolerance grid
(`BoundaryConfig.quantile_grid`, and `_build_tolerance_grid` modes)
so the mass curves resolve pileup transitions in the ≤ 0.005 tolerance
region, where visual inspection of the per-parameter overviews shows
current detection is producing `t_star` magnitudes that are off by a
decade or more on 9 of 12 parameters.

## Motivation

B achieved TP=24/24 on the CSV boolean ground truth. Visual review of
post-B per-parameter overview PDFs shows `t_star` magnitudes
mis-calibrated on A_He lower, e_dv_ap upper, e_dv_pp both, vy both,
vz both, w_cost both, e_w_p1 upper, e_w_p2 upper, e_w_a upper — i.e.
the boolean is right but the cut position is wrong. Root cause per
the e_dv_pp log-y panel: the mass curve's crossover with uniform
lives at the left edge of the grid and Kneedle has no resolution to
find the knee. B's diagnostic established true pileup widths span
1e-7 to 5e-4 in normalized space; the grid must span that.

## Read First

1. `dispatches/boundary-fn-diagnostics-2026-04-17.md` — per-FN true
   pileup widths (1e-7 to 5e-4 normalized).
2. `dispatches/override_review_results.md` — current `t_star`
   magnitudes; identifies which parameters have magnitude errors.
3. `dispatches/tolerance-validation-2026-04-XX.md` (if Task C has
   committed) — formal OFF/WITHIN/NO-HINT classification.
4. `src/fitqc/config.py` — `BoundaryConfig.quantile_grid` default and
   `grid_mode` values.
5. `src/fitqc/boundary.py:_build_tolerance_grid` (progressive grid
   construction) and `_compute_quantile_curves_boundary` (148-218).
6. `dispatches/plot_all_ppa12_diagnostics.py` — driver for the
   overview PDFs used to visually verify improvements.

## Investigation protocol

1. **Audit current grid**: enumerate the grid points actually
   evaluated for each parameter's detection pass; compare against
   B's diagnostic true pileup widths. Record the coverage gap.
2. **Design candidate grids** (each tested as a separate `grid_mode`
   or a drop-in replacement for the default):
   - Log-spaced `[1e-7, 3e-7, 1e-6, ..., 1e-1]` (uniform log density).
   - Hybrid: current progressive grid + log-spaced extension below 1e-4.
   - Piecewise dense: dense below 1e-4, sparser above.
3. **Prototype** in `dispatches/prototype_grid_<candidate>.py`; run
   detection on all 12 parameters for each candidate; tabulate
   `t_star` magnitude delta vs CSV scale hint.
4. **Dialectic per CLAUDE.md** to pick the winner.
5. **Commit to config**; re-run `analyze_overrides.py`; verify
   TP=24/24 preserved and zero new FPs on the previously-correct 14.
6. **Regenerate** overview PDFs; visually verify the 9 affected
   parameters now show resolved mass-curve structure below t=0.05.

## Acceptance Criteria

- [ ] New `BoundaryConfig.quantile_grid` default (or new `grid_mode`
      value) committed, with the decision justified in a docstring or
      commit body referencing the dialectic.
- [ ] `python analyze_overrides.py` regenerated; TP=24/24 preserved;
      zero new FPs.
- [ ] For the 9 parameters flagged in cluster C1, `t_star` magnitudes
      are within ±1 decade of the CSV-documented scale (or flagged
      with a written justification per Task C's convention).
- [ ] `tests/test_boundary.py` (or `test_boundary_quantile.py`) gets
      at least one new test covering detection on a synthetic tight
      delta pileup with width 1e-6.
- [ ] `python -m pytest tests/ -q` passes at least the post-B
      baseline count.

## Anti-Patterns

- Do NOT silently tune `excess_ratio` or `pileup_threshold` to paper
  over grid issues. This task owns the grid only.
- Do NOT re-introduce M1.
- Do NOT modify CSV ground truth.
- Do NOT change detection boolean semantics; TP=24/24 must hold.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Baseline before change
python analyze_overrides.py
grep -E "t_lo_star|t_hi_star" dispatches/override_review_results.md | head -30

# After change
python analyze_overrides.py
python dispatches/plot_all_ppa12_diagnostics.py

# Test suite
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
```

## Out of Scope

- Derivative-based detection (`calibration-derivative-refine`).
- Interior grid changes (D: `calibration-interior-det`).
- End-to-end mask validation (E: `calibration-end-to-end`).
- Plot axis-scale changes (`calibration-plot-axis-scale`).

## Open Items

- PROPOSED: log-spaced vs hybrid vs piecewise. Resolved by dialectic
  in the prototype phase; winner minimizes total magnitude error
  across the 12 parameters and avoids regressing any of the 14 TPs.
- PROPOSED: grid top end may need to extend above 0.25 for some
  upper-side parameters. Evaluate during prototype.
