"""Figure 4 of Phase 2 — 0° equatorial reference, Hayne vs M&S.

Reproduces Martinez & Siegler (2021) Fig 4: a 4-panel comparison at the
equator (0°, highlands A0=0.12) between the Hayne chi-T^3 and M&S K(T,rho)
thermal models.

Panels:
  (a) T_s(t) — full diurnal surface temperature
  (b) T(z)   — subsurface profile at solar noon (peak T_s)
  (c) ΔT_s   — T_M&S(t) − T_Hayne(t) surface residual
  (d) ΔT(z)  — T_M&S(z) − T_Hayne(z) at solar noon

Key modelling choices (identical to fig2_diurnal_45N.py):
- Vasavada (2012) angle-dependent albedo baked into insolation
- Hayne 2017 density profile and specific heat
- 80-lunation spin-up, surface-cell tol = 0.01 K
- Q_b = 0.018 W/m² (global mean; lunar.constants.Q_B_EQUATORIAL)

Output: ``output/figures/phase2_fig4_equator_reference.{pdf,png}``
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SOLAR_CONSTANT
from lunar.grid import make_geometric_grid
from lunar.phase2_plotting import COLORS, apply_phase2_style, legend_below, savefig_pair
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

T_LUNAR = 29.530589 * 86400.0   # s
LATITUDE_DEG = 0.0
A0 = 0.12                        # highlands Bond albedo (small-i)
DT = 300.0                       # 5-min timestep [s]
SPINUP_LUNATIONS = 80
SPINUP_TOL_K = 0.01
SPINUP_DEPTH_M = 0.10
T_INIT_GUESS = 270.0             # ~equatorial mean
N_LUNATIONS = 1


def vasavada_albedo(cos_i: np.ndarray, A0: float = 0.12) -> np.ndarray:
    """Vasavada (2012) Eq 3: A(i) = A0 + 0.06*i^3 + 0.25*i^8, clamped 0.5."""
    i = np.arccos(np.clip(cos_i, 0.0, 1.0))
    return np.minimum(0.5, A0 + 0.06 * i ** 3 + 0.25 * i ** 8)


def _build_inputs(K_func, t_array, insolation) -> PixelInputs:
    grid = make_geometric_grid()
    rho_z = density_hayne(grid.z_mid)
    K_init = K_func(np.full_like(grid.z_mid, T_INIT_GUESS), grid.z_mid)
    R_z = np.cumsum(grid.dz / K_init)
    T_init = T_INIT_GUESS + Q_B_EQUATORIAL * R_z
    return PixelInputs(
        grid=grid,
        t=t_array,
        bc_mode="radiative",
        insolation=insolation,
        albedo=0.0,
        emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL,
        K_func=K_func,
        rho_func=lambda z: density_hayne(z),
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=SPINUP_LUNATIONS,
        spinup_tol_K=SPINUP_TOL_K,
        spinup_depth_m=SPINUP_DEPTH_M,
    )


def main() -> int:
    n_t = int(N_LUNATIONS * T_LUNAR / DT) + 1
    t = np.linspace(0.0, N_LUNATIONS * T_LUNAR, n_t)
    phase = 2.0 * np.pi * t / T_LUNAR
    cos_lat = np.cos(np.deg2rad(LATITUDE_DEG))
    cos_zenith = np.maximum(0.0, cos_lat * np.cos(phase))
    A_of_t = vasavada_albedo(cos_zenith, A0=A0)
    insolation = (1.0 - A_of_t) * SOLAR_CONSTANT * cos_zenith

    print("Running Phase 1 solver at 0° equator:")
    for label, K_func in [("Hayne", conductivity_hayne), ("Martinez", conductivity_martinez)]:
        t0 = time.time()
        inp = _build_inputs(K_func, t, insolation)
        out = solve_pixel(inp)
        print(
            f"  {label:>10s}: spinup={out.n_spinup_cycles} cycles, "
            f"converged={out.converged}, {time.time()-t0:.1f} s"
        )
        if label == "Hayne":
            out_h = out
        else:
            out_m = out

    # Local time conversion (t=0 = solar noon)
    LT = (12.0 + 24.0 * t / T_LUNAR) % 24.0
    order = np.argsort(LT)
    LT = LT[order]
    Ts_h = out_h.T_surface[order]
    Ts_m = out_m.T_surface[order]

    # Subsurface profiles at solar noon index
    noon_idx = np.argmax(insolation)
    z = out_h.z
    Tz_h = out_h.T[:, noon_idx]
    Tz_m = out_m.T[:, noon_idx]

    print(f"\nEquatorial summary:")
    print(f"  Hayne   T_max={Ts_h.max():.1f} K, T_min={Ts_h.min():.1f} K")
    print(f"  M&S     T_max={Ts_m.max():.1f} K, T_min={Ts_m.min():.1f} K")
    print(f"  Benchmark: T_max ~ 390 K, T_min ~ 95 K (Hayne 2017)")

    apply_phase2_style()
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 9.0))
    ax_a, ax_b = axes[0]
    ax_c, ax_d = axes[1]

    # (a) T_s diurnal
    ax_a.plot(LT, Ts_h, color=COLORS["hayne"], lw=1.7, label="Hayne χ-T³")
    ax_a.plot(LT, Ts_m, color=COLORS["ms"], lw=1.7, label="Martinez & Siegler K(T,ρ)")
    ax_a.set_xlabel("Local time (hr)")
    ax_a.set_ylabel("Surface T (K)")
    ax_a.set_title("(a)  T_s diurnal — equator highlands")
    ax_a.set_xlim(0, 24)
    legend_below(ax_a, ncol=2, pad=0.22)

    # (b) T(z) at solar noon
    ax_b.plot(Tz_h, z, color=COLORS["hayne"], lw=1.7, label="Hayne χ-T³")
    ax_b.plot(Tz_m, z, color=COLORS["ms"], lw=1.7, label="Martinez & Siegler K(T,ρ)")
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Temperature (K)")
    ax_b.set_ylabel("Depth (m)")
    ax_b.set_title("(b)  T(z) at solar noon")
    legend_below(ax_b, ncol=2, pad=0.22)

    # (c) ΔT_s = T_M&S − T_Hayne, surface
    dTs = Ts_m - Ts_h
    ax_c.plot(LT, dTs, color="0.2", lw=1.5)
    ax_c.axhline(0, color="0.6", lw=0.7, ls=":")
    ax_c.set_xlabel("Local time (hr)")
    ax_c.set_ylabel("ΔT_s = T(M&S) − T(Hayne)  (K)")
    ax_c.set_title("(c)  Surface ΔT diurnal")
    ax_c.set_xlim(0, 24)

    # (d) ΔT(z) at solar noon
    dTz = Tz_m - Tz_h
    ax_d.plot(dTz, z, color="0.2", lw=1.5)
    ax_d.axvline(0, color="0.6", lw=0.7, ls=":")
    ax_d.invert_yaxis()
    ax_d.set_xlabel("ΔT = T(M&S) − T(Hayne)  (K)")
    ax_d.set_ylabel("Depth (m)")
    ax_d.set_title("(d)  Subsurface ΔT at solar noon")

    fig.suptitle(
        "Equatorial reference (0° highlands)  —  Fig 4 of Martinez & Siegler (2021)",
        fontsize=13,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig4_equator_reference.pdf"
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"\nSaved {out_path.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
