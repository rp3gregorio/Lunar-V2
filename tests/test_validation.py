"""Tests for the validation-data loaders.

These tests are skipped unless the corresponding files exist under
``data/`` — they are regression checks for the data layer, not unit
tests of synthetic input.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from lunar import validation

_DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.skipif(
    not (_DATA / "apollo" / "a15" / "a15p1f1.tab").is_file(),
    reason="Apollo HFE data not downloaded",
)
def test_load_apollo_hfe_temperature_a15_p1f1():
    rec = validation.load_apollo_hfe_temperature("a15", "p1f1")
    assert rec.mission == "a15"
    assert rec.probe_name == "a15p1f1"
    assert rec.T.ndim == 1
    assert rec.T.size > 1000
    # Apollo 15 probe 1 fast sensor at ~49 cm sits at ~252-253 K.
    # Project benchmark: SKILL.md says "~252 K at 1 m" is the standard
    # validation target; the fast sensor at ~50 cm is slightly warmer.
    assert 240.0 < float(rec.T.mean()) < 260.0


@pytest.mark.skipif(
    not (_DATA / "apollo" / "depth" / "a15p1_depth.tab").is_file(),
    reason="Apollo HFE depth metadata not downloaded",
)
def test_load_apollo_hfe_depth_a15_p1():
    depth = validation.load_apollo_hfe_depth("a15", 1)
    assert depth.dtype.names == ("time_iso", "T", "sensor", "depth_cm", "flags")
    assert depth.size > 0
    # Apollo 15 probe 1 sensors are distributed between ~35 cm and
    # ~140 cm; the exact set of 8 depths matches the Nagihara et al.
    # (2018) restored archive.
    depths = np.unique(depth["depth_cm"])
    assert 30.0 < depths.min() < 50.0
    assert 120.0 < depths.max() < 200.0
    assert 5 <= depths.size <= 10


@pytest.mark.skipif(
    not (_DATA / "diviner" / "pcp_avg_tbol_pols_sum_ltim13_240.tab").is_file(),
    reason="Diviner PCP noon file not downloaded",
)
def test_load_diviner_pcp_noon_south_pole():
    # Only load a head slice so the test stays fast — the file has
    # ~3.5 M rows and the loader is exercised regardless.
    pcp = validation.load_diviner_pcp_polar(
        local_time=13, season="sum", pole="pols", max_rows=50_000
    )
    assert pcp.pole == "pols"
    assert pcp.season == "sum"
    assert pcp.local_time == 13
    assert pcp.tbol.shape == pcp.clat.shape == pcp.x.shape
    assert pcp.tbol.size > 1000
    # All points should be in the south polar cap.
    assert float(pcp.clat.max()) <= -78.0
    # Finite, physically sensible bolometric temperatures.
    finite = pcp.tbol[np.isfinite(pcp.tbol) & (pcp.tbol > 0)]
    assert finite.size > 0
    assert 20.0 < float(finite.min()) < 400.0
    assert 50.0 < float(finite.max()) < 450.0
