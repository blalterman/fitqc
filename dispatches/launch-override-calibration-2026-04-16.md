Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

**Read:** `dispatches/dispatch-override-calibration-2026-04-16.md`

## Commits

- `78c970b` fix(plot): fix boundary elbow overlay, interior color contrast, and add PPA12 diagnostics script
- `46d6cbd` feat(boundary): extract check_excess_mass, store raw elbows, add seam tests
- `7f8d7a7` fix(boundary): complete iterative Kneedle refinement (Fix 5 Part 2)

Analysis work is in untracked files: `analyze_overrides.py`,
`make_inspection_plots.py`, `make_verification_plots.py`, `dispatches/`.

## Key Decisions

- DECIDED: Ground truth is `dispatches/ground_truth_validation.csv`, built from
  visual inspection of raw data distributions. Do NOT use `fitqc_test` metadata
  as ground truth -- it was calibrated with overrides active (circularity).
- DECIDED: M2 (delta-function propagation) is kept. It corrects threshold
  magnitudes for downstream filtering.
- DECIDED: `refine_transition=True` for all comparisons.
- DECIDED: L, U, x0 values in the CSV come from the fitting pipeline, not fitqc.
- PROPOSED: Remove M1 and M3 -- must re-evaluate against corrected ground truth
  before acting. w_const lower IS sticky, so M3 may have been correct there.

## Scope

1. Modify `analyze_overrides.py` to load ground truth from
   `dispatches/ground_truth_validation.csv` instead of `fitqc_test` metadata.
   Re-run to get corrected verdicts.

2. Update `fitqc_test` in all 12 `tests/data/*_test_metadata.json` files to
   match the CSV. Key corrections: np1/vx/vy/vz flip to bilateral stickiness,
   A_He lower flips to False, w_const lower flips to True.

3. Update tests that assert against `fitqc_test` expectations -- they will
   break after metadata changes.

4. Based on revised verdicts: remove, keep, or modify M1/M3 in
   `src/fitqc/boundary.py:682-739`. Do not edit until user approves.

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check
- Test data: `tests/data/{name}_test_sample.parquet` + `{name}_test_metadata.json`
- Use pyarrow (not pandas) for reading parquet
- Sandbox may block `open` commands -- use `dangerouslyDisableSandbox` for those

## Verification

```bash
# Ground truth and analysis artifacts exist
test -f dispatches/ground_truth_validation.csv && echo "OK"
test -f analyze_overrides.py && echo "OK"
test -f dispatches/override_review_results.md && echo "OK"

# Analysis script runs with corrected ground truth
python analyze_overrides.py

# Tests pass after metadata + test updates
python -m pytest tests/ -x -q

# boundary.py unchanged until recommendation approved
git diff --name-only src/fitqc/boundary.py
```

Follow the handoff Resume Protocol to confirm state before acting.
