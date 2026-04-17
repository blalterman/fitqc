# Dispatch: Fix 10 boundary false negatives on real PPA12 data

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** software
**CPM task:** `calibration-boundary-fns` (depends on `calibration-quantile-tests`)

## Scope

The 2^3 factorial analysis against `dispatches/ground_truth_validation.csv`
(after M1 removal) shows 10 of 24 boundary decisions are false negatives.
Investigate each per-parameter, determine the root cause, and apply
evidence-based fixes so re-running `analyze_overrides.py` shows at most 2
remaining false negatives and no new false positives on the 14
currently-correct cases. Ground truth CSV is authoritative — do not
modify it.

## Motivation

Each false negative is a missed data cut in `src/fitqc/report.py:_build_mask`:
detection boolean = False means no cut is applied at that boundary, and
sticky samples leak into the "good" data distribution for real PPA12 runs.
Downstream consumers (PPA integration, papers) depend on those cuts being
correct.

## Two failure groups, distinct root causes

Pulled from `dispatches/override_review_results.md` (all-on config, current
production code):

### Group 1: `t_raw` exists, `t_star = None` (6 cases)

Kneedle finds a candidate elbow, but `_check_excess_mass` rejects it.
Either the elbow is in the wrong place or the `excess_ratio` validation
threshold is too aggressive.

| Parameter | Side | `t_raw` | CSV scale hint |
|-----------|------|---------|----------------|
| e_dv_ap | lower | 0.006071 | noise for \|x\| < 1e-2 |
| vy | lower | 0.250000 | (none; CSV interior guess \|x\| < 1e-1) |
| vy | upper | 0.147250 | (none) |
| vz | lower | 0.159531 | (none; CSV interior guess \|x\| < 1e-1) |
| vz | upper | 0.171768 | (none) |
| e_w_p1 | upper | 0.009063 | (none on upper; CSV interior guess \|x\| < 1e-2) |

Observation: `vy` and `vz` raw elbows at 15-25% of the range are suspiciously
wide. For a parameter with range 400 km/s, that's 60-100 km/s — far wider
than any physical pileup would be. Likely the Kneedle is latching onto a
noise-level transition rather than the actual pileup transition.

### Group 2: `t_raw = None` (4 cases)

Kneedle finds no elbow at all. Mass curve shape does not trigger elbow
detection on the quantile grid `(0.0005, 0.001, ..., 0.25)`.

| Parameter | Side | `t_raw` | CSV says |
|-----------|------|---------|----------|
| np1 | upper | None | sticky at U=100 |
| np2 | upper | None | sticky at U=100 |
| vx | lower | None | sticky at L=-1200 (no scale hint; upper L=-200 has "5-12 km/s inward") |
| e_w_p2 | upper | None | sticky at U=75 |

Observation: np1 and np2 share the same bounds (0.01, 100) and the same
upper false negative pattern. vx lower has no CSV scale hint. These four
may share a common root cause (e.g., pileup fraction below the lowest
quantile grid point, or one-sided mass curve shape that the convex/increasing
elbow detector misses).

## Read First

1. `dispatches/ground_truth_validation.csv` — the ground truth. CSV values
   in the `lower`, `upper`, `interior` columns are bound positions (numeric
   means sticky AT that position); `None` means not sticky. Do not modify.
2. `dispatches/override_review_results.md` — the full factorial output.
   Section "Full Comparison Table" has t_lo_raw / t_lo_star / lo_det per
   parameter and config.
3. `src/fitqc/boundary.py`:
   - Lines 148-218: `_compute_quantile_curves_boundary` (where Kneedle runs)
   - Lines 455-523: `_check_excess_mass` (where validation rejects elbows)
   - M3 block (broad-pileup fallback, inside `if config.refine_transition`) —
     relevant if widening `t_raw` could rescue Group 1 cases
4. `src/fitqc/config.py` — `BoundaryConfig` defaults: `pileup_threshold=0.005`,
   `excess_ratio=1.5`, `min_quantile_agreement=0.5`.
5. `analyze_overrides.py` — factorial harness. Re-run after each fix to
   verify no regression on the 14 currently-correct cases.
6. `dispatches/boundary_inspection.pdf` — raw histograms used to build
   the ground truth CSV. Inspect for each FN to see the actual pileup
   shape and scale.

## Investigation protocol

For each of the 10 false negatives, produce a diagnostic record:

1. **Reproduce** detection for the single parameter using the same config
   as the factorial (`use_quantile_analysis=True, refine_transition=True,
   grid_mode="progressive"`). Record `t_raw`, `t_star`, `lo_det/hi_det`,
   the full mass curve, and `tol_at_quantile` at the refined grid.

2. **Classify** the failure:
   - Group 1: does widening `t_raw` pass `_check_excess_mass`? Or does the
     mass at `t_raw` genuinely not exceed `excess_ratio * t_raw`?
   - Group 2: why does Kneedle return no elbow? Plot `tol_at_quantile` vs
     `quantile_grid`; is the curve monotonic-linear (uniform), or is there
     a knee the algorithm is missing?

3. **Compare to the raw histogram** from `boundary_inspection.pdf`. The
   pileup shape and scale there are the target. For `e_dv_ap lower` the
   CSV hint is "|x| < 1e-2" — the corresponding normalized tolerance for
   range (-150, 150) is `0.01/(300)` ≈ 3.3e-5, well below the Kneedle's
   `t_raw = 0.006`. Understand the scale mismatch before fixing.

4. **Propose fix**. Allowed:
   - Parameter tuning: `pileup_threshold`, `excess_ratio`,
     `min_quantile_agreement`, `quantile_grid` extension (e.g., add lower
     points for sub-percent pileups).
   - Algorithm tweak: bounded to `_check_excess_mass` or
     `_compute_quantile_curves_boundary`, with dialectic evaluation per
     CLAUDE.md's protocol.
   - Do NOT touch M2 or M3 behavior. Do NOT re-introduce M1.

5. **Verify no regression**. After each fix, re-run
   `python analyze_overrides.py` and diff the new
   `dispatches/override_review_results.md` against the old. The 14
   currently-correct cases must stay correct. New false positives are
   blockers — roll back and try differently.

## Acceptance Criteria

- [ ] `python analyze_overrides.py` regenerates
      `dispatches/override_review_results.md` with ≤ 2 remaining false
      negatives (tolerable: up to 2 cases that require separate interior-
      detection investigation in the calibration-interior-det task).
- [ ] Zero new false positives on the 14 currently-correct
      parameter-side combinations. Verified by diffing the new results
      markdown against the pre-change version.
- [ ] Per-parameter diagnostic record written for each of the 10 FNs,
      stating: root-cause group, what was tried, what worked, why.
      Committed as `dispatches/boundary-fn-diagnostics-<date>.md`.
- [ ] All production-code changes (if any) have at least one new or
      updated test in `tests/test_boundary.py` or
      `tests/test_boundary_seams_overrides.py`.
- [ ] `python -m pytest tests/ -q` shows no new failures (the 3 pre-existing
      `test_boundary_quantile.py` failures remain excluded until Task A's
      session lands them).

## Anti-Patterns

- Do NOT modify `dispatches/ground_truth_validation.csv`. It is empirical
  ground truth from visual inspection. If the pipeline disagrees, the
  pipeline is wrong.
- Do NOT lower `excess_ratio` blindly to 1.0 or below. That would
  introduce false positives on genuinely uniform data.
- Do NOT re-introduce M1 or any "spread-pileup propagation" override.
  The factorial showed M1 had zero detection effect; re-introducing it
  contradicts the calibration-against-ground-truth approach.
- Do NOT fix per-parameter with magic numbers. Each fix must have a
  mechanism that generalizes, not a "if parameter == 'vy': t_raw = 0.1"
  patch.
- Do NOT batch all 10 fixes into one commit. One commit per root-cause
  category (or per parameter if the mechanism is parameter-specific) so
  rollback is surgical.

## Verification

Reproduce current state:

```bash
python analyze_overrides.py
grep -E "^\| (M1|M2|M3) " dispatches/override_review_results.md | head
# Expected summary in results: M1 0/24 no effect, M3 1/24 helps, M2 0/24 no effect
# Expected FN count (all-on): 10 (e_dv_ap lower, np1 upper, np2 upper, vx lower,
# vy lower, vy upper, vz lower, vz upper, e_w_p1 upper, e_w_p2 upper)
```

After each fix attempt:

```bash
# Regenerate results
python analyze_overrides.py

# Count FNs in current "all-on" column
python -c "
import re, pathlib
md = pathlib.Path('dispatches/override_review_results.md').read_text()
params = ['A_He','e_dv_ap','e_dv_pp','np1','np2','vx','vy','vz','w_const','e_w_p1','e_w_p2','e_w_a']
# (full FN check implementation left to executor; see Read First #2)
"

# Regression check
python -m pytest tests/ -q
```

Final verification:

```bash
# ≤ 2 FNs remaining
python analyze_overrides.py && \
  grep -c "expected: True" dispatches/override_review_results.md

# No test regressions
python -m pytest tests/ -q --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup

# Expected: 415 passed (same as pre-work baseline)
```

## Out of Scope

- Fixing the 3 `test_boundary_quantile.py` failures (Task A:
  `calibration-quantile-tests`).
- Validating `t_star` magnitudes against histograms (Task C:
  `calibration-tolerance-mags`).
- Interior stickiness detection (Task D: `calibration-interior-det`).
- End-to-end mask validation on real PPA12 data (Task E:
  `calibration-end-to-end`).
- Changes to M2 or M3 override mechanisms.
- Updating `analyze_overrides.py` itself (separate task
  `analyze-overrides-m1-cleanup`).

## Open Items

- PROPOSED: `vy` and `vz` bilateral false negatives may turn out to be
  interior-spike masquerading as boundary-spike (their raw elbows at
  15-25% of range are suspiciously wide). If investigation shows the
  true pileup is interior at x0=0, the fix belongs in Task D, and
  those two parameters are the "≤ 2 remaining" allowance in the
  acceptance criteria. Verify before bucketing.
- PROPOSED: `np1` upper and `np2` upper may share a common root cause
  since both parameters have identical bounds (0.01, 100). Investigate
  one, check if the fix transfers.
