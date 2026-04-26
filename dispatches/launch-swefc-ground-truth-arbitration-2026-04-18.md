# Launch: Build swefc ground-truth arbitration fixture

Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here. Treat it as your
   hypothesis for HOW to execute the work.
3. Read the dispatch and other files referenced below against your
   plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance Criterion
   in the dispatch, honors every Anti-Pattern, and resolves every Open
   Item (either by answering or by flagging as a user question). Do not
   rewrite scope or intent.
5. Present the revised plan for user approval with a "Revisions from
   initial draft" preface.
6. Execute only after user approval.

---

## Dispatch

`/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-ground-truth-arbitration-2026-04-18.md`

## Scope (summary)

Encode the user's 2026-04-17 full-dataset bullet list as a
machine-readable fixture (`dispatches/ground_truth_swefc.json` or
`.yaml`) parallel to `dispatches/ground_truth_validation.csv`. Produce
`dispatches/ground-truth-arbitration-2026-04-18.md` enumerating CSV-vs-swefc
deltas. CSV must not be edited.

## Read

1. Dispatch (above).
2. `dispatches/ground_truth_validation.csv` — existing schema anchor.
3. `dispatches/plot_swefc_fit_param_hists.py` — parameter tuple catalog.

## Prior session commits

- `cdee81f` docs(dispatches): add broad-pileup algorithm dispatch and grid prototypes
- Plan session 2026-04-18 produced the dispatches for this work order.

## Verification

```bash
ls dispatches/ground_truth_swefc.*
ls dispatches/ground-truth-arbitration-2026-04-18.md
git diff dispatches/ground_truth_validation.csv  # must be empty
```

## Operational constraints

- No edits under `src/fitqc/`.
- No pytest runs required.
- Do not commit `swefc.h5`.
