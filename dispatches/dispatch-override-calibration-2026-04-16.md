Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

# Dispatch: Re-evaluate overrides against empirical ground truth and tune detection

**Generated:** 2026-04-16
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Work type:** analysis + software

## Scope

Three sequential tasks:

1. **Re-run override verdicts** against the empirical ground truth CSV
   (`dispatches/ground_truth_validation.csv`) instead of `fitqc_test` metadata.
   The prior session's verdicts used pipeline-generated metadata as ground truth,
   which is circular. The CSV was built from visual inspection of raw data
   distributions.

2. **Update `fitqc_test` metadata** in `tests/data/*_test_metadata.json` to match
   the empirical ground truth. Several metadata entries are wrong:
   - A_He: lower should be False (spike is at ~0.1, not at L=0)
   - np1: both should be True (metadata said False/False)
   - vx: both should be True (metadata said False/False)
   - vy: both should be True (metadata said False/False)
   - vz: both should be True (metadata said False/False)
   - w_const: lower should be True (metadata said False)
   - e_w_p2: lower should be True (metadata said False)
   - e_w_a: interior count is 2 (spikes at 0 and ~-25)

3. **Remove M1 and M3 or keep them** based on the revised verdicts. The prior
   session recommended removing both, but that was based on the wrong ground truth.
   With w_const lower confirmed sticky, M3's detection there was correct -- the
   verdict may flip. Re-evaluate before acting.

## Motivation

The boundary QC pipeline has three override mechanisms (M1, M2, M3) whose
correctness was evaluated against `fitqc_test` metadata. That metadata was
calibrated with the overrides active, making the evaluation circular. The user
built empirical ground truth by visually inspecting raw data histograms
(linear-x, log-x, linear-y, log-y) for all 12 PPA12 parameters.

DECIDED: Ground truth comes from the CSV, not from pipeline metadata.
DECIDED: M2 (delta-function propagation) is kept -- it corrects threshold
magnitudes for downstream filtering without affecting detection.
DECIDED: Comparison uses `refine_transition=True` (overrides only fire with
refinement enabled).
PROPOSED: Remove M1 and M3 -- needs re-evaluation against corrected ground truth.

## Read First

1. `dispatches/ground_truth_validation.csv` -- empirical ground truth from visual
   inspection. Columns: parameter, L, U, x0, lower, upper, interior, note.
   "None" = no stickiness; a value matching L/U = stickiness confirmed at that bound.
   Interior is an integer count of interior sticky points, or "None" for none.

2. `dispatches/override_review_results.md` -- the prior session's full factorial
   analysis (8 configs x 12 datasets = 96 runs). The comparison table data is
   correct; only the verdicts (which used wrong ground truth) need re-evaluation.

3. `analyze_overrides.py` -- the analysis script that produced the 96-run results.
   Uses source-string monkey-patching via exec() to disable individual overrides.
   Can be modified to use the CSV as ground truth instead of fitqc_test metadata.

4. `src/fitqc/boundary.py:682-739` -- M1 and M3 override blocks
5. `src/fitqc/boundary.py:857-906` -- M2 override block

## Key Decisions

- DECIDED: L, U, x0 values in the CSV come from the fitting pipeline that
  produced the data, not from fitqc metadata. There is a difference.
- DECIDED: Do not use pipeline-generated metadata as ground truth to evaluate
  the pipeline itself. This is encoded in the scientific-research.md rule.
- DECIDED: M2 is kept regardless of re-evaluation.
- DECIDED: No source code changes until verdicts are re-evaluated.

## Acceptance Criteria

- [ ] Override verdicts re-computed against `ground_truth_validation.csv`
- [ ] Per-override verdict table updated with corrected ground truth
- [ ] `fitqc_test` metadata in all 12 JSON files updated to match CSV
- [ ] Existing tests updated to match corrected metadata (tests will break
      after metadata update)
- [ ] Final recommendation on M1/M3 with evidence from corrected verdicts
- [ ] If removing overrides: boundary.py modified, tests pass

## Anti-Patterns

- Do NOT use `fitqc_test.expected_*_stickiness` as ground truth -- use the CSV.
  The metadata was calibrated with overrides active (circularity).
- Do NOT assume M3 should be removed -- the prior verdict was based on wrong
  ground truth. w_const lower IS sticky, so M3 may have been correct there.
- Do NOT change override behavior before re-evaluating verdicts.
- Do NOT edit `boundary.py` until the user approves the revised recommendation.

## Verification

```bash
# Prerequisites: analysis script and ground truth exist
test -f analyze_overrides.py && echo "OK" || echo "MISSING"
test -f dispatches/ground_truth_validation.csv && echo "OK" || echo "MISSING"
test -f dispatches/override_review_results.md && echo "OK" || echo "MISSING"

# After metadata updates: tests should pass with corrected expectations
python -m pytest tests/ -x -q

# No changes to boundary.py until recommendation is approved
git diff --name-only src/fitqc/boundary.py  # should be empty initially
```
