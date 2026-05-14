"""Figure 7 of Phase 2 — mean T vs latitude, the headline global result.

Reproduces Martinez & Siegler (2021) Fig 7: mean surface temperature and
mean T at z=1m plotted vs latitude (0°–80°N) for both K models and both
terrain types (highlands A0=0.12, mare A0=0.07).

Apollo 15/17 HFE subsurface validation markers are plotted at:
  - Apollo 15: 26.1° N,  ~252 K mean at z=1 m (Nagihara et al. 2018)
  - Apollo 17: 20.2° N,  ~255 K mean at z=1 m (Nagihara et al. 2018)

Diviner Tbol band-mean is overlaid where GCP data are on disk; a note is
printed instead if missing.

Parallelism: uses ProcessPoolExecutor over 17 latitudes × 2 K models ×
2 terrain types = 68 solver calls. Runtime ~1-4 hours depending on core
count and whether Numba JIT is available.

Output: ``output/figures/phase2_fig7_latitude_sweep.{pdf,png}``
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

# Latitude grid: 0° to 80° in 5° steps  (17 points)
LAT_GRID = np.arange(0.0, 81.0, 5.0)

# Apollo HFE sites (Nagihara et al. 2018, JGR:Planets 123, 1125-1139)
APOLLO_15 = {"lat": 26.1, "T_1m_K": 252.0, "label": "Apollo 15 HFE (~1 m)"}
APOLLO_17 = {"lat": 20.2, "T_1m_K": 255.0, "label": "Apollo 17 HFE (~1 m)"}

A0_HIGHLANDS = 0.12   # Hayne 2017 Table 1
A0_MARE = 0.07        # Martinez & Siegler 2021


def _run_one(lat_deg: float, A0: float, K_func_name: str) -> dict:
    """Process-pool worker: solve at one (lat, terrain, K-model) triple."""
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

    T_LUNAR = 29.530589 * 86400.0
    DT = 300.0

    K_func = conductivity_hayne if K_func_name == "hayne" else conductivity_martinez
    T_guess = max(90.0, 270.0 - abs(lat_deg) * 2.0)

    n_t = int(1 * T_LUNAR / DT) + 1
    t = np.linspace(0.0, T_LUNAR, n_t)
    phase = 2.0 * np.pi * t / T_LUNAR
    cos_lat = np.cos(np.deg2rad(lat_deg))
    cos_zenith = np.maximum(0.0, cos_lat * np.cos(phase))
    i_arr = np.arccos(np.clip(cos_zenith, 0.0, 1.0))
    A_of_t = np.minimum(0.5, A0 + 0.06 * i_arr ** 3 + 0.25 * i_arr ** 8)
    insolation = (1.0 - A_of_t) * SOLAR_CONSTANT * cos_zenith

    grid = make_geometric_grid()
    K_init = K_func(np.full_like(grid.z_mid, T_guess), grid.z_mid)
    R_z = np.cumsum(grid.dz / K_init)
    T_init = T_guess + Q_B_EQUATORIAL * R_z

    inp = PixelInputs(
        grid=grid, t=t, bc_mode="radiative",
        insolation=insolation, albedo=0.0, emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL, K_func=K_func,
        rho_func=lambda z: density_hayne(z),
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=80,
        spinup_tol_K=0.01,
        spinup_depth_m=0.10,
    )
    out = solve_pixel(inp)
    T_mean_s = float(out.T_surface.mean())
    # Mean T at z ≈ 1 m (interpolate from cell-midpoint grid)
    T_mean_1m = float(np.interp(1.0, out.z, out.T.mean(axis=1)))
    return {
        "lat": lat_deg, "A0": A0, "model": K_func_name,
        "T_mean_s": T_mean_s,
        "T_mean_1m": T_mean_1m,
        "converged": out.converged,
        "n_spinup": out.n_spinup_cycles,
    }


def _load_diviner_mean(lat: float) -> float | None:
    """Return Diviner Tbol mean at ±0.5° of lat, or None if not on disk."""
    band_lo = int(np.floor(lat / 10.0)) * 10
    band_hi = band_lo + 10
    try:
        from lunar.diviner import load_gcp_band, select_diurnal_curve
        band = load_gcp_band(band_lo, band_hi, columns=("tbol",))
        LT, T = select_diurnal_curve(band, latitude=lat, channel="tbol",
                                     half_width_deg=0.5)
        return float(T.mean()) if T.size > 0 else None
    except (FileNotFoundError, KeyError):
        return None


def main() -> int:
    t0_wall = time.time()
    print(f"Latitude sweep: {LAT_GRID[0]:.0f}°–{LAT_GRID[-1]:.0f}°, "
          f"{len(LAT_GRID)} points × 2 models × 2 terrains "
          f"= {len(LAT_GRID)*4} solver calls")

    tasks = [
        (lat, A0, model, terrain)
        for lat in LAT_GRID
        for terrain, A0 in [("highlands", A0_HIGHLANDS), ("mare", A0_MARE)]
        for model in ("hayne", "martinez")
    ]

    results: list[dict] = []
    done = 0
    with ProcessPoolExecutor() as ex:
        futs = {ex.submit(_run_one, lat, A0, mdl): (lat, A0, mdl, ter)
                for lat, A0, mdl, ter in tasks}
        for fut in as_completed(futs):
            lat, A0, mdl, ter = futs[fut]
            r = fut.result()
            r["terrain"] = ter
            results.append(r)
            done += 1
            elapsed = time.time() - t0_wall
            eta = elapsed / done * (len(tasks) - done)
            print(
                f"  [{done:>2d}/{len(tasks)}] lat={lat:+.0f}° {ter:>9s} {mdl:>10s}: "
                f"T_mean={r['T_mean_s']:.1f} K  T_1m={r['T_mean_1m']:.1f} K  "
                f"ETA {eta/60:.0f} min"
            )

    print(f"\nTotal runtime: {(time.time()-t0_wall)/60:.1f} min")

    # --- Optional Diviner mean T_bol per latitude ---
    div_lats, div_Ts = [], []
    for lat in LAT_GRID:
        Td = _load_diviner_mean(lat)
        if Td is not None:
            div_lats.append(lat)
            div_Ts.append(Td)
    has_diviner = len(div_lats) > 0

    # --- Organise results into arrays ---
    def _arr(terrain: str, model: str, key: str) -> np.ndarray:
        vals = [r[key] for r in results
                if r["terrain"] == terrain and r["model"] == model]
        lats = [r["lat"] for r in results
                if r["terrain"] == terrain and r["model"] == model]
        order = np.argsort(lats)
        return np.array(vals)[order]

    lats_sorted = np.sort(LAT_GRID)

    Ts_hl_h  = _arr("highlands", "hayne",    "T_mean_s")
    Ts_hl_m  = _arr("highlands", "martinez", "T_mean_s")
    Ts_ma_h  = _arr("mare",      "hayne",    "T_mean_s")
    Ts_ma_m  = _arr("mare",      "martinez", "T_mean_s")

    T1_hl_h  = _arr("highlands", "hayne",    "T_mean_1m")
    T1_hl_m  = _arr("highlands", "martinez", "T_mean_1m")
    T1_ma_h  = _arr("mare",      "hayne",    "T_mean_1m")
    T1_ma_m  = _arr("mare",      "martinez", "T_mean_1m")

    # --- Plot ---
    apply_phase2_style()
    fig, (ax_s, ax_1m) = plt.subplots(1, 2, figsize=(14.0, 5.8))

    for ax, (Yhl_h, Yhl_m, Yma_h, Yma_m), ylabel, title in [
        (ax_s,
         (Ts_hl_h, Ts_hl_m, Ts_ma_h, Ts_ma_m),
         "Mean surface T (K)",
         "Mean surface T vs latitude"),
        (ax_1m,
         (T1_hl_h, T1_hl_m, T1_ma_h, T1_ma_m),
         "Mean T at z=1 m (K)",
         "Mean T at 1 m depth vs latitude"),
    ]:
        ax.plot(lats_sorted, Yhl_h, color=COLORS["hayne"],
                lw=1.8, ls="-",  label="Hayne — highlands")
        ax.plot(lats_sorted, Yhl_m, color=COLORS["ms"],
                lw=1.8, ls="-",  label="M&S — highlands")
        ax.plot(lats_sorted, Yma_h, color=COLORS["hayne"],
                lw=1.8, ls="--", label="Hayne — mare")
        ax.plot(lats_sorted, Yma_m, color=COLORS["ms"],
                lw=1.8, ls="--", label="M&S — mare")
        ax.set_xlabel("Latitude (°N)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xlim(0, 80)

    # Diviner mean Tbol overlay on surface panel
    if has_diviner:
        ax_s.scatter(div_lats, div_Ts, s=20, color=COLORS["diviner"],
                     zorder=4, label="Diviner Tbol (mean)")
    else:
        ax_s.text(0.97, 0.97, "Diviner: not downloaded",
                  transform=ax_s.transAxes, ha="right", va="top",
                  fontsize=8, color="0.5")

    # Apollo HFE subsurface markers on 1-m panel (Nagihara et al. 2018)
    for ap in (APOLLO_15, APOLLO_17):
        ax_1m.scatter([ap["lat"]], [ap["T_1m_K"]], s=80,
                      color=COLORS["apollo"], marker="*", zorder=5,
                      label=ap["label"])

    legend_below(ax_s, ncol=3, pad=0.22)
    legend_below(ax_1m, ncol=3, pad=0.22)

    fig.suptitle(
        "Mean T vs latitude — Fig 7 of Martinez & Siegler (2021)",
        fontsize=13,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig7_latitude_sweep.pdf"
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"Saved {out_path.relative_to(_REPO_ROOT)}")

    # Print numerical table
    print(f"\n{'Lat':>5}  {'Ts Hl-H':>9}  {'Ts Hl-M':>9}  "
          f"{'T1m Hl-H':>10}  {'T1m Hl-M':>10}")
    print("-" * 55)
    for i, lat in enumerate(lats_sorted):
        print(f"{lat:5.1f}  {Ts_hl_h[i]:9.1f}  {Ts_hl_m[i]:9.1f}  "
              f"{T1_hl_h[i]:10.1f}  {T1_hl_m[i]:10.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
