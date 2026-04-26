Do *NOT* execute the instructions below. First, give me a /plan-draft for HOW
you will execute them. Verify the prompt's prerequisites before execution -- do
not rewrite scope or intent, they were reviewed in the prior session. Do not
read feedback or dispatch documents yet -- partial reads will distort context
before we have a plan. Once I approve your plan, then execute.

---

# Dispatch: Review Boundary Override Mechanisms (M1/M2/M3)

**Generated:** 2026-04-15
**Branch:** `claude/fitqc-ppa12-validation-vwKdg`
**Work type:** analysis

## Scope

Determine whether the M1, M2, and M3 override mechanisms in `run_boundary_qc`
are helping or harming boundary detection on real data. These overrides were
added as special-case handlers for edge cases (spread pileups, delta functions,
broad pileups) but may be silently transforming correct detection values into
incorrect ones.

Deliverables:

1. **Comparison table** for all 12 PPA12 datasets: run boundary QC with all
   overrides enabled (current behavior) vs each override individually disabled
   vs all overrides disabled. Record `t_lo_raw`, `t_lo_star`, `t_hi_raw`,
   `t_hi_star`, and detection booleans for each configuration.

2. **Per-override verdict**: for each of M1, M3, and M2, state whether it
   improved, degraded, or had no effect on detection for each dataset.

3. **Recommendation**: which overrides to keep, simplify, or remove, with
   specific evidence from the comparison table.

Do NOT change production code. This dispatch is analysis-only.

## Motivation

During PPA12 calibration, boundary detection produced unexpected results.
The pipeline has 3 override mechanisms that silently transform raw elbow
values between detection and validation. Seam tests now document their
current behavior but cannot tell us whether that behavior is correct --
only a comparison against real data can.

The overrides are:

- **M1 (spread-pileup propagation)**: When `t_raw < pileup_threshold` and
  `quantile_elbow > pileup_threshold` and `mass(0) < 1e-10`, replaces
  `t_raw` with `max(q_ref/2, pileup_threshold)`. Intended to handle
  diffuse pileups where the tolerance elbow underestimates pileup width.

- **M3 (broad-pileup fallback)**: When `mass_ratio < 2*excess_ratio`,
  searches backward through the mass curve for the largest tolerance still
  showing excess. Replaces `t_raw` if the broad value exceeds 3x the
  original. Intended to catch wide pileups that quantile analysis
  underestimates.

- **M2 (delta-function propagation)**: After `check_excess_mass`, when
  `t_raw < 1e-10` and `mass(0) > 2*pileup_threshold`, replaces `t_star`
  with `mass(0)`. Intended to set the cut tolerance to the exact pileup
  fraction for delta-function pileups.

M1 and M3 modify `t_lo_raw` before validation. M2 modifies `t_lo_star` after
validation. All three only fire with `refine_transition=True`.

## Read First

1. `src/fitqc/boundary.py:682-739` -- M1 and M3 override blocks (modify `t_lo_raw`)
2. `src/fitqc/boundary.py:857-906` -- M2 override block (modifies `t_lo_star`)
3. `src/fitqc/boundary.py:444-513` -- `_check_excess_mass` (the validation step between raw and star)
4. `tests/test_boundary_seams_overrides.py` -- seam tests documenting current override behavior
5. `tests/conftest.py:338-360` -- `all_ppa12_test_cases` fixture (loads all 12 datasets)

## Acceptance Criteria

- [ ] Comparison table covers all 12 datasets x 5 configurations (all overrides on, M1-off, M3-off, M2-off, all overrides off)
- [ ] Each cell has `t_lo_raw`, `t_lo_star`, `t_hi_raw`, `t_hi_star`, `lower_detected`, `upper_detected`
- [ ] Per-override verdict for each dataset (improved / degraded / no effect)
- [ ] Recommendation with specific evidence citing dataset names and value comparisons
- [ ] No production code changes

## Anti-Patterns

- Do NOT modify `boundary.py` or any source code -- this is analysis-only
- Do NOT assume overrides are wrong; some may be genuinely needed for edge cases
- Do NOT evaluate detection correctness by "does it look right"; compare against
  known pileup fractions from the test metadata (`fitqc_test` field)
- Do NOT run with `refine_transition=False` as a baseline -- the overrides only
  fire with refinement enabled, so the comparison must use refinement

## Verification

```bash
# The analysis script should produce a table and recommendation
# Verify it runs without error on all 12 datasets:
python -m pytest tests/conftest.py --collect-only -q | grep "all_ppa12"

# Verify raw elbows are available (prerequisite from prior session):
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
```
