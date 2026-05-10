"""Figure 5 of Phase 2 — nighttime diurnal at 4 latitudes, Hayne vs M&S.

Reproduces Martinez & Siegler (2021) Fig 5: a 2×2 panel of surface
temperature vs local time (nighttime zoom) at:
  - 45° N highlands  (A0=0.12)
  - 70° N highlands  (A0=0.12)
  - 30° N mare       (A0=0.07)
  - 60° N mare       (A0=0.07)

Diviner T7 (10–12 µm) is overlaid where the GCP band file is present.
The script runs gracefully without Diviner; a warning is printed instead.

Output: ``output/figures/phase2_fig5_multilat_diurnal.{pdf,png}``
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

# The four published latitudes (lat_deg, albedo, terrain_label, diviner_band)
CASES = [
    (45.0, 0.12, "45° N highlands",  (40, 50)),
    (70.0, 0.12, "70° N highlands",  (60, 70)),
    (30.0, 0.07, "30° N mare",       (20, 30)),
    (60.0, 0.07, "60° N mare",       (50, 60)),
]


def vasavada_albedo(cos_i: np.ndarray, A0: float) -> np.ndarray:
    i = np.arccos(np.clip(cos_i, 0.0, 1.0))
    return np.minimum(0.5, A0 + 0.06 * i ** 3 + 0.25 * i ** 8)


def _run_one_case(lat_deg: float, A0: float, K_func_name: str) -> dict:
    """Worker: run the solver at one lat × K model. Returns surface T array."""
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
    T_init_guess = max(150.0, 270.0 - abs(lat_deg) * 1.5)

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
    return {
        "lat": lat_deg, "model": K_func_name,
        "T_surface": out.T_surface.tolist(),
        "t": t.tolist(),
        "converged": out.converged,
        "n_spinup": out.n_spinup_cycles,
    }


def _load_diviner(lat_band: tuple[int, int], lat_deg: float) -> tuple | None:
    """Return (LT, T) Diviner T7 array or None if data not on disk."""
    try:
        from lunar.diviner import load_gcp_band, select_diurnal_curve
        band = load_gcp_band(lat_band[0], lat_band[1], columns=("t7",))
        return select_diurnal_curve(band, latitude=lat_deg, channel="t7",
                                    half_width_deg=0.5)
    except FileNotFoundError:
        return None


def main() -> int:
    print("Running 4 latitudes × 2 K models (parallel workers):")
    tasks = [
        (lat, A0, model)
        for lat, A0, _, _ in CASES
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
                f"spinup={r['n_spinup']} cycles, converged={r['converged']}"
            )

    apply_phase2_style()
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.0))

    for idx, (lat, A0, label, div_band) in enumerate(CASES):
        ax = axes.flat[idx]
        r_h = results[(lat, "hayne")]
        r_m = results[(lat, "martinez")]

        t = np.array(r_h["t"])
        T_LUNAR_s = T_LUNAR
        LT = (12.0 + 24.0 * t / T_LUNAR_s) % 24.0
        LT_wrap = np.where(LT <= 8, LT + 24, LT)
        night = (LT >= 16) | (LT <= 8)
        order = np.argsort(LT_wrap[night])

        ax.plot(LT_wrap[night][order], np.array(r_h["T_surface"])[night][order],
                color=COLORS["hayne"], lw=1.7, label="Hayne χ-T³")
        ax.plot(LT_wrap[night][order], np.array(r_m["T_surface"])[night][order],
                color=COLORS["ms"], lw=1.7, label="Martinez & Siegler K(T,ρ)")

        # Diviner overlay (optional)
        div = _load_diviner(div_band, lat)
        if div is not None:
            LT_d, T_d = div
            LT_d_w = np.where(LT_d <= 8, LT_d + 24, LT_d)
            nd = (LT_d >= 16) | (LT_d <= 8)
            ax.scatter(LT_d_w[nd], T_d[nd], s=14, color=COLORS["diviner"],
                       zorder=3, label="Diviner T7")
        else:
            ax.text(0.97, 0.95, "Diviner: not downloaded",
                    transform=ax.transAxes, ha="right", va="top",
                    fontsize=8, color="0.5")

        ax.set_title(label)
        ax.set_xlim(16, 32)
        ax.set_xticks([16, 18, 20, 22, 24, 26, 28, 30, 32])
        ax.set_xticklabels(["16", "18", "20", "22", "00", "02", "04", "06", "08"])
        ax.set_xlabel("Local time")
        ax.set_ylabel("Surface T (K)")

    # Single shared legend on first panel
    legend_below(axes[0, 0], ncol=3, pad=0.22)

    fig.suptitle(
        "Nighttime T_s at 4 latitudes — Fig 5 of Martinez & Siegler (2021)",
        fontsize=13,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig5_multilat_diurnal.pdf"
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"\nSaved {out_path.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
