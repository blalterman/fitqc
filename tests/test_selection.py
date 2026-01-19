"""Tests for the selection module."""

import numpy as np

from fitqc.selection import select_elbow


class TestSelection:
    """Tests for elbow detection using kneed library."""

    def test_elbow_on_known_curve(self):
        """Test elbow detection on a known exponential saturation curve."""
        x = np.linspace(0.1, 10, 100)
        y = 1 - np.exp(-x)
        elbow = select_elbow(x, y, curve="concave", direction="increasing")
        assert 1.5 < elbow < 4.0

    def test_elbow_on_step_function(self):
        """Test elbow detection on a step function."""
        x = np.linspace(0, 10, 101)
        y = np.where(x < 5, 0.0, 1.0)
        elbow = select_elbow(x, y, curve="concave", direction="increasing")
        assert 4.0 < elbow < 6.0

    def test_elbow_returns_none_for_linear(self):
        """Test that linear data returns None (no elbow exists)."""
        x = np.linspace(0, 10, 100)
        y = x / 10
        elbow = select_elbow(x, y, curve="concave", direction="increasing")
        assert elbow is None

    def test_elbow_log_space_ecdf_like(self):
        """Test elbow detection with log-space x-axis (ECDF-like data)."""
        eps = np.logspace(-8, -2, 50)
        p = 1 - np.exp(-eps * 1e6)
        elbow = select_elbow(eps, p, curve="concave", direction="increasing", log_x=True)
        assert 1e-7 < elbow < 1e-4
