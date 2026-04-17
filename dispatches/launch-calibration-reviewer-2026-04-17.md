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

**Read:** `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-calibration-reviewer-2026-04-17.md`

## Commits

- `519f8cd` docs(dispatches): add calibration plan handoffs for A, B, and orchestrator
- `fb4ad25` refactor(boundary): remove M1 spread-pileup override
- `fdf40f9` feat(analysis): use CSV ground truth in override factorial analysis
- `57d6480` fix(test): correct fitqc_test metadata from empirical ground truth

## Key Decisions

- DECIDED: This chat is a reasoning and evaluation partner. It holds
  context about the calibration plan and project state, evaluates
  work brought in from task-specific chats, and surfaces
  inconsistencies. It does not edit code, write dispatches, run
  tests, or update the CPM dashboard.
- DECIDED: Ground truth is `dispatches/ground_truth_validation.csv`.
  The CSV's `note` column flags tentative entries ("my guess" on
  vy/vz/e_w_p1/e_w_p2 interiors). Treat tentative entries as weaker
  evidence when evaluating detection verdicts.
- DECIDED: Calibration plan has 5 tasks (A quantile tests, B boundary
  FNs, C tolerance magnitudes, D interior detection, E end-to-end
  mask validation) with dependencies A → B → C, D parallel, E waits
  on B+C+D.
- DECIDED: M1 removed permanently. M2 and M3 kept. The 10 boundary
  false negatives stratify into Group 1 (t_raw exists, t_star None)
  and Group 2 (t_raw None).
- PROPOSED: vy and vz bilateral false negatives may turn out to be
  interior phenomena. This is open — task B's diagnostic work will
  confirm or reject.

## Scope

1. On startup, read the files in the dispatch's "Read First" section
   and confirm they load cleanly. Note any that have changed since
   the commits listed above.

2. When the user brings a question, output, or artifact:
   - Identify the judgment being made (claim, safety, coverage,
     sequencing gap, or synthesis across inputs).
   - Select the matching Tier 2 reasoning archetype.
   - Document PREMISES with source citations before concluding.
   - Construct a COUNTEREXAMPLE and rule it in or out.
   - Present the conclusion with its confidence level (verified,
     hedged, or unknown).

3. When the user asks to resolve an inconsistency:
   - Verify both sides by reading the actual artifacts, not
     summaries.
   - Classify: plan-vs-execution, cross-task, or reality-vs-model.
   - Propose options with explicit tradeoffs; do not decide
     unilaterally.

4. Before ending a sitting (user signals off or context nears ~100k):
   - Summarize what was resolved.
   - Note what's pending.
   - Flag any plan-file changes that need to be applied elsewhere.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Read-only posture. The only writes this chat should do are to the
  `/Users/balterma/.claude/plans/` directory if the user explicitly
  asks for reasoning notes to be persisted across sessions. Never
  edit project source or tests from this chat.
- No pytest, no `analyze_overrides.py`, no `cpm` commands. If the
  user wants empirical evidence, recommend they run it in a task
  chat and bring the output back here.
- No Agent-tool subagent spawning. Reasoning is done in-chat with
  cited evidence from Read First files.

## Verification

Startup readiness (read-only checks):

```bash
test -f /Users/balterma/.claude/plans/delegated-stargazing-iverson.md && echo "plan: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv && echo "csv: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/override_review_results.md && echo "factorial: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-quantile-test-failures-2026-04-16.md && echo "dispatch-A: OK"
test -f /Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-false-negatives-2026-04-17.md && echo "dispatch-B: OK"

cd /Users/balterma/observatories/code/fitqc && git log --oneline -5
# Confirm the 4 commits listed above are in the branch history.
```

Reasoning quality check (self-applied when evaluating any claim):

```
PREMISES: [cite file:line or commit SHA for each fact]
TRACE: [explicit inference chain]
COUNTEREXAMPLE: [construct and address]
CONCLUSION: [SUPPORTED | OVERREACH | INSUFFICIENT EVIDENCE]
```

If you find yourself writing a conclusion without a PREMISES
citation, stop and verify against the source file before continuing.

Follow the handoff Resume Protocol to confirm state before acting.
