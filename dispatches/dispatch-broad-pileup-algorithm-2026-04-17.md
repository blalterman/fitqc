# Dispatch: Fix the broad-pileup miscalibration in Kneedle elbow interpretation

**Generated:** 2026-04-17
**Branch:** `claude/fitqc-ppa12-validation-vwKdg` (or successor)
**Work type:** algorithm / code
**CPM task:** `calibration-broad-pileup-elbow` (new; blocker for several
`calibration-tolerance-mags` follow-ups)

## Scope

Replace the current primary-path `_compute_quantile_curves_boundary` +
Kneedle elbow detection with a mechanism that reports pileup **width**,
not pileup **fractional mass**, when the boundary pileup is broad (mass
fraction ≥ quantile_grid minimum).

Change must:
- Preserve TP=24/24 on the PPA12 boolean ground truth.
- Preserve behavior of existing sparse-pileup detections (e_dv_ap lower,
  e_w_p1 upper, w_const lower, and the 10 fallback-resolved cases).
- Not touch `excess_ratio`, `pileup_threshold`, M2, M3, CSV, or the
  subgrid excess-mass fallback.

## Motivation

After the 2026-04-17 grid-resolution work (commit 6bac9e9 + c3a45be),
the primary path still reports `t_star` off by 2–3 decades for
broad-pileup parameters. Affected (param, side, current t_star, truth):

| Param     | Side  | t_star current | CSV truth (normalized) | Delta (decades) |
|-----------|-------|----------------|------------------------|-----------------|
| A_He      | lower | 1.642e-2       | ~4e-3                  | 0.61            |
| e_dv_ap   | upper | 1.158e-2       | ~1e-3                  | 1.06            |
| e_dv_pp   | lower | 1.178e-1       | ~6.7e-5                | 3.25            |
| e_dv_pp   | upper | 4.132e-2       | ~6.7e-5                | 2.79            |
| e_w_a     | upper | 9.660e-2       | (unknown)              | —               |

Empirically the reported `t_star` ≈ pileup's fractional mass:
- e_dv_pp lower: 11799/100000 = 0.118 → reported 0.1178 ✓
- A_He lower:    1688/100000  = 0.017 → reported 0.01642 ✓
- e_w_a upper:   9668/100000  = 0.097 → reported 0.0966 ✓

## Mechanism (traced)

In `src/fitqc/boundary.py:_compute_quantile_curves_boundary`:

```python
mass_curve = np.array([tail_mass(u_sorted, tol) for tol in tol_grid])
tol_at_quantile = np.interp(quantile_grid, mass_curve, tol_grid)
elbow_quantile = select_elbow(quantile_grid, tol_at_quantile, ...)
```

For a boundary pileup of width `w` and fractional mass `f` plus uniform
remainder `(1 - f)`:

- `mass_curve(tol)` ≈ `f` for `tol ≥ w` (pileup fully captured)
- `mass_curve(tol)` continues to rise linearly with slope `(1 - f)` for
  `tol > w` (uniform remainder contributes)
- Therefore, for every `q ≤ f`, `tol_at_quantile[q]` clamps to
  `tol_grid[0]` (since `np.interp` extrapolates left-edge when `q` is
  below the minimum `mass_curve` value)
- The `(quantile, tol_at_quantile)` curve is flat at `tol_grid[0]` for
  `q ≤ f` and linear (slope ≈ `1 / (1 - f)`) for `q > f`
- `select_elbow(curve="convex", direction="increasing")` identifies the
  kink at `q ≈ f`, whose mapped tolerance is approximately `f` itself
  (since the uniform segment has slope ≈ 1 after the kink)

So the primary path correctly detects *that* a pileup exists, but
reports its *fractional mass* in place of its *width*.

## Read First

1. `src/fitqc/boundary.py:148-218` — the miscalibrated primary path.
2. `src/fitqc/boundary.py:95-150` — tolerance grid construction
   (already extended with `progressive_log`).
3. `dispatches/boundary-fn-diagnostics-2026-04-17.md` — empirical widths
   for 10 FN-diagnostic cases. Use these as ground truth for testing the
   replacement mechanism.
4. `dispatches/dispatch-grid-resolution-2026-04-17.md` + commits
   `6bac9e9`, `c3a45be`, `f198b7b` — what the grid work did and did not
   fix; why grid-only changes cannot reach this miscalibration.

## Investigation protocol

1. **Independent verification** of the mechanism above: for one broad
   case (e_dv_pp lower), print `mass_curve`, `tol_at_quantile`, and the
   detected `elbow_quantile`. Confirm `elbow_quantile ≈ f` and
   `mapped_tolerance ≈ f`.
2. **Design candidate replacements**:
   - **A:** Detect pileup width as the tol where `mass_curve` first
     crosses `f - ε` (i.e., the "last tol before the plateau begins").
   - **B:** Two-stage detection: first estimate `f` from the
     `tol_at_quantile` elbow, then scan `mass_curve` to find the tol
     where mass reaches `α × f` for small `α` (e.g. 0.5). Report that
     tol as the width.
   - **C:** Apply a derivative-based detector to the raw `mass_curve`
     directly (aligns with the separate `calibration-derivative-refine`
     task; check whether this supersedes the current approach entirely).
3. **Prototype each in `dispatches/prototype_broad_pileup_<x>.py`**;
   run on all 12 PPA12 datasets plus three synthetic broad pileups.
4. **Dialectic per CLAUDE.md** to pick the winner.
5. **Commit to `boundary.py`**; re-run `analyze_overrides.py`; verify
   TP=24/24, zero new FPs, and magnitudes within ±1 decade for the
   cluster above.
6. **Add tests** covering each broad-pileup width scale represented
   in the PPA12 data (1e-2, 1e-3, 1e-4).

## Acceptance Criteria

- [ ] Primary path for broad pileups returns `t_star` within ±1 decade
      of CSV-documented width (not fractional mass) for A_He lower,
      e_dv_ap upper, e_dv_pp both, and e_w_a upper where CSV provides
      a width.
- [ ] `python analyze_overrides.py`: TP=24/24 preserved; zero new FPs.
- [ ] At least one new test per acceptance condition above in
      `tests/test_boundary.py` or `tests/test_boundary_quantile.py`.
- [ ] `python -m pytest tests/ -q` passes at least the post-grid-resolution
      baseline count (429 after f198b7b).

## Anti-Patterns

- Do NOT tune `excess_ratio`, `pileup_threshold`, or the subgrid fallback
  to paper over the miscalibration — the root cause is elbow
  interpretation, not detection sensitivity.
- Do NOT re-introduce M1, modify CSV, or change detection boolean
  semantics.
- Do NOT re-open the grid-resolution scope (commit 6bac9e9, c3a45be,
  f198b7b settled that dialectic; `progressive_log` is the agreed
  diagnostic mode, extended `quantile_grid` is the production default).

## Out of Scope

- Derivative-based detection (`calibration-derivative-refine`) unless
  the dialectic in step 4 chooses mechanism C and converges with that
  task.
- Interior grid changes (`calibration-interior-det`).
- End-to-end mask validation (`calibration-end-to-end`).
- Plot axis-scale changes (`calibration-plot-axis-scale`).

## Open Items

- PROPOSED: mechanisms A / B / C above. Resolved by dialectic in
  prototype phase.
- PROPOSED: should `f` be estimated from `tol_at_quantile[-1]` (largest
  quantile where the curve is still flat at `tol_grid[0]`) or from the
  mass-curve plateau directly? Evaluate during prototype.
- PROPOSED: unclear whether the fix should replace or supplement the
  current Kneedle path. Evaluate the regression risk on the sparse-pileup
  cases that currently succeed via primary path (e_dv_ap lower,
  e_w_p1 upper, w_const lower, np1 lower, np2 lower, e_w_p2 lower).
