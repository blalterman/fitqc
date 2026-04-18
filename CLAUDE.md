# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development (conda preferred per user rule; pip works)
pip install -e ".[dev]"
pre-commit install

# Run full test suite
python -m pytest tests/ -q

# Run a single test file or test
python -m pytest tests/test_boundary.py -q
python -m pytest tests/test_boundary.py::TestBoundaryQC::test_delta_pileup_detection -q

# Lint + format (ruff is wired through pre-commit)
ruff check src/ tests/
ruff format src/ tests/

# Build sphinx docs
cd docs && make html
```

Pytest config lives in `pyproject.toml` (`[tool.pytest.ini_options]`): verbose by default, collects from `tests/`. Pre-commit runs `ruff` (with `--fix`), `ruff-format`, and a whole-repo `ruff-format-check-all` gate.

## Architecture

### Two detection axes, one pipeline

`fitqc` detects optimizer stickiness in fitted parameter samples. Two axes, two modules:

- `src/fitqc/boundary.py` — boundary pileup (samples clustered near the lower `L` or upper `U` bound). Entry: `run_boundary_qc(x, L, U, config) -> BoundaryResult`.
- `src/fitqc/interior.py` — x0 stickiness (samples clustered at the optimizer's initial guess). Entry: `run_interior_qc(x, x0, L, U, config) -> InteriorResult`.

Both detectors share a common coordinate pattern: transform to a normalized space, compute a mass curve (cumulative fraction within a tolerance), and find the elbow via `src/fitqc/selection.py::select_elbow` (a thin wrapper around `kneed.KneeLocator`). Understanding this shared pattern unlocks both modules — they are not otherwise coupled.

High-level orchestrator in `src/fitqc/report.py::run_qc` wires a parameter spec (`QCSpec`: `param_names`, `x0`, `bounds`) through both detectors, emits a JSON-serializable `QCReport`, and returns keep-masks per parameter.

### Module map (behavior, not structure)

- `config.py` — `QCSpec` (user-facing) + `BoundaryConfig`, `InteriorConfig`, `PlotConfig`, `PrecisionConfig` dataclasses. `BoundaryConfig.grid_mode` governs the tolerance-grid shape (`uniform`, `progressive`, `progressive_log`); `quantile_grid` is the eps grid used by the quantile-analysis path.
- `selection.py` — the kneedle wrapper. **Every `t_star` / `eps_star` in the codebase comes from this function.** Changing it changes every detection output. Both `boundary.py` and `interior.py` call `select_elbow`; the C3 re-scope dispatch proposes replacing kneedle with a monotonic-spline + analytic second-derivative method.
- `sortedops.py`, `_quantile_utils.py`, `precision.py` — numerical primitives shared by boundary detection. Pure functions.
- `stickiness.py` — legacy/shared stickiness utilities.
- `synth.py` — synthetic data generators used by tests.
- `plot.py` — diagnostic plotting (2908 LOC; most of the UI surface).

### Filter terminology gotcha

The visualization filters in `plot.py` use names that mismatch scientific intuition (this is documented in `README.md` and `COMPLETE_FILTER_TAXONOMY.md` — always consult when touching filter-comparison plots):

- **"Boundary filter"** removes *out-of-bounds* samples (`x < L` or `x > U`), **not** boundary-sticky samples. On data where all `x ∈ [L, U]`, Panel 2 of filter-comparison plots is identical to Panel 1.
- **"Interior filter"** removes *x0-sticky* samples (near the initial guess), **not** samples in the interior region.
- **"Combined filter"** is the only filter that removes boundary-sticky samples, using thresholds detected by `run_boundary_qc`.

Names are retained to match the module names (`boundary.py` / `interior.py`), not to match what gets filtered.

## Calibration workflow

This project maintains two separate calibration harnesses, one per dataset:

- `analyze_overrides.py` — drives detection on the 10k parquet subset in `tests/data/` with CSV ground truth at `dispatches/ground_truth_validation.csv`. Scoped to unit tests and public-software deployment fixtures.
- `analyze_swefc_calibration.py` — drives detection on the full `swefc.h5` dataset (gitignored, lives at repo root) with JSON ground truth at `dispatches/ground_truth_swefc.json`. This is the authoritative calibration target.

**Do not add a dataset-switching flag or env-var to `analyze_overrides.py`.** When a new calibration dataset enters scope, create a new dataset-specific harness that imports from `src/fitqc/`; the existing subset harness stays untouched so the test suite keeps exercising it.

### Ground-truth JSON schema

`dispatches/ground_truth_swefc.json` distinguishes two fields that are easy to conflate:

- `x0` — the optimizer's initial guess (pipeline metadata, copied from the CSV). Fixed fact about the fitter.
- `interior_locations` — empirical list of x-values where visual inspection observed a spike. Drives detection.

They usually coincide, but exceptions exist: `e.w.a` has `x0=0` and `interior_locations=[0, -25]` (a second, empirical spike at −25); `ab.a` has `x0=0` and `interior_locations=[1]` (the empirical spike is at `x=1`, while `x=0` is lower-boundary stickiness overlapping `L=0`). The harness iterates `interior_locations`, not `x0`.

### Dispatches and handoffs

`dispatches/` holds cross-session work orders (`dispatch-*.md`) paired with launch prompts (`launch-*.md`). Launch prompts follow the plan-first meta-instruction: the receiving session produces a plan-draft from the launch prompt *before* reading the dispatch, then revises against it. This prevents anchoring on the dispatch's specific framing.

Parallel Claude sessions on this repo **must** run in their own `git worktree` — never spin up a second session in the same working directory. The only safe cross-worktree operation is `git merge --ff-only` after the worktree has rebased. Worktrees at sibling paths (e.g., `../fitqc-<role>`) work when unsandboxed; nested at `./worktrees/<role>/` also works.

## Data and gitignore

- `swefc.h5` at repo root is the full calibration dataset; gitignored, never committed.
- `*.png` and `*.pdf` are gitignored — diagnostic figures are regenerated per run.
- `tests/data/*_full.parquet` is gitignored; `*_test_sample.parquet` fixtures are tracked.

## Known constraints

- `kneed>=0.8` is a hard dependency; all elbow detection flows through `selection.py`. The C3 re-scope proposes replacing it behind a `BoundaryConfig.detector_mode` flag rather than removing it outright.
- M1 spread-pileup override was removed in commit `fb4ad25`; `analyze_overrides.py` may reference it in comments or marker-based logic. Verify empirically before assuming the override is live.
- Override mechanisms M2 (delta-function) and M3 (broad-pileup) are documented by seam tests in `tests/test_boundary_seams_overrides.py` pending a focused review.
