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

# Launch: Audit swefc calibration harness at high effort

## Read

1. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-harness-audit-2026-04-18.md`
   — the audit dispatch itself. Authoritative scope, acceptance
   criteria, anti-patterns, and audit checklist.
2. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-harness-2026-04-18.md`
   — the parent dispatch whose execution is being audited.
3. `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_swefc.json`
   — `_meta.notes` documents `x0` vs `interior_locations` semantics.

## Scope

Audit and correct the six artifacts produced under the parent dispatch:

- `/Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
- `/Users/balterma/observatories/code/fitqc/tests/test_swefc_harness.py`
- `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_swefc_diagnostics.py`
- `/Users/balterma/observatories/code/fitqc/dispatches/swefc_calibration_report.md`
   (regenerated from harness run)
- `/Users/balterma/observatories/code/fitqc/figures/swefc_calibration_report.pdf`
   (regenerated from harness run)
- `/Users/balterma/observatories/code/fitqc/figures/swefc_overview.pdf`
   (regenerated from `plot_all_swefc_diagnostics.py`, ~12 min runtime)

The audit dispatch contains an explicit Audit Checklist; work through
every item and close each one with either "confirmed correct" or a
diff. Do not skip items.

## Prior session commits

- `faf9e28` docs(ground-truth): clarify n_param.p2 below_lower_cut semantics
- `3b2829b` feat(ground-truth): port CSV ground truth to JSON for swefc harness
- `06698ad` chore(gitignore): exclude swefc.h5 from repo

The prior low-effort session created the three code files and the
initial report / figure outputs without committing them. The current
working tree contains those files untracked; `git status` will show
them alongside the entire dispatches directory.

## Key decisions

- DECIDED: `ab.a` ground truth correction — `x0=0` (pipeline initial
  guess), `interior_locations=[1]` (empirical spike at x=1). The 120K
  samples at exactly x=0 are lower-boundary stickiness overlapping L=0,
  not interior. Evidence in
  `/Users/balterma/observatories/code/fitqc/dispatches/inspect_ab_a_interior.py`
  and `figures/ab_a_interior_zoom.pdf`. Do not revert this.
- DECIDED: `x0` vs `interior_locations` are distinct. `x0` is
  optimizer metadata from the upstream CSV; `interior_locations` is
  the empirical list driving detection. The harness iterates
  `interior_locations`; `x0` is carried as metadata only.
- DECIDED: primary overview page uses `interior_locations[0]` when
  interior is asserted, falls back to `x0` otherwise. Rationale: the
  primary page should show the empirical spike, not the pipeline
  initial guess.
- DECIDED: Known baseline is 11/12 all-three pass. `ab.a` interior
  FAIL because the x=1 spike is ~22% above baseline — weaker than
  the current detector's tuning. This goes in the detector-tuning
  dispatch, not this one.
- DECIDED: `src/fitqc/` and `analyze_overrides.py` are frozen in this
  dispatch. Detector fixes land in
  `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-detector-tuning-swefc-2026-04-18.md`.
- PROPOSED: smoke tests in `tests/test_swefc_harness.py` load the
  harness via `importlib.util` rather than as a package import.
  Flagged as Open Item O2 in the audit dispatch.

## Operational constraints

- Working directory: `/Users/balterma/observatories/code/fitqc`
- Branch: `claude/fitqc-ppa12-validation-vwKdg` (stay on it)
- `swefc.h5` lives at repo root, is gitignored, must not be committed.
- Frozen paths: `/Users/balterma/observatories/code/fitqc/src/fitqc/`
  and `/Users/balterma/observatories/code/fitqc/analyze_overrides.py`.
  Any required change there goes into the detector-tuning dispatch.
- Overview PDF regeneration takes ~12 minutes on the 7.5M-row dataset.
  Start it in the background once the audit edits are stable; do not
  wait on it to do other work.
- Conda/pip: existing environment already has pandas, numpy,
  matplotlib, pyarrow, pytest. No new dependencies are expected.

## Verification criteria

Copy-paste, run in order, check output:

```bash
cd /Users/balterma/observatories/code/fitqc

# 1. Harness end-to-end
python analyze_swefc_calibration.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json
# expect final line: Done in <t>s  —  all-three pass: 11/12

# 2. Full test suite
python -m pytest tests/ -q
# expect last line: 435 passed ... (or higher with added audit tests)

# 3. Frozen-path check
git diff analyze_overrides.py
git diff src/fitqc/
# expect: no output for either

# 4. Overview PDF regeneration
python dispatches/plot_all_swefc_diagnostics.py
# expect final line: Done in ~720-800s -> /Users/balterma/observatories/code/fitqc/figures/swefc_overview.pdf

# 5. Overview page count
python -c "import re; d=open('figures/swefc_overview.pdf','rb').read(); \
  print('pages:', len(re.findall(rb'/Type\s*/Page[^s]', d)))"
# expect: pages: 13

# 6. swefc.h5 remains gitignored
git status --porcelain | grep -E "swefc\.h5" && echo "BAD: tracked" || echo "OK: ignored"
# expect: OK: ignored
```

## Prerequisites (no project file — run inline)

```bash
cd /Users/balterma/observatories/code/fitqc
test -f swefc.h5 && echo OK_DATA || echo MISS_DATA
test -f dispatches/ground_truth_swefc.json && echo OK_TRUTH || echo MISS_TRUTH
test -f analyze_swefc_calibration.py && echo OK_HARNESS || echo MISS_HARNESS
test -f tests/test_swefc_harness.py && echo OK_TESTS || echo MISS_TESTS
test -f dispatches/plot_all_swefc_diagnostics.py && echo OK_OVERVIEW || echo MISS_OVERVIEW
python -c "import pandas as pd; print(len(pd.read_hdf('swefc.h5', key='ppa12_apeq')))"
# expect: 7549989
```

If any `MISS_*` or a row count other than 7549989 appears, stop and
ask the user before proceeding.

No project-level launch-prerequisites file exists at
`tools/docs/launch-prerequisites.md`. Create one if this project
develops recurring pre-session checks.

## Resume protocol

Before acting on the plan produced in step 5:

1. `git status` — confirm the working tree matches the state
   described in "Prior session commits" (three code files untracked,
   `ground_truth_swefc.json` modified).
2. Re-run the Verification block above (at least steps 1-3) to
   baseline the current behavior before making changes. Record the
   output of step 1 so you can diff after your audit edits.
3. If step 1's harness run deviates from 11/12, stop and ask the user
   before editing anything — a deviation means the starting state is
   not what this dispatch assumes.

Follow the handoff Resume Protocol to confirm state before acting.
