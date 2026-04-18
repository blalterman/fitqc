# Launch: D (interior-det) delta re-validation on swefc.h5

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

`/Users/balterma/observatories/code/fitqc/dispatches/dispatch-swefc-D-revalidation-2026-04-18.md`

## Scope (summary)

Run `analyze_swefc_calibration.py` restricted to six delta parameters
(`v_param.y.p1`, `v_param.z.p1`, `e.w.p1`, `e.w.p2`, `e.w.a`, `ab.a`).
Produce `dispatches/swefc_interior_det_report-2026-04-18.md` with
detected-vs-asserted interior loci and pass/fail. No edits to
`src/fitqc/interior.py`.

## Read

1. Dispatch (above).
2. `dispatches/ground_truth_swefc.json`.
3. `analyze_swefc_calibration.py` (from harness dispatch).
4. `src/fitqc/interior.py`.

## Prerequisites (verify before running)

```bash
test -f analyze_swefc_calibration.py && echo OK_HARNESS || echo MISSING_HARNESS
test -f swefc.h5 && echo OK_DATA || echo MISSING_DATA
```

## Verification

```bash
python analyze_swefc_calibration.py --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json

ls dispatches/swefc_interior_det_report-2026-04-18.md
ls figures/swefc_ab_a_zoom_0_to_2.5.pdf
git diff src/fitqc/interior.py   # must be empty
python -m pytest tests/ -q
```

## Operational constraints

- Do not tune `interior.py`. Report root cause only.
- Full pass across all 12 bullet-list parameters + ab.a [0, 2.5] zoom
  plot at the current diagnostic resolution.
