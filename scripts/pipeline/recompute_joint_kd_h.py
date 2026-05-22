#!/usr/bin/env python3
"""Recompute the joint K_d-H RMSE grid over an extended H range.

The original phase-A pipeline swept H = 3-10 cm. For Figure 8 we want
the panel to span H = 1-11 cm so the joint-minimum marker has visible
headroom and the colour map fills the panel with real (not
extrapolated) data. This script recomputes ONLY the joint_kd_h block,
over H = 1-11 cm at 1 cm steps, and patches output/phase_a_results.json
in place; nothing else in the results file is touched.

Run from the repo root:
  python scripts/pipeline/recompute_joint_kd_h.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "figures"))

from scripts.pipeline.phase_a_pipeline import SITES, joint_kd_h_dense  # noqa: E402

# Extended H grid: 1-11 cm at 1 cm steps (was 3-10 cm).
H_GRID = np.linspace(0.01, 0.11, 11)


def main():
    res_path = ROOT / "output" / "phase_a_results.json"
    results = json.loads(res_path.read_text())

    for name, cfg in SITES.items():
        ks = results[name]["kd_star"]
        # same K_d span as the original pipeline (0.55-1.45 x K_d*)
        kd_g = np.linspace(0.55 * ks, 1.45 * ks, 8)
        print(f"=== {cfg['label']}: joint K_d-H sweep, "
              f"H = 1-11 cm x {len(kd_g)} K_d ===", flush=True)
        rmse2d = joint_kd_h_dense(cfg, kd_g, H_GRID)
        i, j = np.unravel_index(np.argmin(rmse2d), rmse2d.shape)
        results[name]["joint_kd_h"] = dict(
            h_grid=H_GRID.tolist(), kd_grid=kd_g.tolist(),
            rmse2d=rmse2d.tolist(),
            h_min=float(H_GRID[i]), kd_min=float(kd_g[j]),
            rmse_min=float(rmse2d[i, j]))
        print(f"  joint min: K_d = {kd_g[j]*1e3:.2f} mW/m/K, "
              f"H = {H_GRID[i]*100:.1f} cm, RMSE = {rmse2d[i, j]:.3f} K",
              flush=True)

    res_path.write_text(json.dumps(results, indent=2))
    print(f"\npatched {res_path}")


if __name__ == "__main__":
    main()
