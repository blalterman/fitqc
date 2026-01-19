fitqc Documentation
===================

Fit QC diagnostics for detecting optimizer stickiness in fitted parameters.

Overview
--------

When fitting models to data using bootstrap, MCMC, or Monte Carlo methods, optimizers can get "stuck" in two ways:

1. **Boundary stickiness** -- Fitted values pile up at parameter bounds (L or U)
2. **Initial-guess stickiness** -- Fitted values cluster at the initial guess (x0)

``fitqc`` provides automated detection of these issues across multiple parameters, with diagnostic plots and JSON-serializable reports.

Installation
------------

.. code-block:: bash

   pip install fitqc

For development:

.. code-block:: bash

   pip install -e ".[dev]"

Quick Start
-----------

.. code-block:: python

   from fitqc import run_qc, QCSpec

   # Your fitted parameter samples (e.g., from 10,000 bootstrap fits)
   params = {
       "alpha": alpha_samples,  # shape (10000,)
       "beta": beta_samples,    # shape (10000,)
   }

   # Define the parameter specification
   spec = QCSpec(
       param_names=["alpha", "beta"],
       x0={"alpha": 1.0, "beta": 2.0},           # Initial guesses
       bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},  # Bounds
   )

   # Run QC
   report, masks = run_qc(params, spec)

   # Check results
   for name in spec.param_names:
       if report.interior_results[name].spike_detected:
           print(f"{name}: x0 stickiness detected!")
       if report.boundary_results[name].lower_pileup_detected:
           print(f"{name}: lower bound pileup detected!")

   # Filter to good samples only
   combined_mask = masks["alpha"] & masks["beta"]
   clean_alpha = params["alpha"][combined_mask]
   clean_beta = params["beta"][combined_mask]

   # Save report to JSON
   with open("qc_report.json", "w") as f:
       f.write(report.to_json(indent=2))

How It Works
------------

Interior QC (x0 Stickiness)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Detects samples clustered at the initial guess using:

1. Normalize distances from x0: ``z = |x - x0| / (U - L)``
2. Build histogram of z-values
3. Detect narrow spike at z ≈ 0 using ``scipy.signal.find_peaks``
4. Select detection threshold (eps*) via elbow detection

Boundary QC (Pileup)
~~~~~~~~~~~~~~~~~~~~

Detects samples clustered at bounds using:

1. Normalize positions: ``u = (x - L) / (U - L)``
2. Compute cumulative mass near boundaries
3. Detect excess mass via elbow detection
4. Independent thresholds for lower (t_lo*) and upper (t_hi*)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   quickstart
   developer

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   api/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
