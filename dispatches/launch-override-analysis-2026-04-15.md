Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

**Read:** `dispatches/dispatch-override-analysis-2026-04-15.md`

## Commits to Verify

The receiving session should confirm HEAD includes these before acting:

- `46d6cbd` feat(boundary): extract check_excess_mass, store raw elbows, add seam tests
- `7f8d7a7` fix(boundary): complete iterative Kneedle refinement (Fix 5 Part 2)

## Key Decisions

- DECIDED: Comparison must use `refine_transition=True` throughout.
  `refine_transition=False` changes the detection algorithm, not just
  the overrides.
- DECIDED: Judge correctness against empirical pileup fractions from raw
  data, not test metadata (circularity risk).
- DECIDED: Analysis-only. No production code changes.
- PROPOSED: Disable overrides via source-line excision
  (`inspect.getsource` + block removal by comment markers + `exec`).
  Validate this approach or choose a cleaner alternative.

## Scope

Write `analyze_overrides.py` at repo root. Run boundary QC on all 12 PPA12
datasets under 5 configurations:

1. `all_on` -- current behavior (M1 + M3 + M2 active)
2. `no_m1` -- M1 disabled
3. `no_m3` -- M3 disabled
4. `no_m2` -- M2 disabled
5. `all_off` -- all overrides disabled

For each dataset x config, record `t_lo_raw`, `t_lo_star`, `t_hi_raw`,
`t_hi_star`, `lower_pileup_detected`, `upper_pileup_detected`.

Compute empirical pileup fractions from raw data. Produce per-dataset trace,
per-override verdicts, and a summary comparison table.

Save report to `~/Documents/Obsidian-Vault/fitqc/reports/override-analysis-2026-04-15.md`.

## Operational Constraints

- Branch: `claude/fitqc-ppa12-validation-vwKdg`
- Pre-commit hooks: ruff linting + whole-repo format check
- Test data: `tests/data/{name}_test_sample.parquet` + `{name}_test_metadata.json`
- Parquet reading: pyarrow (`pq.read_table`), NOT pandas
- Config: `BoundaryConfig(use_quantile_analysis=True, refine_transition=True, grid_mode='progressive')`
- Override comment markers: `"# Mechanism 1 —"`, `"# Mechanism 3 —"`, `"# Mechanism 2 —"`

## Verification

```bash
# Prerequisites — expected: "Prerequisites OK"
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

# Analysis runs — expected: per-dataset traces + summary table
python analyze_overrides.py

# No source changes — expected: empty output
git diff --name-only src/

# Tests pass — expected: "N passed" with exit code 0
python -m pytest tests/ -x -q
```

Follow the handoff Resume Protocol to confirm state before acting.
