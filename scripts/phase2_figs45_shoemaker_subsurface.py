"""Phase 2 Figures 4 and 5 — Shoemaker PSR subsurface.

Reproduces the subsurface part of Martinez & Siegler (2021) LPSC abstract:

  Fig 4: T(z) profile at the Shoemaker tile, Hayne (chi-T^3) vs
         M&S K(T, rho), Dirichlet surface BC at the Diviner-derived
         time-mean (44 K), Q_b = 0.018 W/m^2.
  Fig 5: Delta-T(z) = T_M&S(z) - T_Hayne(z), the K-model-induced
         depth-dependent disagreement that the paper's 2D 4-m map
         captures at one depth slice. We plot the full depth
         dependence as a 1D proxy for the 2D map (which needs
         per-pixel bowl-crater insolation we don't yet have).

For a constant-T_surface Dirichlet BC the time-mean energy equation
collapses to the steady-state heat equation

    K(T(z), rho(z)) dT/dz = Q_b   (constant geothermal upward flux),

solved as an ODE downward from z=0 (T = T_surface) with RK4 on the
geometric depth grid.

Output: ``output/figures/phase2_fig4_shoemaker_Tz.{pdf,png}``,
        ``output/figures/phase2_fig5_dT_vs_depth.{pdf,png}``
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import Q_B_EQUATORIAL  # 0.018 W/m^2 (M&S global value)
from lunar.diviner import load_gcp_band
from lunar.grid import make_geometric_grid
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne,
)

# Shoemaker target (Mazarico+ 2011; Williams+ 2019 PSR catalog)
SHOEMAKER_LAT = -87.91
SHOEMAKER_LON = 45.51
Z_MAX = 5.0    # m — must reach > 4 m to trace the paper's "4-m" depth
DZ0 = 0.002    # 2 mm top layer
GROWTH = 0.10  # finer growth than Phase 1 default for clean profiles


def shoemaker_surface_T() -> tuple[float, dict]:
    """Diviner-derived time-mean surface T at the Shoemaker tile."""
    band = load_gcp_band(-90, -80, columns=("tbol", "t9"))
    i_target = np.argmin(
        (band.clon - SHOEMAKER_LON) ** 2
        + (band.clat - SHOEMAKER_LAT) ** 2
    )
    cell_mask = (
        (band.clon == band.clon[i_target])
        & (band.clat == band.clat[i_target])
    )
    tbol = band.channels["tbol"][cell_mask]
    valid = tbol > -9000
    return float(tbol[valid].mean()), {
        "clon": float(band.clon[i_target]),
        "clat": float(band.clat[i_target]),
        "tbol_mean": float(tbol[valid].mean()),
        "tbol_min": float(tbol[valid].min()),
        "tbol_max": float(tbol[valid].max()),
        "n_samples": int(valid.sum()),
    }


def integrate_steady_state(
    T_surface: float,
    z_face: np.ndarray,
    K_func,
    Q_b: float = Q_B_EQUATORIAL,
) -> np.ndarray:
    """Integrate the steady-state heat equation downward from z=0.

    Solves dT/dz = Q_b / K(T, rho(z)) using RK4 on the cell faces of
    the geometric depth grid. Returns ``T_face`` at every face.
    """
    n_faces = z_face.size
    T_face = np.empty(n_faces)
    T_face[0] = T_surface

    def rhs(z: float, T: float) -> float:
        K = float(K_func(np.array([T]), np.array([z]))[0])
        return Q_b / K

    for i in range(n_faces - 1):
        z_i, T_i = z_face[i], T_face[i]
        h = z_face[i + 1] - z_face[i]
        k1 = rhs(z_i, T_i)
        k2 = rhs(z_i + 0.5 * h, T_i + 0.5 * h * k1)
        k3 = rhs(z_i + 0.5 * h, T_i + 0.5 * h * k2)
        k4 = rhs(z_i + h, T_i + h * k3)
        T_face[i + 1] = T_i + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    return T_face


def main() -> int:
    # Diviner Shoemaker reference
    T_surf, meta = shoemaker_surface_T()
    print(
        f"Shoemaker tile (clon={meta['clon']:.2f}, clat={meta['clat']:.2f}):\n"
        f"  Tbol mean {meta['tbol_mean']:.2f} K, "
        f"range {meta['tbol_min']:.1f}..{meta['tbol_max']:.1f} K, "
        f"n={meta['n_samples']}"
    )

    grid = make_geometric_grid(z_max=Z_MAX, dz0=DZ0, growth=GROWTH)
    z_face = grid.z_face
    print(
        f"Grid: {grid.n_layers} layers, z_max={z_face[-1]:.2f} m, "
        f"dz0={grid.dz[0]*1000:.2f} mm, dz_max={grid.dz[-1]*100:.2f} cm"
    )

    print(f"Integrating steady-state T(z) at T_surface = {T_surf:.2f} K...")
    T_h = integrate_steady_state(T_surf, z_face, conductivity_hayne)
    T_m = integrate_steady_state(T_surf, z_face, conductivity_martinez)
    dT = T_m - T_h
    z_cm = z_face * 100.0  # convert to cm for plotting

    # ---- Figure 4: T(z) profile, Hayne vs M&S ----
    fig4, ax = plt.subplots(figsize=(6.5, 5.8), constrained_layout=True)
    ax.plot(T_h, z_face, color="#d62728", lw=1.8, label="Hayne χ-T³")
    ax.plot(T_m, z_face, color="#1f77b4", lw=1.8, label="Martinez & Siegler K(T, ρ)")
    ax.axhline(0.0, color="0.4", lw=0.7, ls=":")
    ax.invert_yaxis()
    ax.set_xlabel("Temperature (K)", fontsize=11)
    ax.set_ylabel("Depth (m)", fontsize=11)
    ax.set_title(
        "Phase 2 Fig. 4 — Shoemaker PSR T(z) profile\n"
        f"Dirichlet T(0)={T_surf:.1f} K (Diviner Tbol time-mean), "
        f"Q_b={Q_B_EQUATORIAL*1e3:.0f} mW/m²",
        fontsize=11,
    )
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(alpha=0.3)
    fig4_path = _REPO_ROOT / "output" / "figures" / "phase2_fig4_shoemaker_Tz.pdf"
    fig4_path.parent.mkdir(parents=True, exist_ok=True)
    fig4.savefig(fig4_path)
    fig4.savefig(fig4_path.with_suffix(".png"), dpi=150)
    plt.close(fig4)
    print(f"Saved {fig4_path.relative_to(_REPO_ROOT)}")

    # ---- Figure 5 (1D proxy): ΔT vs depth ----
    fig5, ax = plt.subplots(figsize=(6.5, 5.0), constrained_layout=True)
    ax.plot(z_face, dT, color="0.15", lw=1.8)
    ax.axhline(0.0, color="0.5", lw=0.6, ls=":")
    ax.axvline(4.0, color="#d62728", lw=0.8, ls="--",
               label=f"4 m (paper depth): ΔT = {np.interp(4.0, z_face, dT):+.2f} K")
    ax.set_xlabel("Depth (m)", fontsize=11)
    ax.set_ylabel("ΔT = T(M&S) − T(Hayne)  (K)", fontsize=11)
    ax.set_xlim(0, Z_MAX)
    ax.set_title(
        "Phase 2 Fig. 5 (1D proxy) — K-model T-disagreement vs depth at Shoemaker\n"
        "(Replaces the paper's 2D 4-m ΔT map; same physics, single column)",
        fontsize=10,
    )
    ax.legend(loc="best", fontsize=10, framealpha=0.9)
    ax.grid(alpha=0.3)
    fig5_path = _REPO_ROOT / "output" / "figures" / "phase2_fig5_dT_vs_depth.pdf"
    fig5.savefig(fig5_path)
    fig5.savefig(fig5_path.with_suffix(".png"), dpi=150)
    plt.close(fig5)
    print(f"Saved {fig5_path.relative_to(_REPO_ROOT)}")

    # ---- Numerical summary ----
    print("\nKey points along T(z):")
    for z_target in (0.0, 0.05, 0.10, 0.50, 1.0, 2.0, 4.0, Z_MAX):
        Th = float(np.interp(z_target, z_face, T_h))
        Tm = float(np.interp(z_target, z_face, T_m))
        print(
            f"  z = {z_target:5.2f} m: "
            f"Hayne {Th:6.2f} K, M&S {Tm:6.2f} K, ΔT = {Tm-Th:+6.2f} K"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
