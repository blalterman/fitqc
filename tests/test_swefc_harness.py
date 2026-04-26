"""Smoke test for analyze_swefc_calibration.py.

Exercises loader glue + driver + report + figure writers using a
synthesized in-memory HDF5 (no dependency on the committed-out
``swefc.h5``). Does not assert detection correctness — that is the
harness run itself, not this unit test.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parent.parent
HARNESS_PATH = REPO / "analyze_swefc_calibration.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("analyze_swefc_calibration", HARNESS_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_swefc_calibration"] = module
    spec.loader.exec_module(module)
    return module


def _make_fake_swefc(tmp_path: Path) -> Path:
    """Build a tiny swefc-shaped HDF5 from the parquet test fixtures.

    Columns use the same three-level tuple layout as the real swefc.h5
    (``("v_param", "y", "p1")`` etc.). Values are pulled from the
    existing parquet fixtures so the harness sees realistic
    distributions, but the file is small and disposable.
    """
    vy = pq.read_table(REPO / "tests" / "data" / "vy_test_sample.parquet")["values"].to_numpy()
    # One column is enough for the smoke test — ``run_one`` is called
    # per-parameter and does not care about the full swefc schema.
    df = pd.DataFrame({("v_param", "y", "p1"): vy})
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    out = tmp_path / "mini_swefc.h5"
    df.to_hdf(out, key="ppa12_apeq", mode="w", format="fixed")
    return out


def _single_entry_truth(tmp_path: Path) -> Path:
    truth = {
        "_meta": {"source": "test_swefc_harness.py synthetic"},
        "parameters": [
            {
                "parameter": "v_param.y.p1",
                "column_tuple": ["v_param", "y", "p1"],
                "L": -200,
                "U": 200,
                "x0": 0,
                "lower": True,
                "upper": True,
                "interior": True,
                "interior_locations": [0],
                "below_lower_cut": False,
                "csv_interior_divergence": False,
                "note": "synthetic",
            }
        ],
    }
    out = tmp_path / "mini_truth.json"
    out.write_text(json.dumps(truth))
    return out


def test_run_one_returns_expected_fields(tmp_path):
    module = _load_harness()
    h5 = _make_fake_swefc(tmp_path)
    df = module.load_swefc(h5)
    truth = module.load_truth(_single_entry_truth(tmp_path))
    result = module.run_one(df, truth[0])

    assert result.name == "v_param.y.p1"
    assert result.n_samples > 0
    assert isinstance(result.detected_lower, bool)
    assert isinstance(result.detected_upper, bool)
    assert isinstance(result.detected_interior, bool)
    assert isinstance(result.interior_hits, list)
    assert result.interior_locations == [0.0]
    assert result.L == -200
    assert result.U == 200
    assert result.x0 == 0


def test_main_end_to_end(tmp_path):
    module = _load_harness()
    h5 = _make_fake_swefc(tmp_path)
    truth = _single_entry_truth(tmp_path)
    report = tmp_path / "report.md"
    figure = tmp_path / "figure.pdf"

    rc = module.main(
        [
            "--h5",
            str(h5),
            "--truth",
            str(truth),
            "--output-report",
            str(report),
            "--output-figure",
            str(figure),
        ]
    )
    assert rc in (0, 1)  # 0 = all pass, 1 = at least one mismatch; both are valid outcomes
    assert report.exists()
    assert figure.exists()
    text = report.read_text()
    assert "v_param.y.p1" in text
    assert "## Per-parameter results" in text
