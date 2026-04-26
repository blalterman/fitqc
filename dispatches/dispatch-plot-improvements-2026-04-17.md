# Dispatch: Plot quality improvements + per-parameter overview

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** software

## Scope

Fix 7 plot quality issues in `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` and add a new single-page per-parameter overview plotter. Work lands as 9 sequential batches (B1–B9), one commit per batch, each with its own verification gate (G1–G9). All batches are plotting-side only; detection code is untouched.

### Batches

**B1 — Driver fix (empty `*_interior_elbows.png`)**
File: `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py` line ~94.
Pass `InteriorConfig(use_quantile_analysis=True)` to `run_interior_qc`. Without the flag, `InteriorResult.quantile_elbows` is None (`src/fitqc/interior.py:184,398`) and the plotter falls through to the placeholder branch at `src/fitqc/plot.py:1505-1509`.

**B2 — `plot_boundary_diagnostics` auto-zoom** (`src/fitqc/plot.py:125-325`)
Compute y-range from the mass-curve magnitude within `tol_grid <= max(t_star, pileup_threshold * 4)`. Compute x-range as `max(t_star * 4, pileup_threshold * 4)`. Apply to the two linear panels. Log-magnitude panel keeps full range.

**B3 — `plot_histogram_tolerance_overlays` log-y + interior cuts** (`src/fitqc/plot.py:637-764`)
Add optional `x0: float | None = None`, `eps_star: float | None = None`, `t_lo_star: float | None = None`, `t_hi_star: float | None = None` kwargs. When `x0` and `eps_star` provided, also remove samples with `|x - x0| < eps_star * max(x0 - L, U - x0)` (matches `src/fitqc/report.py:_build_mask` lines 263-321 and `src/fitqc/interior.py::compute_z`). Draw vertical cut markers when `t_lo_star` / `t_hi_star` supplied. Set `ax.set_yscale("log")` on both panels.

**B4 — `plot_ecdf_tolerance_overlays` t_star markers + zoom** (`src/fitqc/plot.py:492-635`)
Add optional `t_lo_star` / `t_hi_star`. Draw `ax.axvline(t_star, color="red", lw=2)` and legend entry when supplied. When `max(y) - min(y) < 0.05`, zoom: `ax.set_ylim(min(y) - 0.005, max(y) + 0.005)`.

**B5 — `plot_quantile_spacing_overlays` clarity** (`src/fitqc/plot.py:328-489`)
Update title to `"Spacing dq between adjacent samples in the lowest q={q_max:.2g} of values"`. Update y-label to `"Spacing dq = |x[i+1] - x[i]|"`. Add upper-right annotation: `"Compression (smaller dq) = pileup; Expansion (larger dq) = gap"`.

**B6 — `plot_interior_diagnostics` symlog y** (`src/fitqc/plot.py:30-122`)
After the z-histogram bar plot, `ax1.set_yscale("symlog", linthresh=1)` (symlog because counts can be 0).

**B7 — New `plot_parameter_overview`** (`src/fitqc/plot.py`, appended at end)
Signature:
```python
def plot_parameter_overview(
    param_name: str,
    x: np.ndarray,
    x0: float | None,
    L: float,
    U: float,
    interior_result: InteriorResult | None,
    boundary_result: BoundaryResult,
    config: PlotConfig | None = None,
) -> Figure:
```
4×2 grid: raw histogram (log-y) with all cut markers; filtered histogram (log-y) with `"kept N of M samples"` annotation; lower-boundary mass curve (zoomed per B2); upper-boundary mass curve (zoomed); interior z-histogram (log-y); interior mass-curve (log-x). Title shows `param_name`, `L`, `U`, `x0`, and TP/FN status vs `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv`. Footer lists `t_lo_star`, `t_hi_star`, `eps_star`, `lo_det`, `hi_det`, `spike_detected`. Replicate the cut logic from `src/fitqc/report.py:_build_mask` (lines 263-321) inline — do not import the private helper.

**B8 — Driver emits overview PDF** (`dispatches/plot_all_ppa12_diagnostics.py`)
After the 7-figure suite, call `plot_parameter_overview` per parameter and append to `matplotlib.backends.backend_pdf.PdfPages`. Write to `/Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf` (12 pages).

**B9 — Tests** (`tests/test_plot*.py`)
Minimum 5 new tests:
- `test_boundary_diagnostics_zooms_to_pileup_region`
- `test_histogram_overlays_log_y_and_interior_cuts`
- `test_ecdf_overlays_marks_t_star`
- `test_interior_diagnostics_uses_log_y_on_z`
- `test_parameter_overview_smoke` (exercises both `interior_result=None` and populated paths)

### Decisions

| Item | Status | Notes |
|---|---|---|
| In-place modification of `src/fitqc/plot.py` (no `_v2` siblings) | PROPOSED | Back-compat via optional kwargs only |
| Interior elbow fix in driver, not plotter | PROPOSED | Detection-logic changes are out of scope |
| Single multi-page PDF at `figures/ppa12_overview.pdf` | PROPOSED | Alternative: 12 PNGs |
| `plot_parameter_overview` lives in `src/fitqc/plot.py` | PROPOSED | Alternative: new `src/fitqc/overview.py` |
| Histogram interior cuts via optional kwargs on existing plotter | PROPOSED | Alternative: separate function |
| Detection baseline TP=24 FN=0 from commit `44447a0` must not regress | DECIDED | User-confirmed in prior session |
| Do not modify `src/fitqc/boundary.py`, `src/fitqc/interior.py` detection logic | DECIDED | Scope boundary |
| Do not touch M2 / M3 blocks in `boundary.py` | DECIDED | Protected in prior session |
| Do not modify `dispatches/ground_truth_validation.csv` | DECIDED | Empirical ground truth |
| Do not modify `analyze_overrides.py` | DECIDED | Separate task |

PROPOSED items may be overridden by the user during execution.

## Motivation

Commit `44447a0` fixed all 10 boundary FNs (TP=24, FN=0) but visual review of the regenerated per-parameter plots exposed quality issues that prevent a reader from judging detection correctness. The user reviewed the existing `figures/<param>/*.png` output and flagged 7 distinct problems plus a request for a new per-parameter overview. Without these fixes, the next calibration stage (Task C on `t_star` magnitudes) will have no reliable visual verification path.

## Read First

1. `/Users/balterma/.claude/plans/do-not-execute-the-glimmering-catmull.md` — the plan with batch-level detail and verification gates.
2. `/Users/balterma/.claude/plans/handoff-the-glimmering-catmull.md` — status table, resume protocol, operational constraints.
3. `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` — the 6 plotters to modify (line ranges in each batch above).
4. `/Users/balterma/observatories/code/fitqc/src/fitqc/report.py` lines 263-321 — `_build_mask` reference for cut logic replicated in B7.
5. `/Users/balterma/observatories/code/fitqc/src/fitqc/interior.py` lines 184, 398 — `quantile_elbows` field wiring explaining why B1 driver fix resolves the empty interior elbow plots.
6. `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py` — driver, line ~94 for B1 fix.
7. `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv` — read-only reference for TP/FN status annotations on the overview.
8. Existing `/Users/balterma/observatories/code/fitqc/figures/<param>/*.png` — visual reference for current state of each plot type.

## Acceptance Criteria

- [ ] Each of B1–B9 landed as its own commit in conventional-commits format.
- [ ] Each of G1–G9 green per the plan's verification gates.
- [ ] `python -m pytest tests/ -q` shows ≥ 422 passed and includes ≥ 5 new plot tests.
- [ ] `python analyze_overrides.py` all-on column shows TP=24, FN=0 (same as commit `44447a0` baseline).
- [ ] `/Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf` exists with 12 pages, one per parameter.
- [ ] `git diff src/fitqc/boundary.py src/fitqc/interior.py dispatches/ground_truth_validation.csv` is empty at end-of-task.
- [ ] `git diff src/fitqc/plot.py` shows only additive backward-compatible changes to existing plotter signatures.
- [ ] One per-parameter overview opened and visually approved by the user before B7+B8 commits.

## Anti-Patterns

- Do NOT modify detection logic in `src/fitqc/boundary.py` or `src/fitqc/interior.py` — scope violation; prior session confirmed detection is correct given the CSV ground truth.
- Do NOT import the private `_build_mask` helper from `src/fitqc/report.py` in B7 — replicate its cut logic inline so the overview plotter remains self-contained.
- Do NOT batch multiple B's into one commit — each batch is one commit for rollback clarity.
- Do NOT skip any G1–G9 verification gate — prior work showed stacking fixes past a failing gate leads to silent regressions.
- Do NOT introduce per-parameter magic numbers in plot code — zoom ranges must derive from the result object (e.g., `t_star`, `pileup_threshold`), not from parameter names.
- Do NOT promote throwaway `dispatches/plot_*` driver scripts to production code without explicit user approval — they are visualization drivers, not library code.

## Verification

Run these commands; each should produce the noted output.

```bash
# Prerequisite baseline
git -C /Users/balterma/observatories/code/fitqc log --oneline -1 src/fitqc/boundary.py
# Expect: 44447a0 fix(boundary): add sub-grid excess-mass fallback for thin delta pileups

python -m pytest tests/ -q | tail -1
# Expect: 422 passed (or more after B9)

python analyze_overrides.py 2>&1 | tail -3
# Expect: all-on column shows TP=24 FN=0
```

Per-batch fast regression check (runs in seconds, not 90s):

```bash
python /Users/balterma/observatories/code/fitqc/dispatches/diagnose_boundary_24.py 2>&1 | tail -3
# Expect: TP=24  FN=0  FP=0  TN=0
```

End-of-task:

```bash
# All 12 overview pages rendered
ls -lh /Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf
# Expect: file exists, size > 1MB

# No detection drift
git -C /Users/balterma/observatories/code/fitqc diff src/fitqc/boundary.py src/fitqc/interior.py dispatches/ground_truth_validation.csv
# Expect: empty

# Plotting changes are additive
git -C /Users/balterma/observatories/code/fitqc diff --stat src/fitqc/plot.py
# Expect: ~6 functions modified, 1 function added, lines-added > lines-removed
```

Per-batch visual checks are specified in the plan (G1–G9). The receiving session should run each after its batch commit and fix regressions before proceeding to the next batch.

## Out of Scope

- `t_star` magnitude recalibration — Task C (`calibration-tolerance-mags`).
- Interior stickiness detection changes — Task D (`calibration-interior-det`).
- End-to-end mask validation on real PPA12 data — Task E (`calibration-end-to-end`).
- Changes to M2 or M3 override mechanisms in `src/fitqc/boundary.py`.
- Changes to the quantile-based detection core in `src/fitqc/interior.py`.
