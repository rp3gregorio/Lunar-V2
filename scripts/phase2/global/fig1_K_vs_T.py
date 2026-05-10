"""K(T, rho) overlay — Phase 2 figure 1 in our notebook ordering.

This corresponds to **Fig 3 of the Martinez & Siegler (2021) JGR paper**
(a multi-density extension of their single-density K(T) comparison). The
paper's Fig 1 is a *different* plot showing K(T) at rho=1300 across three
models (Woods-Robinson, Hayne, Vasavada top-layer) — that's a separate
script (fig1_three_models.py, future work).

Reproduces thermal conductivity vs temperature for eight bulk densities,
standard Hayne (2017) chi-T^3 model vs Martinez & Siegler density-and-
temperature-dependent low-T model. Pure analytical, no Diviner required.

Output: ``output/figures/phase2_fig1_K_vs_T_multi_rho.pdf``
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import (
    H_PARAMETER, CHI_RADIATIVE, T_REFERENCE,
    K_DEEP, K_SURFACE,
    RHO_SURFACE, RHO_DEEP,
    MS_A1, MS_A2, MS_B1, MS_B2,
)
from lunar.phase2_plotting import (
    apply_phase2_style, legend_below, savefig_pair,
)
from lunar.properties import _woods_robinson_kam

# Temperature grid covering the full lunar range plus the low-T regime
# the M&S model targets (PSRs at 25-100 K, polar nights, dayside peaks).
T = np.linspace(1.0, 400.0, 800)

# Bulk densities to overlay. The Hayne H-parameter envelope spans
# rho_s to rho_d (1100 to 1800 kg/m^3); we sample 1100, 1200, ..., 1700
# to mirror LPSC Fig 1's seven-curve layout.
DENSITIES = np.arange(1100, 1701, 100)


def K_hayne_from_rho(T_arr: np.ndarray, rho: float) -> np.ndarray:
    """Hayne (2017) K(T) at a given bulk density.

    Uses the linear K_c <-> rho relationship implied by combining the
    Hayne H-parameter density profile with the linear-in-(rho_d - rho)
    K_c profile: K_c = K_d - (K_d - K_s) * (rho_d - rho) / (rho_d - rho_s).
    """
    Kc = K_DEEP - (K_DEEP - K_SURFACE) * (RHO_DEEP - rho) / (RHO_DEEP - RHO_SURFACE)
    return Kc * (1.0 + CHI_RADIATIVE * (T_arr / T_REFERENCE) ** 3)


def K_martinez(T_arr: np.ndarray, rho: float) -> np.ndarray:
    """Martinez & Siegler (2021) K(T, rho) — same form as in lunar.properties."""
    k_am = _woods_robinson_kam(T_arr)
    contact = (MS_A1 * rho + MS_A2) * k_am
    radiative = (MS_B1 * rho + MS_B2) * T_arr ** 3
    return contact + radiative


def main() -> int:
    apply_phase2_style()
    fig, ax = plt.subplots(figsize=(8.0, 5.6))

    cmap = plt.get_cmap("viridis", len(DENSITIES))
    for i, rho in enumerate(DENSITIES):
        color = cmap(i)
        ax.plot(
            T, K_hayne_from_rho(T, rho) * 1e3,
            color=color, linestyle="--", linewidth=1.4,
            label=f"{rho:.0f} kg/m³ (Hayne, dashed)",
        )
        ax.plot(
            T, K_martinez(T, rho) * 1e3,
            color=color, linestyle="-", linewidth=1.7,
        )

    ax.set_xlabel("Temperature (K)")
    ax.set_ylabel(r"Thermal conductivity $K\;\times 10^{-3}$  (W m$^{-1}$ K$^{-1}$)")
    ax.set_xlim(0, 400)
    ax.set_ylim(0, 16)
    ax.set_title(
        "K(T, ρ): Hayne χ-T³ (dashed) vs Martinez & Siegler K(T,ρ) (solid)\n"
        "Replicates Fig 3 of Martinez & Siegler (2021)"
    )

    legend_below(ax, ncol=4, pad=0.20)

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig1_K_vs_T_multi_rho.pdf"
    savefig_pair(fig, out_path)
    plt.close(fig)

    # Brief numerical sanity check vs LPSC Fig 1 visual targets:
    #   At T=400 K, rho=1700 kg/m^3, both models give roughly 14e-3 W/m/K.
    #   At T=100 K, the M&S curve is markedly LOWER than Hayne (the
    #   "previously unaccounted-for drop" the abstract describes).
    rho_test = 1700.0
    print(f"K(T=400K, rho={rho_test:.0f}):  "
          f"Hayne {K_hayne_from_rho(np.array([400.0]), rho_test)[0]*1e3:.2f}, "
          f"M&S   {K_martinez(np.array([400.0]), rho_test)[0]*1e3:.2f} (×1e-3 W/m/K)")
    print(f"K(T=100K, rho={rho_test:.0f}):  "
          f"Hayne {K_hayne_from_rho(np.array([100.0]), rho_test)[0]*1e3:.2f}, "
          f"M&S   {K_martinez(np.array([100.0]), rho_test)[0]*1e3:.2f} (×1e-3 W/m/K)")
    print(f"Saved {out_path.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
