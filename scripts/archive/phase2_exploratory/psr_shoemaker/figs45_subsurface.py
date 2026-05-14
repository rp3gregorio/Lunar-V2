"""Phase 2 Figures 4 and 5 — Shoemaker PSR subsurface T(z) profiles.

Steady-state heat-equation profiles using the surface BC from the same
reference dataset as the published Shoemaker figures: the Dave-Paige
Diviner-pipeline reference temperatures in ``shoemakerIllumination.mat``.

  Fig 4: T(z) profile, Hayne chi-T^3 vs M&S K(T, rho), Dirichlet surface
         BC at the daveTemp time-mean = 34.2 K, Q_b = 0.018 W/m^2.
  Fig 5: Delta-T(z) = T_M&S(z) - T_Hayne(z) — the K-model-induced
         depth-dependent disagreement. A 1-D proxy for the paper's 2-D
         4-m ΔT map (the 2-D version needs per-pixel illumination maps).

For a constant Dirichlet surface BC the time-mean energy equation collapses
to the steady-state heat equation

    K(T(z), rho(z))  dT/dz = Q_b   (constant geothermal upward flux)

solved as an ODE downward from z=0 (T = T_surface) with RK4 on the
geometric depth grid.

Note on the surface BC choice
------------------------------
The ``daveTemp`` field in ``shoemakerIllumination.mat`` is the Dave-Paige
Diviner-pipeline reference temperature at the Shoemaker tile (mean 34.2 K).
This is the same external validation target the upstream Martinez & Siegler
solver is compared against (see ``heat1DShoemaker.m``), so using it for
the Dirichlet BC makes Figs 4 & 5 internally consistent with Fig 3.

The Diviner GCP ``Tbol`` product at the nearest 0.25-deg grid cell gives
44.4 K — a different observational product, different projection, different
averaging. We use ``daveTemp`` here for consistency with the upstream paper.

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

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import Q_B_EQUATORIAL
from lunar.grid import make_geometric_grid
from lunar.illumination import load_shoemaker_illumination
from lunar.phase2_plotting import (
    COLORS, apply_phase2_style, legend_below, savefig_pair,
)
from lunar.properties import conductivity_hayne, conductivity_martinez

Z_MAX = 5.0   # m — must reach > 4 m to trace the paper's "4-m" depth
DZ0 = 0.002   # 2 mm top layer
GROWTH = 0.10


def integrate_steady_state(
    T_surface: float,
    z_face: np.ndarray,
    K_func,
    Q_b: float = Q_B_EQUATORIAL,
) -> np.ndarray:
    """RK4 integration of dT/dz = Q_b / K(T, rho(z)) downward from z=0."""
    T_face = np.empty(z_face.size)
    T_face[0] = T_surface

    def rhs(z: float, T: float) -> float:
        return Q_b / float(K_func(np.array([T]), np.array([z]))[0])

    for i in range(z_face.size - 1):
        z_i, T_i = z_face[i], T_face[i]
        h = z_face[i + 1] - z_face[i]
        k1 = rhs(z_i,             T_i)
        k2 = rhs(z_i + 0.5 * h,  T_i + 0.5 * h * k1)
        k3 = rhs(z_i + 0.5 * h,  T_i + 0.5 * h * k2)
        k4 = rhs(z_i + h,         T_i +        h * k3)
        T_face[i + 1] = T_i + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    return T_face


def main() -> int:
    # Surface BC: time-mean of daveTemp (same reference the upstream solver uses)
    sh = load_shoemaker_illumination()
    T_surf = float(sh["T_reference"].mean())
    T_surf_min = float(sh["T_reference"].min())
    T_surf_max = float(sh["T_reference"].max())
    print(
        f"Shoemaker daveTemp reference (upstream shoemakerIllumination.mat):\n"
        f"  mean = {T_surf:.2f} K, range = {T_surf_min:.1f} - {T_surf_max:.1f} K, "
        f"lat = {sh['latitude']:.2f}, lon = {sh['longitude']:.2f}"
    )
    print(f"  -> using T_surface = {T_surf:.2f} K as Dirichlet BC for T(z) profiles")

    grid = make_geometric_grid(z_max=Z_MAX, dz0=DZ0, growth=GROWTH)
    z_face = grid.z_face
    print(
        f"Grid: {grid.n_layers} layers, z_max = {z_face[-1]:.2f} m, "
        f"dz0 = {grid.dz[0]*1e3:.2f} mm, dz_max = {grid.dz[-1]*1e2:.1f} cm"
    )

    T_h = integrate_steady_state(T_surf, z_face, conductivity_hayne)
    T_m = integrate_steady_state(T_surf, z_face, conductivity_martinez)
    dT = T_m - T_h

    apply_phase2_style()

    # ---- Figure 4: T(z) profile ----
    fig4, ax4 = plt.subplots(figsize=(7.0, 6.0))
    ax4.plot(T_h, z_face, color=COLORS["hayne"], lw=1.9, label="Hayne χ-T³")
    ax4.plot(T_m, z_face, color=COLORS["ms"], lw=1.9,
             label="Martinez & Siegler K(T, ρ)")
    ax4.invert_yaxis()
    ax4.set_xlabel("Temperature (K)")
    ax4.set_ylabel("Depth (m)")
    ax4.set_title(
        "Shoemaker PSR T(z) profile  (Fig 11 of Martinez & Siegler 2021)\n"
        f"Dirichlet T(0) = {T_surf:.1f} K (daveTemp mean, upstream .mat), "
        f"Q_b = {Q_B_EQUATORIAL*1e3:.0f} mW/m²"
    )
    legend_below(ax4, ncol=2, pad=0.15)
    fig4_path = _REPO_ROOT / "output" / "figures" / "phase2_fig4_shoemaker_Tz.pdf"
    fig4_path.parent.mkdir(parents=True, exist_ok=True)
    savefig_pair(fig4, fig4_path)
    plt.close(fig4)
    print(f"Saved {fig4_path.relative_to(_REPO_ROOT)}")

    # ---- Figure 5: ΔT vs depth ----
    dT_4m = float(np.interp(4.0, z_face, dT))
    fig5, ax5 = plt.subplots(figsize=(7.5, 5.2))
    ax5.plot(z_face, dT, color="0.15", lw=1.9, label="ΔT = T(M&S) − T(Hayne)")
    ax5.axhline(0.0, color="0.6", lw=0.6, ls=":")
    ax5.axvline(4.0, color=COLORS["highlight"], lw=1.0, ls="--",
                label=f"4 m (paper depth):  ΔT = {dT_4m:+.1f} K")
    ax5.set_xlabel("Depth (m)")
    ax5.set_ylabel("ΔT = T(M&S) − T(Hayne)  (K)")
    ax5.set_xlim(0, Z_MAX)
    ax5.set_title(
        "K-model ΔT vs depth at Shoemaker  (1-D proxy for Fig 9 of M&S 2021)"
    )
    legend_below(ax5, ncol=2, pad=0.18)
    fig5_path = _REPO_ROOT / "output" / "figures" / "phase2_fig5_dT_vs_depth.pdf"
    savefig_pair(fig5, fig5_path)
    plt.close(fig5)
    print(f"Saved {fig5_path.relative_to(_REPO_ROOT)}")

    # ---- Numerical summary ----
    print(f"\nT(z) summary — Dirichlet T(0) = {T_surf:.2f} K, Q_b = {Q_B_EQUATORIAL*1e3:.0f} mW/m²")
    print(f"{'z (m)':>7}  {'Hayne (K)':>10}  {'M&S (K)':>10}  {'ΔT (K)':>10}")
    print("-" * 44)
    for z_t in (0.0, 0.05, 0.10, 0.50, 1.0, 2.0, 4.0, Z_MAX):
        Th = float(np.interp(z_t, z_face, T_h))
        Tm = float(np.interp(z_t, z_face, T_m))
        print(f"{z_t:7.2f}  {Th:10.2f}  {Tm:10.2f}  {Tm-Th:+10.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
