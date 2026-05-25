#!/usr/bin/env python3
"""Sensitivity of the retrieved K_d* to the deep bulk density rho_d.

The discrete 3-layer model takes a per-site deep bulk density rho_d
as its only site-specific input (it sets the transition-ramp
curvature: a denser column compacts faster). Rather than asserting a
single value per site from a single source, we sweep rho_d over the
1700-2000 kg/m^3 range spanned by the Apollo regolith cores
(Mitchell et al. 1973; Carrier, Olhoeft & Mendell 1991, the Lunar
Sourcebook compilation) and report how the retrieved K_d* responds.

Output: a JSON + a summary table showing K_d*(rho_d) for each site
across the proven range.

Run from the repo root:
  python scripts/pipeline/compute_rho_d_sensitivity.py
"""
from __future__ import annotations
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "figures"))

from lunar.apollo_helpers import extract_sensor_stability        # noqa: E402
from scripts.pipeline import phase_a_pipeline as pap             # noqa: E402

# Apollo-core deep bulk density range: 1700-2000 kg/m^3
# (Mitchell+ 1973; Carrier, Olhoeft & Mendell 1991, Lunar Sourcebook ch. 9).
RHO_GRID = np.arange(1700.0, 2001.0, 50.0)        # 7 values

KD_GRID = {"A15": np.linspace(1.5e-3, 15.0e-3, 28),
           "A17": np.linspace(3.0e-3, 22.0e-3, 30)}


def deep_obs(site_cfg):
    obs = extract_sensor_stability(site_cfg["mission"],
                                   min_depth_cm=site_cfg["MIN_DEPTH_CM"])
    deep = np.asarray(obs["deep_mask"], dtype=bool)
    z = np.asarray(obs["depth_cm_all"])[deep] / 100.0
    T = np.asarray(obs["T_eq_all"])[deep]
    return z, T


def retrieve_kd_3layer(site_cfg, rho_deep, kd_grid, z_obs, T_obs):
    """K_d* under the 3-layer model with a specified rho_deep."""
    # Inject rho_deep by giving the cfg a temporary tag and patching the
    # module-level TL_RHO_SITE dict for the duration of this call.
    cfg = deepcopy(site_cfg)
    tmp_tag = f"__sweep_{int(rho_deep)}"
    cfg["tag"] = tmp_tag
    pap.TL_RHO_SITE[tmp_tag] = float(rho_deep)
    try:
        R = np.empty((len(z_obs), len(kd_grid)))
        for k, kd in enumerate(kd_grid):
            z_mid, T_mean = pap.run_with(cfg, kd=kd, k_model="3layer")
            R[:, k] = np.interp(z_obs, z_mid, T_mean) - T_obs
        kd_star, _ = pap.kd_star_from_residuals(R, kd_grid)
    finally:
        del pap.TL_RHO_SITE[tmp_tag]
    return float(kd_star)


def main():
    obs = {s: deep_obs(pap.SITES[s]) for s in ("A15", "A17")}
    out = {"rho_deep_kg_m3": RHO_GRID.tolist(),
           "A15": [], "A17": [],
           "nominal": {"A15": 1825.0, "A17": 1960.0}}

    print(f"{'rho_d (kg/m^3)':>14} | {'A15 K_d* (mW/m/K)':>18} "
          f"| {'A17 K_d* (mW/m/K)':>18}", flush=True)
    print("-" * 60, flush=True)

    for rho in RHO_GRID:
        row = []
        for s in ("A15", "A17"):
            z, T = obs[s]
            kd_mw = retrieve_kd_3layer(pap.SITES[s], rho, KD_GRID[s],
                                       z, T) * 1e3
            out[s].append(kd_mw)
            row.append(kd_mw)
        print(f"{rho:>14.0f} | {row[0]:>18.3f} | {row[1]:>18.3f}",
              flush=True)

    print("-" * 60)
    for s in ("A15", "A17"):
        v = np.array(out[s])
        spread = v.max() - v.min()
        nom = out["nominal"][s]
        # K_d* at the nominal density
        kd_at_nom = float(np.interp(nom, RHO_GRID, v))
        print(f"  {s}: K_d* range {v.min():.2f}-{v.max():.2f} mW/m/K "
              f"(spread {spread:.2f}; "
              f"{100*spread/kd_at_nom:.1f}% of nominal K_d* = "
              f"{kd_at_nom:.2f})")

    json.dump(out, open(ROOT / "output" / "rho_d_sensitivity.json", "w"),
              indent=2)
    print("\nwrote output/rho_d_sensitivity.json")


if __name__ == "__main__":
    main()
