"""Shared pytest fixtures for fitqc tests.

This module provides fixtures for test data, including real-world validation
data from the Wind/SWE PPA12 dataset.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


# =============================================================================
# Common fixtures
# =============================================================================


@pytest.fixture
def rng():
    """Seeded random number generator for reproducibility."""
    return np.random.default_rng(42)


# =============================================================================
# Real-world test data fixtures (Wind/SWE PPA12)
# =============================================================================


@pytest.fixture
def a_he_test_data_path() -> Path:
    """Path to A_He test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def a_he_metadata(a_he_test_data_path) -> dict:
    """Load A_He test metadata.

    Returns:
        Dictionary with keys:
        - name: Parameter name ("A_He")
        - x0: Initial guess (0.0)
        - L: Lower bound (0.0)
        - U: Upper bound (25.0)
        - units: Parameter units ("%")
        - n_samples: Number of samples in test file
        - fitqc_test: Expected detection results
    """
    meta_path = a_he_test_data_path / "A_He_test_metadata.json"
    with open(meta_path) as f:
        return json.load(f)


@pytest.fixture
def a_he_values(a_he_test_data_path) -> np.ndarray:
    """Load A_He test values.

    Returns:
        Array of 100,000 A_He values from Wind/SWE PPA12 dataset.
        This is a uniform random subsample that preserves the distribution
        characteristics of the full 7.5M sample dataset.

    Distribution characteristics:
        - ~1.6% of values at lower boundary (L=0.0)
        - ~0.4% of values at upper boundary (U=25.0)
        - Mean ~3.55, Std ~2.86
    """
    data_path = a_he_test_data_path / "A_He_test_sample.parquet"
    return pd.read_parquet(data_path)["values"].values


@pytest.fixture
def a_he_test_case(a_he_values, a_he_metadata) -> dict:
    """Complete A_He test case with values, bounds, and expected results.

    This fixture provides everything needed to test boundary detection on
    real-world data that exhibits known stickiness at the lower boundary.

    Returns:
        Dictionary with:
        - values: np.ndarray of parameter values
        - L: Lower bound (0.0)
        - U: Upper bound (25.0)
        - x0: Initial guess (0.0)
        - expected: Dictionary of expected detection results
    """
    return {
        "values": a_he_values,
        "L": a_he_metadata["L"],
        "U": a_he_metadata["U"],
        "x0": a_he_metadata["x0"],
        "expected": a_he_metadata["fitqc_test"],
    }
