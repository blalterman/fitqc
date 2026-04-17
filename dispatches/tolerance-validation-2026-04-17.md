# Tolerance magnitude validation — 2026-04-17

Analysis-only validation of `t_star` magnitudes against the ground truth
CSV scale hints for all 24 (parameter, side) detected boundary pileups
under the `all-on` config. Dispatch:
`dispatches/dispatch-tolerance-mags-2026-04-17.md`.

## Inputs

- `dispatches/override_review_results.md` — `t_lo_star` / `t_hi_star`
  in the `all-on` rows.
- `dispatches/ground_truth_validation.csv` — `L`, `U`, `note` per parameter.
- `dispatches/boundary-fn-diagnostics-2026-04-17.md` — per-FN "True scale"
  tol for 10 of the 24 cases; used when `t_star == 0.0` and the case
  was a former FN.

## Method

1. `t_star` is in normalized u-space (`u = (x - L) / (U - L)`; boundary.py
   L149, L160).
2. CSV scale hints are in real units. Convert: `u_hint = s_real / (U - L)`.
   For a range hint (5–12 km/s), use the midpoint (8.5 km/s).
3. When `t_star == 0.0` (delta exactly at u=0 or u=1), substitute the
   fallback "True scale" tol from `boundary-fn-diagnostics-2026-04-17.md`
   if that case appears in the per-FN table. Justification stated inline.
4. `|Δ decades| = |log10(compare_t) - log10(u_hint)|`; WITHIN ≤1, OFF >1.
5. No CSV boundary-relevant hint → NO HINT; justify from the FN-diagnostic
   "True scale" tol when available, else from interior-only note status.

## Results

| # | Parameter | Side  | t_star    | CSV hint (real)      | hint (u)  | compare_t | |Δ dec| | Verdict  | Justification |
|---|-----------|-------|-----------|----------------------|-----------|-----------|---------|----------|---------------|
| 1 | A_He      | lower | 0.016420  | ~1e-1 (x scale)      | 4.00e-03  | 1.64e-02  | 0.61    | WITHIN   | Stickiness region extends to ~1e-1 in x; range=25; hint_u = 0.1/25 = 4.00e-03; t_star within 0.6 dec |
| 2 | A_He      | upper | 0.000100  | —                    | —         | —         | —       | NO HINT  | CSV note addresses lower boundary only (A_He in [0,25]); upper not documented |
| 3 | e_dv_ap   | lower | 0.000000  | —                    | —         | —         | —       | NO HINT  | CSV note "noise for \|x\|<1e-2" describes interior stickiness (near x=0), not the boundary pileup at u=0 — interior stickiness is out-of-scope for this task (handled in a separate chat); former FN, fallback tol≈1e-3 per FN diag row #1 |
| 4 | e_dv_ap   | upper | 0.011580  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only (see row 3); no boundary scale hint available; pre-B TP |
| 5 | e_dv_pp   | lower | 0.117810  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only (see row 3); no boundary scale hint available; pre-B TP |
| 6 | e_dv_pp   | upper | 0.041320  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only (see row 3); no boundary scale hint available; pre-B TP |
| 7 | np1       | lower | 0.001551  | —                    | —         | —         | —       | NO HINT  | CSV note empty; pre-B TP; fallback not invoked |
| 8 | np1       | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Former FN; fallback true scale tol≈1e-7 per FN diag row #7; t_star=0 lands exactly on the delta-at-u=1 pileup |
| 9 | np2       | lower | 0.000366  | —                    | —         | —         | —       | NO HINT  | CSV note describes interior only ("No interior stickiness visible"); pre-B TP |
| 10 | np2      | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Former FN; fallback true scale tol≈1e-5 per FN diag row #8 (2 samples at u=1) |
| 11 | vx       | lower | 0.000000  | —                    | —         | —         | —       | NO HINT  | CSV note addresses upper only; former FN; fallback true scale tol≈1e-7 per FN diag row #9 |
| 12 | vx       | upper | 0.001590  | 5–12 km/s inward     | 8.50e-03  | 1.59e-03  | 0.73    | WITHIN   | range=1000; hint_u = 8.5/1000 = 8.50e-03; t_star is 0.7 dec below midpoint of stated 5–12 km/s band |
| 13 | vy       | lower | 0.000000  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only; former FN; fallback true scale tol≈1e-7 per FN diag row #2 |
| 14 | vy       | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback true scale tol≈1e-7 per FN diag row #3 |
| 15 | vz       | lower | 0.000000  | —                    | —         | —         | —       | NO HINT  | CSV note describes interior only ("|x|<1e-1" interior spike guess); former FN; fallback tol≈1e-7 per FN diag row #4 |
| 16 | vz       | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback tol≈1e-7 per FN diag row #5 |
| 17 | w_const  | lower | 0.250000  | —                    | —         | —         | —       | NO HINT  | CSV note empty; pre-B TP. Note: t_star=0.25 is a very aggressive cut (25% of range); `project_override_review.md` previously flagged M2 producing 78% lower-cut — follow-up visual review warranted |
| 18 | w_const  | upper | 0.000100  | —                    | —         | —         | —       | NO HINT  | CSV note empty; pre-B TP |
| 19 | e_w_p1   | lower | 0.001450  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only (interior spike at x0=0, eps_star=1.33e-9 per 2026-04-17 interior.py); pre-B TP |
| 20 | e_w_p1   | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback tol≈1e-3 per FN diag row #6 |
| 21 | e_w_p2   | lower | 0.001000  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only (interior spike at x0=0, eps_star=1.10e-8 per 2026-04-17 interior.py); pre-B TP |
| 22 | e_w_p2   | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback tol≈1e-7 per FN diag row #10 (35% delta at u=1) |
| 23 | e_w_a    | lower | 0.000100  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only ("two interior spikes"); pre-B TP |
| 24 | e_w_a    | upper | 0.096600  | —                    | —         | —         | —       | NO HINT  | Interior-only note; pre-B TP. Note: t_star=0.0966 is ~10% of range — aggressive cut; follow-up visual review warranted |

## Scope: interior stickiness is out-of-scope

The CSV `note` column mixes boundary observations with interior stickiness
descriptions. Interior stickiness is being handled in a separate chat; this
task addresses boundary pileup only. Therefore any CSV note describing
interior behavior (`|x|<1e-2` noise for `e_dv_ap`/`e_dv_pp`, the `|x|<1e-1`
interior-spike guess for `vz`, the now-confirmed interior spike descriptions
for `e_w_p1`/`e_w_p2` (sharpened in commits `a890205`/`ac89109`), and the
explicit "interior spike" / "interior stickiness" wording for `vy`/`e_w_a`)
is **not** reused as a boundary scale hint here. Rows whose boundary hint
would otherwise have come only from such notes are classified NO HINT.

Under this scoping rule, only two CSV notes carry boundary-relevant scale
information: `A_He` lower ("stickiness region extends to ~1e-1", explicitly
boundary because L=x0=0) and `vx` upper ("5–12 km/s inward from U=-200",
explicitly boundary).

## Summary

- WITHIN: 2 / 24  (A_He lower, vx upper)
- OFF:    0 / 24
- NO HINT: 22 / 24

The two hinted cases both land within ±1 decade. No OFF cases under the
scoping rule above. The dispatch Open Item L115–116 (large-fraction
threshold trigger) does not fire.

## Follow-up notes (worth flagging, independent of hints)

- **w_const lower (row 17)**: `t_star = 0.250` is a 25% cut of the 145
  range. This aligns with the existing `project_override_review.md`
  concern about M2 producing a 78% lower-cut; the mask-validation task
  (E) should verify this cut matches the visual pileup.
- **e_w_a upper (row 24)**: `t_star = 0.0966` is ~10% of range. Also
  warrants mask-validation attention.
- **e_dv_pp lower (row 5)**: `t_star = 0.118` is a 12% cut of the 150
  range (~18 km/s). Large relative to the other `e_dv_*` values;
  mask-validation (E) should confirm this reflects a real wide pileup
  rather than elbow-detection overshoot.
- **e_dv_pp upper (row 6)**: `t_star = 0.0413` is a 4% cut (~6 km/s).
  Smaller than row 5 but still worth visual confirmation in E.
- Neither these nor the rows above can be classified against the CSV
  under the current notes.

## Assumptions and caveats

- u-space hint conversion uses a linear `u = (x - L) / (U - L)` map.
  The production pipeline uses the same map (`boundary.py` L149,160);
  this is consistent.
- For `vx`'s "5–12 km/s" band, the midpoint (8.5 km/s) is used. A
  different choice within the band shifts the decades by at most
  log10(12/5) ≈ 0.38, so the WITHIN verdict is robust.
- For `t_star == 0.0` cases (delta at u=0 or u=1), the fallback tol
  is used as the scale proxy for comparison. This is a judgment call
  documented above.
- Interior-only CSV notes are not reused as boundary hints (see caveat
  for rows 3–6 where the dispatch overrides this convention).
- No raw histogram re-inspection was performed; all visual-scale
  evidence comes from the prior FN deep-diagnostic artifact.

## Verification

- `dispatches/ground_truth_validation.csv` unchanged (CSV authoritative).
- No `src/` edits, no config changes.
- Pytest baseline (with the 3 known quantile-test deselects) unchanged
  at 422 passed.
