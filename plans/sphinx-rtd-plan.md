# Sphinx + RTD Documentation Plan

Human reference document for the Sphinx/RTD setup. AI executes from `prompts/sphinx-rtd-setup.md`.

## Decisions & Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source format | reStructuredText | Repo has no markdown narrative docs; rST is Sphinx native |
| API generation | autodoc + autosummary | Standard, well-supported, generates from docstrings |
| Dependency location | pyproject.toml `[docs]` extra | Consistent with existing `[dev]` extra; single source of truth |
| Python for RTD | 3.13 | Highest supported version |
| Theme | sphinx_rtd_theme | RTD standard, well-maintained |
| Landing page content | Source from README.md | Avoids duplicating 162 lines of existing content |

## Expected Output

```
docs/
├── conf.py
├── index.rst           # Landing page (description, install, quickstart)
├── api/
│   └── index.rst       # autosummary toctree
├── developer.rst       # Project layout, tests, building docs
├── Makefile
└── make.bat
.readthedocs.yaml       # RTD v2 config
pyproject.toml          # (modified: add [docs] extra)
README.md               # (modified: add RTD badge)
```

## PR Review Checklist

- [ ] `pip install -e ".[docs]"` succeeds
- [ ] `python -m sphinx -b html docs docs/_build/html` succeeds without errors
- [ ] `.readthedocs.yaml` exists and uses config version 2
- [ ] API reference renders public modules/classes (not private/internal)
- [ ] Landing page includes description, installation, quickstart
- [ ] Developer section documents: project layout, running tests, building docs locally
- [ ] RTD badge added to README.md
- [ ] Single commit with conventional format
