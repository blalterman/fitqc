# Dispatch: Build swefc.h5 calibration harness

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** code + analysis
**CPM task:** `calibration-swefc-harness` (new)
**Depends on:** `calibration-swefc-ground-truth` (fixture must exist)

## Scope

Build `analyze_swefc_calibration.py` at repo root — a new, swefc-specific
calibration harness that loads the full `swefc.h5` dataset, runs the
existing `src/fitqc/boundary.py` detection path per parameter, and
compares results against the swefc ground-truth fixture from the
arbitration dispatch. **Do not modify `analyze_overrides.py` or
`src/fitqc/`.** The harness is a driver only.

## Motivation

The 10k parquet subset + `ground_truth_validation.csv` are no longer the
calibration target — the user has firmed up a full-dataset ground truth
from visual inspection. The subset remains for unit tests / regression
anchoring. The swefc harness is how we measure detection quality on the
full distribution going forward.

## Read First

1. `dispatches/ground_truth_swefc.json` (from arbitration dispatch).
2. `dispatches/plot_swefc_fit_param_hists.py` — HDF5 load pattern:
   `pd.read_hdf(H5, key="ppa12_apeq")`, MultiIndex column tuples
   (`("v_param", "x", "p1")` etc.). Reuse `BASE_PARAMS` tuple list.
3. `analyze_overrides.py` lines 1–80 — driver ergonomics to parallel:
   `BoundaryConfig(use_quantile_analysis=True, refine_transition=True,
   grid_mode="progressive")`, `fitqc.boundary as bmod`.
4. `src/fitqc/boundary.py:_compute_quantile_curves_boundary`
   (lines 148–218) — per-parameter pure function; signature:
   `(u_sorted, tol_grid, quantile_grid) -> (curves, t_star_list)`.
5. `src/fitqc/config.py` — `BoundaryConfig` knobs (`grid_mode`,
   `quantile_grid`, `pileup_threshold`, `excess_ratio`,
   `refine_transition`).

## Harness structure

1. **Loader.** `load_swefc(h5_path)` → DataFrame with MultiIndex
   columns. Assert file exists and optionally checksum.
2. **Per-parameter driver.** Iterate the 12 parameters in the swefc
   fixture; for each, extract the column, drop NaN, normalize to
   `u ∈ [0,1]` the same way `analyze_overrides.py` does, call
   `_compute_quantile_curves_boundary` with the shared `BoundaryConfig`
   defaults.
3. **Comparison.** Load swefc fixture; for each parameter report
   pass/fail on lower/upper/interior detection vs bullet-list truth.
   Tabulate to stdout and to `dispatches/swefc_calibration_report.md`.
4. **Figure output.** `figures/swefc_calibration_report.pdf` — one
   panel per parameter with boundary markers and detected `t_star`s
   overlaid, styled like the existing override overview PDFs.

## CLI

```
python analyze_swefc_calibration.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json \
  --output-report dispatches/swefc_calibration_report.md \
  --output-figure figures/swefc_calibration_report.pdf \
  [--param v_param.y.p1]      # optional single-parameter filter
```

`swefc.h5` lives at repo root and is gitignored — do not attempt to
commit it.

## Validation protocol

1. **Bullet coverage.** For each of the 12 parameters, the report shows
   asserted-vs-detected for lower/upper/interior. Mismatches listed
   explicitly; no silent failures.
2. **Test-suite no-regression.** `pytest tests/ -q` still passes at
   post-C1 baseline.

## Acceptance Criteria

- [ ] `analyze_swefc_calibration.py` committed at repo root.
- [ ] `python analyze_swefc_calibration.py --h5 ./swefc.h5` runs
      end-to-end and writes report + figure.
- [ ] Bullet coverage table reports pass/fail per parameter against
      `ground_truth_swefc.json`.
- [ ] `analyze_overrides.py` unchanged (byte-identical).
- [ ] `src/fitqc/` unchanged.
- [ ] `pytest tests/ -q` passes at baseline.
- [ ] New harness-level smoke test at `tests/test_swefc_harness.py`
      that stubs a small HDF5 fixture (or parametrizes on the parquet
      subset) to exercise loader + driver.

## Anti-Patterns

- Do NOT extend `analyze_overrides.py` — new file only.
- Do NOT modify `src/fitqc/boundary.py` or `config.py`. If detection
  needs tuning, raise an issue; out of scope here.
- Do NOT commit `swefc.h5` to the repo.
- Do NOT silently reshape the ground-truth fixture — if schema needs
  extension, go back to the arbitration dispatch.
- Do NOT re-open C1 grid-resolution if a parameter misbehaves on full
  data — branch a `grid-resolution-swefc-followup` dispatch instead.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Harness end-to-end
python analyze_swefc_calibration.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json

# No regression
python -m pytest tests/ -q
python analyze_overrides.py   # byte-identical to prior output
```

## Out of Scope

- C4 (broad-pileup algorithm) — independent track.
- D delta re-validation — separate dispatch.
- Updating parent plan Task E — user-approval-required amendment, not
  this dispatch.
- CPM sync — deferred.

## Timing note

C4 (broad-pileup algorithm) modifies
`_compute_quantile_curves_boundary`. This harness depends on that
function. Ship this dispatch against the current implementation; after
C4 merges, re-run the harness and refresh the report — do not block
this on C4.
