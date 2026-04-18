Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here. Treat it as your
   hypothesis for HOW to execute the work.
3. Read the dispatch, plan, and other files referenced in the "Read First"
   section against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance Criterion in
   the dispatch, honors every Anti-Pattern, and resolves every Open Item
   (either by answering or by flagging as a user question). Do not rewrite
   scope or intent — they were reviewed in the prior session.
5. Present the revised plan for user approval. Prefix it with a "Revisions
   from initial draft" section noting what changed between steps 2 and 4.
6. Execute only after user approval.

---

# Dispatch: Audit swefc calibration harness at high effort

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** software / analysis
**Parent dispatch:** `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-harness-2026-04-18.md`

## Scope

Audit every artifact produced under the parent dispatch, correct
defects, and regenerate outputs. The deliverables are the same files
the parent dispatch produced:

1. `/Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
2. `/Users/balterma/observatories/code/fitqc/tests/test_swefc_harness.py`
3. `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_swefc_diagnostics.py`
4. `/Users/balterma/observatories/code/fitqc/dispatches/swefc_calibration_report.md`
5. `/Users/balterma/observatories/code/fitqc/figures/swefc_calibration_report.pdf`
6. `/Users/balterma/observatories/code/fitqc/figures/swefc_overview.pdf`

Treat current file contents as suspect — read each in full, cross-check
against the parent dispatch's acceptance criteria and the ground-truth
JSON schema, fix what is wrong, leave what is correct.

The parent dispatch's frozen-path constraint still applies:
`/Users/balterma/observatories/code/fitqc/analyze_overrides.py` and
everything under `/Users/balterma/observatories/code/fitqc/src/fitqc/`
are off-limits. If you find a detector defect, record it against
`/Users/balterma/observatories/code/fitqc/dispatches/dispatch-detector-tuning-swefc-2026-04-18.md`
rather than editing `src/fitqc/`.

## Motivation

The parent dispatch was executed under low-effort harness settings.
The user caught one semantic defect: `ab.a` in
`ground_truth_swefc.json` had `x0` conflated with `interior_locations`,
and the harness / overview inherited that confusion. The user does not
trust the remaining artifacts without an independent audit and asked
for re-execution under high effort. The suspicion is that other
semantic issues may be latent in the harness, test fixture, or
overview generator.

The correction for `ab.a` has already been applied in the current
working tree: `x0=0` (pipeline initial guess), `interior_locations=[1]`
(empirical spike center). `_meta.notes` in the JSON now documents the
schema distinction. The audit must preserve this semantics, not
regress it.

## Read First

1. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-harness-2026-04-18.md`
   — the parent dispatch. Every acceptance criterion it lists is
   still authoritative. Read the full text, not a summary.
2. `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_swefc.json`
   — schema, exceptions, and `_meta.notes` field explaining
   `x0` vs `interior_locations`. Note the two documented exceptions
   (`e.w.a` with `interior_locations=[0, -25]`, `ab.a` with `x0=0`
   and `interior_locations=[1]`).
3. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-detector-tuning-swefc-2026-04-18.md`
   — defines what is OUT of scope for this audit (anything under
   `src/fitqc/`). Read so you know where the boundary is.
4. `/Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py`
   — current harness. Audit `run_one`, per-parameter loop, ground-truth
   loading, CLI, report writer, figure writer. The function that matters
   most is `run_one`: it iterates `interior_locations` (not `x0`),
   OR-aggregates detection across locations, and records
   `interior_hits` as `(location, eps_star)` pairs. Confirm this
   behavior and its semantics match the JSON schema.
5. `/Users/balterma/observatories/code/fitqc/tests/test_swefc_harness.py`
   — smoke tests. Confirm they test the loader, `run_one`, and the
   end-to-end `main` path without over-asserting detection outcomes
   (detection is the harness's job, not the unit test's).
6. `/Users/balterma/observatories/code/fitqc/dispatches/plot_all_swefc_diagnostics.py`
   — overview generator. The current primary-page selection uses
   `interior_locations[0]` when interior is asserted, falling back to
   `x0` only when no empirical locations exist. Confirm this matches
   the schema intent: empirical drives visualization, pipeline
   metadata is secondary.
7. `/Users/balterma/observatories/code/fitqc/dispatches/plot_swefc_fit_param_hists.py`
   — SWEFC HDF5 schema reference. The MultiIndex column tuples
   (`("v_param", "x", "p1")` etc.) and the `pd.read_hdf(H5,
   key="ppa12_apeq")` pattern both come from here.
8. `/Users/balterma/observatories/code/fitqc/dispatches/inspect_ab_a_interior.py`
   + `/Users/balterma/observatories/code/fitqc/figures/ab_a_interior_zoom.pdf`
   — evidence that `ab.a` interior spike is at x=1 (not x=0) and that
   x=0 samples are lower-boundary stickiness. Do not discard this
   evidence if you question the ground truth.
9. `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-ground-truth-arbitration-2026-04-18.md`
   — provenance of the ground truth. Read for context on why
   `_meta.source` cites both the CSV and the 2026-04-17 visual-inspection
   bullet list.

## Prerequisites

Run before starting the audit. If any line does not produce the
expected output, stop and ask the user.

```bash
cd /Users/balterma/observatories/code/fitqc
test -f swefc.h5 && echo OK_DATA                            # expect OK_DATA
test -f dispatches/ground_truth_swefc.json && echo OK_TRUTH # expect OK_TRUTH
test -f analyze_swefc_calibration.py && echo OK_HARNESS     # expect OK_HARNESS
test -f tests/test_swefc_harness.py && echo OK_TESTS        # expect OK_TESTS
test -f dispatches/plot_all_swefc_diagnostics.py && echo OK_OVERVIEW
                                                            # expect OK_OVERVIEW
python -c "import pandas as pd; df = pd.read_hdf('swefc.h5', key='ppa12_apeq'); print(len(df))"
                                                            # expect 7549989
python -m pytest tests/ -q 2>&1 | tail -2
                                                            # expect 435 passed
```

## Audit checklist

Work through every item. For each, record what you read and what you
changed (or confirmed correct). Skipping an item is a failure.

### Harness (`analyze_swefc_calibration.py`)

- [ ] CLI matches parent dispatch §58-67: `--h5`, `--truth`,
      `--output-report`, `--output-figure`, `--param`.
- [ ] Loader uses `pd.read_hdf(h5_path, key="ppa12_apeq")`.
- [ ] Parameter column selection uses `column_tuple` from the ground
      truth entry, converted to `tuple` before DataFrame indexing.
- [ ] BoundaryConfig matches `analyze_overrides.py:43-47`:
      `BoundaryConfig(use_quantile_analysis=True,
      refine_transition=True, grid_mode="progressive")`.
- [ ] InteriorConfig: `InteriorConfig(use_quantile_analysis=True)`.
- [ ] `run_one` iterates `interior_locations` (the empirical list),
      NOT `x0`. `x0` is metadata.
- [ ] Interior detection OR-aggregates: parameter is interior-true if
      any location fires.
- [ ] `interior_hits` records `(location, eps_star)` for each firing
      location — needed for report and figure.
- [ ] NaN handling: drop non-finite before detection, report
      `n_dropped_nan` per parameter.
- [ ] Report writes to path from `--output-report` (default
      `dispatches/swefc_calibration_report.md`).
- [ ] Figure writes to path from `--output-figure` (default
      `figures/swefc_calibration_report.pdf`).
- [ ] Exit code is 0 on full pass, 1 on any mismatch — so CI can
      detect regressions.

### Smoke tests (`tests/test_swefc_harness.py`)

- [ ] Tests load the harness as a module (not via subprocess) to keep
      diagnostics usable.
- [ ] Fixture synthesizes a mini HDF5 from existing parquet under
      `tests/data/`; does not rely on `swefc.h5`.
- [ ] Asserts cover: loader returns a DataFrame, `run_one` returns a
      ParamResult with the expected fields, `main` produces report +
      figure files.
- [ ] Tests do NOT assert specific detection booleans — that is the
      harness's job on the real dataset. Asserting shape is the
      unit-test scope.
- [ ] `pytest tests/ -q` shows baseline count (currently 435) with
      the new tests included.

### Overview generator (`dispatches/plot_all_swefc_diagnostics.py`)

- [ ] Loads `swefc.h5` once, then iterates all 12 ground-truth
      entries.
- [ ] Primary page location: uses `interior_locations[0]` when
      interior is asserted, falls back to `x0` otherwise. Rationale
      is documented in-file.
- [ ] Secondary pages: one per additional empirical interior location
      (e.g. `e.w.a` has 0 and -25, so one secondary page for the
      non-primary location).
- [ ] Calls `run_boundary_qc` and `run_interior_qc` directly — no
      imports from `analyze_swefc_calibration.py` that would couple
      the two.
- [ ] Writes `figures/swefc_overview.pdf` via `PdfPages`.
- [ ] Uses the same `BoundaryConfig`/`InteriorConfig` as the harness,
      OR documents the divergence in a comment with justification.

### Report and figure regeneration

After audit edits, re-run:

- [ ] `python analyze_swefc_calibration.py` — produces report + small
      figure. Expect 11/12 all-three pass (ab.a interior FAIL is the
      known detector-tuning item).
- [ ] `python dispatches/plot_all_swefc_diagnostics.py` — produces
      `figures/swefc_overview.pdf`. ~12 minutes on 7.5M-row data.
      Expect 13 pages (12 params + one secondary for `e.w.a`).
- [ ] Confirm visually that `ab.a`'s primary page centers on x=1, not
      x=0. If it centers on x=0 the primary-location-selection logic
      is wrong.

## Acceptance Criteria

- [ ] Every item in the Audit Checklist above is closed with either
      "confirmed correct" or a diff.
- [ ] `python /Users/balterma/observatories/code/fitqc/analyze_swefc_calibration.py
      --h5 ./swefc.h5 --truth dispatches/ground_truth_swefc.json`
      runs and prints `all-three pass: 11/12`. `ab.a` interior FAIL
      is expected and captured in the detector-tuning dispatch; any
      other FAIL is a regression and must be investigated, not
      accepted.
- [ ] `python -m pytest tests/ -q` passes with the current test count
      (435 as of this dispatch). New tests welcome; removing tests
      requires justification.
- [ ] `git diff analyze_overrides.py src/fitqc/` is empty.
- [ ] `git status` shows `swefc.h5` untracked (gitignored).
- [ ] `dispatches/swefc_calibration_report.md` lists
      `interior_locations` per parameter and pass/fail per axis.
- [ ] `figures/swefc_overview.pdf` is 13 pages. Primary page for
      `ab.a` shows x0=1 (empirical interior), not x0=0.
- [ ] If any defect is found that would require `src/fitqc/` changes
      to fix, the executing session appends it to
      `dispatches/dispatch-detector-tuning-swefc-2026-04-18.md` under
      a dated entry, not to this dispatch.

## Anti-Patterns

- Do NOT treat the current implementations as correct by default.
  The whole reason for this dispatch is that low effort produced
  semantic defects the user had to catch. Read every function body
  against the parent dispatch and the schema.
- Do NOT modify `/Users/balterma/observatories/code/fitqc/analyze_overrides.py`
  or anything under `/Users/balterma/observatories/code/fitqc/src/fitqc/`.
  That is the detector-tuning dispatch's scope.
- Do NOT modify `dispatches/ground_truth_swefc.json` to make
  detection "pass". The ground truth is user-arbitrated; if the
  detector misses, that is a detector-tuning finding, not a
  ground-truth error.
- Do NOT conflate `x0` with `interior_locations`. `x0` is pipeline
  metadata (optimizer initial guess); `interior_locations` is the
  empirical list of spike centers that drives detection. The
  harness iterates the latter.
- Do NOT commit `swefc.h5`. It is gitignored and large.
- Do NOT skip regenerating `figures/swefc_overview.pdf` because it is
  slow. Plan for ~12 minutes; pick a sensible moment in the session
  to start it.
- Do NOT weaken the acceptance criterion from 11/12 to 12/12 by
  expanding detector tolerance. A 12/12 result without a deliberate
  detector-tuning commit is a red flag.
- Do NOT truncate, paraphrase, or "improve" the parent dispatch's
  acceptance criteria. They were reviewed once under low effort and
  once under high; any change here needs explicit user approval.
- Do NOT assume a passing test means the semantic model is right.
  The low-effort run passed tests and still had `x0` vs
  `interior_locations` wrong.

## Verification

```bash
cd /Users/balterma/observatories/code/fitqc

# Harness end-to-end — expect 11/12 pass
python analyze_swefc_calibration.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json

# Test suite — expect 435 passed (or more, if new audit-level tests)
python -m pytest tests/ -q

# Frozen-path audit — expect empty output from both diffs
git diff analyze_overrides.py
git diff src/fitqc/

# Overview regeneration — expect 13 pages at figures/swefc_overview.pdf
python dispatches/plot_all_swefc_diagnostics.py

# Page count check
python -c "import re; d=open('figures/swefc_overview.pdf','rb').read(); \
  print('pages:', len(re.findall(rb'/Type\s*/Page[^s]', d)))"
# expect: pages: 13

# Unstaged state audit — expect swefc.h5 untracked, no modifications to
# frozen paths
git status --porcelain | grep -E "swefc.h5|analyze_overrides|src/fitqc" || echo "clean"
# expect: clean
```

## Open Items

- O1. If the receiving session finds the `run_one` signature needs a
  new field (e.g. per-location detection booleans beyond
  `interior_hits`), is that an in-scope audit fix or should it land
  in the detector-tuning dispatch? PROPOSED answer: in-scope here if
  it does not change `src/fitqc/`. Flag if you disagree.
- O2. The current smoke tests use `importlib.util` to load the
  harness module. This works but is unconventional. Is it worth
  promoting `analyze_swefc_calibration.py` to an importable module
  (move it under a package, or add a `pyproject.toml` entry)? PROPOSED
  answer: leave as-is; the harness is a driver, not a library.
- O3. The detector-tuning dispatch's acceptance requires 12/12 after
  tuning. Should this audit commit any preparatory refactoring that
  would make tuning easier? PROPOSED answer: no, keep the audit
  strictly to correctness of the harness layer.
