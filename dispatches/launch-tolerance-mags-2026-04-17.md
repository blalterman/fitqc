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

**Read:** `dispatches/dispatch-tolerance-mags-2026-04-17.md`

## Recent commits (for orientation)

- `44447a0` fix(boundary): add sub-grid excess-mass fallback for thin delta pileups (B's fix)
- `a828a51` chore(analysis): drop M1 from override factorial harness
- `fb4ad25` refactor(boundary): remove M1 spread-pileup override

## Key Decisions

- DECIDED: B is complete (TP=24/24 per `boundary-fn-diagnostics-2026-04-17.md`).
  C covers all 24 (parameter, side) cases, not "14 + new."
- DECIDED: Ground truth CSV is authoritative; do not modify.
- DECIDED: ±1 decade is the classification threshold.
- DECIDED: C is analysis-only. Any production fix for OFF cases is a
  separate task.
- PROPOSED: CSV `note` column has uneven coverage. For NO HINT cases,
  justify from visual inspection; the dispatch Open Items section
  anticipates this.

## Scope

1. Read `dispatch-tolerance-mags-2026-04-17.md` in full.
2. For each of the 24 (parameter, side) with `t_star != None`, classify
   WITHIN / OFF / NO HINT against the CSV scale hint.
3. Commit the results table as
   `dispatches/tolerance-validation-2026-04-<DATE>.md`.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Analysis-only. No edits to `src/`, no config tuning, no CSV edits.
- Single commit: `docs(analysis): validate t_star magnitudes against CSV scale hints`.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
# Expected: 422 passed

test -f dispatches/tolerance-validation-2026-04-*.md && echo "results: OK"
```
