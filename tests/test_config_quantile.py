"""Tests for quantile-based detection configuration fields.

This module tests the quantile analysis configuration fields added to
InteriorConfig, BoundaryConfig, and PlotConfig dataclasses for multi-curve
threshold estimation.
"""

from fitqc.config import BoundaryConfig, InteriorConfig, PlotConfig

# =============================================================================
# 1. InteriorConfig Quantile Tests
# =============================================================================


class TestInteriorConfigQuantile:
    """Tests for quantile analysis fields in InteriorConfig.

    InteriorConfig gained these fields for multi-curve analysis:
    - use_quantile_analysis: bool (opt-in flag)
    - quantile_grid: tuple[float, ...] (quantiles to analyze)
    - min_quantile_agreement: float (minimum fraction of quantiles that must agree)
    """

    def test_use_quantile_analysis_default_false(self):
        """use_quantile_analysis defaults to False for backward compatibility.

        The quantile analysis feature is opt-in to preserve existing behavior.
        Users who don't specify this parameter get single-curve mode.
        """
        config = InteriorConfig()

        assert config.use_quantile_analysis is False

    def test_quantile_grid_default_is_tuple(self):
        """quantile_grid default should be a tuple of floats.

        A tuple is used (rather than list) because:
        1. Quantile grid values should be immutable after construction
        2. Tuples are hashable, allowing config objects to be used in caches
        """
        config = InteriorConfig()

        assert isinstance(config.quantile_grid, tuple)
        assert len(config.quantile_grid) > 0
        for value in config.quantile_grid:
            assert isinstance(value, float)

    def test_quantile_grid_values_in_valid_range(self):
        """All quantile_grid values must be in the open interval (0, 1).

        Quantiles represent cumulative probabilities, so:
        - Values <= 0 are invalid (no negative probabilities)
        - Values >= 1 are invalid (would represent 100%+ of data)
        """
        config = InteriorConfig()

        for value in config.quantile_grid:
            assert 0 < value < 1, f"Quantile {value} not in (0, 1)"

    def test_quantile_grid_is_sorted(self):
        """quantile_grid values should be in ascending order.

        Ascending order is expected because:
        1. Makes iteration predictable (smallest to largest quantile)
        2. Enables binary search if needed
        3. Convention matches numpy.percentile behavior
        """
        config = InteriorConfig()

        values = list(config.quantile_grid)
        assert values == sorted(values), "quantile_grid is not sorted ascending"

    def test_min_quantile_agreement_default(self):
        """min_quantile_agreement defaults to 0.5 (50%).

        This means at least half of the quantiles in the grid must have
        valid elbows for the multi-curve median aggregation to succeed.
        50% is a reasonable balance between robustness and sensitivity.
        """
        config = InteriorConfig()

        assert config.min_quantile_agreement == 0.5

    def test_min_quantile_agreement_bounds(self):
        """min_quantile_agreement should be in [0, 1] range.

        As a fraction/probability:
        - 0.0 means no agreement required (permissive)
        - 1.0 means all quantiles must agree (strict)
        Default 0.5 is in the valid range.
        """
        config = InteriorConfig()

        assert 0 <= config.min_quantile_agreement <= 1

    def test_config_instantiation_with_custom_quantile_grid(self):
        """Users can override quantile_grid with custom values.

        Custom grids allow users to:
        1. Focus on specific quantile ranges relevant to their data
        2. Increase resolution in areas of interest
        3. Reduce computation by using fewer quantiles
        """
        custom_grid = (0.01, 0.05, 0.10, 0.25, 0.50)
        config = InteriorConfig(quantile_grid=custom_grid)

        assert config.quantile_grid == custom_grid
        assert len(config.quantile_grid) == 5
        # Verify other fields remain at defaults
        assert config.use_quantile_analysis is False
        assert config.min_quantile_agreement == 0.5

    def test_backward_compatibility_no_args(self):
        """InteriorConfig instantiates correctly with no arguments.

        This ensures the new quantile fields don't break existing code
        that creates InteriorConfig() with default values.
        """
        config = InteriorConfig()

        # Original fields should have their defaults
        assert config.eps_log10_min == -12
        assert config.eps_log10_max == -3
        assert config.n_eps == 50
        assert config.n_bins == 100
        assert config.spike_prominence_min == 10.0
        assert config.spike_width_max == 15.0
        assert config.spike_location_max == 0.1

        # New quantile fields should have defaults
        assert config.use_quantile_analysis is False
        assert isinstance(config.quantile_grid, tuple)
        assert config.min_quantile_agreement == 0.5


# =============================================================================
# 2. BoundaryConfig Quantile Tests
# =============================================================================


class TestBoundaryConfigQuantile:
    """Tests for quantile analysis fields in BoundaryConfig.

    BoundaryConfig gained these fields for multi-curve analysis:
    - grid_mode: str ("uniform" or "progressive")
    - use_quantile_analysis: bool (opt-in flag)
    - quantile_grid: tuple[float, ...] (quantiles to analyze)
    - min_quantile_agreement: float (minimum fraction of quantiles that must agree)
    """

    def test_use_quantile_analysis_default_false(self):
        """use_quantile_analysis defaults to False for backward compatibility.

        Like InteriorConfig, this is opt-in to preserve existing single-curve
        behavior for users who don't need multi-curve analysis.
        """
        config = BoundaryConfig()

        assert config.use_quantile_analysis is False

    def test_grid_mode_default_uniform(self):
        """grid_mode defaults to 'uniform' for general-purpose detection.

        Uniform grid mode uses linear spacing from tol_min to tol_max,
        providing equal resolution across the entire tolerance range.
        This is suitable for most use cases.
        """
        config = BoundaryConfig()

        assert config.grid_mode == "uniform"

    def test_grid_mode_accepts_progressive(self):
        """grid_mode accepts 'progressive' for tight pileup detection.

        Progressive mode concentrates sampling resolution near boundaries,
        which is better for detecting very tight pileups (< 1% of range).
        """
        config = BoundaryConfig(grid_mode="progressive")

        assert config.grid_mode == "progressive"

    def test_quantile_grid_default_is_tuple(self):
        """quantile_grid default should be a tuple of floats.

        Same rationale as InteriorConfig: immutability and hashability.
        """
        config = BoundaryConfig()

        assert isinstance(config.quantile_grid, tuple)
        assert len(config.quantile_grid) > 0
        for value in config.quantile_grid:
            assert isinstance(value, float)

    def test_quantile_grid_values_valid(self):
        """quantile_grid values must be in (0, 1) and sorted ascending.

        Combines the validity checks: all values in valid range and properly ordered.
        """
        config = BoundaryConfig()

        values = list(config.quantile_grid)

        # All values in (0, 1)
        for value in values:
            assert 0 < value < 1, f"Quantile {value} not in (0, 1)"

        # Sorted ascending
        assert values == sorted(values), "quantile_grid is not sorted ascending"

    def test_min_quantile_agreement_default(self):
        """min_quantile_agreement defaults to 0.5 (50%).

        Consistent with InteriorConfig, requiring at least half of quantiles
        to have valid elbows for the median aggregation to succeed.
        """
        config = BoundaryConfig()

        assert config.min_quantile_agreement == 0.5

    def test_backward_compatibility_no_args(self):
        """BoundaryConfig instantiates correctly with no arguments.

        This ensures the new fields don't break existing code that
        creates BoundaryConfig() with default values.
        """
        config = BoundaryConfig()

        # Original fields should have their defaults
        assert config.tol_min == 0.0
        assert config.tol_max == 0.05
        assert config.n_tols == 41

        # New fields should have defaults
        assert config.grid_mode == "uniform"
        assert config.use_quantile_analysis is False
        assert isinstance(config.quantile_grid, tuple)
        assert config.min_quantile_agreement == 0.5


# =============================================================================
# 3. PlotConfig Quantile Tests
# =============================================================================


class TestPlotConfigQuantile:
    """Tests for tolerance visualization fields in PlotConfig.

    PlotConfig gained figsize_tolerance for tolerance overlay visualizations
    used in quantile-based detection diagnostics.
    """

    def test_figsize_tolerance_default(self):
        """figsize_tolerance has a reasonable default value.

        The default (12, 8) provides a wide aspect ratio suitable for
        tolerance overlay plots which typically show curves over a range.
        """
        config = PlotConfig()

        assert config.figsize_tolerance is not None
        assert config.figsize_tolerance == (12, 8)

    def test_figsize_tolerance_is_tuple_of_floats(self):
        """figsize_tolerance should be a tuple of two numeric values.

        The tuple represents (width, height) in inches for matplotlib figures.
        Both values should be positive numbers (int or float are acceptable).
        """
        config = PlotConfig()

        assert isinstance(config.figsize_tolerance, tuple)
        assert len(config.figsize_tolerance) == 2

        width, height = config.figsize_tolerance
        assert isinstance(width, int | float)
        assert isinstance(height, int | float)
        assert width > 0
        assert height > 0

    def test_config_with_custom_figsize_tolerance(self):
        """Users can override figsize_tolerance with custom dimensions.

        Custom sizes allow users to:
        1. Match their publication or presentation requirements
        2. Adjust for different screen sizes or aspect ratios
        3. Create larger plots for detailed analysis
        """
        custom_size = (16, 10)
        config = PlotConfig(figsize_tolerance=custom_size)

        assert config.figsize_tolerance == custom_size
        # Verify other fields remain at defaults
        assert config.cmap == "Spectral_r"
        assert config.dpi == 300
        assert config.figsize_interior == (12, 8)
        assert config.figsize_boundary == (14, 10)

    def test_backward_compatibility_no_args(self):
        """PlotConfig instantiates correctly with no arguments.

        This ensures the new figsize_tolerance field doesn't break existing
        code that creates PlotConfig() with default values.
        """
        config = PlotConfig()

        # Original fields should have their defaults
        assert config.cmap == "Spectral_r"
        assert config.dpi == 300
        assert config.include_log_abs_panel is True
        assert config.figsize_interior == (12, 8)
        assert config.figsize_boundary == (14, 10)

        # New field should have default
        assert config.figsize_tolerance == (12, 8)
