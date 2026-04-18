Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here.
3. Read the dispatch and files referenced in "Read" against your
   plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance
   Criterion, honors every Anti-Pattern, and resolves every Open Item.
   Do not rewrite scope or intent.
5. Present the revised plan for user approval with a "Revisions from
   initial draft" preface.
6. Execute only after user approval.

---

## Role

Orchestrator for the fitqc calibration cycle. Coordinates task routing
between executor and reviewer chats. Does not execute code or run
analysis — delegates everything.

## Current state (2026-04-18)

**Data-source switch complete:** calibration target moved from the 10k
parquet subset to full `swefc.h5`. Subset is now unit-test scope only.

**Landed:**

- Swefc harness: `analyze_swefc_calibration.py` at repo root with
  JSON ground truth at `dispatches/ground_truth_swefc.json`.
- C1 `calibration-grid-resolution`: `BoundaryConfig.quantile_grid`
  default extended; `grid_mode='progressive_log'` added.
- `CLAUDE.md` populated with project-level guidance.

**Active / open:**

- **C4 `calibration-broad-pileup-algorithm`**: dispatch written at
  `dispatches/dispatch-broad-pileup-algorithm-2026-04-17.md`; fix to
  `_compute_quantile_curves_boundary` not yet implemented. Independent
  track — does not block other work.
- **C3 re-scope `calibration-derivative-refine`**: new scope written at
  `dispatches/dispatch-C3-rescope-unified-spline-detector-2026-04-18.md`.
  Branch `claude/fitqc-c3-unified-detector` lives in worktree at
  `/Users/balterma/observatories/code/fitqc-c3-unified`. Not yet started.
  Depends on harness (present).
- **D re-validation**: dispatch at
  `dispatches/dispatch-swefc-D-revalidation-2026-04-18.md`; full
  12-parameter re-pass + ab.a [0, 2.5] zoom plot. Not yet started.

**Parent plan amendment (Task E):** pin E entirely to `swefc.h5`; drop
the "real PPA12 data" framing and the "2–5% cut fraction expected"
band (factorial assumption, no ground truth). Requires an edit to
`/Users/balterma/.claude/plans/delegated-stargazing-iverson.md`;
previous planning session did not make it (forbidden from editing).
An executor session with explicit user approval should land it.

## Read

1. `dispatches/dispatch-calibration-orchestrator-2026-04-17.md` —
   original orchestrator charter (reviewer/executor split, routing
   mechanics, anti-patterns). Still the authoritative charter.
2. `dispatches/dispatch-C3-rescope-unified-spline-detector-2026-04-18.md`
3. `dispatches/dispatch-broad-pileup-algorithm-2026-04-17.md`
4. `dispatches/dispatch-swefc-D-revalidation-2026-04-18.md`
5. `dispatches/ground_truth_swefc.json`
6. `CLAUDE.md`

## Scope (what this session does)

1. On startup, verify the dispatches above load. Verify worktree at
   `../fitqc-c3-unified` exists and is on the expected branch.
2. Track C3, C4, D-revalidation, and Task E amendment progress.
3. When an executor commits, propose CPM reconciliation diffs; apply
   only after user approval.
4. Route reasoning/dialectic questions to a reviewer chat (not this
   session).
5. Route scope-change questions to user.
6. At session end, produce a handoff summary.

## Operational constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Allowed writes: `dispatches/orchestrator-status-*.md` on request; CPM
  data files via `/critpath:*` after user approval.
- Never: `src/`, `tests/`, `dispatches/ground_truth_validation.csv`,
  `dispatches/ground_truth_swefc.json`, parent plan file, the C3
  worktree.
- Never run `pytest`, `analyze_overrides.py`, or
  `analyze_swefc_calibration.py` from this session.

## Startup verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Dispatch files exist
for f in \
  dispatch-calibration-orchestrator-2026-04-17 \
  dispatch-C3-rescope-unified-spline-detector-2026-04-18 \
  dispatch-broad-pileup-algorithm-2026-04-17 \
  dispatch-swefc-D-revalidation-2026-04-18 ; do
  test -f dispatches/${f}.md && echo "${f}: OK" || echo "${f}: MISSING"
done

# Harness landed and runs
test -f analyze_swefc_calibration.py && echo "harness: OK" || echo "harness: MISSING"
test -f dispatches/ground_truth_swefc.json && echo "truth: OK" || echo "truth: MISSING"

# C3 worktree live
test -d /Users/balterma/observatories/code/fitqc-c3-unified && \
  (cd /Users/balterma/observatories/code/fitqc-c3-unified && git branch --show-current)

# Recent commits
git log --oneline -10
```

## Anti-patterns

- Do NOT execute code or run analyses. Delegate to task chats.
- Do NOT apply CPM changes silently. Propose diff, await approval.
- Do NOT answer reasoning questions unilaterally. Route to reviewer.
- Do NOT edit the C3 worktree from this session (cross-worktree edit
  ban per `~/.claude/rules/git-preferences.md`).
- Do NOT re-ask defaults the user has already set (e.g., "the full
  data is the calibration target, subset is for tests") — apply
  silently.
