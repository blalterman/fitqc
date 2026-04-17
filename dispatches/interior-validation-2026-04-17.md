# Interior Detection Validation Results

**Date:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Harness:** `dispatches/diagnose_interior_12.py`
**Ground truth:** `dispatches/ground_truth_validation.csv` (`interior` column)

## Post-review addendum (2026-04-17)

This document was updated after initial commit following user review:

- **np2 "FP" reinterpreted.** A hi-res histogram
  (`figures/np2/np2_interior_hires.png`, script
  `dispatches/diagnose_np2_hires_hist.py`) reveals 1.5% of samples at
  exactly `|x|=0` — a real pileup. The detector is likely correct; the
  CSV claim of "no interior stickiness" was made from ratio plots that
  masked the direct-value pileup. See revised "Algorithmic FP: np2"
  section below.
- **e_w_a secondary x0=-25 calibration added.**
  `dispatches/plot_all_ppa12_diagnostics.py` now appends a second
  overview page for e_w_a at `x0=-25` and saves
  `*_interior_diagnostics_x0neg25.png` plus `*_interior_elbows_x0neg25.png`.
  Secondary detector run: `spike_detected=True, spike_z_loc=0.005,
  eps_star=1e-12`.
- **Follow-up list trimmed.** #3 (CSV note sharpening) completed in
  this dispatch; #4 (multi-spike detection) deferred per user.

## Summary

| Class | Count | Parameters |
|-------|------:|:-----------|
| TP    | 7 | A_He, e_dv_ap, e_dv_pp, vy, e_w_p1, e_w_p2, e_w_a |
| FN    | 0 | — |
| FP    | 1 | np2 |
| TN    | 0 | — |
| SKIP  | 4 | np1, vx, vz, w_const |

**Evaluable rows (x0 available):** 8. Agreement on evaluable rows: 7/8 (87.5%).

The detector recovers every CSV-confirmed interior spike (no false
negatives). One false positive (np2) and four SKIP classifications (x0
null in metadata) require follow-up.

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
| vz      | None | True  | —     | —     | —        | SKIP | **my guess** |
| w_const | None | False | —     | —     | —        | SKIP | (empty) |
| e_w_p1  | 0    | True  | True  | 0.005 | 1.33e-09 | TP   | **my guess** |
| e_w_p2  | 0    | True  | True  | 0.005 | 1.10e-08 | TP   | **my guess** |
| e_w_a   | 0    | True  | True  | 0.045 | 1.00e-12 | TP   | confirmed (2 spikes) |

## "my guess" disposition (acceptance criterion)

Three CSV rows carry the "my guess" tag:

- **`vz`** — CSV: `interior=0` ("my guess |x| < 1e-1"); metadata: `x0=null`.
  Detector SKIPs (requires scalar x0). **Algorithmic gap** — the detector
  as designed cannot evaluate moment-based parameters. This is neither a
  sharpenable note nor a routine FN; it is a **follow-up design
  question**:
  - Option A: extend `interior.py` to support `x0=None` by treating
    `|x|` as distance from 0 when metadata has no scalar x0.
  - Option B: revise CSV/metadata to drop the interior claim for vz
    until the detector supports moment-based x0.
  - User decision required (CSV numeric flip requires user approval
    regardless).

- **`e_w_p1`** — CSV: `interior=0` ("my guess |x| < 1e-2"); detector:
  TP, `spike_z_loc=0.005`, `eps_star=1.33e-9`. **Guess confirmed by
  detector.** Recommendation: sharpen CSV note to record confirmation
  (note only; numeric unchanged).

- **`e_w_p2`** — CSV: `interior=0` ("my guess |x| < 2e-1"); detector:
  TP, `spike_z_loc=0.005`, `eps_star=1.10e-8`. **Guess confirmed by
  detector.** Recommendation: sharpen CSV note to record confirmation
  (note only; numeric unchanged).

## Algorithmic FP: np2 — revised after hi-res inspection

CSV row for np2:
- `interior=None`
- `note`: "No interior stickiness visible in np2/np1 or np2/(np1+np2)
  ratio plots."

**Initial classification (FP) looks incorrect.** A high-resolution
histogram (`dispatches/diagnose_np2_hires_hist.py` →
`figures/np2/np2_interior_hires.png`) reveals that 1507 of 100000
samples (1.5%) have `|x - 0| < 1e-6`, with `min(|x|) = 0` exactly.
This is a real pileup of samples at x=0, not a numeric-precision
artifact.

The CSV "no interior stickiness" judgment was made from the np2/np1
and np2/(np1+np2) ratio plots, which could mask a direct-value pileup.
The detector is looking at the raw np2 distribution and finding a
genuine spike.

**Proposed disposition:** treat np2 as a **detector TP vs a stale CSV
claim**, not an algorithmic FP. The CSV `interior` value for np2
should likely flip from `None` to a numeric indicating stickiness at
x=0, but this is a **numeric-column change** and requires explicit
user approval. User should inspect
`figures/np2/np2_interior_hires.png` and confirm.

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

1. **np2 ground-truth reconciliation** — hi-res inspection shows a
   real 1.5% pileup at `|x|=0` (see
   `figures/np2/np2_interior_hires.png`). The detection is likely
   correct; CSV claim is likely stale. **Action:** user reviews the
   figure and decides whether to flip np2's CSV `interior` value from
   `None` to a numeric value reflecting the pileup. Numeric flip
   requires explicit user approval (dispatch anti-pattern).
   Suggested task ID: `calibration-interior-np2-csv-update`.
2. **Moment-based x0 support** — `np1`, `vx`, `vz`, `w_const` have
   `x0=null` in metadata (moment-based x0). Options:
   - **Option A — set vz x0=0 in CSV and metadata JSON.** Physically
     defensible for vz (velocity ⊥ ecliptic, centered near 0).
     *Does not generalize* to vx (centered near bulk solar-wind
     speed) or np1/w_const (non-negative with x0 inside range).
   - **Option B — extend `interior.py` to support `x0=None`** by
     treating `|x|` as distance from 0.
   - **Option C — drop the vz interior claim** until the detector
     supports moment-based x0.
   User decision required; pending.
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
