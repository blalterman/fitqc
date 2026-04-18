# Dispatch: Calibration Orchestrator (C1-C4 + follow-up coordination)

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** coordination / dashboard / dispatch-writing

## Scope

Coordinate execution of the 4 follow-up calibration tasks spun out of
the 2026-04-17 per-parameter review:
- `calibration-grid-resolution` (C1)
- `calibration-plot-axis-scale` (C2)
- `calibration-derivative-refine` (C3; depends on C1)
- `calibration-precision-note` (C4)

Track status. Reconcile the PM Dashboard against git reality. Write
small-scope follow-up dispatches when task outputs identify new work.
Escalate blockers to the user. Route reasoning questions to the
calibration reviewer chat (distinct role; see
`dispatches/dispatch-calibration-reviewer-2026-04-17.md`).

## What this chat does

1. **Task tracking**: maintain a lightweight status board for the 4
   tasks. Optionally commit a snapshot as
   `dispatches/orchestrator-status-2026-04-XX.md` on user request.
2. **CPM sync**: after a task commits, run
   `/critpath:discover-status fitqc` and `/critpath:update-status fitqc`
   to reconcile the dashboard. Surface reconciliation diffs to the
   user before applying.
3. **CPM structural changes**: when the user approves a new task
   (e.g., from a C3 dialectic that recommends Replace), run
   `/critpath:add-tasks fitqc` with a payload. Always surface the
   payload for user approval first.
4. **Small dispatch maintenance**: if a task executor hits a
   blocker requiring a small scope addition, either invoke
   `/dispatch` for a new work order or draft suggested wording the
   user can apply elsewhere. For substantial scope changes, escalate.
5. **Escalation routing**:
   - Deep reasoning / dialectic → reviewer chat.
   - Scope changes to parent calibration plan → user approves; this
     chat may write the plan-file amendment only with explicit
     approval.
   - Empirical evidence gathering → task chats; never run pytest or
     `analyze_overrides.py` from this chat.

## What this chat does NOT do

- Edit `src/`, `tests/`, or data. Executors handle those.
- Run `analyze_overrides.py`, pytest, or `plot_all_ppa12_diagnostics.py`.
  Read executor output; don't re-run it.
- Make binding scope decisions unilaterally.
- Produce Tier-2 reasoning certificates — invoke the reviewer chat.
- Update CPM silently. Always surface the diff.

## Read First

1. `dispatches/dispatch-grid-resolution-2026-04-17.md` (C1)
2. `dispatches/dispatch-plot-axis-scale-2026-04-17.md` (C2)
3. `dispatches/dispatch-derivative-refinement-2026-04-17.md` (C3)
4. `dispatches/dispatch-e-w-p2-precision-note-2026-04-17.md` (C4)
5. `dispatches/dispatch-calibration-reviewer-2026-04-17.md` — the
   reviewer's charter. Understand the reviewer/orchestrator boundary.
6. `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md` —
   the parent calibration plan. Source of truth for scope.

## Acceptance Criteria

- [ ] Status board maintained and current; on request, a
      committable snapshot is written under `dispatches/`.
- [ ] CPM dashboard reconciled with git commits for C1-C4 whenever
      asked; no silent status drift.
- [ ] Every executor-surfaced blocker is presented to the user with
      options, not resolved unilaterally.
- [ ] Reasoning questions (coverage judgments, change-safety
      assessments, tradeoffs) are routed to the reviewer chat rather
      than answered here.
- [ ] At end-of-session, a handoff note summarizes: what's resolved,
      what's pending, what's blocked, what's been committed.

## Anti-Patterns

- Do NOT run reasoning archetypes unilaterally. Defer to the reviewer.
- Do NOT edit production code, tests, or data.
- Do NOT update CPM without surfacing the diff first.
- Do NOT conflate orchestration with execution. Task chats execute.
- Do NOT modify the parent calibration plan file without explicit
  user approval for each edit.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Current state snapshot
git log --oneline -10

# CPM status (read-only)
conda run -n critpath cpm pipeline-status | grep -E "calibration"

# Orchestrator snapshot (optional, on user request)
test -f dispatches/orchestrator-status-2026-04-*.md
```

## Out of Scope

- All substantive src/tests/data edits (C1-C4 executors).
- Reasoning / evaluation / dialectic (reviewer chat).
- Authoring deep-design specifications (planning sessions via
  `/plan-draft`).
- Running empirical checks directly.
