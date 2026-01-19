"""fitqc: Fit QC diagnostics for detecting optimizer stickiness.

This package provides tools to detect two types of optimizer stickiness in fitted parameters:
1. Boundary stickiness - samples stuck near parameter bounds (L/U)
2. Initial-guess stickiness - samples stuck near x0 (optimizer fallback)
"""

__version__ = "0.1.0"

# Public API will be exported here after implementation
__all__: list[str] = []
