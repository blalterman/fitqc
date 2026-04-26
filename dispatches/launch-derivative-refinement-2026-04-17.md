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

**Read:** `dispatches/dispatch-derivative-refinement-2026-04-17.md`

## Prerequisites (verify before starting)

- [ ] `calibration-grid-resolution` committed with TP=24/24 preserved.
      If not, STOP and escalate; derivatives on a coarse grid are
      uninformative.

## Key Decisions

- DECIDED: This is prototype-only; no changes to `src/fitqc/boundary.py`.
- DECIDED: Derivatives inherit grid-resolution problems, so C1 is a
  hard prerequisite.
- DECIDED: Results must pair with the prototype version that
  produced them (single commit).
- PROPOSED: Smoothing kernel σ = 0.1 in log10(t); sensitivity sweep.
- PROPOSED: Derivative threshold `dM/dt ≤ 1.2`; sensitivity sweep.

## Scope

1. Confirm C1 is done; if not, STOP.
2. Write `dispatches/prototype_dmdt_t_star.py` (computes dM/dt,
   finds threshold crossing, tabulates vs Kneedle).
3. Write `dispatches/derivative-refinement-results-2026-04-XX.md`
   with the comparison table, sensitivity sweep, and dialectic.
4. Single commit bundling script + results.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Prototype-only. No `src/` edits. No CSV edits. No config changes.
- Single commit: `feat(dispatches): prototype dM/dt-based t_star refinement`.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
# Prerequisite gate
grep -n "log-spaced" src/fitqc/config.py || grep -nE "grid_mode.*log" src/fitqc/config.py
# Expected: evidence C1 has committed a log-spaced grid option.

python dispatches/prototype_dmdt_t_star.py
test -f dispatches/derivative-refinement-results-2026-04-*.md
python -m pytest tests/ -q --deselect ...
```
