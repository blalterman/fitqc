#!/usr/bin/env python3
"""Download intersphinx inventory files for offline documentation builds.

This script downloads the objects.inv files from external documentation
projects (NumPy, SciPy, etc.) and stores them locally. This enables:
- Deterministic CI builds that don't depend on external server availability
- Offline documentation development
- Faster builds (no network fetches)

Usage:
    python scripts/update_intersphinx.py

The downloaded files are stored in docs/_intersphinx/ and should be
committed to the repository.
"""

import urllib.request
from pathlib import Path

INVENTORIES = {
    "python": "https://docs.python.org/3/objects.inv",
    "numpy": "https://numpy.org/doc/stable/objects.inv",
    "scipy": "https://docs.scipy.org/doc/scipy/objects.inv",
    "matplotlib": "https://matplotlib.org/stable/objects.inv",
}

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "_intersphinx"


def download_inventories() -> None:
    """Download all intersphinx inventory files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in INVENTORIES.items():
        out_path = OUTPUT_DIR / f"{name}.inv"
        print(f"Downloading {name} from {url}...")
        try:
            urllib.request.urlretrieve(url, out_path)
            size = out_path.stat().st_size
            print(f"  ✓ Saved {out_path} ({size:,} bytes)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            raise


if __name__ == "__main__":
    download_inventories()
    print("\nDone! Inventory files are ready for offline builds.")
