# Dispatch: Data Cut Calibration Orchestrator

**Generated:** 2026-04-17
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** coordination (non-executing)
**CPM task:** `calibration` (parent)

## Scope

Coordinate the 5 calibration subtasks (A-E) in the `calibration` critical
path. Produce dispatches and launch prompts for tasks C, D, E as their
predecessors complete. Verify acceptance criteria on task outputs. Update
the CPM dashboard to reflect ground truth as tasks land. Surface blockers
to the user. Queue task launches for the user to start in new chats.

This role is coordinator-only. It does NOT edit production code, run
pytest fixes, re-run `analyze_overrides.py`, or merge branches. All
executing work happens in task-specific chats launched from the queued
launch prompts.

## Motivation

The calibration plan decomposes into 5 sequenced tasks that may span days
and multiple executor sessions. Without a persistent coordinator role:
- Dispatches for C, D, E get written reactively, out of order, or not at all.
- The CPM dashboard drifts from reality (tasks stay `pending` after they
  complete) and the critical path becomes unreliable.
- Verification gaps between tasks are missed (e.g., B's fix passes its
  own criteria but inadvertently breaks A's fix).
- The user holds all the coordination context in their head, which
  doesn't survive context switches.

The orchestrator role absorbs this coordination work. One orchestrator
chat per coordination window (a window is typically 1-3 days or until the
chat hits ~100k context, whichever is first). A fresh orchestrator chat
reads the plan file and CPM state, reconstructs current position, and
picks up from there.

## Read First

1. `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md` — the
   calibration plan. Source of truth for task structure, IDs, durations,
   dependencies. Updated by the orchestrator if scope changes with user
   approval.
2. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-quantile-test-failures-2026-04-16.md` —
   Task A dispatch (test_boundary_quantile.py failures).
3. `/Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-quantile-test-failures-2026-04-16.md` —
   Task A launch prompt.
4. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-false-negatives-2026-04-17.md` —
   Task B dispatch (10 boundary FNs).
5. `/Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-false-negatives-2026-04-17.md` —
   Task B launch prompt.
6. `~/.claude/rules/handoff-protocol.md` — the canonical handoff structure
   C/D/E dispatches must follow.
7. CPM dashboard state: `conda run -n critpath cpm pipeline-status` from
   `/Users/balterma/observatories/code/claude-pm-container/claude-pm` —
   shows which `calibration-*` tasks are pending, ready, complete.

## Responsibilities

### R1. Produce dispatches + launch prompts for C, D, E

When the predecessor of a task is verified complete:
- Task C (`calibration-tolerance-mags`): predecessor is B
- Task D (`calibration-interior-det`): no predecessor (parallel to B, C);
  can be queued any time after orchestrator starts
- Task E (`calibration-end-to-end`): predecessors are B, C, D

Each new dispatch uses the format of the existing A/B dispatches and the
canonical structure in `handoff-protocol.md`. Each new launch prompt
uses the 6-step plan-first template from `handoff-protocol.md` (current
version as of 2026-04-17).

Write to `/Users/balterma/observatories/code/fitqc/dispatches/` with
filenames `dispatch-<slug>-<YYYY-MM-DD>.md` and
`launch-<slug>-<YYYY-MM-DD>.md`. Copy each to
`~/Documents/Obsidian-Vault/fitqc/dispatches/`. Run
`bash ~/.claude/tools/lint-ai-clean.sh <file>` before presenting. Fix
violations and re-lint until clean.

### R2. Verify task completion against acceptance criteria

When the user reports a task chat has finished:
- Read the latest commits in `~/observatories/code/fitqc` on branch
  `claude/fitqc-ppa12-validation-vwKdg`.
- Check each Acceptance Criterion in the task's dispatch against the
  actual state (tests pass, files exist, metrics met).
- If all criteria pass → proceed to R3.
- If any criterion fails → write a gap report to the orchestrator's
  working notes, surface to user, do NOT mark task complete in CPM.

### R3. Update the CPM dashboard

When a task is verified complete (R2 passed):
- Invoke `/critpath:update-status` with:
  - Project: `fitqc`
  - Task: the `calibration-<slug>` ID
  - Status: `complete`
  - `actual_start_date`: date of first commit for that task's work
  - `actual_finish_date`: date of the task's final commit
  - `actual_duration`: elapsed work-hours (best estimate; round to half-hour)
- Run the CPM validation sequence from
  `/Users/balterma/observatories/code/claude-pm-container/claude-pm`:
  ```bash
  conda run -n critpath cpm validate && \
  conda run -n critpath cpm import && \
  conda run -n critpath cpm pipeline
  ```
- Verify the parent `calibration` task rolls up correctly (its
  `percentComplete` should reflect children completion).

### R4. Queue the next task for the user

After R3, identify the next `ready=True` task in the `calibration` parent.
Tell the user:
- Which task is next.
- Path to its launch prompt (absolute path).
- One-line reminder to open a new chat and paste the launch prompt's
  contents.

### R5. Handle blockers and scope changes

If a task session reports a blocker (e.g., the Group 2 FNs require a
new quantile grid that needs user approval):
- Do NOT unilaterally approve scope changes.
- Summarize the blocker for the user in 3-5 sentences.
- Propose options if the blocker has clear resolutions; otherwise ask
  an AskUserQuestion.
- If user approves a scope change, update the plan file
  (`delegated-stargazing-iverson.md`) and re-run R3 as appropriate.

## Workflow state machine

```
                ┌─ verify A → update CPM → queue B
                │
start → queue A ┤─ verify B → update CPM → queue C (write dispatch+launch)
                │                                  → queue D (parallel; write dispatch+launch)
                │
                ├─ verify C → update CPM
                ├─ verify D → update CPM
                │
                └─ when B+C+D verified → queue E (write dispatch+launch)
                                       → verify E → update CPM → done
```

Exit criterion: `calibration` parent task shows `status=complete,
percentComplete=100` in the CPM dashboard and the final commit for
Task E is on `claude/fitqc-ppa12-validation-vwKdg`.

## Acceptance Criteria (per orchestrator window)

An orchestrator chat's session is "done" when any of:
- The next task in the sequence is queued (R1, R4 complete for that task).
- A blocker is surfaced to the user and is awaiting their input.
- The orchestrator chat has crossed ~100k context tokens and a handoff
  to a fresh orchestrator chat is produced.

The overall orchestrator role is done when the Exit criterion above is
met.

## Anti-Patterns

- Do NOT execute task A/B/C/D/E work directly. The orchestrator does
  not edit `src/fitqc/boundary.py`, `tests/`, `analyze_overrides.py`,
  or `ground_truth_validation.csv`. If you are tempted to "just do this
  small fix," write it into the relevant task's dispatch instead.
- Do NOT rewrite the plan without user approval. The plan file is a
  DECIDED artifact from the planning session.
- Do NOT auto-spawn task sessions via the Agent tool. Queue for user;
  let them open new chats. This is a DECIDED workflow preference.
- Do NOT mark a task complete in CPM without verifying all Acceptance
  Criteria against the actual filesystem and git state. "The chat said
  it was done" is not evidence; the dispatch's criteria are.
- Do NOT batch verification of multiple tasks. Verify and CPM-update
  one at a time so the dashboard reflects intermediate state and the
  critical path is always truthful.
- Do NOT skip the clean-lint check on generated dispatches/launches.

## Verification

Orchestrator readiness check on startup:

```bash
# Plan exists
test -f /Users/balterma/.claude/plans/delegated-stargazing-iverson.md && echo "plan: OK"

# A and B dispatches + launches exist
test -f /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-quantile-test-failures-2026-04-16.md && echo "A dispatch: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-quantile-test-failures-2026-04-16.md && echo "A launch: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-false-negatives-2026-04-17.md && echo "B dispatch: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-false-negatives-2026-04-17.md && echo "B launch: OK"

# CPM has the 5 calibration tasks
cd /Users/balterma/observatories/code/claude-pm-container/claude-pm && \
  conda run -n critpath cpm pipeline-status 2>&1 | grep -c "calibration"
# Expected: 6 (parent + 5 subtasks)

# Current branch
cd /Users/balterma/observatories/code/fitqc && git branch --show-current
# Expected: claude/fitqc-ppa12-validation-vwKdg
```

Post-task-completion check (run after R3 for each task):

```bash
# CPM reflects the completed task
cd /Users/balterma/observatories/code/claude-pm-container/claude-pm && \
  conda run -n critpath cpm pipeline-status 2>&1 | grep "calibration-<slug>"
# Expected: status=complete, percentComplete=100

# Parent rollup
conda run -n critpath cpm pipeline-status 2>&1 | grep "^calibration "
# Expected: percentComplete = (completed subtasks) / 5 * 100
```

## Out of Scope

- Writing code fixes for any of tasks A-E (delegated to task chats).
- Modifying `dispatches/ground_truth_validation.csv` (protected).
- Changing M2 or M3 override mechanisms (DECIDED: keep both).
- Re-opening the M1 decision (DECIDED: removed permanently).
- Starting work on non-calibration fitqc tasks (directory-cleanup,
  filter-api-rename, real-world-validation, sphinx-rtd, pypi-deploy,
  ppa-integration, analyze-overrides-m1-cleanup). Those have their
  own CPM entries and are not on this critical path.
- Auto-spawning task sessions (DECIDED: queue for user).

## Open Items

- PROPOSED: If Task B reveals that `vy` and `vz` false negatives are
  interior-spike phenomena, the orchestrator must update Task D's
  scope to include them before writing D's dispatch. Escalate to user
  for approval before the scope change.
- PROPOSED: `actual_duration` estimation for R3 may be hard if a task
  spans multiple chat sessions. Default: estimate from commit
  timestamps minus obvious idle gaps. Flag to user if uncertain.
