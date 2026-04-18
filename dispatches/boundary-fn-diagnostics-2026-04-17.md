# Boundary FN diagnostics — 2026-04-17

Resolution of the 10 boundary false negatives reported in
`override_review_results.md` against `ground_truth_validation.csv`,
under production config `(use_quantile_analysis=True,
refine_transition=True, grid_mode="progressive")`.

## Outcome

- All 24 (parameter, side) cases now match CSV ground truth.
- TP = 24, FN = 0, FP = 0.
- Single commit: `44447a0` (`fix(boundary): add sub-grid excess-mass
  fallback for thin delta pileups`).
- 4 new tests in `tests/test_boundary.py::TestSubgridFallback`.
- `pytest tests/ -q` → 422 passed.
- CSV unchanged: `git diff --name-only dispatches/ground_truth_validation.csv`
  empty.

## Methodology

1. Built `dispatches/diagnose_boundary_24.py` to print TP/FN/FP/TN for
   all 24 (parameter, side) cases in seconds, mirroring the all-on
   column of `analyze_overrides.py`.
2. Built `dispatches/diagnose_boundary_fns_deep.py` to compute
   `tail_mass(u, tol)` at fine tolerances (1e-7 to 1e-1) for each FN.
   This exposed the actual pileup widths and mass/uniform ratios.
3. Synthesised a single root cause from the data, designed a single
   surgical fix, and validated via the 24-row script before paying
   the 90s factorial cost.

## Per-FN diagnostic table

| # | Param | Side | t_raw | t_star (before) | mass(t_raw) | True scale | mass at true scale | Mechanism |
|---|-------|------|-------|-----------------|-------------|------------|---------------------|-----------|
| 1 | e_dv_ap | lower | 0.006071 | None | 0.007010 | tol≈1e-3 (ratio=6.65) | 0.006650 | Kneedle elbow far above true pileup; primary fails excess test |
| 2 | vy | lower | 0.250000 | None | 0.001740 | tol≈1e-7 (ratio=1700) | 0.000170 | Kneedle latched on noise transition; pileup is thin delta |
| 3 | vy | upper | 0.147250 | None | 0.003110 | tol≈1e-7 (ratio=3900) | 0.000390 | Same as #2 |
| 4 | vz | lower | 0.159531 | None | 0.001780 | tol≈1e-7 (ratio=3300) | 0.000330 | Same as #2 |
| 5 | vz | upper | 0.171768 | None | 0.001770 | tol≈1e-7 (ratio=3900) | 0.000390 | Same as #2 |
| 6 | e_w_p1 | upper | 0.009063 | None | 0.004030 | tol≈1e-3 (ratio=3.83) | 0.003830 | Same as #1 |
| 7 | np1 | upper | None | None | — | tol≈1e-7 (ratio=519) | 0.000052 | Kneedle returned no elbow on near-degenerate curve |
| 8 | np2 | upper | None | None | — | tol≈1e-5 (ratio=2.04) | 0.000020 | 2 samples at u=1 — real but very weak |
| 9 | vx | lower | None | None | — | tol≈1e-7 (ratio=812) | 0.000081 | Same as #7 |
| 10 | e_w_p2 | upper | None | None | — | tol≈1e-7 (ratio=3.5e6) | 0.353 | Kneedle fails on flat-zero portion of curve; pileup is 35% delta at u=1 |

## Mechanism

All 10 FNs share one root cause: **the actual boundary pileup is a
delta function at u=0 or u=1 whose width is far smaller than the
quantile_grid floor (default 0.0005)**. The Kneedle-on-(quantile,
tolerance) primary detector either latches on a wide false elbow
(rows 1-6) or returns nothing on the degenerate near-flat curve
(rows 7-10). In both cases `_check_excess_mass` returns
`(False, None)` and the case is missed.

The dispatch's two-group framing (Group 1: t_raw exists, t_star=None;
Group 2: t_raw=None) reflects two failure modes of the same Kneedle
on the same root cause — not two distinct underlying problems. A
single fix mechanism resolves both groups.

## Cluster — single fix (dialectic)

Two fix candidates considered.

### Proposition A — Extend `quantile_grid` lower (e.g. add 1e-7, 1e-5, 1e-4)

**PREMISES**
- P1: Current `BoundaryConfig.quantile_grid` floor is 0.0005.
- P2: True pileup widths range 1e-7 to 5e-4 per the deep diagnostic.
- P3: Kneedle median aggregation uses all quantile grid points.

**FOR**
- Stays inside the existing detection architecture; no new fallback layer.
- More resolution at fine scales should give Kneedle the data points
  it needs to find the true elbow.

**AGAINST**
- For Group-1 cases (vy/vz) the existing Kneedle finds a wide false
  elbow; adding fine grid points might shift the median in either
  direction. Effect on the 14 currently-correct TPs is unpredictable.
- Does not address the e_w_p2 case, where the (quantile, tolerance)
  curve is constant zero over the pileup region and Kneedle's
  normalization divides by zero.

**COUNTEREXAMPLE**
- A TP detection (e.g., w_const lower at t_raw=0.250) where the
  Kneedle elbow currently satisfies excess_mass could regress if the
  median elbow shifts after grid extension.

### Proposition B — Sub-grid excess-mass fallback after `_check_excess_mass` rejects

**PREMISES**
- P1: `_check_excess_mass` returns `(False, None)` only when primary
  detection failed (the case never occurs for TPs).
- P2: For all 10 FNs, mass at fine tols (1e-7 to 1e-4) shows
  excess > 1.5x uniform, with samples lying at u=0 or u=1 exactly.
- P3: For uniform random data, samples within a fine tol can occur
  by chance, but never lie at u=0 exactly.

**FOR**
- Cannot regress any TP by construction: the fallback only runs when
  the primary path returned `det=False`.
- Direct, mechanism-aware: scans the same mass curve quantity used
  by primary detection, just at finer tols.
- Handles e_w_p2 (degenerate curve) without special-casing.

**AGAINST**
- Adds another fallback layer, which the project is incrementally
  reducing (M1 was just removed in `fb4ad25`).
- Naive form (excess_ratio test alone) over-fires on uniform data
  when n is large enough that 1-2 chance samples appear in a fine tol.

**COUNTEREXAMPLE**
- A uniform random distribution at large n could put 1 sample within
  3e-5 of u=0 by chance, satisfying mass > tol * 1.5 (caught by
  `test_multi_curve_no_false_positives_on_uniform`). Resolved by
  adding a delta-function gate: require at least one sample at u=0
  to within 1e-12 (well below float64 precision near 0). Real
  optimizer-stuck samples are at u=0 exactly; chance fluctuations
  are not.

### Decision — Proposition B with delta-function gate

Stronger safety guarantee (cannot regress TPs by construction); aligns
with the dispatch's allowed knob ("algorithm tweak bounded to
`_check_excess_mass`"); single mechanism handles all 10 FNs.

## Implementation

- `src/fitqc/config.py`: added
  `BoundaryConfig.subgrid_fallback_tols: tuple[float, ...] =
  (1e-7, 1e-6, 1e-5, 3e-5, 1e-4, 3e-4)`.
- `src/fitqc/boundary.py`:
  - new `_check_excess_mass_subgrid(u_sorted, subgrid_tols,
    excess_ratio)` — delta-function gate via
    `tail_mass(u_sorted, 1e-12) > 0`, then ascending-tol scan for
    the smallest tol where mass > tol × excess_ratio.
  - call sites in `run_boundary_qc` immediately after the existing
    `_check_excess_mass` calls; only invoked when the primary path
    returned `det=False`. M2 and M3 blocks unchanged.
- `tests/test_boundary.py::TestSubgridFallback`: 4 tests covering
  the delta-pileup-below-floor case, the uniform-FP guard, and two
  direct unit tests of `_check_excess_mass_subgrid`.

## Validation

- `python dispatches/diagnose_boundary_24.py` → TP=24, FN=0, FP=0, TN=0.
- `python analyze_overrides.py` → `all-on` column shows all 12
  parameters with `lo_det=T, hi_det=T`. M3 helps 1/24 (w_const
  lower, unchanged); M2 helps 0/24 (unchanged).
- `python -m pytest tests/ -q` → 422 passed (418 prior + 4 new).
- `git diff --name-only dispatches/ground_truth_validation.csv` →
  empty.
- `git diff src/fitqc/boundary.py | grep -E "Mechanism [123]|spread.pileup"`
  → empty (no M1/M2/M3 contamination).

## Out-of-scope items deferred

- `t_star` magnitude calibration vs histograms (Task C
  `calibration-tolerance-mags`). The fallback returns the smallest
  tol with excess; for broad pileups (e.g., e_w_p2) the chosen value
  is conservative and may need widening.
- Interior stickiness for vy, vz, e_w_p1, e_w_p2, e_w_a (Task D
  `calibration-interior-det`).
- End-to-end mask validation (Task E).
