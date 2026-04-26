Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

**Read:** `dispatches/dispatch-override-review-2026-04-15.md`

## Key Decisions

- DECIDED: M1/M2/M3 overrides are suspected escape hatches causing boundary
  detection problems. This session investigates; it does not change production code.
- DECIDED: Comparison must use `refine_transition=True` (overrides only fire
  with refinement enabled).
- DECIDED: Correctness is judged against known pileup fractions in test metadata
  (`fitqc_test` field), not visual inspection.

## Scope

Run boundary QC on all 12 PPA12 datasets under 5 configurations:

1. All overrides enabled (current behavior)
2. M1 disabled
3. M3 disabled
4. M2 disabled
5. All overrides disabled

Record `t_lo_raw`, `t_lo_star`, `t_hi_raw`, `t_hi_star`, detection booleans.
Produce a comparison table, per-override verdicts, and a recommendation.

Analysis-only. No source code changes.

## Critical Files

- `src/fitqc/boundary.py:682-739` -- M1 and M3 override blocks
- `src/fitqc/boundary.py:857-906` -- M2 override block
- `src/fitqc/boundary.py:444-513` -- `_check_excess_mass`
- `tests/test_boundary_seams_overrides.py` -- seam tests documenting override behavior
- `tests/conftest.py:338-360` -- `all_ppa12_test_cases` fixture
- `tests/data/*_test_metadata.json` -- expected detection results per dataset

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check
- Test data: `tests/data/{name}_test_sample.parquet` + `{name}_test_metadata.json`
- Use pyarrow (not pandas) for reading parquet
- To disable individual overrides, use monkey-patching or conditional flags in
  a standalone analysis script; do NOT edit `boundary.py`

## Verification

```bash
# Prerequisites
python -c "
from fitqc import run_boundary_qc, BoundaryConfig
import numpy as np
rng = np.random.default_rng(42)
x = np.concatenate([rng.uniform(0, 0.01, 500), rng.uniform(0, 10, 9500)])
config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')
result = run_boundary_qc(x, 0.0, 10.0, config)
assert result.t_lo_raw is not None
assert result.kneedle_elbows_lower is not None
print('Prerequisites OK')
"

# Analysis script runs on all 12 datasets without error
python analyze_overrides.py

# Existing tests still pass
python -m pytest tests/ -x -q
```

Follow the handoff Resume Protocol to confirm state before acting.
