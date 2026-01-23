#!/usr/bin/env python3
"""Clean up duplicate plot files - keep only _hires (300 DPI) versions.

This script removes all non-hires plot versions, keeping only the high-resolution
300 DPI versions with _hires suffix.
"""

from pathlib import Path
import subprocess

def main():
    """Remove all non-hires plot versions."""
    figures_dir = Path("figures")

    # Find all PNG files in subdirectories
    all_plots = list(figures_dir.glob("*/*.png"))

    # Separate into hires and non-hires
    hires_plots = [p for p in all_plots if "_hires.png" in p.name]
    non_hires_plots = [p for p in all_plots if "_hires.png" not in p.name]

    print(f"Found {len(all_plots)} total plots:")
    print(f"  - {len(hires_plots)} high-res (300 DPI) versions")
    print(f"  - {len(non_hires_plots)} low-res (150 DPI) versions")
    print()

    if not non_hires_plots:
        print("✓ No duplicate low-res plots found. All clean!")
        return

    print("Removing duplicate low-res versions:")
    print()

    # Group by dataset
    by_dataset = {}
    for plot in non_hires_plots:
        dataset = plot.parent.name
        if dataset not in by_dataset:
            by_dataset[dataset] = []
        by_dataset[dataset].append(plot)

    # Remove each non-hires plot
    removed_count = 0
    for dataset in sorted(by_dataset.keys()):
        plots = by_dataset[dataset]
        print(f"{dataset}:")
        for plot in sorted(plots):
            # Check if hires version exists
            hires_version = plot.parent / plot.name.replace(".png", "_hires.png")
            if hires_version.exists():
                print(f"  - Removing {plot.name} (have {hires_version.name})")
                subprocess.run(["git", "rm", str(plot)], check=True, capture_output=True)
                removed_count += 1
            else:
                print(f"  ⚠ Skipping {plot.name} (no hires version found)")
        print()

    print("="*70)
    print(f"✓ Removed {removed_count} duplicate low-res plots")
    print(f"✓ Kept {len(hires_plots)} high-res (300 DPI) versions")
    print("="*70)

if __name__ == "__main__":
    main()
