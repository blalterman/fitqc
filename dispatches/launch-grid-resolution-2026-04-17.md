Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here.
3. Read the dispatch and other files referenced in the "Read" section
   against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance
   Criterion in the dispatch, honors every Anti-Pattern, and resolves
   every Open Item. Do not rewrite scope or intent.
5. Present the revised plan for user approval. Prefix it with a
   "Revisions from initial draft" section.
6. Execute only after user approval.

---

**Read:** `dispatches/dispatch-grid-resolution-2026-04-17.md`

## Recent commits (for orientation)

- `44447a0` fix(boundary): add sub-grid excess-mass fallback for thin delta pileups
- `a828a51` chore(analysis): drop M1 from override factorial harness
- `fb4ad25` refactor(boundary): remove M1 spread-pileup override

## Key Decisions

- DECIDED: Detection boolean TP=24/24 is invariant; must be preserved.
- DECIDED: No M1 re-introduction; M2/M3 unchanged.
- DECIDED: Ground truth CSV is authoritative.
- DECIDED: Visual verification via `plot_all_ppa12_diagnostics.py` on
  log-y mass curves across all 12 parameters.
- PROPOSED: log-spaced `[1e-7, 3e-7, 1e-6, ..., 1e-1]` is the
  starting candidate; dialectic during prototype phase.

## Scope

1. Audit current grid coverage vs B-diagnostic true pileup widths.
2. Prototype 2-3 candidate grids; dialectic; select.
3. Commit to `BoundaryConfig`; re-run `analyze_overrides.py`.
4. Regenerate overview PDFs; visually verify the 9 magnitude-OFF
   parameters now show resolved structure.
5. Add at least one test on a synthetic tight-pileup case.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Grid-only change: do not touch `excess_ratio`, `pileup_threshold`,
  M2, M3, or CSV.
- Commits: `feat(config): log-spaced tolerance grid for boundary detection`
  (or similar) + test commit(s).

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
python analyze_overrides.py
python dispatches/plot_all_ppa12_diagnostics.py
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
```
