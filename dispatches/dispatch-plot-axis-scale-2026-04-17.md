# Dispatch: Commit log-x row-1 auto-detect with log-spaced bins

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** plot + test
**CPM task:** `calibration-plot-axis-scale` (new; independent of C1/C3/C4)

## Scope

The row-1 log-x auto-detect with log-spaced bins has already been
applied to `src/fitqc/plot.py:plot_parameter_overview`. This task
verifies the change, adds a test covering the wide-range path,
regenerates the 12 parameter overview PDFs, and commits.

## Motivation

np1 and np2 have bounds (0.01, 100) spanning 4 decades. Linear-x on
row 1 compresses all samples below u=0.01 (U-normalized) into <1%
of panel width, hiding the distribution. Auto-detect log-x when
`L > 0 and U / L > 100` emits log-spaced bin edges (via
`np.logspace`) computed from FD/Doane on `log10(x_clean)`, keeping
bin resolution consistent with the axis.

## Read First

1. `src/fitqc/plot.py:plot_parameter_overview` — row-1 panel block
   inside `if n_total > 0:`; the auto-detect lives here.
2. `tests/test_plot_improvements.py::test_parameter_overview_smoke` —
   existing smoke test uses L=0, U=1 (linear-x path only). Add a
   new test case for the log-x path.
3. `dispatches/plot_all_ppa12_diagnostics.py` — driver used to
   regenerate the overview PDFs.

## Implementation protocol

1. **Verify source state**: confirm the log-x block is in
   `plot_parameter_overview` (auto-detect on `L > 0 and U / L > 100`;
   FD/Doane on `log10(x_clean)` when active; `np.logspace` edges;
   `set_xscale("log")` when active). If missing, STOP and escalate —
   the prior session was supposed to apply it.
2. **Add test case** in `test_plot_improvements.py` that renders a
   figure with `L=0.01, U=100`, at least 500 samples, and asserts
   `fig.axes[0].get_xscale() == "log"`. Axes count must still be 22.
3. **Run full test suite**.
4. **Regenerate** `figures/` via `plot_all_ppa12_diagnostics.py`.
5. **Visually verify**:
   - np1, np2 overview PDFs — row 1 now shows log-x.
   - vx, vy, vz, e_dv_* — row 1 remains linear-x (zero-centered).
6. **Single commit**:
   `feat(plot): log-x auto-detect on row-1 for wide-range params`
   bundling the source change (already staged), the new test, and the
   regenerated figures.

## Acceptance Criteria

- [ ] Source state verified (auto-detect + log-spaced bins present).
- [ ] New test in `test_plot_improvements.py` covers `L > 0, U / L > 100`
      path and asserts `xscale == "log"` and axes count == 22.
- [ ] `python -m pytest tests/ -q` passes.
- [ ] Visual verification complete for np1, np2 (log-x active) and
      at least one zero-centered param (linear-x unchanged).
- [ ] Single commit on `claude/fitqc-ppa12-validation-vwKdg`.

## Anti-Patterns

- Do NOT force log-x on all parameters — only when `L > 0` and `U/L > 100`.
- Do NOT change the FD/Doane floor (500) or ceiling (2000).
- Do NOT touch rows 2-6.
- Do NOT add log-x to ECDF or elbow panels in this task.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

grep -n "use_log_x" src/fitqc/plot.py
# Expected: at least one match inside plot_parameter_overview.

python -m pytest tests/test_plot_improvements.py -q
# Expected: new test passes.

python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup

python dispatches/plot_all_ppa12_diagnostics.py
# Visually open: figures/np1/np1_boundary_diagnostics.png (log-x)
#                figures/vx/vx_boundary_diagnostics.png  (linear-x)
```

## Out of Scope

- Log-x on other panels (mass curves already log-y; ECDFs, elbows
  left as-is).
- Grid resolution tuning (`calibration-grid-resolution`).
- Changes to rows 2-6.
