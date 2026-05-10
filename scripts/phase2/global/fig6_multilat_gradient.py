"""Figure 6 of Phase 2 — T(z) subsurface gradients at 4 latitudes.

Reproduces Martinez & Siegler (2021) Fig 6: subsurface temperature profiles
T(z) at the same four latitudes as Fig 5. The profiles use the time-mean
surface temperature from the converged spin-up run as a Dirichlet BC, then
integrate dT/dz = Q_b / K(T, z) downward with RK4.

The four latitudes (from the action plan, matching the paper):
  - 45° N highlands  (A0=0.12)
  - 70° N highlands  (A0=0.12)
  - 30° N mare       (A0=0.07)
  - 60° N mare       (A0=0.07)

Each panel shows Hayne vs M&S T(z) with depth inverted (surface at top).

Output: ``output/figures/phase2_fig6_multilat_gradient.{pdf,png}``
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

from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SOLAR_CONSTANT
from lunar.grid import make_geometric_grid
from lunar.phase2_plotting import COLORS, apply_phase2_style, legend_below, savefig_pair
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

T_LUNAR = 29.530589 * 86400.0
DT = 300.0
SPINUP_LUNATIONS = 80
SPINUP_TOL_K = 0.01
SPINUP_DEPTH_M = 0.10
N_LUNATIONS = 1

CASES = [
    (45.0, 0.12, "45° N highlands"),
    (70.0, 0.12, "70° N highlands"),
    (30.0, 0.07, "30° N mare"),
    (60.0, 0.07, "60° N mare"),
]


def _run_one_case(lat_deg: float, A0: float, K_func_name: str) -> dict:
    """Worker: run solver, return mean T_surface and T(z) profile."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SOLAR_CONSTANT
    from lunar.grid import make_geometric_grid
    from lunar.properties import (
        conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
    )
    from lunar.solver import PixelInputs, solve_pixel
    import numpy as np

    K_func = conductivity_hayne if K_func_name == "hayne" else conductivity_martinez
    T_init_guess = max(100.0, 270.0 - abs(lat_deg) * 1.5)

    n_t = int(N_LUNATIONS * T_LUNAR / DT) + 1
    t = np.linspace(0.0, N_LUNATIONS * T_LUNAR, n_t)
    phase = 2.0 * np.pi * t / T_LUNAR
    cos_lat = np.cos(np.deg2rad(lat_deg))
    cos_zenith = np.maximum(0.0, cos_lat * np.cos(phase))
    i_arr = np.arccos(np.clip(cos_zenith, 0.0, 1.0))
    A_of_t = np.minimum(0.5, A0 + 0.06 * i_arr ** 3 + 0.25 * i_arr ** 8)
    insolation = (1.0 - A_of_t) * SOLAR_CONSTANT * cos_zenith

    grid = make_geometric_grid()
    K_init = K_func(np.full_like(grid.z_mid, T_init_guess), grid.z_mid)
    R_z = np.cumsum(grid.dz / K_init)
    T_init = T_init_guess + Q_B_EQUATORIAL * R_z

    inp = PixelInputs(
        grid=grid, t=t, bc_mode="radiative",
        insolation=insolation, albedo=0.0, emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL, K_func=K_func,
        rho_func=lambda z: density_hayne(z),
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=SPINUP_LUNATIONS,
        spinup_tol_K=SPINUP_TOL_K,
        spinup_depth_m=SPINUP_DEPTH_M,
    )
    out = solve_pixel(inp)
    # Time-mean T(z) — the steady profile over the final lunation
    T_mean_z = out.T.mean(axis=1)   # shape (N_z,)
    T_mean_s = float(out.T_surface.mean())
    return {
        "lat": lat_deg, "model": K_func_name,
        "T_mean_z": T_mean_z.tolist(),
        "T_mean_s": T_mean_s,
        "z_mid": out.z.tolist(),
        "converged": out.converged,
        "n_spinup": out.n_spinup_cycles,
    }


def main() -> int:
    print("Running 4 latitudes × 2 K models (parallel workers):")
    tasks = [
        (lat, A0, model)
        for lat, A0, _ in CASES
        for model in ("hayne", "martinez")
    ]

    results: dict[tuple, dict] = {}
    with ProcessPoolExecutor() as ex:
        futs = {ex.submit(_run_one_case, lat, A0, mdl): (lat, mdl)
                for lat, A0, mdl in tasks}
        for fut in as_completed(futs):
            key = futs[fut]
            r = fut.result()
            results[key] = r
            print(
                f"  lat={key[0]:+.0f}° {key[1]:>10s}: "
                f"T_mean={r['T_mean_s']:.1f} K, "
                f"spinup={r['n_spinup']}, converged={r['converged']}"
            )

    apply_phase2_style()
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 10.0))

    for idx, (lat, A0, label) in enumerate(CASES):
        ax = axes.flat[idx]
        r_h = results[(lat, "hayne")]
        r_m = results[(lat, "martinez")]

        z = np.array(r_h["z_mid"])
        Tz_h = np.array(r_h["T_mean_z"])
        Tz_m = np.array(r_m["T_mean_z"])

        ax.plot(Tz_h, z, color=COLORS["hayne"], lw=1.7, label="Hayne χ-T³")
        ax.plot(Tz_m, z, color=COLORS["ms"], lw=1.7, label="Martinez & Siegler K(T,ρ)")
        ax.invert_yaxis()
        ax.set_title(label)
        ax.set_xlabel("Mean T (K)")
        ax.set_ylabel("Depth (m)")

        # Print numerical summary to stdout
        for z_t in (0.0, 0.5, 1.0, 2.0):
            Th = float(np.interp(z_t, z, Tz_h))
            Tm = float(np.interp(z_t, z, Tz_m))
            print(f"  {label}: z={z_t:.1f} m  Hayne={Th:.1f} K  M&S={Tm:.1f} K  ΔT={Tm-Th:+.2f} K")

    legend_below(axes[0, 0], ncol=2, pad=0.22)

    fig.suptitle(
        "Mean T(z) profiles at 4 latitudes — Fig 6 of Martinez & Siegler (2021)",
        fontsize=13,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig6_multilat_gradient.pdf"
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"\nSaved {out_path.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
