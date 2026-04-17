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
| 3 | e_dv_ap   | lower | 0.000000  | |x|<1e-2 (interior†) | 3.33e-05  | 1.00e-03  | 1.48    | OFF      | t_star=0.0 substituted with fallback tol 1e-3 per FN diag row #1 (ratio=6.65); hint_u = 1e-2/300 = 3.33e-05; Δ ≈ +1.5 dec. See interpretation caveat below |
| 4 | e_dv_ap   | upper | 0.011580  | |x|<1e-2 (interior†) | 3.33e-05  | 1.16e-02  | 2.54    | OFF      | Primary detection (pre-B); hint_u = 3.33e-05; t_star is 2.5 dec above. See interpretation caveat |
| 5 | e_dv_pp   | lower | 0.117810  | |x|<1e-2 (interior†) | 6.67e-05  | 1.18e-01  | 3.25    | OFF      | Primary detection; hint_u = 1e-2/150 = 6.67e-05; t_star is 3.3 dec above. See interpretation caveat |
| 6 | e_dv_pp   | upper | 0.041320  | |x|<1e-2 (interior†) | 6.67e-05  | 4.13e-02  | 2.79    | OFF      | Primary detection; hint_u = 6.67e-05; t_star is 2.8 dec above. See interpretation caveat |
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
| 19 | e_w_p1   | lower | 0.001450  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only ("|x|<1e-2 interior spike guess"); pre-B TP |
| 20 | e_w_p1   | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback tol≈1e-3 per FN diag row #6 |
| 21 | e_w_p2   | lower | 0.001000  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only ("|x|<2e-1 interior spike guess"); pre-B TP |
| 22 | e_w_p2   | upper | 0.000000  | —                    | —         | —         | —       | NO HINT  | Interior-only note; former FN; fallback tol≈1e-7 per FN diag row #10 (35% delta at u=1) |
| 23 | e_w_a    | lower | 0.000100  | —                    | —         | —         | —       | NO HINT  | CSV note interior-only ("two interior spikes"); pre-B TP |
| 24 | e_w_a    | upper | 0.096600  | —                    | —         | —         | —       | NO HINT  | Interior-only note; pre-B TP. Note: t_star=0.0966 is ~10% of range — aggressive cut; follow-up visual review warranted |

† **Interpretation caveat for rows 3–6.** The dispatch cites `e_dv_ap`'s
note `log x and log |x| both look like noise for |x| < 1e-2` as a scale
hint. Geometrically, that note describes noise in the *interior* of the
distribution (near x=0, which for `e_dv_ap`/`e_dv_pp` is the center of
the [-150,150] / [-75,75] domains), not the *boundary* pileup at
x=±L=±U. The pipeline's boundary detection looks for delta pileups near
u=0 and u=1 (the domain edges), which are at x=±150 / x=±75. Applying
`|x|<1e-2` as a boundary scale is therefore a cross-domain comparison.
Two valid readings:
- **Literal (used above):** take the CSV note as a hint regardless of
  its geometric meaning → 4 OFF cases all concentrated on these two
  parameters.
- **Geometric:** treat these notes as interior-only → rows 3–6 become
  NO HINT; summary becomes 2 WITHIN, 22 NO HINT, 0 OFF.

This ambiguity is flagged here rather than resolved unilaterally.

## Summary

- WITHIN: 2 / 24  (A_He lower, vx upper)
- OFF:    4 / 24  (e_dv_ap lower+upper, e_dv_pp lower+upper) — all
  dependent on the interpretation caveat above
- NO HINT: 18 / 24

Of the 6 cases where any CSV note is even arguably applicable, 4 classify
OFF under the literal reading and 0 under the geometric reading.
Per the dispatch Open Items (L115–116, "if ±1 decade flags an
unexpectedly large fraction of cases, stop and surface the distribution"),
this concentration of OFF cases on a single interpretation-sensitive
note pair is explicitly surfaced.

## OFF-case disposition

All 4 OFF cases share the same root evidence: the CSV `|x|<1e-2` note
for `e_dv_ap`/`e_dv_pp`. Recommended follow-up:

1. **User clarification**: confirm whether the note was intended as a
   boundary scale hint or an interior observation. The answer
   reclassifies all 4 at once.
2. **If literal reading holds**: spawn a production task to investigate
   why primary-path detection on `e_dv_ap` upper, `e_dv_pp` lower, and
   `e_dv_pp` upper returns `t_star` 2.5–3.3 decades coarser than the
   documented 1e-2 scale — likely Kneedle elbow detection on the
   (quantile, tolerance) curve before `_check_excess_mass` could
   validate at a finer scale. This is distinct from the former-FN set
   handled by the sub-grid fallback (B).
3. **If geometric reading holds**: reclassify as NO HINT and close the
   open item; consider amending the CSV note column to separate
   boundary hints from interior observations in a future dispatch.

## Other follow-up notes (non-OFF, worth flagging)

- **w_const lower (row 17)**: `t_star = 0.250` is a 25% cut of the 145
  range. This aligns with the existing `project_override_review.md`
  concern about M2 producing a 78% lower-cut; the mask-validation task
  (E) should verify this cut matches the visual pileup.
- **e_w_a upper (row 24)**: `t_star = 0.0966` is ~10% of range. Also
  warrants mask-validation attention.
- Neither can be classified against the CSV under current notes.

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
