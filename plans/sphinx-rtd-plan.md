# Sphinx + RTD Documentation Plan

## Summary
Create Sphinx documentation for fitqc hosted on Read the Docs.

## Analysis of Original Prompt

### Improvements Made

| Change | Rationale |
|--------|-----------|
| Removed role-playing preamble | Claude Code already knows its context |
| Added concrete file references | Grounds task in actual repo state |
| Made decisions explicit (rST, autodoc, pyproject `[docs]` extra) | Original "decide but use default" pattern was contradictory |
| Removed speculative import mitigation strategies | fitqc has no optional deps that would trigger issues |
| Added README.md as content source | Avoids duplicating 162 lines of existing quality content |
| Added single commit instruction | Cleaner for review |
| Added feature branch instruction | Prevents accidental main push |
| Kept RTD config details | RTD YAML is error-prone; explicit guidance helps |
| Kept extension list | Clear spec prevents ambiguity |

### Decisions

1. **Source format:** reStructuredText (repo has no markdown narrative docs)
2. **API generation:** autodoc + autosummary (standard, well-supported)
3. **Dependency location:** pyproject.toml `[docs]` extra (consistent with existing `[dev]` extra)
4. **Python version for RTD:** 3.13 (highest supported)
5. **Theme:** sphinx_rtd_theme (RTD standard)

## Expected Deliverables

```
docs/
├── conf.py
├── index.rst
├── installation.rst
├── quickstart.rst
├── api/
│   └── index.rst (autosummary toctree)
├── developer.rst
├── Makefile
└── make.bat
.readthedocs.yaml
pyproject.toml (add [docs] extra)
```

## Verification Checklist

- [ ] `pip install -e ".[docs]"` succeeds
- [ ] `python -m sphinx -b html docs docs/_build/html` succeeds
- [ ] `.readthedocs.yaml` exists and uses config v2
- [ ] API reference renders public modules/classes
- [ ] Landing page includes description, installation, quickstart
- [ ] Developer section documents: layout, tests, local docs build

## RTD Setup Steps (post-merge)

1. Go to readthedocs.io → Import a Project
2. Connect GitHub repo: blalterman/fitqc
3. RTD auto-detects `.readthedocs.yaml`
4. Trigger first build
5. Verify build succeeds
6. (Optional) Configure custom domain, PR builds, etc.
