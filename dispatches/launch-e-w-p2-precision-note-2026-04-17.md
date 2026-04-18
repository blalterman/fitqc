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

**Read:** `dispatches/dispatch-e-w-p2-precision-note-2026-04-17.md`

## Key Decisions

- DECIDED: The 1e-8 inflection is a machine-precision artifact from
  the upstream data pipeline. Confirmed by user during 2026-04-17
  review.
- DECIDED: This task documents; it does NOT fix detection.
- DECIDED: If the detector latches on 1e-8 under default config,
  escalate as a bug and scope a follow-up. Do not patch here.

## Scope

1. Empirically verify whether the current interior detector selects
   the 1e-8 inflection or the real-scale inflection on e_w_p2.
2. Write `dispatches/e-w-p2-precision-note-2026-04-XX.md`.
3. Add a 1-2 line reference comment in `src/fitqc/config.py`.
4. Single commit.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- No detection-algorithm edits. No config-default changes.
- Single commit: `docs(analysis): document e_w_p2 machine-precision artifact`.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
test -f dispatches/e-w-p2-precision-note-2026-04-*.md
grep -n "precision" src/fitqc/config.py
```
