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

**Read:** `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-calibration-orchestrator-2026-04-17.md`

## Commits

- `fb4ad25` refactor(boundary): remove M1 spread-pileup override
- `fdf40f9` feat(analysis): use CSV ground truth in override factorial analysis
- `57d6480` fix(test): correct fitqc_test metadata from empirical ground truth

## Key Decisions

- DECIDED: The orchestrator is coordinator-only. It produces dispatches/
  launches for tasks C/D/E, verifies task acceptance criteria, updates
  the CPM dashboard, and queues tasks for the user. It does NOT execute
  task work (no code edits, no pytest fixes, no `analyze_overrides.py`
  re-runs, no branch merges).
- DECIDED: When tasks complete, the orchestrator runs
  `/critpath:update-status` to mark them complete in CPM with actual
  dates and duration, then validates via `cpm validate && cpm import &&
  cpm pipeline`.
- DECIDED: Task sessions are queued for the user — they open new chats
  and paste the launch prompt. The orchestrator does NOT use the Agent
  tool to auto-spawn sub-sessions.
- DECIDED: The calibration plan (5 tasks: A quantile tests, B boundary
  FNs, C tolerance mags, D interior detection, E end-to-end mask
  validation) is fixed. Dependencies: A → B → C; D parallel; E waits
  on B, C, D.
- DECIDED: Tasks A and B dispatches + launch prompts already exist in
  `/Users/balterma/observatories/code/fitqc/dispatches/`. The
  orchestrator's first dispatch-writing work is task D (parallel, can
  start any time) or task C/E (gated on B).
- DECIDED: One orchestrator chat per coordination window (~1-3 days or
  ~100k context, whichever is first). When the chat nears its limit,
  hand off to a fresh orchestrator chat via the standard handoff
  protocol.

## Scope

1. On startup, verify orchestrator readiness:
   - Plan file exists at `/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`.
   - A and B dispatches + launches exist at
     `/Users/balterma/observatories/code/fitqc/dispatches/`.
   - CPM shows 6 calibration tasks (parent + 5 subtasks) for project `fitqc`.
   - Repo branch is `claude/fitqc-ppa12-validation-vwKdg`.

2. Identify current calibration state:
   - Read CPM status for each of the 5 subtasks and the parent.
   - Check recent commits on the repo branch for evidence of task-session
     work that hasn't been reflected in CPM yet.
   - Determine the next action: queue a not-yet-started task, verify a
     just-finished one, or write a dispatch for a downstream task
     whose predecessor is now complete.

3. Execute one of the workflow actions:
   - **Queue next task**: produce dispatch + launch prompt if missing,
     tell user the launch prompt path.
   - **Verify completed task**: run the per-criterion check against the
     task's dispatch; report pass/fail.
   - **Update CPM**: `/critpath:update-status` + validation sequence.
   - **Surface blocker**: summarize and AskUserQuestion if options exist.

4. Before ending the session, produce a summary of:
   - What moved (status changes, dispatches produced).
   - What the user should do next (which new chat to open, what decision
     is pending).

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Dashboard: `/Users/balterma/observatories/code/claude-pm-container/claude-pm`
- Conda env for cpm commands: `critpath`
- Pre-commit hooks on the fitqc repo include whole-repo format check.
  The orchestrator does not commit code, so this shouldn't block, but
  any generated file in the repo (dispatches, launches) must pass
  `bash ~/.claude/tools/lint-ai-clean.sh <file>` before being written.
- Sandbox may block `/Users/balterma/.cache/pre-commit/`. If pre-commit
  hook execution fails on that path, use `dangerouslyDisableSandbox:
  true` for that command only (rare for orchestrator work).
- All new dispatches and launches: write to
  `/Users/balterma/observatories/code/fitqc/dispatches/` AND copy to
  `~/Documents/Obsidian-Vault/fitqc/dispatches/`.
- Dispatches follow the structure in
  `~/.claude/rules/handoff-protocol.md` and the format of existing
  A/B dispatches.
- Launch prompts use the 6-step plan-first protocol from the current
  `handoff-protocol.md` (as of 2026-04-17).

## Verification

Startup readiness:

```bash
test -f /Users/balterma/.claude/plans/delegated-stargazing-iverson.md && echo "plan: OK"
ls /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-quantile-test-failures-2026-04-16.md \
   /Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-quantile-test-failures-2026-04-16.md \
   /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-false-negatives-2026-04-17.md \
   /Users/balterma/observatories/code/fitqc/dispatches/launch-boundary-false-negatives-2026-04-17.md \
   2>&1 | grep -c "^/"  # Expected: 4

cd /Users/balterma/observatories/code/fitqc && git branch --show-current
# Expected: claude/fitqc-ppa12-validation-vwKdg

cd /Users/balterma/observatories/code/claude-pm-container/claude-pm && \
  conda run -n critpath cpm pipeline-status 2>&1 | grep -c "calibration"
# Expected: at least 6 (parent + 5 subtasks)
```

Current calibration state (run at the start of each orchestrator chat):

```bash
cd /Users/balterma/observatories/code/claude-pm-container/claude-pm && \
  conda run -n critpath cpm pipeline-status 2>&1 | grep -E "^\s*calibration" | sort
```

Expected output shape: each of the 6 tasks with its status and
percentComplete. The "ready" task(s) indicate what to queue next.

Recent repo activity:

```bash
cd /Users/balterma/observatories/code/fitqc && git log --oneline -10
# Look for commits whose messages reference calibration task IDs.
# Any such commit since last orchestrator run is evidence of work
# that needs verification + CPM update.
```

After any CPM update:

```bash
cd /Users/balterma/observatories/code/claude-pm-container/claude-pm && \
  conda run -n critpath cpm validate && \
  conda run -n critpath cpm import && \
  conda run -n critpath cpm pipeline
# Expected: all three commands succeed. No "error" or "cycle" in output.
```

Follow the handoff Resume Protocol to confirm state before acting.
