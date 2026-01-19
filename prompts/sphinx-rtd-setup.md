# Sphinx + Read the Docs Setup

## Context
- Repository: fitqc (Python package, src/ layout)
- Existing: README.md has installation, quickstart, API overview; pyproject.toml has `[dev]` extra
- Docstring style: NumPy (verify in src/fitqc/*.py)
- Python versions: 3.11, 3.12, 3.13

## Goal
Create Sphinx documentation that builds on Read the Docs.

## Requirements

### Must have
1. Sphinx builds locally without errors
2. `.readthedocs.yaml` (v2 config) at repo root
3. RTD installs package with docs extra reproducibly
4. API reference generated from docstrings (autodoc + autosummary)
5. Landing page with: description, installation, quickstart (source from README.md)
6. Developer section: project layout, running tests, building docs locally

### Configuration
- Theme: sphinx_rtd_theme
- Extensions: autodoc, autosummary, napoleon, viewcode, intersphinx
- Source format: reStructuredText
- Deps: pyproject.toml `[project.optional-dependencies.docs]` (consistent with existing `[dev]` extra)
- Python for RTD: 3.13

## Process
1. Inspect src/fitqc/ to confirm docstring style and public API
2. Add `[docs]` extra to pyproject.toml with sphinx, sphinx_rtd_theme, and any needed extensions
3. Create docs/ skeleton with sphinx-quickstart or equivalent
4. Configure conf.py with extensions and theme
5. Create API reference under docs/api/ using autosummary
6. Create landing page (index.rst) sourcing content from README
7. Create developer guide page
8. Add .readthedocs.yaml at repo root with:
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
9. Verify local build:
   ```bash
   pip install -e ".[docs]"
   python -m sphinx -b html docs docs/_build/html
   ```
10. Add RTD badge to README.md after the CI badge:
    ```markdown
    [![Documentation](https://readthedocs.org/projects/fitqc/badge/?version=latest)](https://fitqc.readthedocs.io/)
    ```
11. Commit to feature branch: `docs/sphinx-rtd-setup`

## Deliverables
- File tree of created/modified files
- Commands to build and preview locally
- RTD setup checklist (what to configure on readthedocs.io)

## Commit
Single commit: `docs: add Sphinx documentation with RTD configuration`
