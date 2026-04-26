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

**Read:** `dispatches/dispatch-interior-det-2026-04-17.md`

## Recent commits (for orientation)

- `44447a0` fix(boundary): add sub-grid excess-mass fallback for thin delta pileups
- `14595de` chore(ground-truth): vy has interior sticky point at x0=0
- `a828a51` chore(analysis): drop M1 from override factorial harness

## Key Decisions

- DECIDED: D evaluates `interior.py` against CSV; does not fix it.
- DECIDED: CSV `interior` numeric values may not be flipped without
  explicit user approval. Only the `note` column may be sharpened.
- DECIDED: Interior detection uses `src/fitqc/interior.py` only; not
  the boundary code path.
- PROPOSED: The "my guess" set in the plan is stale — read CSV fresh.
- PROPOSED: Reuse patterns from `dispatches/diagnose_boundary_24.py`
  when writing the 12-parameter diagnostic harness.

## Scope

1. Read `dispatch-interior-det-2026-04-17.md` in full.
2. Write `dispatches/diagnose_interior_12.py`; run detection on 12
   parameters.
3. Tabulate against CSV `interior` column; produce verdict table.
4. For each "my guess" disagreement, visually re-inspect
   `boundary_inspection.pdf` and either sharpen the CSV note or flag
   as algorithmic FN.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Evaluation-only on `interior.py`. No src/ edits. CSV `note` edits
  allowed; numeric-column edits require user approval.
- Commits:
  - `feat(dispatches): add interior detection diagnostic harness`
    (script + any shared utilities)
  - `docs(analysis): validate interior detection against CSV ground truth`
    (results markdown)
  - `chore(ground-truth): sharpen <parameter> interior note` (if any)

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup
# Expected: 422 passed

test -f dispatches/diagnose_interior_12.py && echo "script: OK"
test -f dispatches/interior-validation-2026-04-*.md && echo "results: OK"
python dispatches/diagnose_interior_12.py | head -15
# Expected: 12-row table to stdout
```
