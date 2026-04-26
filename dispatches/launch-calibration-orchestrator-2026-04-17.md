Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here.
3. Read the dispatch and other files referenced in the "Read" section
   against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance
   Criterion, honors every Anti-Pattern, and resolves every Open Item.
   Do not rewrite scope or intent.
5. Present the revised plan for user approval. Prefix it with a
   "Revisions from initial draft" section.
6. Execute only after user approval.

---

**Read:** `dispatches/dispatch-calibration-orchestrator-2026-04-17.md`

## Recent commits (for orientation)

- `44447a0` fix(boundary): add sub-grid excess-mass fallback for thin delta pileups
- `a828a51` chore(analysis): drop M1 from override factorial harness

## Key Decisions

- DECIDED: This chat coordinates; it does not execute. Executors are
  separate task chats for C1-C4.
- DECIDED: This chat distinct from the reviewer chat. Reasoning /
  dialectic goes to the reviewer
  (`dispatches/dispatch-calibration-reviewer-2026-04-17.md`).
- DECIDED: CPM updates require user approval of the diff before apply.
- DECIDED: No src/tests/data edits. No running pytest or
  `analyze_overrides.py`.
- DECIDED: C3 (`calibration-derivative-refine`) gated on C1 completion.
- DECIDED: C1, C2, C4 are parallel-safe; no file contention.

## Scope

1. On startup, verify the 4 task dispatches load and report each
   task's git status (any commits? diagnostic files present?).
2. Track and report C1-C4 progress as the user requests updates.
3. After commits, propose CPM reconciliation diffs; apply with
   approval.
4. Route reasoning questions to reviewer; route scope-change
   questions to user.
5. At session end, produce a handoff summary.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Allowed writes: `dispatches/orchestrator-status-*.md` (on request);
  CPM data files via `/critpath:*` skills (after user approval).
- Never: `src/`, `tests/`, `dispatches/ground_truth_validation.csv`,
  parent plan file (except on explicit per-edit user approval).

## Verification

Startup:

```bash
cd /Users/balterma/observatories/code/fitqc
for f in dispatch-grid-resolution dispatch-plot-axis-scale \
         dispatch-derivative-refinement dispatch-e-w-p2-precision-note \
         dispatch-calibration-reviewer; do
  test -f dispatches/${f}-2026-04-17.md && echo "${f}: OK" || echo "${f}: MISSING"
done
git log --oneline -10
```

Ongoing (on request):

```bash
conda run -n critpath cpm pipeline-status | grep -E "calibration"
```
