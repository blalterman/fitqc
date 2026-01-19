# fitqc Startup Prompt

Use this prompt to resume work in a new Claude Code session.

---

## Context

You are implementing the `fitqc` Python package for fit QC diagnostics.

**Repository:** https://github.com/blalterman/fitqc (private)

**Key documents:**
- `plans/implementation-plan.md` — Execution plan with parallel phases
- `plans/test-plan.md` — Detailed test specifications with justifications

---

## Quick Summary

**Purpose:** Detect two types of optimizer stickiness in fitted parameters:
1. **Boundary stickiness** — samples stuck near parameter bounds (L/U)
2. **Initial-guess stickiness** — samples stuck near x0 (optimizer fallback)

**Key decisions:**
- Python >=3.13
- BSD-3-Clause license
- NumPy arrays only (no pandas)
- Dependencies: numpy>=1.24, scipy>=1.10, matplotlib>=3.6, kneed>=0.8
- Use `np.finfo(dtype).eps` for machine epsilon (never hardcode)
- Elbow detection via `kneed` package
- Spike detection via `scipy.signal.find_peaks`
- Test-first development with parallel agent execution

---

## Resume Instructions

1. **Read the plans:**
   ```
   Read plans/implementation-plan.md
   Read plans/test-plan.md
   ```

2. **Check current state:**
   ```bash
   git log --oneline -10
   git status
   pytest -q
   ```

3. **Resume from last completed phase**

---

## Parallel Execution Strategy

Use background agents for independent modules:

```
Phase 2 (PARALLEL):
├─ Agent A: test_precision.py → precision.py
├─ Agent B: test_sortedops.py → sortedops.py
└─ Agent C: test_selection.py → selection.py

Phase 4 (PARALLEL):
├─ Agent A: test_interior.py → interior.py
└─ Agent B: test_boundary.py → boundary.py
```

Launch with:
```python
Task(subagent_type="general-purpose", prompt="...", run_in_background=True)
```

---

## Definition of Done

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest -q
python examples/run_array_qc.py
pre-commit run --all-files
```

---

## Module Dependencies

```
config.py (no deps)
    ↓
precision.py, sortedops.py (parallel, only numpy)
    ↓
selection.py (depends on kneed)
    ↓
synth.py (only numpy)
    ↓
interior.py, boundary.py (parallel, depend on sortedops, selection, scipy)
    ↓
report.py (depends on config)
    ↓
plot.py (depends on matplotlib)
    ↓
integration tests (depend on everything)
```

---

## Key Test Requirements

- **Never hardcode machine epsilon** — use `np.finfo(dtype).eps`
- **No trivial tests** — verify numerical values, shapes, types
- **Critical edge case:** Signed log-normal with x0≈0 must NOT trigger false spike
- **Spike detection:** Must use prominence + width + location criteria
- **Plots:** Must return Figure, never call plt.show()

---

## Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, test, chore, docs, refactor
Scope: precision, sortedops, selection, interior, boundary, report, plot, synth

Example: feat(precision): implement ULP and dtype helpers
```

Always include:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
