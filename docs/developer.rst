Developer Guide
===============

This guide covers the development setup and workflow for contributing to ``fitqc``.

Project Layout
--------------

::

   fitqc/
   ├── src/
   │   └── fitqc/
   │       ├── __init__.py      # Package exports
   │       ├── config.py        # Configuration dataclasses
   │       ├── interior.py      # Interior QC (x0 stickiness)
   │       ├── boundary.py      # Boundary QC (pileup)
   │       ├── report.py        # High-level API, JSON serialization
   │       ├── plot.py          # Diagnostic plotting
   │       ├── synth.py         # Synthetic data generators
   │       ├── precision.py     # Floating-point helpers
   │       ├── selection.py     # Threshold selection
   │       └── sortedops.py     # Sorted array operations
   ├── tests/                   # Test suite
   ├── examples/                # Example scripts
   ├── docs/                    # Sphinx documentation
   ├── pyproject.toml           # Project configuration
   └── README.md

Development Setup
-----------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/blalterman/fitqc.git
   cd fitqc
   pip install -e ".[dev]"

Install pre-commit hooks:

.. code-block:: bash

   pre-commit install

Running Tests
-------------

Run the test suite with pytest:

.. code-block:: bash

   pytest

Run with coverage:

.. code-block:: bash

   pytest --cov=fitqc

Code Style
----------

This project uses `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting.

Check code style:

.. code-block:: bash

   ruff check src tests
   ruff format --check src tests

Auto-fix issues:

.. code-block:: bash

   ruff check --fix src tests
   ruff format src tests

Building Documentation
----------------------

Install documentation dependencies:

.. code-block:: bash

   pip install -e ".[docs]"

Build HTML documentation:

.. code-block:: bash

   python -m sphinx -b html docs docs/_build/html

View locally:

.. code-block:: bash

   python -m http.server -d docs/_build/html 8000

Then open http://localhost:8000 in your browser.

Requirements
------------

- Python >= 3.11
- NumPy >= 1.24
- SciPy >= 1.10
- Matplotlib >= 3.6
- kneed >= 0.8
