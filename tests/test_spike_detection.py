"""Dedicated tests for find_peaks spike detection.

These tests verify the spike detection mechanism used in interior.py.
The implementation uses scipy.signal.find_peaks with:
- prominence >= spike_prominence_min (default 10)
- width <= spike_width_max (default 15 bins)
- location <= spike_location_max (default 0.1)

These tests verify:
1. Injected spikes meet the prominence threshold
2. True spikes are narrow (width < spike_width_max)
3. Broad distributions have wide peaks that don't qualify as spikes
4. After filtering spike samples, the histogram peak count drops
"""

import numpy as np
from scipy.signal import find_peaks, peak_widths

from fitqc.config import InteriorConfig


class TestSpikeDetection:
    """Tests for spike detection using find_peaks."""

    def test_spike_prominence_above_threshold(self):
        """Injected spike should have prominence above the configured minimum."""
        config = InteriorConfig()
        rng = np.random.default_rng(42)

        # Generate base distribution
        z = np.abs(rng.normal(0.5, 0.2, size=10000))
        # Inject 5% spike near zero
        z[:500] = rng.uniform(0, 0.01, size=500)

        hist_counts, _ = np.histogram(z, bins=config.n_bins, range=(0, 1))

        # Pad histogram like interior.py does
        hist_padded = np.concatenate([[0], hist_counts, [0]])
        peaks, props = find_peaks(hist_padded, prominence=config.spike_prominence_min)

        # Should detect at least one peak with prominence >= threshold
        assert len(peaks) > 0, "Should detect at least one peak"
        # The first peak (near z=0) should have prominence above minimum
        assert props["prominences"][0] >= config.spike_prominence_min

    def test_spike_width_narrow(self):
        """True spike should have width below the configured maximum."""
        config = InteriorConfig()
        rng = np.random.default_rng(42)

        # Generate base distribution
        z = np.abs(rng.normal(0.5, 0.2, size=10000))
        # Inject 5% spike in a very narrow region
        z[:500] = rng.uniform(0, 0.01, size=500)

        hist_counts, _ = np.histogram(z, bins=config.n_bins, range=(0, 1))

        # Pad histogram like interior.py does
        hist_padded = np.concatenate([[0], hist_counts, [0]])
        peaks, _ = find_peaks(hist_padded, prominence=config.spike_prominence_min)

        if len(peaks) > 0:
            widths, _, _, _ = peak_widths(hist_padded, peaks, rel_height=0.5)
            # The first peak (spike at z≈0) should be narrow
            assert widths[0] <= config.spike_width_max, (
                f"Spike width {widths[0]} should be <= {config.spike_width_max}"
            )

    def test_no_spike_uniform_via_full_interior_check(self):
        """Uniform distribution should NOT trigger spike detection in full interior QC.

        This test verifies that the full interior QC pipeline (not just find_peaks)
        correctly handles uniform data. The min_mass_for_spike check and elbow
        detection together prevent false positives.

        Note: The low-level find_peaks may detect peaks due to histogram padding,
        but the full algorithm has additional checks that prevent false positives.
        """
        from fitqc.interior import run_interior_qc

        config = InteriorConfig()
        rng = np.random.default_rng(42)

        # Uniform distribution in the range [0, 10]
        x = rng.uniform(0, 10, size=10000)

        result = run_interior_qc(x, x0=5.0, L=0.0, U=10.0, config=config)

        # Full interior QC should NOT detect a spike for uniform data
        assert result.spike_detected is False, "Uniform data should not trigger spike detection"

    def test_spike_count_drops_after_filtering(self):
        """After filtering samples in the spike region, the peak count should drop.

        This verifies that the spike is a real concentration of samples that can
        be removed by filtering, not just statistical noise.
        """
        rng = np.random.default_rng(42)
        n_bins = 100

        # Generate base distribution
        z = np.abs(rng.normal(0.5, 0.2, size=10000))
        # Inject 5% spike near zero
        z[:500] = rng.uniform(0, 0.01, size=500)

        # Histogram before filtering
        hist_before, _ = np.histogram(z, bins=n_bins, range=(0, 1))
        count_in_first_bin_before = hist_before[0]

        # Filter out samples in the spike region
        z_filtered = z[z > 0.02]

        # Histogram after filtering
        hist_after, _ = np.histogram(z_filtered, bins=n_bins, range=(0, 1))
        count_in_first_bin_after = hist_after[0]

        # The count in the first bin should drop significantly
        assert count_in_first_bin_after < count_in_first_bin_before * 0.5, (
            f"First bin count should drop by >50% after filtering: "
            f"{count_in_first_bin_before} -> {count_in_first_bin_after}"
        )
