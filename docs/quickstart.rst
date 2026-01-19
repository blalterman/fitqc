Quick Start Guide
=================

This guide provides a quick introduction to using ``fitqc`` for detecting optimizer stickiness.

Configuration
-------------

First, define the specification for your parameters:

.. code-block:: python

   from fitqc import QCSpec, InteriorConfig, BoundaryConfig

   # Required: Parameter specification
   spec = QCSpec(
       param_names=["alpha", "beta"],
       x0={"alpha": 1.0, "beta": 2.0},
       bounds={"alpha": (0.0, 10.0), "beta": (-5.0, 5.0)},
   )

   # Optional: Customize detection parameters
   interior_config = InteriorConfig(
       n_bins=100,      # Histogram bins
       n_eps=50,        # Epsilon grid points
   )

   boundary_config = BoundaryConfig(
       n_tols=41,       # Tolerance grid points
       tol_max=0.05,    # Maximum tolerance to check
   )

Core Functions
--------------

High-level API (recommended):

.. code-block:: python

   from fitqc import run_qc

   report, masks = run_qc(params, spec, interior_config, boundary_config)

Low-level API for more control:

.. code-block:: python

   from fitqc import run_interior_qc, run_boundary_qc

   interior_result = run_interior_qc(x, x0, L, U, config)
   boundary_result = run_boundary_qc(x, L, U, config)

Working with Results
--------------------

Interior result:

.. code-block:: python

   result.spike_detected    # bool: Was a spike detected?
   result.eps_star          # float: Detection threshold (None if not detected)
   result.spike_z_loc       # float: Location of spike in z-space

Boundary result:

.. code-block:: python

   result.lower_pileup_detected  # bool
   result.upper_pileup_detected  # bool
   result.t_lo_star              # float: Lower threshold
   result.t_hi_star              # float: Upper threshold

Masks:

.. code-block:: python

   masks["alpha"]  # bool array: True = good sample, False = stuck sample

Diagnostic Plots
----------------

Generate diagnostic visualizations:

.. code-block:: python

   from fitqc import plot_interior_diagnostics, plot_boundary_diagnostics, PlotConfig

   fig = plot_interior_diagnostics(interior_result, PlotConfig())
   fig = plot_boundary_diagnostics(boundary_result, PlotConfig())

Examples
--------

See ``examples/run_array_qc.py`` in the repository for a complete working example.
