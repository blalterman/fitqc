Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here. Treat it as your
   hypothesis for HOW to execute the work.
3. Read the dispatch, plan, and other files referenced in the "Read" section
   against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance Criterion in
   the dispatch, honors every Anti-Pattern, and resolves every Open Item
   (either by answering or by flagging as a user question). Do not rewrite
   scope or intent — they were reviewed in the prior session.
5. Present the revised plan for user approval. Prefix it with a "Revisions
   from initial draft" section noting what changed between steps 2 and 4.
6. Execute only after user approval.

---

**Read:**

1. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-plot-improvements-2026-04-17.md` — the work order: 9 batches with file paths, acceptance criteria, anti-patterns, verification commands.
2. `/Users/balterma/.claude/plans/handoff-the-glimmering-catmull.md` — status table, critical context, resume protocol, operational constraints.
3. `/Users/balterma/.claude/plans/do-not-execute-the-glimmering-catmull.md` — the plan with batch-level detail and per-batch verification gates G1–G9.

## Commits

- `44447a0` fix(boundary): add sub-grid excess-mass fallback for thin delta pileups
- `a828a51` chore(analysis): drop M1 from override factorial harness
- `a774910` fix(test): weaken broad-pileup assertion to reflect algorithm semantics
- `2014f79` fix(test): correct tolerance-space assertion on tight-pileup elbow
- `cf87887` fix(boundary): preserve raw elbow in delta-function branch

## Key Decisions

- DECIDED: Detection baseline TP=24 FN=0 from commit `44447a0` must not regress. The full factorial check via `python /Users/balterma/observatories/code/fitqc/analyze_overrides.py` (~90s) runs at end-of-task; the fast 24-row check at `/Users/balterma/observatories/code/fitqc/dispatches/diagnose_boundary_24.py` runs after each batch.
- DECIDED: Plotting changes only. Do not modify `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py`, `/Users/balterma/observatories/code/fitqc/src/fitqc/interior.py`, the M2/M3 blocks in `boundary.py`, `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv`, or `/Users/balterma/observatories/code/fitqc/analyze_overrides.py`.
- DECIDED: Pytest baseline is 422 passed. New plot tests in B9 add to this; no regressions allowed.
- DECIDED: One commit per batch (B1 through B9), conventional-commits format. Do not stack on a failed verification gate.
- DECIDED: Throwaway `dispatches/plot_*` driver scripts stay under `dispatches/` and are not promoted to library code without explicit user approval.
- PROPOSED: In-place modification of `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` via additive backward-compatible kwargs (no `_v2` siblings).
- PROPOSED: Empty `*_interior_elbows.png` is a driver bug, fixed in `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py` line ~94 by passing `InteriorConfig(use_quantile_analysis=True)`. Plotter remains unchanged.
- PROPOSED: Per-parameter overview output is one multi-page PDF at `/Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf` (12 pages). Alternative: 12 PNGs.
- PROPOSED: New `plot_parameter_overview` lives in `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` (alternative: new `src/fitqc/overview.py` module).
- PROPOSED: Histogram-overlay interior cuts via new optional `x0` / `eps_star` kwargs on `plot_histogram_tolerance_overlays` (alternative: separate plotter).
- PROPOSED: Boundary-elbow correctness "proof" goes in the new overview (raw vs filtered histogram pair); existing `*_boundary_elbows.png` keeps its current quantile-curve view.

PROPOSED items have not been confirmed by the user. The dispatch flags them; ask the user before building on them if uncertain.

## Scope

Land 9 sequential batches (B1–B9), one commit per batch, each gated by its corresponding G1–G9 verification step. Full per-batch detail in the plan and dispatch. Summary:

- **B1** — `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py` line ~94: pass `InteriorConfig(use_quantile_analysis=True)` to `run_interior_qc`. Resolves empty `*_interior_elbows.png`.
- **B2** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` lines 125-325 (`plot_boundary_diagnostics`): auto-zoom y-range and x-range on the two linear panels.
- **B3** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` lines 637-764 (`plot_histogram_tolerance_overlays`): add optional `x0`/`eps_star`/`t_lo_star`/`t_hi_star` kwargs; apply interior cut; set log-y; draw cut markers.
- **B4** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` lines 492-635 (`plot_ecdf_tolerance_overlays`): optional `t_lo_star`/`t_hi_star` markers; auto-zoom y when panel range < 0.05.
- **B5** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` lines 328-489 (`plot_quantile_spacing_overlays`): title/label/legend clarification.
- **B6** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` lines 30-122 (`plot_interior_diagnostics`): `symlog` y on z-histogram (linthresh=1).
- **B7** — `/Users/balterma/observatories/code/fitqc/src/fitqc/plot.py` (append): new `plot_parameter_overview(param_name, x, x0, L, U, interior_result, boundary_result, config)`. 4×2 grid; replicates `_build_mask` cut logic inline (do not import the private helper from `/Users/balterma/observatories/code/fitqc/src/fitqc/report.py:263-321`).
- **B8** — `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_ppa12_diagnostics.py`: append per-parameter overview pages to `/Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf` via `matplotlib.backends.backend_pdf.PdfPages`.
- **B9** — `/Users/balterma/observatories/code/fitqc/tests/test_plot*.py`: add ≥ 5 new tests (boundary zoom, histogram log-y + interior, ecdf t_star marker, interior symlog, overview smoke).

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: `ruff check --fix`, `ruff-format`, whole-repo `ruff-format --check`. Pre-existing RUF059 errors at `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py:712,719` are unrelated and accepted by pre-commit.
- Untracked Python under `/Users/balterma/observatories/code/fitqc/dispatches/` is included in the whole-repo format check. Run `/opt/anaconda3/envs/fitqc/bin/ruff format <file>` on any new scripts before staging.
- Sandbox may block `~/.cache/pre-commit/` during pre-commit. Retry the failing hook with `dangerouslyDisableSandbox: true` only for that single command.
- `python /Users/balterma/observatories/code/fitqc/analyze_overrides.py` runs ~90s. Use the fast diagnostic at `/Users/balterma/observatories/code/fitqc/dispatches/diagnose_boundary_24.py` between batches; reserve the full factorial for end-of-task.
- Test data parquet files: use `pyarrow`, not `pandas`. Pattern: `pq.read_table(path)["values"].to_numpy()`.

## Verification

Baseline (run before B1):

```bash
git -C /Users/balterma/observatories/code/fitqc log --oneline -1 src/fitqc/boundary.py
# Expect: 44447a0 fix(boundary): add sub-grid excess-mass fallback for thin delta pileups

python -m pytest /Users/balterma/observatories/code/fitqc/tests/ -q | tail -1
# Expect: 422 passed

python /Users/balterma/observatories/code/fitqc/analyze_overrides.py 2>&1 | tail -3
# Expect: all-on column shows TP=24 FN=0
```

Per-batch fast check (after each commit):

```bash
python /Users/balterma/observatories/code/fitqc/dispatches/diagnose_boundary_24.py 2>&1 | tail -3
# Expect: TP=24  FN=0  FP=0  TN=0
```

End-of-task acceptance:

```bash
python -m pytest /Users/balterma/observatories/code/fitqc/tests/ -q | tail -1
# Expect: ≥ 422 passed (more if B9 added tests)

python /Users/balterma/observatories/code/fitqc/analyze_overrides.py 2>&1 | tail -3
# Expect: all-on TP=24 FN=0 unchanged

ls -lh /Users/balterma/observatories/code/fitqc/figures/ppa12_overview.pdf
# Expect: file exists, size > 1MB

git -C /Users/balterma/observatories/code/fitqc diff src/fitqc/boundary.py src/fitqc/interior.py dispatches/ground_truth_validation.csv
# Expect: empty (no detection drift, ground truth untouched)

git -C /Users/balterma/observatories/code/fitqc diff --stat src/fitqc/plot.py
# Expect: ~6 functions modified, 1 function added, lines-added > lines-removed
```

## Prerequisites verified

No `tools/docs/launch-prerequisites.md` was found at the project root; the receiving session should run the baseline commands above before starting B1.

Follow the handoff Resume Protocol to confirm state before acting.
