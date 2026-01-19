# Sphinx + Read the Docs Setup

## Context
- src/ layout, NumPy docstrings, Python 3.11-3.13
- README.md has installation, quickstart, API overview to reuse
- pyproject.toml has existing `[dev]` extra

## Goal
Create Sphinx documentation that builds on Read the Docs.

## Requirements
1. Sphinx builds locally without errors
2. `.readthedocs.yaml` (v2 config) at repo root
3. RTD installs package with docs extra
4. API reference generated from docstrings (autodoc + autosummary)
5. Landing page: description, installation, quickstart (source from README.md)
6. Developer section: project layout, running tests, building docs locally

## Configuration
- Theme: sphinx_rtd_theme
- Extensions: autodoc, autosummary, napoleon, viewcode, intersphinx
- Source format: reStructuredText
- Deps: pyproject.toml `[project.optional-dependencies.docs]`
- Python for RTD: 3.13

## Process
1. Add `[docs]` extra to pyproject.toml with sphinx, sphinx_rtd_theme, and needed extensions
2. Create docs/ skeleton
3. Configure conf.py with extensions and theme
4. Create API reference under docs/api/ using autosummary
5. Create landing page (index.rst) sourcing content from README
6. Create developer guide page
7. Add .readthedocs.yaml at repo root:
   ```yaml
   version: 2
   build:
     os: ubuntu-24.04
     tools:
       python: "3.13"
   sphinx:
     configuration: docs/conf.py
   python:
     install:
       - method: pip
         path: .
         extra_requirements:
           - docs
   ```
8. Add RTD badge to README.md after the CI badge:
   ```markdown
   [![Documentation](https://readthedocs.org/projects/fitqc/badge/?version=latest)](https://fitqc.readthedocs.io/)
   ```
9. Verify local build:
   ```bash
   pip install -e ".[docs]"
   python -m sphinx -b html docs docs/_build/html
   ```
10. Commit to feature branch `docs/sphinx-rtd-setup`:
    ```
    docs: add Sphinx documentation with RTD configuration
    ```

## Output
After completing, report:
1. File tree of created/modified files
2. Build command and result
3. The following manual steps for the user:

---
**Next Steps (Manual - after merging PR):**
1. Go to readthedocs.org → Import a Project
2. Connect GitHub repo: blalterman/fitqc
3. RTD auto-detects .readthedocs.yaml
4. Trigger first build
5. Verify build succeeds at https://fitqc.readthedocs.io/
---
