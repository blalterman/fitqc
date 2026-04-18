# Dispatch: Port ground truth to JSON for swefc harness

**Generated:** 2026-04-18
**Branch:** claude/fitqc-ppa12-validation-vwKdg
**Work type:** data
**CPM task:** `calibration-swefc-ground-truth` (new)

## Scope

Port `dispatches/ground_truth_validation.csv` to
`dispatches/ground_truth_swefc.json` so the new swefc harness can
machine-load it. The numbers in the CSV already match the user's
2026-04-17 bullet list (extracted from source + data); this dispatch
is a format change, not an arbitration. Verify every bullet-list
feature is represented and flag any row that isn't.

## Read First

1. `dispatches/ground_truth_validation.csv` — existing fixture
   (8 cols: `parameter, L, U, x0, lower, upper, interior, note`,
   13 rows).
2. `dispatches/plot_swefc_fit_param_hists.py` — parameter tuple
   catalog (MultiIndex column names).
3. Bullet list in `/Users/balterma/.claude/plans/do-not-execute-the-zippy-cake.md`
   (launch-prompt section) — coverage checklist.

## Deliverable

`dispatches/ground_truth_swefc.json` with one record per parameter.
Minimum schema per record:

```json
{
  "parameter": "v_param.y.p1",
  "column_tuple": ["v_param", "y", "p1"],
  "L": <from CSV>,
  "U": <from CSV>,
  "x0": <from CSV>,
  "lower": <from CSV bool>,
  "upper": <from CSV bool>,
  "interior": <from CSV bool>,
  "interior_locations": [<e.g. 0.0; for e_w_a include 0 and -25>],
  "below_lower_cut": <true for np2>,
  "note": "<from CSV note column>"
}
```

Where the bullet list adds structure the CSV did not encode (e_w_a's
two interior loci, np2's below-lower cut), add fields as above.

## Acceptance Criteria

- [ ] `dispatches/ground_truth_swefc.json` committed.
- [ ] All 12 bullet-list parameters present.
- [ ] For each parameter, JSON values match the CSV row; any
      divergence flagged in the commit body with the reason.
- [ ] `dispatches/ground_truth_validation.csv` unchanged.
- [ ] No `src/fitqc/` edits, no pytest runs required.

## Anti-Patterns

- Do NOT edit the CSV.
- Do NOT invent numbers — if the CSV lacks a value the bullet list
  requires (e.g. e_w_a second locus), flag in a NOTE field rather
  than guessing.

## Out of Scope

- Building the harness (separate dispatch).
- Running detection against the fixture.
