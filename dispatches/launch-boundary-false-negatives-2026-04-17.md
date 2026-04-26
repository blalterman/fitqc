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

**Read:** `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-false-negatives-2026-04-17.md`

## Commits

- `fb4ad25` refactor(boundary): remove M1 spread-pileup override
- `fdf40f9` feat(analysis): use CSV ground truth in override factorial analysis
- `57d6480` fix(test): correct fitqc_test metadata from empirical ground truth
- `7f8d7a7` fix(boundary): complete iterative Kneedle refinement (Fix 5 Part 2)

## Key Decisions

- DECIDED: Ground truth is `dispatches/ground_truth_validation.csv`, built
  from visual inspection of raw data in
  `dispatches/boundary_inspection.pdf`. The pipeline is wrong when it
  disagrees. Do not edit the CSV.
- DECIDED: M2 stays (threshold-only corrections for delta pileups). M3
  stays (helps on w_const lower, confirmed by factorial against the
  corrected CSV). M1 is removed permanently.
- DECIDED: `refine_transition=True, use_quantile_analysis=True,
  grid_mode="progressive"` is the production config (matches
  `analyze_overrides.py` CONFIG).
- DECIDED: This task's acceptance criterion is ≤ 2 remaining false
  negatives. If `vy` and `vz` bilateral FNs turn out to be interior
  phenomena masquerading as boundary, they count toward the allowance
  and move to Task D.
- DECIDED: Task A (`calibration-quantile-tests`) is the critical-path
  predecessor. Verify its dispatch completed and tests pass before
  starting this task.
- PROPOSED: The 10 FNs split into two groups — Group 1 (6 cases,
  `t_raw` exists but `t_star = None`, failing `_check_excess_mass`
  validation) and Group 2 (4 cases, `t_raw = None`, Kneedle finds no
  elbow). The groups likely need different fixes. Verify the grouping
  holds when you run the factorial.

## Scope

1. Verify prerequisites:
   - `git log --oneline -5` shows Task A's commits landed (tests
     `test_boundary_quantile.py` passing).
   - `python -m pytest tests/ -q` passes (current baseline: 421
     expected after A lands, or 418 + 3 deselected if A not landed).
   - `dispatches/ground_truth_validation.csv` unchanged from commit
     `fdf40f9` (`git log -- dispatches/ground_truth_validation.csv`).

2. For each of 10 false negatives, produce a diagnostic record (see
   dispatch "Investigation protocol"):
   - e_dv_ap lower
   - np1 upper
   - np2 upper
   - vx lower
   - vy lower, vy upper
   - vz lower, vz upper
   - e_w_p1 upper
   - e_w_p2 upper

3. Apply evidence-based fixes. Commit surgically (one commit per
   root-cause category, or per parameter if mechanism is parameter-
   specific).

4. Regenerate `dispatches/override_review_results.md` by running
   `python analyze_overrides.py`. Verify ≤ 2 remaining false
   negatives, zero new false positives.

5. Write the per-parameter diagnostic record to
   `dispatches/boundary-fn-diagnostics-2026-04-17.md` (or current date).

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff lint + whole-repo format check. Untracked
  Python files in the repo are checked too; run `ruff format <file>`
  on any new scripts before staging.
- Sandbox may block `/Users/balterma/.cache/pre-commit/`. If pre-commit
  fails with "Operation not permitted" on that path, use
  `dangerouslyDisableSandbox: true` for that specific command only.
- Test data parquet files: use `pyarrow`, not `pandas`. Pattern:
  `pq.read_table(path)["values"].to_numpy()` (see
  `analyze_overrides.py:load_datasets`).
- Protected files — do NOT modify without explicit user approval in
  the chat:
  - `/Users/balterma/observatories/code/fitqc/dispatches/ground_truth_validation.csv`
  - M2 block in `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py`
    (delta-function propagation, lines ~827+ after M1 removal)
  - M3 block in the same file (broad-pileup fallback)
- `analyze_overrides.py` runtime: ~90 seconds for all 96 experiments.
  Plan iteration cycles accordingly.

## Verification

Reproduce current state (before any changes):

```bash
python analyze_overrides.py
```

Expected summary section:
```
### M1
- Helps: 0 / 24
### M3
- Helps: 1 / 24
### M2
- Helps: 0 / 24
```

Expected all-on false negatives (parameter, side):
```
e_dv_ap lower  |  np1 upper  |  np2 upper  |  vx lower
vy lower       |  vy upper   |  vz lower   |  vz upper
e_w_p1 upper   |  e_w_p2 upper
```

After fixes, confirm acceptance:

```bash
# Regenerate, then count FNs
python analyze_overrides.py
python -c "
import re, pathlib
lines = pathlib.Path('dispatches/override_review_results.md').read_text().splitlines()
# Parse the all-on rows and compare to CSV ground truth
# (full implementation left to executor — this is a sanity-check hint)
"

# Regression on existing tests
python -m pytest tests/ -q \
  --deselect tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  --deselect tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup

# If Task A landed first, include those 3 tests too (no deselect)
python -m pytest tests/ -q
# Expected: 421 passed (if A landed) OR 418 passed 3 deselected
```

Final acceptance check:

```bash
# Diagnostic record exists
test -f dispatches/boundary-fn-diagnostics-*.md && echo "diagnostics: OK"

# Factorial re-run with new code shows ≤ 2 FNs
# (executor must parse results.md to count programmatically)

# Ground truth CSV unchanged
git diff --name-only dispatches/ground_truth_validation.csv
# Expected: empty
```

Follow the handoff Resume Protocol to confirm state before acting.
