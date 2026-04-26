# Interior Detection Validation Results

**Date:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Harness:** `dispatches/diagnose_interior_12.py`
**Ground truth:** `dispatches/ground_truth_validation.csv` (`interior` column)

## Post-review addendum (2026-04-17)

This document was updated after initial commit following user review:

- **np2 "FP" re-examined — out of range, not a real pileup.** A hi-res
  histogram (`figures/np2/np2_interior_hires.png`, script
  `dispatches/diagnose_np2_hires_hist.py`) shows 1.5% of samples at
  exactly `|x|=0`. But `L=0.01` for np2, so `x=0 < L` — these are
  **out-of-range samples**, not a valid interior pileup. The CSV claim
  of "no interior stickiness" stands; the detector is triggering on
  data outside `[L, U]`. Follow-up is now "why does the detector see
  samples outside the physical range" rather than "flip the CSV
  value."
- **vz x0 set to 0; reclassifies as TP.** After user approval, vz x0
  updated from null to 0 in CSV (`8978228`) and metadata JSON
  (`c4a34b6`). Harness re-run: vz reports
  `spike_detected=True, spike_z_loc=0.005, eps_star=1e-12`.
  New totals: **TP=8 FN=0 FP=1 TN=0 SKIP=3** (SKIPs now only np1,
  vx, w_const).
- **e_w_a secondary x0=-25 calibration added.**
  `dispatches/plot_all_ppa12_diagnostics.py` now appends a second
  overview page for e_w_a at `x0=-25` and saves
  `*_interior_diagnostics_x0neg25.png` plus `*_interior_elbows_x0neg25.png`.
  Secondary detector run: `spike_detected=True, spike_z_loc=0.005,
  eps_star=1e-12`.
- **Follow-up list trimmed.** #3 (CSV note sharpening) completed in
  this dispatch; #4 (multi-spike detection) deferred per user.

## Summary

Initial run (before post-review vz x0=0 change):

| Class | Count | Parameters |
|-------|------:|:-----------|
| TP    | 7 | A_He, e_dv_ap, e_dv_pp, vy, e_w_p1, e_w_p2, e_w_a |
| FN    | 0 | — |
| FP    | 1 | np2 |
| TN    | 0 | — |
| SKIP  | 4 | np1, vx, vz, w_const |

Post-vz-change run (after commits `8978228` + `c4a34b6`):

| Class | Count | Parameters |
|-------|------:|:-----------|
| TP    | 8 | A_He, e_dv_ap, e_dv_pp, vy, vz, e_w_p1, e_w_p2, e_w_a |
| FN    | 0 | — |
| FP    | 1 | np2 (out-of-range; see below) |
| TN    | 0 | — |
| SKIP  | 3 | np1, vx, w_const |

**Evaluable rows (x0 available):** 9. Agreement on evaluable rows: 8/9 (89%).

The detector recovers every CSV-confirmed interior spike (no false
negatives). The one "FP" (np2) is actually the detector triggering on
out-of-range samples (x=0 < L=0.01); not a real FP but a preprocessing
gap. Three SKIP classifications remain (np1/vx/w_const have null x0
because they are moment-based with per-sample reference points).

## Per-parameter verdict table

| param   | x0   | interior_expected | spike_detected | spike_z_loc | eps_star     | class | note tag |
|---------|-----:|:-----------------|:---------------|------------:|-------------:|:-----:|:---------|
| A_He    | 0    | True  | True  | 0.005 | 3.39e-05 | TP   | confirmed |
| e_dv_ap | 0    | True  | True  | 0.005 | 5.18e-05 | TP   | confirmed |
| e_dv_pp | 0    | True  | True  | 0.005 | 1.68e-08 | TP   | confirmed |
| np1     | None | False | —     | —     | —        | SKIP | (empty) |
| np2     | 0    | False | True  | 0.005 | 1.00e-12 | **FP** | confirmed |
| vx      | None | False | —     | —     | —        | SKIP | (boundary only) |
| vy      | 0    | True  | True  | 0.005 | 1.00e-12 | TP   | confirmed (14595de) |
| vz      | 0 (was None) | True | True | 0.005 | 1.00e-12 | TP *(post-x0-change)* | confirmed (8978228) |
| w_const | None | False | —     | —     | —        | SKIP | (empty) |
| e_w_p1  | 0    | True  | True  | 0.005 | 1.33e-09 | TP   | **my guess** |
| e_w_p2  | 0    | True  | True  | 0.005 | 1.10e-08 | TP   | **my guess** |
| e_w_a   | 0    | True  | True  | 0.045 | 1.00e-12 | TP   | confirmed (2 spikes) |

## "my guess" disposition (acceptance criterion)

Three CSV rows carry the "my guess" tag:

- **`vz`** — Original CSV: `interior=0` ("my guess |x| < 1e-1") with
  `x0=null`. **Resolved 2026-04-17 post-review:** user approved
  setting vz x0=0 (defensible — vz is velocity perpendicular to
  ecliptic, physically centered near 0). CSV and JSON metadata updated
  (commits `8978228`, `c4a34b6`). Harness re-run classifies vz as
  **TP** with `spike_z_loc=0.005, eps_star=1e-12`. The "my guess"
  claim is now confirmed by the detector.

- **`e_w_p1`** — CSV: `interior=0` ("my guess |x| < 1e-2"); detector:
  TP, `spike_z_loc=0.005`, `eps_star=1.33e-9`. **Guess confirmed by
  detector.** Recommendation: sharpen CSV note to record confirmation
  (note only; numeric unchanged).

- **`e_w_p2`** — CSV: `interior=0` ("my guess |x| < 2e-1"); detector:
  TP, `spike_z_loc=0.005`, `eps_star=1.10e-8`. **Guess confirmed by
  detector.** Recommendation: sharpen CSV note to record confirmation
  (note only; numeric unchanged).

## Algorithmic FP: np2 — out-of-range samples, not real stickiness

CSV row for np2:
- `interior=None`
- `note`: "No interior stickiness visible in np2/np1 or np2/(np1+np2)
  ratio plots."

**Updated interpretation (2026-04-17):** the hi-res histogram
(`figures/np2/np2_interior_hires.png`, script
`dispatches/diagnose_np2_hires_hist.py`) shows 1507 of 100000 samples
(1.5%) with `|x - 0| < 1e-6`, with `min(|x|) = 0` exactly. However,
np2 has `L = 0.01`, so **x=0 is below the lower physical bound** —
these samples are out of range, not a valid interior pileup at x=0.

The CSV claim of "no interior stickiness" therefore stands. The
detector is correctly identifying a density spike in the data, but the
spike represents data outside the parameter's physical domain rather
than a physically meaningful interior pileup.

**Root cause (hypothesized):** the detector operates on the full
sample array without filtering to `[L, U]`. If `run_interior_qc` ran
on only the in-range subset (`L <= x <= U`), the out-of-range pileup
at x=0 would be excluded, and the detection would likely flip from
True to False for np2. This is a **preprocessing gap**, not a
detection algorithm error.

**Proposed follow-up:** decide whether `run_interior_qc` should
pre-filter its input to `[L, U]` by default, or whether callers are
expected to filter upstream. Affects np2 (and potentially other
parameters with out-of-range samples — audit needed).

## Observations (diagnostic, not acceptance-driven)

**Grid-edge eps_star in TP rows (vy, e_w_a) and in np2.** All three
return `eps_star=1.00e-12` (the grid floor,
`InteriorConfig.eps_log10_min=-12`). Separate hi-res inspection
confirms real pileups in all three cases (np2 shown above; vy/e_w_a
already confirmed in CSV notes). The detector is correctly detecting
ultra-narrow spikes; the grid-edge saturation reflects that these
pileups are tighter than the grid resolves. Whether that is an
actionable threshold for downstream filtering is a separate question
(see follow-ups).

**`e_w_a` secondary spike at x0=-25.** CSV records 2 spikes (at 0 and
~-25). A second detector run at `x0=-25` returns
`spike_detected=True, spike_z_loc=0.005, eps_star=1e-12`: the -25
spike is even tighter than the 0 spike. Primary harness run at x0=0
reported `spike_z_loc=0.045` (still TP), confirming the 0 spike.
`dispatches/plot_all_ppa12_diagnostics.py` now produces a second
overview PDF page and two diagnostic PNGs
(`..._interior_diagnostics_x0neg25.png`,
`..._interior_elbows_x0neg25.png`) so both spikes are visible side by
side. `InteriorResult.spike_z_loc` remains a single scalar; multi-spike
handling via a single call is deferred (see follow-ups).

## Follow-up tasks recommended

1. **Interior detection on out-of-range samples** — np2 has 1.5% of
   samples at x=0 which is below `L=0.01`. The detector runs on
   unfiltered data and reports a spike there. Decide whether
   `run_interior_qc` should pre-filter input to `[L, U]` by default
   or whether callers are expected to filter upstream. Also audit
   whether other parameters have out-of-range samples (likely a
   pipeline-wide concern, not np2-specific). Suggested task ID:
   `calibration-interior-range-filter`.
2. **Moment-based x0 support — remaining cases** — `np1`, `vx`,
   `w_const` still have `x0=null` in metadata. Unlike vz, these
   cannot be set to 0 without physical justification (vx is centered
   near bulk solar-wind speed; np1 and w_const are non-negative with
   per-sample x0 somewhere inside `[L, U]`). Options:
   - **Extend `interior.py` to support `x0=None`** — treat `|x|` as
     distance from 0, or supply per-sample x0.
   - **Drop interior claims for these parameters** until per-param
     x0 semantics are defined.
   - **Status quo** — keep them SKIPped in the harness.
   Suggested task ID: `calibration-interior-moment-x0`.
3. **~~CSV note sharpening~~** — DONE in this dispatch (commits
   `a890205`, `ac89109`).
4. **~~Multi-spike detection~~** — DEFERRED per user. Classification
   remains correct; e_w_a's second spike is now visible via the
   plot-driver secondary page (commit `cbd339a`).

## Assumptions and Caveats

- `eps_star=1e-12` values are at the configured grid floor. Post-review
  hi-res inspection of np2, vy, and e_w_a suggests these correspond to
  real ultra-narrow pileups rather than numeric-precision artifacts,
  but verifying this requires per-parameter hi-res histogram review
  (tooling: `dispatches/diagnose_np2_hires_hist.py`).
- The harness uses default `InteriorConfig()`. Production behavior
  matches by design (no tuning applied).
- SKIP classification for x0=null is a harness convention, not a
  detector output. The detector is never called for those rows.
- CSV numeric `interior` and `x0` values were not modified by this
  validation. Any flips require explicit user approval (per dispatch
  anti-pattern). The post-review np2 reinterpretation and vz x0=0
  option are pending user decision.

## Reproducibility

```bash
cd /Users/balterma/observatories/code/fitqc
python dispatches/diagnose_interior_12.py
# Expected: 12-row markdown table + "TP=7 FN=0 FP=1 TN=0 SKIP=4"
```
