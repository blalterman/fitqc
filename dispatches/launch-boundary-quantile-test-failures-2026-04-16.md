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

**Read:** `/Users/balterma/observatories/code/fitqc/dispatches/dispatch-boundary-quantile-test-failures-2026-04-16.md`

## Commits

- `fb4ad25` refactor(boundary): remove M1 spread-pileup override
- `fdf40f9` feat(analysis): use CSV ground truth in override factorial analysis
- `57d6480` fix(test): correct fitqc_test metadata from empirical ground truth
- `7f8d7a7` fix(boundary): complete iterative Kneedle refinement (Fix 5 Part 2)

## Key Decisions

- DECIDED: The three failures are pre-existing and unrelated to M1 removal.
  Confirmed by running the same tests against `78c970b` (pre-M1-removal)
  and reproducing the same failures.
- DECIDED: Detection booleans pass in all three cases. The failures are on
  numeric bounds for `t_star` / `elbow`, not on whether stickiness was
  detected.
- DECIDED: M1 stays removed. The failure resolutions must NOT reintroduce
  M1's spread-pileup override behavior.
- PROPOSED: Each failure's fix is evidence-driven from git-blame of the
  assertion plus tracing through the algorithm. The prior session traced
  each failure to a root cause (documented in the dispatch) but did not
  git-blame or apply fixes.

## Scope

1. Run the three failing tests and confirm they reproduce:
   `/Users/balterma/observatories/code/fitqc/tests/test_boundary_quantile.py`
   - `TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow`
   - `TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup`
   - `TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup`

2. For each failure, git-blame the failing assertion to find original
   intent:
   - `git blame -L 365,365 tests/test_boundary_quantile.py`
   - `git blame -L 455,455 tests/test_boundary_quantile.py`
   - `git blame -L 507,507 tests/test_boundary_quantile.py`

3. For each failure, determine the root cause from the dispatch's trace
   evidence plus git-blame: stale assertion bounds, algorithm regression,
   or known limitation. Record the decision in the commit message or a
   code comment.

4. Apply fixes per the determination. If any algorithm change is needed
   (not just test updates), surface to the user BEFORE modifying
   `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py`.

5. Verify all 421 tests pass (was 418 + 3 failed).

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check. Run
  `ruff format` on any new/modified Python files before staging.
- Test data parquet files use pyarrow (not pandas) — see
  `/Users/balterma/observatories/code/fitqc/tests/conftest.py`.
- Sandbox may block access to `/Users/balterma/.cache/pre-commit/`.
  If pre-commit fails with "Operation not permitted", use
  `dangerouslyDisableSandbox: true` for that command only.
- Production files protected — do NOT modify without user approval:
  - `/Users/balterma/observatories/code/fitqc/src/fitqc/boundary.py`
    (algorithm behavior: `_check_excess_mass`,
    `_compute_quantile_curves_boundary`, M2/M3 overrides)

## Verification

Reproduce the failures before starting:

```bash
python -m pytest \
  tests/test_boundary_quantile.py::TestQuantileCurveComputation::test_quantile_curve_tight_pileup_shows_elbow \
  tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_detects_tight_pileup \
  tests/test_boundary_quantile.py::TestMultiCurveIntegration::test_multi_curve_handles_broad_pileup \
  -v
```

Expected output: 3 failed.

After fixes, the same command must report 3 passed. Then confirm no
regression:

```bash
python -m pytest tests/ -q
```

Expected output: `421 passed` (currently `418 passed, 3 failed`).

Confirm `src/fitqc/boundary.py` untouched unless an algorithm change was
explicitly approved:

```bash
git diff --name-only src/fitqc/boundary.py
```

Expected output: empty (no changes) unless user approved algorithm fix.

Follow the handoff Resume Protocol to confirm state before acting.
