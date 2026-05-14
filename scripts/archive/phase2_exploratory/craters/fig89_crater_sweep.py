"""Figures 8 & 9 of Phase 2 — crater floor temperature sweep.

Reproduces Martinez & Siegler (2021) Figs 8 & 9: surface min/max temperature
and subsurface ΔT on a bowl-crater floor as a function of crater size
(D = 5, 8, 16) and southern latitude (75°S – 89.9°S in 1° steps).

Insolation uses ``lunar.illumination.crater_floor_insolation()`` — a direct
port of the upstream MATLAB ``insolationcrater.m`` function.

  Fig 8: T_min and T_max at the crater floor surface vs latitude, one
         sub-panel per crater diameter D.
  Fig 9: ΔT = T_M&S(z) − T_Hayne(z) at depths z=1 m and z=2 m vs latitude,
         one sub-panel per crater diameter D.

Runtime: ~90 solver calls (3 D × 15 lats × 2 K models). PSR floors are
cold (~50-120 K) and receive nearly constant insolation, so spin-up usually
converges in < 20 cycles. Expect ~30–90 min with multiprocessing.

References:
- Martinez & Siegler (2021) JGR:Planets 126, e2021JE006829, Figs 8-9
- crater_floor_insolation(): ported from upstream insolationcrater.m

Output:
  ``output/figures/phase2_fig8_crater_Tsurf.{pdf,png}``
  ``output/figures/phase2_fig9_crater_dT.{pdf,png}``
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL
from lunar.grid import make_geometric_grid
from lunar.phase2_plotting import COLORS, apply_phase2_style, legend_below, savefig_pair
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

T_LUNAR = 29.530589 * 86400.0   # s
DT = 600.0                        # 10-min timestep — PSR Q barely changes
SPINUP_LUNATIONS = 80
SPINUP_TOL_K = 0.01
SPINUP_DEPTH_M = None             # check all depths for cold PSR convergence
N_LUNATIONS = 1

# D = crater_diameter / sub-solar_disk_diameter (dimensionless, M&S 2021)
D_VALUES = [5, 8, 16]

# Southern latitudes (75°S–89.9°S in 1° steps → 15 latitudes)
LAT_GRID = -np.arange(75.0, 90.0, 1.0)   # [-75, -76, ..., -89]

Z_1M = 1.0   # m
Z_2M = 2.0   # m


def _run_one(lat_deg: float, D: int, K_func_name: str) -> dict:
    """Worker: run solver on crater floor, return T_surface stats and T(z)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL
    from lunar.grid import make_geometric_grid
    from lunar.illumination import crater_floor_insolation
    from lunar.properties import (
        conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
    )
    from lunar.solver import PixelInputs, solve_pixel
    import numpy as np

    T_LUNAR_s = 29.530589 * 86400.0
    DT_local = 600.0

    K_func = conductivity_hayne if K_func_name == "hayne" else conductivity_martinez

    n_t = int(1 * T_LUNAR_s / DT_local) + 1
    t = np.linspace(0.0, T_LUNAR_s, n_t)

    # Absorbed insolation on crater floor (already (1−A) factored in)
    insolation = crater_floor_insolation(
        t,
        latitude_deg=lat_deg,
        diameter_norm=float(D),
        bond_albedo=0.12,
        emissivity=0.95,
    )

    # Cold PSR initial guess based on expected equilibrium
    Q_mean = insolation.mean()
    from lunar.constants import EMISSIVITY_DEFAULT, SIGMA_SB
    T_guess = max(30.0, (Q_mean / (EMISSIVITY_DEFAULT * SIGMA_SB)) ** 0.25)

    grid = make_geometric_grid()
    K_init = K_func(np.full_like(grid.z_mid, T_guess), grid.z_mid)
    R_z = np.cumsum(grid.dz / K_init)
    T_init = T_guess + Q_B_EQUATORIAL * R_z

    inp = PixelInputs(
        grid=grid, t=t, bc_mode="radiative",
        insolation=insolation,
        albedo=0.0,           # baked into crater_floor_insolation
        emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL,
        K_func=K_func,
        rho_func=lambda z: density_hayne(z),
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=80,
        spinup_tol_K=0.01,
        spinup_depth_m=None,
    )
    out = solve_pixel(inp)
    T_mean_z = out.T.mean(axis=1)   # shape (N_z,)
    return {
        "lat": lat_deg, "D": D, "model": K_func_name,
        "T_min": float(out.T_surface.min()),
        "T_max": float(out.T_surface.max()),
        "T_mean_s": float(out.T_surface.mean()),
        "T_mean_1m": float(np.interp(1.0, out.z, T_mean_z)),
        "T_mean_2m": float(np.interp(2.0, out.z, T_mean_z)),
        "converged": out.converged,
        "n_spinup": out.n_spinup_cycles,
    }


def main() -> int:
    t0_wall = time.time()
    n_tasks = len(D_VALUES) * len(LAT_GRID) * 2
    print(f"Crater sweep: {len(D_VALUES)} D × {len(LAT_GRID)} lats × 2 models "
          f"= {n_tasks} solver calls")

    tasks = [
        (lat, D, model)
        for D in D_VALUES
        for lat in LAT_GRID
        for model in ("hayne", "martinez")
    ]

    results: list[dict] = []
    done = 0
    with ProcessPoolExecutor() as ex:
        futs = {ex.submit(_run_one, lat, D, mdl): (lat, D, mdl)
                for lat, D, mdl in tasks}
        for fut in as_completed(futs):
            lat, D, mdl = futs[fut]
            r = fut.result()
            results.append(r)
            done += 1
            elapsed = time.time() - t0_wall
            eta = elapsed / done * (n_tasks - done)
            print(
                f"  [{done:>2d}/{n_tasks}] lat={lat:+.0f}° D={D:>2d} {mdl:>10s}: "
                f"T_min={r['T_min']:.1f} K  T_max={r['T_max']:.1f} K  "
                f"converged={r['converged']}  ETA {eta/60:.0f} min"
            )

    print(f"\nTotal runtime: {(time.time()-t0_wall)/60:.1f} min")

    def _arr(D: int, model: str, key: str) -> np.ndarray:
        vals = [r[key] for r in results if r["D"] == D and r["model"] == model]
        lats = [r["lat"] for r in results if r["D"] == D and r["model"] == model]
        order = np.argsort(lats)[::-1]   # 75° first (least negative)
        return np.array(lats)[order], np.array(vals)[order]

    # ---- Figure 8: T_min and T_max vs latitude ----
    apply_phase2_style()
    fig8, axes8 = plt.subplots(1, 3, figsize=(15.0, 5.0), constrained_layout=True)

    for ax, D in zip(axes8, D_VALUES):
        lats_h, Tmin_h = _arr(D, "hayne",    "T_min")
        _,      Tmax_h = _arr(D, "hayne",    "T_max")
        _,      Tmin_m = _arr(D, "martinez", "T_min")
        _,      Tmax_m = _arr(D, "martinez", "T_max")

        lat_plot = np.abs(lats_h)   # plot as positive south
        ax.fill_between(lat_plot, Tmin_h, Tmax_h,
                        color=COLORS["hayne"], alpha=0.25, label=None)
        ax.fill_between(lat_plot, Tmin_m, Tmax_m,
                        color=COLORS["ms"], alpha=0.25, label=None)
        ax.plot(lat_plot, Tmin_h, color=COLORS["hayne"], lw=1.5,
                ls="-",  label="Hayne — T_min")
        ax.plot(lat_plot, Tmax_h, color=COLORS["hayne"], lw=1.5,
                ls="--", label="Hayne — T_max")
        ax.plot(lat_plot, Tmin_m, color=COLORS["ms"], lw=1.5,
                ls="-",  label="M&S — T_min")
        ax.plot(lat_plot, Tmax_m, color=COLORS["ms"], lw=1.5,
                ls="--", label="M&S — T_max")

        ax.axhline(110.0, color="0.5", lw=0.8, ls=":", label="110 K ice-stability")
        ax.set_title(f"D = {D}")
        ax.set_xlabel("|Latitude| (°S)")
        ax.set_ylabel("Surface T (K)")
        ax.set_xlim(75, 90)

    legend_below(axes8[0], ncol=3, pad=0.22)
    fig8.suptitle(
        "Crater floor T_min / T_max — Fig 8 of Martinez & Siegler (2021)",
        fontsize=13,
    )
    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    p8 = out_dir / "phase2_fig8_crater_Tsurf.pdf"
    savefig_pair(fig8, p8)
    plt.close(fig8)
    print(f"Saved {p8.relative_to(_REPO_ROOT)}")

    # ---- Figure 9: ΔT at 1m and 2m vs latitude ----
    fig9, axes9 = plt.subplots(1, 3, figsize=(15.0, 5.0), constrained_layout=True)

    for ax, D in zip(axes9, D_VALUES):
        lats_h, T1m_h = _arr(D, "hayne",    "T_mean_1m")
        _,      T2m_h = _arr(D, "hayne",    "T_mean_2m")
        _,      T1m_m = _arr(D, "martinez", "T_mean_1m")
        _,      T2m_m = _arr(D, "martinez", "T_mean_2m")

        lat_plot = np.abs(lats_h)
        dT_1m = T1m_m - T1m_h
        dT_2m = T2m_m - T2m_h

        ax.plot(lat_plot, dT_1m, color=COLORS["hayne"], lw=1.7,
                label="ΔT at z=1 m")
        ax.plot(lat_plot, dT_2m, color=COLORS["ms"],    lw=1.7,
                label="ΔT at z=2 m")
        ax.axhline(0, color="0.6", lw=0.7, ls=":")
        ax.set_title(f"D = {D}")
        ax.set_xlabel("|Latitude| (°S)")
        ax.set_ylabel("ΔT = T(M&S) − T(Hayne)  (K)")
        ax.set_xlim(75, 90)

    legend_below(axes9[0], ncol=2, pad=0.22)
    fig9.suptitle(
        "Crater ΔT (M&S − Hayne) at 1m & 2m — Fig 9 of Martinez & Siegler (2021)",
        fontsize=13,
    )
    p9 = out_dir / "phase2_fig9_crater_dT.pdf"
    savefig_pair(fig9, p9)
    plt.close(fig9)
    print(f"Saved {p9.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
