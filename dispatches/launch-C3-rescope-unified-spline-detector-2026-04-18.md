# Launch: C3 re-scope — unified `|x − c|` spline detector

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

`/Users/balterma/observatories/code/fitqc/dispatches/dispatch-C3-rescope-unified-spline-detector-2026-04-18.md`

## Scope (summary)

Three integrated changes, shipped together, validated in parallel:

1. Coordinate unification on `d = |x − c|` with `center_type` ∈
   `{lower, upper, interior}`.
2. Dense ECDF grid (~1000 log-spaced eps points) replacing the
   current 30-point `quantile_grid`.
3. Monotonic C² cubic spline + analytic `argmax(d²M/d(log ε)²)`
   replacing kneedle. No sensitivity parameter; residual-based
   uncertainty.

Phase 1–2 prototype in `dispatches/`, no `src/fitqc/` edits. Phase 3
integration only after parallel validation passes.

## Read

1. Dispatch (above).
2. `dispatches/ground_truth_swefc.json`.
3. `analyze_swefc_calibration.py` (harness, from Task #2).
4. `src/fitqc/boundary.py` lines 148–218.
5. `src/fitqc/interior.py` lines 1–100.
6. `src/fitqc/config.py`.

## Prerequisites (verify before starting)

```bash
test -f analyze_swefc_calibration.py && echo OK_HARNESS || echo MISSING_HARNESS
test -f dispatches/ground_truth_swefc.json && echo OK_TRUTH || echo MISSING_TRUTH
test -f swefc.h5 && echo OK_DATA || echo MISSING_DATA
```

If any MISSING, stop and ask.

## Verification

```bash
python dispatches/prototype_unified_spline_detector.py \
  --h5 ./swefc.h5 \
  --truth dispatches/ground_truth_swefc.json \
  --report dispatches/unified_detector_comparison_report.md \
  --figure figures/unified_detector_overlay.pdf

ls dispatches/unified_detector_comparison_report.md
ls figures/unified_detector_overlay.pdf
git diff src/fitqc/   # must be empty through Phase 1-2
python -m pytest tests/ -q
```

## Operational constraints

- Phase 1–2: no `src/fitqc/` edits.
- Phase 3 gated on Phase 2 validation passing (spline at parity with
  kneedle on current TPs; spline catches `ab.a` at x=1 and `e.w.a`
  at −25 where interior.py cannot).
- Do not remove kneedle or legacy detectors in Phase 3; gate unified
  behind `BoundaryConfig.detector_mode`.
- Null-reference models are preserved (uniform-tail for boundaries;
  local-density for interior). Null-model changes are out of scope.

## Key anti-patterns

- No `BoundaryConfig` sensitivity knob analogous to kneedle's `S`.
- No signed-distance handling; `|x − c|` fold is correct by the
  stickiness definition (above-L, below-U, bilateral-around-interior).
- No deletion of `boundary.py` / `interior.py` in this dispatch.

## Depends on

- Task #2 (`calibration-swefc-harness`) must be live so the prototype
  can run in parallel with the harness's current-detector output.
