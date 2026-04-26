# Dispatch: D (interior-det) full re-validation on swefc.h5

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** analysis
**CPM task:** `calibration-interior-det-swefc` (new; follow-on to D)
**Depends on:** `calibration-swefc-harness` (harness must run)

## Scope

Run interior detection against all 12 bullet-list parameters on
`swefc.h5` using `analyze_swefc_calibration.py`. Report detected vs
asserted interior loci per parameter. In addition, produce a high-res
histogram plot of `ab.a` restricted to x ∈ [0, 2.5] at the current
diagnostic resolution so the user can estimate the internal sticky
point.

## Parameter set (full pass)

All 12 bullet-list parameters. Interior assertions concentrate on:

- `v_param.y.p1` — interior locus
- `v_param.z.p1` — interior locus
- `e.w.p1` — interior (log-x-bounded)
- `e.w.p2` — interior (log-x-bounded)
- `e.w.a` — two interior loci: 0 and -25
- `e.dv.pp` — interior
- `e.dv.ap` — interior
- `ab.a` (A_He) — interior + [0, 2.5] zoom plot

Parameters with no interior assertion (vx, w_const, np1, np2) are
included to confirm no false-positive interior detections on full data.

## Read First

1. `dispatches/ground_truth_swefc.json` (from arbitration dispatch).
2. `analyze_swefc_calibration.py` (from harness dispatch).
3. `src/fitqc/interior.py` — current interior detection pass.
4. Parent plan D entry in
   `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`.

## Investigation protocol

1. Run the swefc harness across all 12 parameters.
2. For each parameter with an interior assertion: compare detected
   loci to the JSON fixture's `interior_locations`.
3. For each parameter without an interior assertion: confirm no
   interior detection.
4. Tabulate pass/fail + detected-vs-asserted deltas.
5. If a parameter fails, stratify root cause into one of:
   (a) detection threshold, (b) locus precision, (c) multi-modal
   handling (e_w_a), (d) false positive. Report only; do not fix.
6. Produce `figures/swefc_ab_a_zoom_0_to_2.5.pdf`: histogram of `ab.a`
   on x ∈ [0, 2.5] at the same resolution used by
   `dispatches/plot_swefc_fit_param_hists.py` (reuse its binning
   strategy on the sliced data).

## Acceptance Criteria

- [ ] `dispatches/swefc_interior_det_report-2026-04-18.md` committed,
      one row per parameter with detected vs asserted interior loci
      and pass/fail.
- [ ] `figures/swefc_ab_a_zoom_0_to_2.5.pdf` committed (or output path
      documented; figure goes to the figures directory).
- [ ] Any failures root-caused into one of the four categories above;
      no silent fixes.
- [ ] `src/fitqc/interior.py` unchanged (reporting only).
- [ ] No test-suite regressions.

## Anti-Patterns

- Do NOT tune `interior.py` in this dispatch.
- Do NOT substitute bullet-list assertions with harness outputs if
  they disagree — bullets (encoded in the JSON fixture) win for swefc.
- Do NOT change `ab.a` bin counts or axis treatment relative to the
  existing diagnostic plot; the zoom is a slice, not a re-styling.

## Out of Scope

- Fixes to interior detection.
- Subset CSV re-validation.

## Open Items

- For `e.w.a`: report format for multi-locus detection (0 AND -25).
  Executor proposes a format in the plan-draft step.
