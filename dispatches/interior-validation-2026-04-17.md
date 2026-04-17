# Interior Detection Validation Results

**Date:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Harness:** `dispatches/diagnose_interior_12.py`
**Ground truth:** `dispatches/ground_truth_validation.csv` (`interior` column)

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

## Algorithmic FP: np2

CSV row for np2:
- `interior=None`
- `note`: "No interior stickiness visible in np2/np1 or np2/(np1+np2)
  ratio plots."

The note is **confirmed** (not "my guess"), so per dispatch protocol
step 3 this disagreement is flagged as a **suspected algorithmic FP**
without visual re-inspection.

Diagnostic observation: `eps_star=1.00e-12` is the floor of the eps
grid (`eps_log10_min=-12`). A detection at the grid edge can indicate
either:
- A genuinely ultra-tight concentration at x0=0 below the grid
  resolution, OR
- Numeric-precision artifact rather than a physical pileup.

Given CSV confirmation that np2 shows no visible interior stickiness
in any ratio plot, the grid-edge eps_star supports the latter
interpretation. Follow-up: investigate why `run_interior_qc` triggers
spike detection on np2 despite no visible histogram spike.

## Observations (diagnostic, not acceptance-driven)

**Grid-edge eps_star in TP rows (vy, e_w_a).** Both return
`eps_star=1.00e-12` — the same grid floor that flags np2 as FP. For
vy/e_w_a the spike is visually confirmed; for np2 it is not. The
detector currently cannot distinguish "genuine ultra-narrow spike" from
"numeric-precision artifact" when eps_star saturates at the grid
minimum. A follow-up task could consider widening `eps_log10_min`,
adding a minimum-mass gate, or a separate significance test.

**`e_w_a` double-spike handling.** CSV records 2 spikes (at 0 and ~-25).
`InteriorResult.spike_z_loc` is a single scalar; detector reported
`spike_z_loc=0.045`. Classified TP because `spike_detected=True` —
acceptable by classification rule, but the detector cannot report
multiple spikes by design. Not an algorithmic miss on this run;
documented as a known design limitation.

## Follow-up tasks recommended

1. **np2 FP investigation** — root-cause the spurious detection on
   np2. Likely related to grid-edge eps_star interaction with
   numeric precision. Suggested task ID: `calibration-interior-np2-fp`.
2. **Moment-based x0 support** — decide between extending
   `interior.py` to handle `x0=None` or revising the ground-truth
   claim for vz. Suggested task ID: `calibration-interior-moment-x0`.
3. **CSV note sharpening** (this dispatch): sharpen e_w_p1 and e_w_p2
   notes to record detector confirmation.
4. **Multi-spike detection** (optional) — consider extending
   `InteriorResult` to report all detected spikes, not just the most
   prominent. Relevant for e_w_a. Not urgent — classification is
   correct on this dataset.

## Assumptions and Caveats

- `eps_star=1e-12` values are at the configured grid floor. Treating
  them as "detections" is the current detector contract; whether they
  correspond to physically meaningful pileups is an open question.
- The harness uses default `InteriorConfig()`. Production behavior
  matches by design (no tuning applied).
- SKIP classification for x0=null is a harness convention, not a
  detector output. The detector is never called for those rows.
- CSV numeric `interior` values were not modified by this validation.
  Any flips require explicit user approval (per dispatch anti-pattern).

## Reproducibility

```bash
cd /Users/balterma/observatories/code/fitqc
python dispatches/diagnose_interior_12.py
# Expected: 12-row markdown table + "TP=7 FN=0 FP=1 TN=0 SKIP=4"
```
