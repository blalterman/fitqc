"""Integration tests for elbow detection visualization workflow.

Tests complete pipelines: data generation → QC analysis → visualization
"""

import matplotlib.pyplot as plt
import numpy as np

from fitqc.boundary import run_boundary_qc
from fitqc.config import BoundaryConfig, InteriorConfig, PlotConfig
from fitqc.interior import run_interior_qc
from fitqc.plot import plot_kneedle_internals, plot_quantile_elbows_detailed


class TestElbowVizIntegration:
    """End-to-end tests with real QC results."""

    def test_interior_spike_to_visualization_pipeline(self):
        """Full pipeline: synthetic spike → detection → visualization."""
        rng = np.random.default_rng(42)

        # 1. Create data with known spike at x0=0.5
        n_spike = 500
        n_uniform = 9500
        x_spike = np.full(n_spike, 0.5)
        x_uniform = rng.uniform(0.0, 1.0, n_uniform)
        x = np.concatenate([x_spike, x_uniform])

        # 2. Run interior QC with quantile analysis
        config = InteriorConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.005, 0.01, 0.02, 0.05, 0.10),
        )
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # 3. Verify detection succeeded
        assert result.spike_detected, "Should detect spike in synthetic data"
        assert result.eps_star is not None, "Should find eps_star threshold"
        assert result.quantile_elbows is not None, "Should compute quantile elbows"
        assert len(result.quantile_elbows) == 6, "Should have 6 quantile elbows"

        # 4. Visualize quantile elbows - verify structure
        fig1 = plot_quantile_elbows_detailed(result, PlotConfig())
        assert len(fig1.axes) >= 1, "Should create at least 1 panel"

        # Verify scatter points created
        main_ax = next(ax for ax in fig1.axes if ax.get_position().width > 0.1)
        scatter_collections = [c for c in main_ax.collections if hasattr(c, "get_offsets")]

        # Count valid elbows
        n_valid = sum(1 for v in result.quantile_elbows.values() if v is not None)
        if scatter_collections:
            total_points = sum(len(c.get_offsets()) for c in scatter_collections)
            assert total_points == n_valid, (
                f"Expected {n_valid} scatter points for valid elbows, got {total_points}"
            )

        plt.close(fig1)

        # 5. Visualize Kneedle internals for main mass curve - verify structure
        fig2 = plot_kneedle_internals(
            result.eps_grid,
            result.mass_curve,
            curve="concave",
            direction="increasing",
            log_x=True,
            config=PlotConfig(),
        )
        assert len(fig2.axes) == 4, "Should create exactly 4 panels"

        # Verify each panel has data
        for ax in fig2.axes:
            has_lines = len(ax.get_lines()) > 0
            has_collections = len(ax.collections) > 0
            assert has_lines or has_collections, f"Panel '{ax.get_title()}' has no visual content"

        plt.close(fig2)

    def test_boundary_pileup_to_visualization_pipeline(self):
        """Full pipeline: boundary pileup → detection → visualization."""
        rng = np.random.default_rng(42)

        # 1. Create data with lower boundary pileup
        n_pileup = 1000
        n_uniform = 9000
        x_pileup = rng.uniform(0.0, 0.005, n_pileup)
        x_uniform = rng.uniform(0.0, 1.0, n_uniform)
        x = np.concatenate([x_pileup, x_uniform])

        # 2. Run boundary QC with quantile analysis
        config = BoundaryConfig(
            use_quantile_analysis=True,
            quantile_grid=(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10),
        )
        result = run_boundary_qc(x, L=0.0, U=1.0, config=config)

        # 3. Verify quantile_elbows is populated
        assert result.quantile_elbows is not None, "Should compute quantile elbows"
        assert "lower" in result.quantile_elbows, "Should have lower boundary elbows"
        assert "upper" in result.quantile_elbows, "Should have upper boundary elbows"

        # 4. Visualize quantile elbows (should create 2 panels for boundary)
        fig = plot_quantile_elbows_detailed(result, PlotConfig())

        main_axes = [ax for ax in fig.axes if ax.get_position().width > 0.1]
        assert len(main_axes) == 2, (
            f"Expected 2 main panels for BoundaryResult (lower + upper), got {len(main_axes)}"
        )

        # Verify titles mention lower/upper
        titles = [ax.get_title().lower() for ax in main_axes]
        assert any("lower" in t for t in titles), "Should have 'lower' in one title"
        assert any("upper" in t for t in titles), "Should have 'upper' in one title"

        plt.close(fig)

    def test_clean_data_no_stickiness_visualization(self):
        """Clean data (no stickiness) → graceful visualization."""
        rng = np.random.default_rng(42)

        # 1. Clean uniform data (no spike)
        x = rng.uniform(0.0, 1.0, 10000)

        # 2. Run interior QC with quantile analysis
        config = InteriorConfig(use_quantile_analysis=True)
        result = run_interior_qc(x, x0=0.5, L=0.0, U=1.0, config=config)

        # 3. Visualize regardless of detection outcome - should not crash
        fig1 = plot_quantile_elbows_detailed(result, PlotConfig())
        assert len(fig1.axes) >= 1, "Should create figure even with clean data"
        plt.close(fig1)

        # 4. Visualize mass curve - should not crash
        fig2 = plot_kneedle_internals(
            result.eps_grid,
            result.mass_curve,
            curve="concave",
            direction="increasing",
            log_x=True,
        )
        assert len(fig2.axes) == 4, "Should create 4 panels even with clean data"
        plt.close(fig2)
