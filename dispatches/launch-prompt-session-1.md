Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent. Do not read feedback or dispatch documents yet --
partial reads will distort context before we have a plan. Once I approve your
plan, then execute.

---

**Read:** `dispatches/dispatch-boundary-seam-tests-2026-04-15.md`
**Read:** `~/.claude/plans/effervescent-exploring-whale.md`

## Scope

Extract `check_excess_mass` to a testable module-level function, store raw
Kneedle elbows in `BoundaryResult`, and write ~30 integration seam tests
covering all 10 handoff points in the boundary QC pipeline.

Execution order: extract function first, add fields second, write tests third.

Do NOT change detection logic, interior pipeline, or plot functions.

## Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check
- Use pyarrow (not pandas) for reading parquet in tests
- Test data: `tests/data/{name}_test_sample.parquet` + `{name}_test_metadata.json`

## Verification

```bash
python -m pytest tests/ -x -q
python -m pytest tests/test_boundary_seams.py -v
python -c "
from fitqc import run_boundary_qc, BoundaryConfig
import numpy as np
rng = np.random.default_rng(42)
x = np.concatenate([rng.uniform(0, 0.01, 500), rng.uniform(0, 10, 9500)])
config = BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')
result = run_boundary_qc(x, 0.0, 10.0, config)
assert result.t_lo_raw is not None
assert result.kneedle_elbows_lower is not None
print(f't_lo_raw={result.t_lo_raw}, t_lo_star={result.t_lo_star}')
print('PASS')
"
```
