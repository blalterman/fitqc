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


# =============================================================================
# Helper function for loading test data
# =============================================================================


def _load_test_case(data_dir: Path, name: str) -> dict:
    """Load a test case by parameter name.

    Args:
        data_dir: Path to tests/data directory
        name: Parameter name (e.g., "A_He", "e_dv_pp")

    Returns:
        Dictionary with values, L, U, x0, expected
    """
    values = pd.read_parquet(data_dir / f"{name}_test_sample.parquet")["values"].values
    with open(data_dir / f"{name}_test_metadata.json") as f:
        meta = json.load(f)
    return {
        "values": values,
        "L": meta["L"],
        "U": meta["U"],
        "x0": meta["x0"],
        "expected": meta["fitqc_test"],
    }


# =============================================================================
# e_dv_pp: Proton-proton drift velocity perturbation
# Exhibits BOTH lower and upper boundary stickiness (~12% at L, ~4% at U)
# =============================================================================


@pytest.fixture
def e_dv_pp_test_case() -> dict:
    """Test case for e_dv_pp parameter.

    Distribution characteristics:
        - ~11.7% at lower boundary (L=-75.0)
        - ~4.1% at upper boundary (U=75.0)
        - ~1.6% at x0=0.0

    This parameter exhibits strong bilateral boundary stickiness,
    making it ideal for testing detection at both boundaries.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "e_dv_pp")


# =============================================================================
# e_dv_ap: Alpha-proton drift velocity perturbation
# Exhibits boundary stickiness at both bounds
# =============================================================================


@pytest.fixture
def e_dv_ap_test_case() -> dict:
    """Test case for e_dv_ap parameter.

    Distribution characteristics:
        - ~0.6% at lower boundary (L=-150.0)
        - ~1.2% at upper boundary (U=150.0)
        - ~1.6% at x0=0.0

    This parameter exhibits moderate boundary stickiness at both bounds.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "e_dv_ap")


# =============================================================================
# np1: Proton core density (moment-based, no fixed x0)
# Minimal boundary stickiness - useful as negative control
# =============================================================================


@pytest.fixture
def np1_test_case() -> dict:
    """Test case for np1 parameter (1M sample for adequate boundary coverage).

    Distribution characteristics:
        - ~0% at lower boundary (L=0.01)
        - ~0.005% at upper boundary (U=100.0)
        - No fixed x0 (moment-based)

    This parameter has minimal boundary stickiness and serves as a
    negative control - detection should return False for both boundaries.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "np1")


# =============================================================================
# Velocity components (moment-based x0)
# =============================================================================


@pytest.fixture
def vx_test_case() -> dict:
    """Test case for vx (x-velocity toward Sun).

    Distribution characteristics:
        - ~0.007% at lower boundary (L=-1200)
        - ~0.30% at upper boundary (U=-200)
        - Moment-based x0 (varies per sample)

    Negative control for boundary stickiness.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "vx")


@pytest.fixture
def vy_test_case() -> dict:
    """Test case for vy (y-velocity).

    Distribution characteristics:
        - ~0.014% at lower boundary (L=-200)
        - ~0.042% at upper boundary (U=200)
        - Moment-based x0 (varies per sample)

    CRITICAL NOTE: Small shoulders observed around 0 in tolerance histograms.
    These may be initial guesses or moment analysis artifacts. Testing whether
    our methods can detect these subtle spikes. May require interior detection
    methods beyond tolerance histograms.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "vy")


@pytest.fixture
def vz_test_case() -> dict:
    """Test case for vz (z-velocity perpendicular to ecliptic).

    Distribution characteristics:
        - ~0.048% at lower boundary (L=-200)
        - ~0.034% at upper boundary (U=200)
        - Moment-based x0 (varies per sample)

    Negative control for boundary stickiness.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "vz")


# =============================================================================
# Thermal speed parameters
# =============================================================================


@pytest.fixture
def w_const_test_case() -> dict:
    """Test case for w_const (thermal speed).

    Distribution characteristics:
        - ~0.032% at lower boundary (L=5.0)
        - ~0.73% at upper boundary (U=150.0) - UPPER STICKINESS
        - Moment-based x0 (varies per sample)

    Single-sided upper boundary stickiness test case.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "w_const")


@pytest.fixture
def e_w_p2_test_case() -> dict:
    """Test case for e_w_p2 (beam thermal speed perturbation).

    Distribution characteristics:
        - ~0.45% at lower boundary (L=-75)
        - ~35% at upper boundary (U=75) - EXTREME UPPER STICKINESS
        - ~1.6% at x0=0

    Extreme upper boundary stickiness (~35%) with interior stickiness at x0.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "e_w_p2")


@pytest.fixture
def e_w_p1_test_case() -> dict:
    """Test case for e_w_p1 (core anisotropy coefficient).

    Distribution characteristics:
        - ~1.24% at lower boundary (L=-75) - LOWER STICKINESS
        - ~0.38% at upper boundary (U=75)
        - ~1.6% at x0=0

    Single-sided lower boundary stickiness with interior stickiness at x0.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "e_w_p1")


@pytest.fixture
def e_w_a_test_case() -> dict:
    """Test case for e_w_a (alpha thermal speed perturbation).

    Distribution characteristics:
        - ~0.72% at lower boundary (L=-60) - LOWER STICKINESS
        - ~9.7% at upper boundary (U=200) - UPPER STICKINESS
        - ~1.6% at x0=0

    CRITICAL NOTE: Multiple initial guess options exist. Different versions
    of the initial guess are used in the fitting algorithm. The documented
    x0=0 shows up at transformed variable < 0, requiring careful analysis
    of interior stickiness patterns.

    Bilateral boundary stickiness with complex interior behavior.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "e_w_a")


# =============================================================================
# Density parameters
# =============================================================================


@pytest.fixture
def np2_test_case() -> dict:
    """Test case for np2 (beam density).

    Distribution characteristics:
        - ~0% at lower boundary (L=0.01)
        - ~0.005% at upper boundary (U=100)
        - ~1.5% at x0=0 - INTERIOR STICKINESS

    Interior stickiness only (no boundary stickiness).
    Initial guess is 10% of core density, introduced at Level 3.
    """
    data_dir = Path(__file__).parent / "data"
    return _load_test_case(data_dir, "np2")


# =============================================================================
# Convenience fixture for all test cases
# =============================================================================


@pytest.fixture
def all_ppa12_test_cases() -> dict:
    """Load all PPA12 test cases as a dictionary.

    Returns:
        Dictionary mapping parameter name to test case dict.
    """
    data_dir = Path(__file__).parent / "data"
    params = [
        "A_He",
        "e_dv_ap",
        "e_dv_pp",
        "np1",
        "np2",
        "vx",
        "vy",
        "vz",
        "w_const",
        "e_w_p1",
        "e_w_p2",
        "e_w_a",
    ]
    return {name: _load_test_case(data_dir, name) for name in params}
