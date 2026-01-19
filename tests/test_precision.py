"""Tests for the precision module - floating-point precision utilities."""

import numpy as np
import pytest

from fitqc.precision import effective_dtype, eps_from_ulp, quantize_scalar, ulp_at


class TestEffectiveDtype:
    """Tests for effective_dtype function."""

    def test_float32_array_returns_float32(self):
        x = np.array([1.0, 2.0], dtype=np.float32)
        assert effective_dtype(x, "auto") == np.float32

    def test_float64_array_returns_float64(self):
        x = np.array([1.0, 2.0], dtype=np.float64)
        assert effective_dtype(x, "auto") == np.float64

    def test_override_to_float32(self):
        x = np.array([1.0, 2.0], dtype=np.float64)
        assert effective_dtype(x, "float32") == np.float32

    def test_override_to_float64(self):
        x = np.array([1.0, 2.0], dtype=np.float32)
        assert effective_dtype(x, "float64") == np.float64


class TestUlpAt:
    """Tests for ulp_at function - unit in last place calculation."""

    def test_ulp_at_one_float64(self):
        ulp = ulp_at(1.0, np.float64)
        expected = np.finfo(np.float64).eps  # Machine introspection
        assert ulp == pytest.approx(expected, rel=1e-10)

    def test_ulp_at_one_float32(self):
        ulp = ulp_at(1.0, np.float32)
        expected = np.finfo(np.float32).eps  # Machine introspection
        assert ulp == pytest.approx(expected, rel=1e-6)

    def test_ulp_increases_with_magnitude(self):
        ulp_small = ulp_at(1.0, np.float64)
        ulp_large = ulp_at(1e6, np.float64)
        assert ulp_large > ulp_small * 1e5


class TestQuantizeScalar:
    """Tests for quantize_scalar function."""

    def test_quantize_preserves_float64_representable(self):
        val = 1.5
        assert quantize_scalar(val, np.float64) == val

    def test_quantize_to_float32_loses_precision(self):
        # Use a float64 value that's between two float32 representable values
        # We need to construct a float64 value with more precision than float32 can represent
        eps32 = float(np.finfo(np.float32).eps)  # Convert to Python float for float64 arithmetic
        val = 1.0 + 1.5 * eps32  # float64 value between float32 representables
        q = quantize_scalar(val, np.float32)
        assert q != val  # Quantization rounds to nearest float32
        assert abs(q - 1.0) <= 2 * eps32


class TestEpsFromUlp:
    """Tests for eps_from_ulp function."""

    def test_eps_from_ulp_at_center(self):
        x0, L, U = 0.5, 0.0, 1.0
        eps = eps_from_ulp(x0, L, U, np.float64, mult=1)
        expected = ulp_at(0.5, np.float64) / 1.0
        assert eps == pytest.approx(expected, rel=1e-10)

    def test_eps_scales_with_mult(self):
        eps1 = eps_from_ulp(0.5, 0.0, 1.0, np.float64, mult=1)
        eps4 = eps_from_ulp(0.5, 0.0, 1.0, np.float64, mult=4)
        assert eps4 == pytest.approx(4 * eps1, rel=1e-10)

    def test_eps_with_larger_range(self):
        x0, L, U = 5.0, 0.0, 10.0
        eps = eps_from_ulp(x0, L, U, np.float64, mult=1)
        expected = ulp_at(5.0, np.float64) / 10.0
        assert eps == pytest.approx(expected, rel=1e-10)
