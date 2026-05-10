"""Figure 1 of Phase 2 — analytical K(T, rho) overlay.

Reproduces the comparison shown in Martinez & Siegler (2021) LPSC abstract
Fig 1: thermal conductivity vs temperature for several bulk densities,
standard Hayne (2017) chi-T^3 model vs Martinez & Siegler density-and-
temperature-dependent low-T model. Pure analytical, no Diviner data
required.

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
)
from lunar.properties import _woods_robinson_kam
from lunar.constants import MS_A1, MS_A2, MS_B1, MS_B2

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
    fig, ax = plt.subplots(figsize=(7.5, 5.0), constrained_layout=True)

    cmap = plt.get_cmap("viridis", len(DENSITIES))
    for i, rho in enumerate(DENSITIES):
        color = cmap(i)
        ax.plot(
            T, K_hayne_from_rho(T, rho) * 1e3,
            color=color, linestyle="--", linewidth=1.4,
            label=f"Hayne {rho:.0f} kg/m³",
        )
        ax.plot(
            T, K_martinez(T, rho) * 1e3,
            color=color, linestyle="-", linewidth=1.6,
        )

    ax.set_xlabel("Temperature (K)", fontsize=12)
    ax.set_ylabel(r"Thermal conductivity (W m$^{-1}$ K$^{-1}$) $\times 10^{-3}$",
                  fontsize=12)
    ax.set_xlim(0, 400)
    ax.set_ylim(0, 16)
    ax.grid(alpha=0.3)
    ax.set_title(
        "Phase 2 Fig. 1 — K(T, ρ): Hayne (2017) vs Martinez & Siegler (2021)\n"
        "Solid = M&S low-T model, Dashed = Hayne χ-T³",
        fontsize=11,
    )

    # Two-column legend, sized to fit
    leg = ax.legend(
        loc="upper left", fontsize=8, ncol=2, framealpha=0.9,
        title="Hayne curves only (solid M&S overlap at same color)",
        title_fontsize=8,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig1_K_vs_T_multi_rho.pdf"
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=150)
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
