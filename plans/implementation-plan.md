# fitqc Implementation Plan

## Executive Summary

Create a standalone Python package (`fitqc`) implementing fit QC diagnostics for:
1. **Boundary stickiness** — detecting samples stuck near parameter bounds (L/U)
2. **Initial-guess stickiness** — detecting samples stuck near x0 (optimizer fallback)

**Repository:** https://github.com/blalterman/fitqc (private)

---

## Final Decision Matrix

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python version | `>=3.13` | Fresh package, mature ecosystem, no legacy users |
| License | BSD-3-Clause | Scientific Python convention, endorsement protection |
| Layout | `src/` | PEP 621 best practice |
| Tooling | ruff + pytest + pre-commit | Modern standard |
| Data interface | NumPy arrays only | Minimal deps, clear separation |
| Elbow detection | `kneed` package | Established library, published algorithm |
| Spike detection | `scipy.signal.find_peaks` | Required by prompt, robust |
| JSON serialization | `dataclasses.asdict()` + `NumpyEncoder` | No extra deps |
| Machine epsilon | `np.finfo(dtype).eps` | Never hardcode; use NumPy introspection |

**Dependencies:**
```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.6",
    "kneed>=0.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1",
    "pre-commit>=3.0",
]
```

---

## Repository Structure

```
fitqc/
├── pyproject.toml
├── README.md
├── .pre-commit-config.yaml
├── .gitignore
├── src/fitqc/
│   ├── __init__.py
│   ├── config.py          # Dataclass configs
│   ├── precision.py       # ULP, dtype helpers
│   ├── sortedops.py       # Sorted array operations
│   ├── selection.py       # Elbow detection (wraps kneed)
│   ├── interior.py        # Interior QC (x0 stickiness)
│   ├── boundary.py        # Boundary QC (L/U stickiness)
│   ├── report.py          # Result dataclasses, JSON
│   ├── synth.py           # Synthetic data generators
│   └── plot.py            # Plotting functions
├── tests/
│   ├── test_precision.py
│   ├── test_sortedops.py
│   ├── test_selection.py
│   ├── test_interior.py
│   ├── test_boundary.py
│   ├── test_spike_detection.py
│   ├── test_plot_smoke.py
│   ├── test_smoke_pipeline.py
│   └── test_integration_end2end.py
├── examples/
│   └── run_array_qc.py
└── plans/
    ├── implementation-plan.md
    └── test-plan.md
```

---

## Module Responsibilities

| Module | Responsibility | Dependencies |
|--------|----------------|--------------|
| `config.py` | Dataclass definitions only, no logic | — |
| `precision.py` | `effective_dtype()`, `ulp_at()`, `quantize_scalar()` | numpy |
| `sortedops.py` | `tail_mass()`, `quantile_by_index()`, `slice_by_range()` | numpy |
| `selection.py` | `select_elbow()` wrapping kneed | kneed, sortedops |
| `interior.py` | Compute z → histogram → find_peaks → select eps* | scipy, sortedops, selection |
| `boundary.py` | Compute u → tail curves → select t_lo*, t_hi* | sortedops, selection |
| `report.py` | Result dataclasses, `to_dict()`, `to_json()` | config |
| `synth.py` | Synthetic data generators with artifact injection | numpy |
| `plot.py` | All plotting functions, return Figure | matplotlib |

---

## Parallel Execution Strategy

Use background/parallel agents for ~40% time reduction.

```
Phase 1: Scaffold (SEQUENTIAL - foundation)
├─ 1.1 pyproject.toml, __init__.py, .gitignore
├─ 1.2 .pre-commit-config.yaml
└─ 1.3 config.py (all dataclasses)
[Commit after each, verify install]

Phase 2: Core Modules (PARALLEL - 3 agents)
├─ Agent A: test_precision.py → precision.py
├─ Agent B: test_sortedops.py → sortedops.py
└─ Agent C: test_selection.py → selection.py
[Wait for all, then commit each]

Phase 3: Synthetic Data (SEQUENTIAL - needed for algorithm tests)
└─ synth.py
[Commit]

Phase 4: Algorithm Modules (PARALLEL - 2 agents)
├─ Agent A: test_interior.py → interior.py + test_spike_detection.py
└─ Agent B: test_boundary.py → boundary.py
[Wait for all, then commit each]

Phase 5: Reporting & Plotting (PARALLEL - 2 agents)
├─ Agent A: report.py
└─ Agent B: test_plot_smoke.py → plot.py
[Wait for all, then commit each]

Phase 6: Integration (SEQUENTIAL - depends on everything)
├─ test_integration_end2end.py
├─ test_smoke_pipeline.py
├─ examples/run_array_qc.py
└─ README.md
[Commit after each]
```

---

## Atomic Commit Plan

### Phase 1: Scaffold
| # | Commit Message | Files |
|---|----------------|-------|
| 1.1 | `chore: initial package scaffold` | pyproject.toml, src/fitqc/__init__.py, .gitignore |
| 1.2 | `chore: add pre-commit and ruff config` | .pre-commit-config.yaml |
| 1.3 | `chore: add config dataclasses` | src/fitqc/config.py |

### Phase 2: Core Modules (Test-First, Parallel)
| # | Commit Message | Files |
|---|----------------|-------|
| 2.1 | `test(precision): add tests for ULP and dtype helpers` | tests/test_precision.py |
| 2.2 | `feat(precision): implement ULP and dtype helpers` | src/fitqc/precision.py |
| 2.3 | `test(sortedops): add tests for sorted array ops` | tests/test_sortedops.py |
| 2.4 | `feat(sortedops): implement sorted array ops` | src/fitqc/sortedops.py |
| 2.5 | `test(selection): add tests for elbow detection` | tests/test_selection.py |
| 2.6 | `feat(selection): implement elbow detection with kneed` | src/fitqc/selection.py |

### Phase 3: Algorithm Modules (Test-First, Parallel)
| # | Commit Message | Files |
|---|----------------|-------|
| 3.1 | `feat(synth): add synthetic data generators` | src/fitqc/synth.py |
| 3.2 | `test(interior): add tests for interior QC` | tests/test_interior.py |
| 3.3 | `feat(interior): implement interior QC` | src/fitqc/interior.py |
| 3.4 | `test(spike): add spike detection tests` | tests/test_spike_detection.py |
| 3.5 | `test(boundary): add tests for boundary QC` | tests/test_boundary.py |
| 3.6 | `feat(boundary): implement boundary QC` | src/fitqc/boundary.py |

### Phase 4: Reporting & Plotting (Test-First, Parallel)
| # | Commit Message | Files |
|---|----------------|-------|
| 4.1 | `feat(report): add result dataclasses and JSON serialization` | src/fitqc/report.py |
| 4.2 | `test(plot): add plot smoke tests` | tests/test_plot_smoke.py |
| 4.3 | `feat(plot): implement plotting functions` | src/fitqc/plot.py |

### Phase 5: Integration
| # | Commit Message | Files |
|---|----------------|-------|
| 5.1 | `test(integration): add end-to-end pipeline test` | tests/test_integration_end2end.py |
| 5.2 | `test(smoke): add multi-distribution smoke tests` | tests/test_smoke_pipeline.py |
| 5.3 | `feat(api): finalize public API exports` | src/fitqc/__init__.py |
| 5.4 | `docs: add example script` | examples/run_array_qc.py |

### Phase 6: Documentation
| # | Commit Message | Files |
|---|----------------|-------|
| 6.1 | `docs: add README with quickstart and API overview` | README.md |

---

## Verification Criteria (Definition of Done)

```bash
pip install -e ".[dev]"      # Installation works
ruff check .                  # Linting passes
ruff format --check .         # Formatting passes
pytest -q                     # All tests pass
python examples/run_array_qc.py  # Example produces output
pre-commit run --all-files    # Hooks pass
```

---

## Public API Summary

### Configuration Dataclasses
```python
@dataclass
class PrecisionConfig:
    precision_mode: Literal["auto", "float32", "float64"] = "auto"
    compare_mode: Literal["quantize_to_storage", "analysis_dtype"] = "quantize_to_storage"

@dataclass
class InteriorConfig:
    eps_log10_min: float = -12
    eps_log10_max: float = -3
    n_eps: int = 50
    # ... spike detection params

@dataclass
class BoundaryConfig:
    tol_min: float = 0.0
    tol_max: float = 0.05
    n_tols: int = 41
    # ... quantile grid params

@dataclass
class PlotConfig:
    cmap: str = "viridis"
    dpi: int = 150
    include_log_abs_panel: bool = True

@dataclass
class QCSpec:
    param_names: list[str]
    x0: dict[str, float]
    bounds: dict[str, tuple[float, float]]
```

### Core Functions
```python
def compute_u(x: np.ndarray, L: float, U: float) -> np.ndarray
def compute_z(x: np.ndarray, x0: float, L: float, U: float) -> np.ndarray
def run_interior_qc(...) -> InteriorResult
def run_boundary_qc(...) -> BoundaryResult
def run_qc(...) -> tuple[QCReport, dict[str, np.ndarray]]
```

---

## Test Plan Reference

See: [test-plan.md](./test-plan.md)
