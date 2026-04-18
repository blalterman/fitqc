# Dispatch: Detector tuning on swefc full-dataset calibration

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** software
**Parent dispatch:** `dispatches/dispatch-swefc-harness-2026-04-18.md`

## Scope

Tune the boundary and interior detectors in `src/fitqc/` so that the
detected cut *widths* (`t_lo_star`, `t_hi_star`, `eps_star`) match
visual expectation on the full 7.55M-sample `swefc.h5` dataset. The
swefc harness at `/Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
reports 12/12 boolean pass, yet
`/Users/balterma/observatories/code/fitqc/figures/swefc_overview.pdf`
shows the cut widths are wrong on nearly every parameter. Fix the
widths; do not weaken the boolean detection.

The parent dispatch explicitly calls out this work as a follow-up and
forbids it there: *"do NOT re-open C1 grid-resolution if a parameter
misbehaves on full data — branch a grid-resolution-swefc-followup
dispatch instead"*. This is that follow-up and unlocks
`src/fitqc/` modifications.

## Motivation

The swefc harness closed the boolean calibration loop (12/12 lower +
upper + interior pass). Visual review of `swefc_overview.pdf` by the
user on 2026-04-18 exposed a second-order issue: the cut thresholds
that downstream filtering would apply are systematically wrong.

Two failure modes dominate:

1. **Exterior under-cut.** Nine of twelve parameters leave visible
   boundary stickiness above the detected `t_lo_star` / `t_hi_star`.
   Shelves that are obvious on the histogram survive the cut.
2. **Interior over-cut on narrow spikes.** Three parameters
   (`v_param.y.p1`, `v_param.z.p1`, `e.w.a` at x0=-25) show interior
   cuts that excise healthy neighbors of the spike.

The user's hypothesis (to validate, not assume): the Kneedle / quantile
elbow stage latches to extreme or smallest-quantile values on 7.5M
distributions in ways that 10K parquet subsets did not expose. The
grid-mode (`progressive` vs `progressive_log`) and the `quantile_grid`
boundaries in `src/fitqc/config.py:BoundaryConfig` are likely suspects.

## Read First

1. `/Users/balterma/observatories/code/fitqc/figures/swefc_overview.pdf`
   — 13-page overview. Each page contains the full plot_parameter_overview
   output (mass curves, quantile elbows, histogram, detected cuts).
   This is the primary input.
2. `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_swefc.json`
   — asserted `L`, `U`, `x0`, `interior_locations`, `lower`, `upper`,
   `interior` per parameter. Authoritative for what should be detected.
3. `/Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
   — harness that must still report 12/12 after tuning. Read for the
   configs in use (`BoundaryConfig(use_quantile_analysis=True,
   refine_transition=True, grid_mode="progressive")` and
   `InteriorConfig(use_quantile_analysis=True)`).
4. `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_swefc_diagnostics.py`
   — overview PDF generator. Uses `grid_mode="progressive_log"`; note
   this differs from the harness. Alignment may be part of the fix.
5. `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py`
   lines 585-end (`run_boundary_qc`) and the refinement path from line
   ~720 (`_refine_elbow_iteratively`, `_subgrid_excess_fallback`).
6. `/Users/balterma/observatories/code/fitqc/src/fitqc/interior.py`
   lines 261-end (`run_interior_qc`).
7. `/Users/balterma/observatories/code/fitqc/src/fitqc/config.py`
   — `BoundaryConfig.quantile_grid` (starts at 1e-5) and
   `BoundaryConfig.subgrid_fallback_tols`. The docstring already notes
   the 1e-5 floor was added for sparse pileups; 7.5M data may need a
   different shape.
8. `/Users/balterma/observatories/code/fitqc/figures/ab_a_interior_zoom.pdf`
   + `/Users/balterma/observatories/code/fitqc/dispatches/inspect_ab_a_interior.py`
   — evidence that `ab.a` x0=0 is correct (120,712 samples at exactly
   x=0). The issue is `eps_star` width, not x0 location.

## Per-parameter findings (2026-04-18 visual review)

| # | parameter | lower | upper | interior | Notes |
|---|-----------|-------|-------|----------|-------|
| 1 | `v_param.x.p1` | under-cut | under-cut | n/a (x0=null) | No visible inflection on tol axis; Kneedle latches to extremes. |
| 2 | `v_param.y.p1` | under-cut | under-cut | over-cut | Quantile elbows appear to latch to the smallest quantile. |
| 3 | `v_param.z.p1` | under-cut | under-cut | over-cut | Same shape as v_param.y.p1, less extreme. |
| 4 | `w.const` | **under-cut (large)** | under-cut (small) | n/a | Broad shelves visible at both L=5 and U=150. |
| 5 | `n_param.p1` | **over-cut (large)** | ok | n/a | Kept region starts ~0.13, but shelf ends ~0.05-0.08. Removes distribution body. |
| 6 | `n_param.p2` | **over-cut (large)** | ok | n/a | Same as n_param.p1. |
| 7 | `e.w.p1` | under-cut | slightly short | ok | Broader lower stickiness missed. |
| 8 | `e.w.p2` | under-cut | under-cut | ok | Interior is fine. |
| 9 | `e.w.a` (x0=0) | under-cut | under-cut | no visible cut | Primary-page interior cut at 0 not visible. |
| 10 | `e.w.a` (x0=-25 secondary) | under-cut | under-cut | over-cut | Interior cut too aggressive at -25. |
| 11 | `e.dv.pp` | under-cut | under-cut | ok | |
| 12 | `e.dv.ap` | under-cut | under-cut | ok | |
| 13 | `ab.a` | ok | under-cut | **FAIL (missed)** | Ground truth corrected 2026-04-18: x=0 is lower-boundary stickiness (L=0, 120,712 samples), not interior. Interior is at x=1 only (~3.2K excess over ~14.7K baseline = ~22% bump). Boolean harness now reports interior=FAIL because the detector's spike criteria (`spike_prominence_min=10`, etc.) are tuned for much sharper spikes. Upper shelf also broader than current cut (32,459 samples at x=25). |

### 2026-04-18 (audit follow-up): `n_param.p2` interior FP at x0=0

The audit-regenerated `figures/swefc_overview.pdf` shows
`n_param.p2` with `interior: FP`. Ground truth says
`interior=false, interior_locations=[]`, but the overview script's
x0-fallback (`primary_loc = x0 = 0` when `interior_locations` is
empty) runs `run_interior_qc` at x0=0 and the detector fires
spuriously. The boolean harness does not show this because it only
iterates `interior_locations`; the FP is overview-only and reflects
detector behavior at the pipeline x0 rather than at any empirical
spike center. Investigate alongside O4 (u-transform of log-scaled
data on `n_param.p1`/`n_param.p2`).

### 2026-04-18 (audit follow-up): preserve `e.dv.ap` interior cut

User visual review of the audit-regenerated overview confirms
`e.dv.ap` interior cut is *perfect*. Tuning must not regress this
cut while addressing the under-cut exterior or the
`v_param.y.p1` / `v_param.z.p1` interior over-cut. Treat `e.dv.ap`
as a fixed reference: any change to interior detector parameters
(`spike_prominence_min`, `eps_grid`, etc.) must leave its
`eps_star` essentially unchanged.

Pattern summary:
- Exterior systematically under-cut (9 of 12 params, both sides).
- Two parameters (`n_param.p1`, `n_param.p2`) are the opposite: lower
  cut too wide. These use log-scaled distributions bounded at 0.01;
  worth checking whether log-scale vs linear u-transform is the root
  cause.
- Interior over-cut on three params; interior under-cut (visually
  invisible) on two (`e.w.a` x0=0, `ab.a`).
- Common thread: Kneedle / quantile elbow behavior degrades on 7.5M
  distributions relative to the 10K subsets that calibrated it.

## Acceptance Criteria

- [ ] `python /Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
      reports 12/12 boolean pass after tuning. Current baseline is 11/12:
      `ab.a` interior fails because the x=1 spike is a ~22% bump over
      baseline, below the detector's prominence tuning. Fix must bring
      this back to pass without new false positives elsewhere.
- [ ] `python /Users/balterma/observatories/code/fitqc/dispatches/plot_all_swefc_diagnostics.py`
      regenerates `figures/swefc_overview.pdf`. User visual review
      confirms: exterior cuts cover the visible shelves in each of the
      9 under-cut parameters without eating the distribution body;
      interior cuts on `v_param.y.p1`, `v_param.z.p1`, and `e.w.a`
      (x0=-25) are narrowed to cover only the spike; `n_param.p1` and
      `n_param.p2` lower cuts no longer eat the distribution body; the
      `ab.a` and `e.w.a` (x0=0) interior cuts are visible on the
      overview.
- [ ] `python -m pytest tests/ -q` passes at baseline (435 tests).
- [ ] `python /Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py`
      regenerates `figures/ppa12_overview.pdf`. TP count on the
      parquet-subset ground truth (`ground_truth_validation.csv` via
      `analyze_overrides.load_ground_truth`) does not regress from the
      pre-tuning baseline.
- [ ] Every `src/fitqc/` edit is justified in its commit message by
      evidence from the overview PDFs, not by intuition.

## Anti-Patterns

- Do NOT modify `dispatches/ground_truth_swefc.json`. It is user-
  arbitrated and authoritative. If a tuning change makes a previously
  `true` detection flip to `false`, that is a regression, not an
  opportunity to re-classify the ground truth.
- Do NOT modify `analyze_swefc_calibration.py` to paper over detection
  changes. The harness is frozen at the scope of the parent dispatch.
- Do NOT tune with the parquet subsets alone. Every change must be
  evaluated against the full 7.55M-sample `swefc.h5`. The 10K subsets
  are what calibrated the current latching behavior.
- Do NOT silently change config defaults without tracing every
  downstream consumer. `BoundaryConfig` defaults are referenced by
  tests and `analyze_overrides.py`. Changes to `quantile_grid`,
  `pileup_threshold`, or `excess_ratio` need the chain-trace
  discipline from `~/.claude/rules/accurate-over-helpful.md`.
- Do NOT treat "more cut" as uniformly better. `n_param.p1` and
  `n_param.p2` are already cutting too much; the direction of the fix
  depends on the parameter.
- Do NOT re-open `_compute_quantile_curves_boundary` without reading
  it in full. The low-level function's contract
  (`(u_sorted, tol_grid, quantile_grid) -> (tol_at_quantile,
  elbows_per_quantile)`) is consumed by both the boundary path and
  the refinement loop; breaking either cascades.

## Open Items for the Executing Session

- O1. Is the root cause in the quantile-grid shape, the Kneedle
  detection, or the u-transform for log-scaled parameters
  (`n_param.p1`, `n_param.p2`)? Investigate before proposing changes.
- O2. Should the harness and the overview generator use the same
  `grid_mode`? Currently the harness uses `progressive` and the
  overview uses `progressive_log`. Alignment may or may not be part
  of the fix — decide explicitly.
- O3. Does the interior detector for `e.w.a` at x0=0 need multi-peak
  handling, or is the single-location call correct and only eps_star
  needs widening?
- O4. For the two `n_param.*` parameters, does the issue live in
  u-transform of log-distributed data, or in the detector seeing the
  natural distribution body as "pileup"?

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Boolean regression check
python analyze_swefc_calibration.py \
  --h5 ./swefc.h5 --truth dispatches/ground_truth_swefc.json

# Visual check (slow: ~12 min on 7.5M rows)
python dispatches/plot_all_swefc_diagnostics.py
# -> inspect figures/swefc_overview.pdf page-by-page

# Test suite
python -m pytest tests/ -q

# Parquet-subset regression
python dispatches/plot_all_ppa12_diagnostics.py
# -> inspect figures/ppa12_overview.pdf for TP count
```
