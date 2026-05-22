#!/usr/bin/env python3
"""Recompute the polar cold-trap depth by genuine forward integration.

Figure 9 claims z_stable(K_d) is obtained by integrating the steady-state
relation  dT/dz = Q_b / K(T,z)  downward through the Hayne (2017)
K(T,z) profile until the temperature reaches the ice-stability
threshold T_stable. The previously stored cold_trap.depth_stable_m,
however, was simply the constant-K Fourier formula
    z = (T_stable - T_surf) * K_d / Q_b,
which is exactly linear in K_d -- so panel (a) showed a straight line
and the panel-(b) ratio eta collapsed to 1.0 by construction.

This script performs the real integration. K(T,z) varies both with
depth (the K_s -> K_d transition over the e-folding scale H) and with
temperature (the chi*(T/T_ref)^3 radiative term), so the genuine
z_stable(K_d) is mildly curved and eta departs from 1.

It patches output/phase2_results.json in place, replacing
cold_trap.depth_stable_m and adding the polar boundary parameters so
the figure can read them rather than hard-coding defaults.

Run from the repo root:
  python scripts/pipeline/recompute_cold_trap.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lunar.properties import conductivity_hayne          # noqa: E402
from lunar.constants import K_SURFACE, H_PARAMETER, CHI_RADIATIVE  # noqa: E402

# Polar boundary conditions (Schorghofer & Aharonson 2005-style).
QB_POLAR  = 0.012      # W m^-2
T_SURF    = 80.0       # K, polar mean surface temperature
T_STABLE  = 110.0      # K, ice-stability threshold


def z_stable(kd, qb=QB_POLAR, t_surf=T_SURF, t_stable=T_STABLE,
             dz=1e-3, z_max=200.0):
    """Depth at which T reaches t_stable, by forward-integrating
    dT/dz = qb / K(T,z) downward from the surface.

    K(T,z) is the Hayne (2017) profile with deep conductivity kd. The
    integration uses a simple adaptive-free RK4 step on a fine grid;
    dz = 1 mm is far finer than any structure in K(T,z).
    """
    T = t_surf
    z = 0.0

    def dTdz(z_, T_):
        K = conductivity_hayne(T_, z_, Ks=K_SURFACE, Kd=kd,
                               H=H_PARAMETER, chi=CHI_RADIATIVE)
        return qb / float(K)

    while T < t_stable and z < z_max:
        k1 = dTdz(z,            T)
        k2 = dTdz(z + dz/2, T + dz/2 * k1)
        k3 = dTdz(z + dz/2, T + dz/2 * k2)
        k4 = dTdz(z + dz,   T + dz   * k3)
        T_next = T + dz/6.0 * (k1 + 2*k2 + 2*k3 + k4)
        if T_next >= t_stable:
            # linear interpolation for the sub-step crossing depth
            frac = (t_stable - T) / (T_next - T)
            return z + frac * dz
        T, z = T_next, z + dz
    return z


def main():
    res_path = ROOT / "output" / "phase2_results.json"
    d = json.loads(res_path.read_text())
    ct = d["cold_trap"]
    kd_grid = np.array(ct["kd_grid"])            # W m^-1 K^-1

    print(f"Forward-integrating cold-trap depth over {len(kd_grid)} "
          f"K_d values (Q_b={QB_POLAR*1e3:.0f} mW/m^2, "
          f"T_surf={T_SURF:.0f} K, T_stable={T_STABLE:.0f} K) ...",
          flush=True)
    depth = np.array([z_stable(kd) for kd in kd_grid])

    # deep-limit (constant-K Fourier) prediction, for the eta ratio
    z_dl = (T_STABLE - T_SURF) * kd_grid / QB_POLAR
    eta = depth / z_dl

    ct["depth_stable_m"]   = depth.tolist()
    ct["Qb_polar"]         = QB_POLAR
    ct["T_surface_polar"]  = T_SURF
    ct["T_ice_stable"]     = T_STABLE
    ct["method"]           = ("forward RK4 integration of dT/dz = "
                              "Q_b/K(T,z) through the Hayne (2017) "
                              "K(T,z) profile")
    res_path.write_text(json.dumps(d, indent=2))

    print(f"  z_stable range : {depth.min():.3f} - {depth.max():.3f} m")
    print(f"  eta range      : {eta.min():.4f} - {eta.max():.4f}  "
          f"(departure from the constant-K limit)")
    print(f"patched {res_path}")


if __name__ == "__main__":
    main()
