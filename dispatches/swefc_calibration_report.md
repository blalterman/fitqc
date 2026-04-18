# swefc.h5 calibration report

- Generated: 2026-04-18 05:36:24
- Dataset: `swefc.h5` key `ppa12_apeq`
- Ground truth: `dispatches/ground_truth_swefc.json`
- Config: `BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode="progressive")`, `InteriorConfig(use_quantile_analysis=True)`

## Summary

- Lower pass: **12/12**
- Upper pass: **12/12**
- Interior pass: **11/12**
- All-three pass: **11/12**

## Per-parameter results

| parameter | n | lower (truth/detected) | upper (truth/detected) | interior (truth/detected) | t_lo_star | t_hi_star | interior hits (loc: eps*) |
|---|---|---|---|---|---|---|---|
| `v_param.x.p1` | 7549989 | true/true (PASS) | true/true (PASS) | [—] false/false (PASS) | 1e-07 | 0.0001 | — |
| `v_param.y.p1` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.0001 | 1e-07 | 0: 0.0005 |
| `v_param.z.p1` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.0001 | 0.0001 | 0: 0.000295 |
| `w.const` | 7549989 | true/true (PASS) | true/true (PASS) | [—] false/false (PASS) | 0.0001 | 0.0001 | — |
| `n_param.p1` | 7549989 | true/true (PASS) | true/true (PASS) | [—] false/false (PASS) | 0.00119 | 1e-07 | — |
| `n_param.p2` | 7549989 | true/true (PASS) | true/true (PASS) | [—] false/false (PASS) | 0.000138 | 1e-07 | — |
| `e.w.p1` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.000419 | 0.001 | 0: 0.000406 |
| `e.w.p2` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.0001 | 1e-07 | 0: 0.0005 |
| `e.w.a` | 7549989 | true/true (PASS) | true/true (PASS) | [0,-25] true/true (PASS) | 0.0001 | 0.0969 | -25: 0.000644 |
| `e.dv.pp` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.117 | 0.0407 | 0: 6.65e-06 |
| `e.dv.ap` | 7549989 | true/true (PASS) | true/true (PASS) | [0] true/true (PASS) | 0.0001 | 0.000643 | 0: 0.000142 |
| `ab.a` | 7549989 | true/true (PASS) | true/true (PASS) | [1] true/false (FAIL) | 0.016 | 0.0001 | — |

## Mismatches

- `ab.a` — interior: truth=True detected=False
  - note: A_He. Optimizer x0=0 (pipeline fact) coincides with L=0, but the empirical interior spike is at x=1 — NOT at x0. The 120,712 samples at exactly x=0 are lower-boundary stickiness (covered by lower=true). Interior spike at x=1 is ~3.2K excess over ~14.7K baseline per ab_a_interior_zoom.pdf 2026-04-18 — a ~22% bump, weaker than current detector tuning. Upper shelf at U=25 (32,459 samples at x=25).
