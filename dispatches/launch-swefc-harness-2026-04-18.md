# Launch: Build swefc.h5 calibration harness

Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /plan-draft based only on what you read here.
3. Read the dispatch and referenced files against your plan-draft.
4. Revise your plan-draft against every Acceptance Criterion,
   Anti-Pattern, and Open Item. Do not rewrite scope or intent.
5. Present the revised plan with a "Revisions from initial draft"
   preface and wait for approval.
6. Execute only after user approval.

---

## Dispatch

`/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-harness-2026-04-18.md`

## Scope (summary)

Build `analyze_swefc_calibration.py` at repo root. Loader reads
`swefc.h5` via `pd.read_hdf(H5, key="ppa12_apeq")`; per-parameter driver
reuses `src/fitqc/boundary.py` functions with `BoundaryConfig` defaults;
comparison against `dispatches/ground_truth_swefc.json`. Produces report
+ figure. `analyze_overrides.py` and `src/fitqc/` unchanged.

## Read

1. Dispatch (above).
2. `dispatches/ground_truth_swefc.json` (must exist — from prior dispatch).
3. `dispatches/plot_swefc_fit_param_hists.py` — HDF5 schema + BASE_PARAMS.
4. `analyze_overrides.py` lines 1–80 — driver pattern.
5. `src/fitqc/boundary.py` lines 148–218 — `_compute_quantile_curves_boundary`.
6. `src/fitqc/config.py` — `BoundaryConfig`.

## Prerequisites (verify before coding)

```bash
test -f dispatches/ground_truth_swefc.json \
  || test -f dispatches/ground_truth_swefc.yaml \
  && echo OK_FIXTURE || echo MISSING_FIXTURE
test -f swefc.h5 && echo OK_DATA || echo MISSING_DATA
```

If either is MISSING, stop and ask the user.

## Verification

```bash
python analyze_swefc_calibration.py --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json

python -m pytest tests/ -q
git diff analyze_overrides.py src/fitqc/   # must be empty
```

## Operational constraints

- `swefc.h5` is gitignored. Do not commit it.
- Do not modify `analyze_overrides.py` or `src/fitqc/`.
- If detection misbehaves on full data, do not re-open C1; branch a
  `grid-resolution-swefc-followup` dispatch instead.
