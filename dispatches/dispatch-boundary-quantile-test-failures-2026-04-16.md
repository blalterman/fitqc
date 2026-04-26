# Dispatch: Resolve 3 pre-existing test failures in test_boundary_quantile.py

**Generated:** 2026-04-16
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** software

## Scope

Determine the correct resolution for three failing tests in
`tests/test_boundary_quantile.py` and apply it. Each failure is a mismatch
between a test assertion and the pipeline's actual output on synthetic data.
Detection booleans pass in all three; only numeric bounds on `t_star` or
`elbow` fail. The resolution may be updating the assertion, fixing the
algorithm, or documenting a known limitation — determined per-failure from
evidence, not guessed.

## Motivation

These failures were present before the recent override-calibration work and
are unrelated to it (confirmed by running the tests against commit 78c970b,
before M1 removal in fb4ad25). They likely predate commit 7f8d7a7
(iterative Kneedle refinement, Fix 5 Part 2), which changed elbow
computation semantics. Leaving them failing makes `pytest -x` unusable as a
regression gate on this branch.

## Read First

1. `src/fitqc/boundary.py:148-218` — `_compute_quantile_curves_boundary`.
   Returns `(tol_at_quantile, elbows_per_quantile)` where `elbows[0]` is a
   *tolerance* (not a quantile). Failure 1 hinges on this contract.
2. `src/fitqc/boundary.py:455-523` — `_check_excess_mass`. When
   `t_raw < pileup_threshold` it enters the delta-function branch and
   returns a tolerance-grid point, not `t_raw`. Failure 2 hinges on this.
3. `tests/test_boundary_quantile.py` lines 363-367, 435-460, 480-509 — the
   three failing tests.
4. `src/fitqc/config.py` — `BoundaryConfig` defaults (`pileup_threshold`,
   `refine_transition`, `quantile_grid`) that the tests interact with.

## The 3 Failures

### Failure 1: `TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow`

**Line:** tests/test_boundary_quantile.py:363-367
**Assertion:** `0.01 <= elbows[0] <= 0.10`
**Actual:** `elbows[0] = 0.00192`
**Test data:** 5% pileup in `uniform(0, 0.002)`, 95% uniform in `(0, 1)`

Traced behavior (verified by instrumenting
`_compute_quantile_curves_boundary`):
- `select_elbow` returns `elbow_quantile = 0.05` — correct, equals the
  pileup fraction
- Conversion `elbow_tol = np.interp(0.05, quantile_grid, tol_at_quantile)`
  returns `0.00192`, which ≈ the pileup width `0.002`
- The test's variable name `elbow_q` is misleading — `elbows[0]` is a
  tolerance, per the function's return contract

Investigation: git-blame line 365 to find when `[0.01, 0.10]` was chosen and
what behavior it expected. Compare to current return contract.

### Failure 2: `TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup`

**Line:** tests/test_boundary_quantile.py:435-460
**Assertion:** `t_lo_star == pytest.approx(0.003, abs=0.002)`
**Actual:** `t_lo_star = 0.0001`, `t_lo_raw = 0.00265`
**Config:** `refine_transition=False` (default), `use_quantile_analysis=True`,
`quantile_grid=(0.005, 0.01, 0.02, 0.03, 0.05, 0.10)`
**Test data:** 3% pileup in `uniform(0, 0.003)`, 97% uniform in `(0, 1)`

Traced behavior:
- `t_lo_raw = 0.00265` correctly matches the pileup width (0.003)
- `_check_excess_mass` sees `t_lo_raw (0.00265) < pileup_threshold (0.005)`,
  enters the delta-function branch, returns `tol_grid[first_excess_point] ≈
  0.0001` instead of `t_lo_raw`

Investigation: is the delta-branch behavior correct for this case? A 3%
pileup in 0.3% range is concentrated but not a true delta (mass(0) = 0,
`lower_mass_curve[0] = 0`). Should `_check_excess_mass` return `t_raw`
instead of a grid point when `t_raw` is a valid non-zero elbow?

### Failure 3: `TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup`

**Line:** tests/test_boundary_quantile.py:480-509
**Assertion:** `t_lo_star >= 0.02`
**Actual:** `t_lo_star = 0.01257`, `t_lo_raw = 0.01257`
**Config:** `refine_transition=False` (default), `use_quantile_analysis=True`,
`quantile_grid=(0.01, 0.02, 0.05, 0.10, 0.15)`
**Test data:** 15% pileup in `uniform(0, 0.05)`, 85% uniform in `(0, 1)`

Traced behavior:
- Kneedle elbow lands at `0.01257`, underestimating the pileup extent (0.05)
- `lower_mass_curve[0] = 0.0` (not a delta)
- Neither iterative refinement nor M3 (broad-pileup fallback) runs because
  `refine_transition=False`. M3 is inside the `if config.refine_transition:`
  block and is the mechanism designed to expand `t_raw` on broad pileups.

Investigation: should this test enable `refine_transition=True`? Real
pipeline calls use it (see `analyze_overrides.py:43-48`). Or should the
non-refined path handle broad pileups? git-blame line 507 to find original
intent.

## Acceptance Criteria

- [ ] For each failure: a decision is recorded in the fix (either in a
      commit message or a comment on the modified assertion) stating whether
      the root cause is stale test bounds, algorithm regression, or known
      limitation — with git-blame evidence supporting the decision
- [ ] All three tests pass: `python -m pytest tests/test_boundary_quantile.py -q`
      reports zero failures
- [ ] No regression elsewhere: `python -m pytest tests/ -q` shows the same
      pass count as current (418 + 3 = 421 passing)
- [ ] If any algorithm change is proposed (not just test updates), it is
      surfaced to the user BEFORE modifying `src/fitqc/boundary.py`

## Anti-Patterns

- Do NOT adjust assertion bounds to whatever the algorithm currently
  produces without investigating whether that output is correct. "Make the
  test pass" is not the goal — "make the test correct" is.
- Do NOT modify `_check_excess_mass`, `_compute_quantile_curves_boundary`,
  or M2/M3 behavior without user approval. These are production code
  protected by the current test suite; changes require dialectic evaluation
  per CLAUDE.md.
- Do NOT skip the git-blame step. The tests' original intent is evidence;
  without it, a fix is a guess.
- Do NOT re-enable M1 or reintroduce the spread-pileup override. That
  decision was made against empirical ground truth in commit fb4ad25.

## Verification

Reproduce the failures:

```bash
python -m pytest \
  tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup \
  -v
```

Expected: 3 failed before work, 3 passed after.

Confirm no regression:

```bash
python -m pytest tests/ -q
```

Expected: 421 passed (was 418 passed + 3 failed).

Git-blame the assertions (one per failure):

```bash
git blame -L 365,365 tests/test_boundary_quantile.py
git blame -L 455,455 tests/test_boundary_quantile.py
git blame -L 507,507 tests/test_boundary_quantile.py
```

## Out of Scope

- The 10 false negatives on real PPA12 data (separate dispatch)
- Any change to M2 or M3 override behavior
- Re-running `analyze_overrides.py` or regenerating override review results
- Refactoring `_check_excess_mass` beyond what these failures require
