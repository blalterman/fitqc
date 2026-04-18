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

**Read:** `dispatches/dispatch-plot-axis-scale-2026-04-17.md`

## Key Decisions

- DECIDED: Source change (log-x auto-detect + log-spaced bins) is
  already applied in the prior session. Verify; do not reapply.
- DECIDED: Auto-detect threshold is `L > 0 and U / L > 100`. Do not
  change.
- DECIDED: FD/Doane computed on `log10(x_clean)` when log-x; on raw
  x when linear. Floor 500, ceiling 2000 preserved.
- DECIDED: Log-x applies only to row 1 in this task.

## Scope

1. Verify source state matches the dispatch spec.
2. Add a test covering the log-x path.
3. Regenerate 12 overview PDFs; visually confirm np1/np2 log-x and a
   zero-centered param unchanged.
4. Single commit.

## Operational Constraints

- Repo: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- If source state does NOT match dispatch, STOP and escalate.
  Do not reapply the source change without confirming.
- Single commit: `feat(plot): log-x auto-detect on row-1 for wide-range params`.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc
grep -n "use_log_x" src/fitqc/plot.py
python -m pytest tests/test_plot_improvements.py -q
python dispatches/plot_all_ppa12_diagnostics.py
```
