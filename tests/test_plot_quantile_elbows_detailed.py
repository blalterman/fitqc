"""Tests for plot_quantile_elbows_detailed function.

All tests verify specific properties: type, dtype, shape, or numeric content.
"""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from fitqc.boundary import BoundaryResult
from fitqc.config import PlotConfig
from fitqc.interior import InteriorResult
from fitqc.plot import plot_quantile_elbows_detailed

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def plot_config() -> PlotConfig:
    """Default PlotConfig for tests."""
    return PlotConfig()


@pytest.fixture
def custom_plot_config() -> PlotConfig:
    """Custom PlotConfig with non-default settings."""
    return PlotConfig(
        cmap="viridis",
        dpi=150,
        figsize_tolerance=(10, 6),
    )


@pytest.fixture
def interior_result_with_quantile_elbows() -> InteriorResult:
    """Create an InteriorResult with populated quantile_elbows."""
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=True,
        spike_z_loc=0.02,
        eps_star=1e-6,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows={
            0.001: 1e-9,
            0.005: 5e-8,
            0.01: 1e-7,
            0.02: 5e-7,
            0.05: 1e-6,
            0.10: 5e-6,
        },
    )


@pytest.fixture
def interior_result_partial_none_elbows() -> InteriorResult:
    """Create an InteriorResult where some quantile elbows are None."""
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=True,
        spike_z_loc=0.02,
        eps_star=1e-6,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.01, 0.5, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows={
            0.001: 1e-9,
            0.005: None,  # No elbow found
            0.01: 1e-7,
            0.02: None,  # No elbow found
            0.05: 1e-6,
            0.10: 5e-6,
        },
    )


@pytest.fixture
def interior_result_none_quantile_elbows() -> InteriorResult:
    """Create an InteriorResult with quantile_elbows=None."""
    rng = np.random.default_rng(42)
    return InteriorResult(
        spike_detected=False,
        spike_z_loc=None,
        eps_star=None,
        eps_grid=np.logspace(-12, -3, 50),
        mass_curve=np.linspace(0.001, 0.1, 50),
        hist_counts=rng.integers(0, 100, size=100).astype(float),
        hist_edges=np.linspace(0, 1, 101),
        quantile_elbows=None,
    )


@pytest.fixture
def boundary_result_with_quantile_elbows() -> BoundaryResult:
    """Create a BoundaryResult with populated quantile_elbows."""
    return BoundaryResult(
        lower_pileup_detected=True,
        upper_pileup_detected=False,
        t_lo_star=0.008,
        t_hi_star=None,
        tol_grid=np.linspace(0, 0.05, 41),
        lower_mass_curve=np.linspace(0, 0.15, 41),
        upper_mass_curve=np.linspace(0, 0.05, 41),
        quantile_elbows={
            "lower": {
                0.001: 0.0001,
                0.002: 0.0003,
                0.005: 0.001,
                0.01: 0.003,
                0.02: 0.008,
            },
            "upper": {
                0.001: 0.001,
                0.002: 0.002,
                0.005: 0.005,
                0.01: 0.01,
            },
        },
    )


@pytest.fixture
def boundary_result_none_quantile_elbows() -> BoundaryResult:
    """Create a BoundaryResult with quantile_elbows=None."""
    return BoundaryResult(
        lower_pileup_detected=False,
        upper_pileup_detected=False,
        t_lo_star=None,
        t_hi_star=None,
        tol_grid=np.linspace(0, 0.05, 41),
        lower_mass_curve=np.linspace(0, 0.05, 41),
        upper_mass_curve=np.linspace(0, 0.05, 41),
        quantile_elbows=None,
    )


# =============================================================================
# TestPlotQuantileElbowsDetailedInteriorStructure
# =============================================================================


class TestPlotQuantileElbowsDetailedInteriorStructure:
    """Tests for interior plot structure and layout."""

    def test_interior_creates_exactly_one_main_panel(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that interior plot creates exactly one main panel (excluding colorbar).

        Verifies the figure structure by counting axes with width > 0.1 (main panels,
        not colorbars which have narrow width).
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            # Filter out colorbar axes (width <= 0.1)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) == 1, f"Expected 1 main panel, got {len(main_axes)}"
        finally:
            plt.close(fig)

    def test_interior_y_axis_uses_log_scale(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that interior plot uses log scale on y-axis for epsilon values.

        Epsilon values span many orders of magnitude (1e-9 to 1e-6), so log scale
        is essential for visualization.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Verify y-axis uses log scale
            yscale = ax.get_yscale()
            assert yscale == "log", f"Expected log scale on y-axis, got {yscale}"
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedInteriorScatterPoints
# =============================================================================


class TestPlotQuantileElbowsDetailedInteriorScatterPoints:
    """Tests for scatter point rendering in interior plots."""

    def test_scatter_point_count_matches_valid_elbows(
        self, interior_result_partial_none_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that scatter point count exactly matches number of non-None elbows.

        Verifies that the plot only shows markers for quantiles where an elbow was
        successfully detected (not None).
        """
        fig = plot_quantile_elbows_detailed(interior_result_partial_none_elbows, plot_config)
        try:
            # Count expected valid elbows
            quantile_elbows = interior_result_partial_none_elbows.quantile_elbows
            assert quantile_elbows is not None
            n_valid = sum(1 for v in quantile_elbows.values() if v is not None)

            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Count scatter points
            total_scatter_points = 0
            for coll in ax.collections:
                if hasattr(coll, "get_offsets"):
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        total_scatter_points += len(offsets)

            assert total_scatter_points == n_valid, (
                f"Expected {n_valid} scatter points for valid elbows, got {total_scatter_points}"
            )
        finally:
            plt.close(fig)

    def test_scatter_x_coordinates_match_quantile_keys(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that scatter x-coordinates match the quantile keys.

        Verifies shape, dtype, and numeric values using np.testing.assert_allclose.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            quantile_elbows = interior_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None

            # Get valid elbows and expected x-coordinates
            valid_items = [(q, eps) for q, eps in quantile_elbows.items() if eps is not None]
            expected_x = np.array([q for q, _ in valid_items])

            # Get scatter offsets
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Extract x-coordinates from scatter collections
            scatter_x = []
            for coll in ax.collections:
                if hasattr(coll, "get_offsets") and len(coll.get_offsets()) > 0:
                    offsets = coll.get_offsets()
                    scatter_x.extend(offsets[:, 0])

            scatter_x = np.array(scatter_x)

            # Verify shape
            assert scatter_x.shape == expected_x.shape, (
                f"Expected shape {expected_x.shape}, got {scatter_x.shape}"
            )

            # Verify dtype is numeric
            assert np.issubdtype(scatter_x.dtype, np.number), (
                f"Expected numeric dtype, got {scatter_x.dtype}"
            )

            # Verify values match (sorted for consistent comparison)
            np.testing.assert_allclose(
                np.sort(scatter_x),
                np.sort(expected_x),
                rtol=1e-10,
                err_msg="Scatter x-coordinates do not match quantile keys",
            )
        finally:
            plt.close(fig)

    def test_scatter_y_coordinates_match_elbow_values(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that scatter y-coordinates match the elbow epsilon values.

        Verifies shape, dtype, and numeric values using np.testing.assert_allclose.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            quantile_elbows = interior_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None

            # Get valid elbows and expected y-coordinates
            valid_items = [(q, eps) for q, eps in quantile_elbows.items() if eps is not None]
            expected_y = np.array([eps for _, eps in valid_items])

            # Get scatter offsets
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Extract y-coordinates from scatter collections
            scatter_y = []
            for coll in ax.collections:
                if hasattr(coll, "get_offsets") and len(coll.get_offsets()) > 0:
                    offsets = coll.get_offsets()
                    scatter_y.extend(offsets[:, 1])

            scatter_y = np.array(scatter_y)

            # Verify shape
            assert scatter_y.shape == expected_y.shape, (
                f"Expected shape {expected_y.shape}, got {scatter_y.shape}"
            )

            # Verify dtype is numeric
            assert np.issubdtype(scatter_y.dtype, np.number), (
                f"Expected numeric dtype, got {scatter_y.dtype}"
            )

            # Verify values match (sorted for consistent comparison)
            # Use relative tolerance for log-scale values
            np.testing.assert_allclose(
                np.sort(scatter_y),
                np.sort(expected_y),
                rtol=1e-6,
                err_msg="Scatter y-coordinates do not match elbow epsilon values",
            )
        finally:
            plt.close(fig)

    def test_scatter_offsets_array_shape(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that scatter offsets array has correct shape (n, 2).

        Verifies ndim, shape[1], and that shape[0] matches expected point count.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            quantile_elbows = interior_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None
            n_valid = sum(1 for v in quantile_elbows.values() if v is not None)

            # Get scatter offsets
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Find scatter collection
            scatter_coll = None
            for coll in ax.collections:
                if hasattr(coll, "get_offsets") and len(coll.get_offsets()) > 0:
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        scatter_coll = offsets
                        break

            assert scatter_coll is not None, "Expected to find scatter collection"

            # Verify offsets shape
            assert scatter_coll.ndim == 2, f"Expected ndim=2, got {scatter_coll.ndim}"
            assert scatter_coll.shape[1] == 2, f"Expected shape[1]=2, got {scatter_coll.shape[1]}"
            assert scatter_coll.shape[0] == n_valid, (
                f"Expected shape[0]={n_valid}, got {scatter_coll.shape[0]}"
            )
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedInteriorReferenceLine
# =============================================================================


class TestPlotQuantileElbowsDetailedInteriorReferenceLine:
    """Tests for horizontal reference line at eps_star."""

    def test_horizontal_line_exists_at_eps_star(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that a horizontal line exists at eps_star value.

        Finds lines with constant y-value and verifies one is at eps_star.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            eps_star = interior_result_with_quantile_elbows.eps_star
            assert eps_star is not None

            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Find horizontal lines (constant y-value)
            horizontal_y_values = []
            for line in ax.get_lines():
                ydata = line.get_ydata()
                if len(ydata) >= 2:
                    # Check if y-values are constant (horizontal line)
                    if np.allclose(ydata, ydata[0], rtol=1e-10):
                        horizontal_y_values.append(ydata[0])

            # Verify at least one horizontal line exists at eps_star
            found_eps_star_line = False
            for y_val in horizontal_y_values:
                if np.isclose(y_val, eps_star, rtol=1e-6):
                    found_eps_star_line = True
                    break

            assert found_eps_star_line, (
                f"Expected horizontal line at eps_star={eps_star}, "
                f"found horizontal lines at: {horizontal_y_values}"
            )
        finally:
            plt.close(fig)

    def test_horizontal_line_spans_full_x_range(
        self, interior_result_with_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that the horizontal reference line spans at least 80% of x-axis range.

        Verifies the line spans most of the plot width, not just a small segment.
        """
        fig = plot_quantile_elbows_detailed(interior_result_with_quantile_elbows, plot_config)
        try:
            eps_star = interior_result_with_quantile_elbows.eps_star
            assert eps_star is not None

            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Get x-axis limits
            xlim = ax.get_xlim()
            x_range = xlim[1] - xlim[0]

            # Find horizontal line at eps_star
            found_line_span = False
            for line in ax.get_lines():
                ydata = line.get_ydata()
                xdata = line.get_xdata()
                if len(ydata) >= 2 and np.allclose(ydata, ydata[0], rtol=1e-10):
                    if np.isclose(ydata[0], eps_star, rtol=1e-6):
                        # Check line span
                        line_span = max(xdata) - min(xdata)
                        if line_span >= 0.8 * x_range:
                            found_line_span = True
                            break

            assert found_line_span, (
                f"Expected horizontal line at eps_star to span >= 80% of x-axis range "
                f"({0.8 * x_range:.3f})"
            )
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedBoundaryStructure
# =============================================================================


class TestPlotQuantileElbowsDetailedBoundaryStructure:
    """Tests for boundary plot structure with two panels."""

    def test_boundary_creates_exactly_two_main_panels(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that boundary plot creates exactly two main panels (lower and upper).

        Filters out colorbar axes and verifies exactly 2 main panels exist.
        """
        fig = plot_quantile_elbows_detailed(boundary_result_with_quantile_elbows, plot_config)
        try:
            # Filter out colorbar axes (width <= 0.1)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) == 2, f"Expected 2 main panels, got {len(main_axes)}"
        finally:
            plt.close(fig)

    def test_boundary_panels_have_lower_upper_in_titles(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that boundary panels have 'lower' and 'upper' in their titles.

        Verifies titles contain the boundary names to help users identify panels.
        """
        fig = plot_quantile_elbows_detailed(boundary_result_with_quantile_elbows, plot_config)
        try:
            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 2

            # Get titles
            titles = [ax.get_title().lower() for ax in main_axes[:2]]

            # Verify one has 'lower' and one has 'upper'
            has_lower = any("lower" in t for t in titles)
            has_upper = any("upper" in t for t in titles)

            assert has_lower, f"Expected one panel to have 'lower' in title, got titles: {titles}"
            assert has_upper, f"Expected one panel to have 'upper' in title, got titles: {titles}"
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedBoundaryScatterPoints
# =============================================================================


class TestPlotQuantileElbowsDetailedBoundaryScatterPoints:
    """Tests for scatter points in boundary plots."""

    def test_boundary_lower_panel_scatter_count(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that lower panel scatter count matches valid lower elbows.

        Verifies the first panel (lower boundary) has correct number of scatter points.
        """
        fig = plot_quantile_elbows_detailed(boundary_result_with_quantile_elbows, plot_config)
        try:
            quantile_elbows = boundary_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None
            lower_elbows = quantile_elbows.get("lower", {})
            n_valid_lower = sum(1 for v in lower_elbows.values() if v is not None)

            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 2

            # Check first panel (lower boundary)
            ax_lower = main_axes[0]
            total_scatter_points = 0
            for coll in ax_lower.collections:
                if hasattr(coll, "get_offsets"):
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        total_scatter_points += len(offsets)

            assert total_scatter_points == n_valid_lower, (
                f"Expected {n_valid_lower} scatter points in lower panel, "
                f"got {total_scatter_points}"
            )
        finally:
            plt.close(fig)

    def test_boundary_scatter_coordinates_match_data(
        self, boundary_result_with_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that boundary scatter coordinates match quantile elbow data.

        Verifies offsets shape (n, 2) and that x/y coordinates match expected values.
        """
        fig = plot_quantile_elbows_detailed(boundary_result_with_quantile_elbows, plot_config)
        try:
            quantile_elbows = boundary_result_with_quantile_elbows.quantile_elbows
            assert quantile_elbows is not None
            lower_elbows = quantile_elbows.get("lower", {})

            # Get valid lower elbows
            valid_items = [(q, tol) for q, tol in lower_elbows.items() if tol is not None]
            expected_x = np.array([q for q, _ in valid_items])
            expected_y = np.array([tol for _, tol in valid_items])

            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 2
            ax_lower = main_axes[0]

            # Get scatter offsets
            scatter_offsets = None
            for coll in ax_lower.collections:
                if hasattr(coll, "get_offsets") and len(coll.get_offsets()) > 0:
                    scatter_offsets = coll.get_offsets()
                    break

            assert scatter_offsets is not None, "Expected scatter collection in lower panel"

            # Verify shape
            assert scatter_offsets.shape == (len(expected_x), 2), (
                f"Expected shape {(len(expected_x), 2)}, got {scatter_offsets.shape}"
            )

            # Verify x-coordinates
            scatter_x = np.sort(scatter_offsets[:, 0])
            np.testing.assert_allclose(
                scatter_x,
                np.sort(expected_x),
                rtol=1e-10,
                err_msg="Scatter x-coordinates do not match quantile keys",
            )

            # Verify y-coordinates
            scatter_y = np.sort(scatter_offsets[:, 1])
            np.testing.assert_allclose(
                scatter_y,
                np.sort(expected_y),
                rtol=1e-6,
                err_msg="Scatter y-coordinates do not match tolerance values",
            )
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedEdgeCases
# =============================================================================


class TestPlotQuantileElbowsDetailedEdgeCases:
    """Tests for edge cases and error handling."""

    def test_interior_with_none_quantile_elbows_shows_message(
        self, interior_result_none_quantile_elbows: InteriorResult, plot_config: PlotConfig
    ):
        """Test that interior plot shows message when quantile_elbows is None.

        Verifies that a message about missing quantile data appears in title or text elements.
        """
        fig = plot_quantile_elbows_detailed(interior_result_none_quantile_elbows, plot_config)
        try:
            # Get main axes
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Check for message in title or text objects
            has_message = False

            # Check title
            title = ax.get_title().lower()
            if "no quantile" in title or "not available" in title or "quantile" in title:
                has_message = True

            # Check text objects
            for text in ax.texts:
                text_content = text.get_text().lower()
                if "no quantile" in text_content or "not available" in text_content:
                    has_message = True
                    break

            assert has_message, (
                "Expected to find message about missing quantile data in title or text objects"
            )
        finally:
            plt.close(fig)

    def test_interior_with_empty_quantile_elbows_dict(self, plot_config: PlotConfig):
        """Test that interior plot handles empty quantile_elbows dict gracefully.

        Verifies the function doesn't crash with an empty dict and creates a valid figure.
        """
        rng = np.random.default_rng(42)
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=rng.integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={},  # Empty dict
        )

        fig = plot_quantile_elbows_detailed(result, plot_config)
        try:
            assert isinstance(fig, Figure)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1, "Expected at least one main panel"
        finally:
            plt.close(fig)

    def test_interior_with_all_none_values(self, plot_config: PlotConfig):
        """Test that interior plot shows 0 scatter points when all elbows are None.

        Verifies that when all quantile elbows are None, no scatter points are plotted.
        """
        rng = np.random.default_rng(42)
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=rng.integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={0.01: None, 0.05: None, 0.10: None},  # All None
        )

        fig = plot_quantile_elbows_detailed(result, plot_config)
        try:
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Count scatter points
            total_scatter_points = 0
            for coll in ax.collections:
                if hasattr(coll, "get_offsets"):
                    offsets = coll.get_offsets()
                    if len(offsets) > 0:
                        total_scatter_points += len(offsets)

            assert total_scatter_points == 0, (
                f"Expected 0 scatter points when all elbows are None, got {total_scatter_points}"
            )
        finally:
            plt.close(fig)

    def test_interior_with_single_quantile(self, plot_config: PlotConfig):
        """Test that interior plot handles single quantile correctly.

        Verifies offsets.shape == (1, 2) and coordinates match the single quantile.
        """
        rng = np.random.default_rng(42)
        result = InteriorResult(
            spike_detected=True,
            spike_z_loc=0.02,
            eps_star=1e-6,
            eps_grid=np.logspace(-12, -3, 50),
            mass_curve=np.linspace(0.01, 0.5, 50),
            hist_counts=rng.integers(0, 100, size=100).astype(float),
            hist_edges=np.linspace(0, 1, 101),
            quantile_elbows={0.05: 1e-6},  # Single quantile
        )

        fig = plot_quantile_elbows_detailed(result, plot_config)
        try:
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1
            ax = main_axes[0]

            # Get scatter offsets
            scatter_offsets = None
            for coll in ax.collections:
                if hasattr(coll, "get_offsets") and len(coll.get_offsets()) > 0:
                    scatter_offsets = coll.get_offsets()
                    break

            assert scatter_offsets is not None, "Expected scatter collection"

            # Verify shape
            assert scatter_offsets.shape == (1, 2), (
                f"Expected shape (1, 2) for single quantile, got {scatter_offsets.shape}"
            )

            # Verify coordinates
            assert np.isclose(scatter_offsets[0, 0], 0.05, rtol=1e-10), (
                f"Expected x-coordinate 0.05, got {scatter_offsets[0, 0]}"
            )
            assert np.isclose(scatter_offsets[0, 1], 1e-6, rtol=1e-6), (
                f"Expected y-coordinate 1e-6, got {scatter_offsets[0, 1]}"
            )
        finally:
            plt.close(fig)

    def test_boundary_none_quantile_elbows(
        self, boundary_result_none_quantile_elbows: BoundaryResult, plot_config: PlotConfig
    ):
        """Test that boundary plot handles quantile_elbows=None gracefully.

        Verifies the function creates a valid figure without crashing.
        """
        fig = plot_quantile_elbows_detailed(boundary_result_none_quantile_elbows, plot_config)
        try:
            assert isinstance(fig, Figure)
            # Should still create panels (possibly with messages)
            main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
            assert len(main_axes) >= 1, "Expected at least one main panel"
        finally:
            plt.close(fig)


# =============================================================================
# TestPlotQuantileElbowsDetailedConfiguration
# =============================================================================


class TestPlotQuantileElbowsDetailedConfiguration:
    """Tests for PlotConfig application."""

    def test_custom_dpi_applied(
        self, interior_result_with_quantile_elbows: InteriorResult, custom_plot_config: PlotConfig
    ):
        """Test that custom DPI from PlotConfig is applied to the figure.

        Verifies fig.dpi matches config.dpi exactly.
        """
        fig = plot_quantile_elbows_detailed(
            interior_result_with_quantile_elbows, custom_plot_config
        )
        try:
            expected_dpi = custom_plot_config.dpi
            actual_dpi = fig.dpi

            assert actual_dpi == expected_dpi, f"Expected DPI={expected_dpi}, got {actual_dpi}"
        finally:
            plt.close(fig)

    def test_custom_figsize_applied(
        self, interior_result_with_quantile_elbows: InteriorResult, custom_plot_config: PlotConfig
    ):
        """Test that custom figsize from PlotConfig is applied to the figure.

        Verifies fig.get_size_inches() matches config.figsize_tolerance using
        np.testing.assert_allclose.
        """
        fig = plot_quantile_elbows_detailed(
            interior_result_with_quantile_elbows, custom_plot_config
        )
        try:
            expected_size = np.array(custom_plot_config.figsize_tolerance)
            actual_size = fig.get_size_inches()

            # Verify shape
            assert actual_size.shape == (2,), f"Expected shape (2,), got {actual_size.shape}"

            # Verify dtype is numeric
            assert np.issubdtype(actual_size.dtype, np.number), (
                f"Expected numeric dtype, got {actual_size.dtype}"
            )

            # Verify values match
            np.testing.assert_allclose(
                actual_size,
                expected_size,
                rtol=1e-6,
                err_msg=f"Expected figsize {expected_size}, got {actual_size}",
            )
        finally:
            plt.close(fig)
