"""Figure 2 of Phase 2 — 45 deg N highlands diurnal curve.

Reproduces Martinez & Siegler (2021) LPSC abstract Fig 2: surface
temperature vs local time at a 45 deg N highlands site, comparing the
standard Hayne (2017) chi-T^3 thermal model against the Martinez &
Siegler density-and-temperature-dependent model, with Diviner T7 (10-12
um, ~93-275 K mid-band) brightness temperatures overlaid.

The replication uses:
- Phase 1 Crank-Nicolson solver (lunar.solver.solve_pixel)
- M&S K(T, rho) via lunar.properties.conductivity_martinez
- Hayne density(z) and specific-heat(T) (Phase 1 defaults)
- Q_b = 0.018 W/m^2 (Martinez global mean; lunar.constants.Q_B_EQUATORIAL)
- A = 0.12 highlands (scalar; Feng (2020) angle-dep is a future refinement)
- 30-lunation spin-up to dT < 1e-5 K

Output: ``output/figures/phase2_fig2_diurnal_45N.{pdf,png}``
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import (
    EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SOLAR_CONSTANT,
)
from lunar.diviner import load_gcp_band, select_diurnal_curve
from lunar.grid import make_geometric_grid
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

# Lunar synodic period [s]: 29.530589 days x 86400 s/day.
T_LUNAR = 29.530589 * 86400.0  # 2551443.84 s
LATITUDE_DEG = 45.0
ALBEDO = 0.12          # highlands scalar; cf. Feng 2020 angle-dep
N_LUNATIONS = 1        # report one lunation of output
DT = 300.0             # 5-minute timesteps
SPINUP_LUNATIONS = 30
SPINUP_TOL_K = 1e-5
T_INIT_GUESS = 220.0   # near steady-state mean for 45 deg N


def _build_inputs(K_func, label: str, t_array, insolation):
    grid = make_geometric_grid()
    rho_z = density_hayne(grid.z_mid)
    K_init = K_func(np.full_like(grid.z_mid, T_INIT_GUESS), grid.z_mid)
    R_z = np.cumsum(grid.dz / K_init)            # thermal resistance to depth
    T_init = T_INIT_GUESS + Q_B_EQUATORIAL * R_z  # Q*R warming with depth
    return PixelInputs(
        grid=grid,
        t=t_array,
        bc_mode="radiative",
        insolation=insolation,
        albedo=ALBEDO,
        emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL,
        K_func=K_func,
        rho_func=lambda z: rho_z,
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=SPINUP_LUNATIONS,
        spinup_tol_K=SPINUP_TOL_K,
    ), label


def _run(inputs: PixelInputs, label: str):
    t0 = time.time()
    out = solve_pixel(inputs)
    dt = time.time() - t0
    print(
        f"  {label:>12s}: spinup={out.n_spinup_cycles:>2d} lunations, "
        f"converged={out.converged}, runtime={dt:.1f} s"
    )
    return out


def main() -> int:
    # Time array & insolation (one lunation, t=0 == solar noon)
    n_t = int(N_LUNATIONS * T_LUNAR / DT) + 1
    t = np.linspace(0.0, N_LUNATIONS * T_LUNAR, n_t)
    phase = 2.0 * np.pi * t / T_LUNAR
    cos_lat = np.cos(np.deg2rad(LATITUDE_DEG))
    insolation = SOLAR_CONSTANT * cos_lat * np.maximum(0.0, np.cos(phase))
    print(f"Grid points: {n_t}, max insolation: {insolation.max():.0f} W/m^2")

    # Solver runs — Hayne (chi-T^3) and M&S (density-temperature) K models
    print("Running Phase 1 solver:")
    inputs_h, _ = _build_inputs(conductivity_hayne, "Hayne", t, insolation)
    out_h = _run(inputs_h, "Hayne")
    inputs_m, _ = _build_inputs(conductivity_martinez, "Martinez", t, insolation)
    out_m = _run(inputs_m, "Martinez")

    # Convert physical time -> local time. t=0 is solar noon, so:
    LT_model = (12.0 + 24.0 * t / T_LUNAR) % 24.0
    order = np.argsort(LT_model)
    LT_model = LT_model[order]
    Ts_h = out_h.T_surface[order]
    Ts_m = out_m.T_surface[order]

    # Diviner T7 diurnal at 45.25 deg N (single 0.5 deg row)
    print("Loading Diviner 40-50 N band, extracting 45 N diurnal...")
    band = load_gcp_band(40, 50, columns=("t7",))
    LT_div, T_div = select_diurnal_curve(
        band, latitude=45.25, channel="t7", half_width_deg=0.25
    )
    print(f"  Diviner T7 at 45 N: {T_div.size} LT bins, "
          f"range {T_div.min():.1f}-{T_div.max():.1f} K")

    # Plot — full diurnal panel + nighttime zoom
    fig, axes = plt.subplots(
        1, 2, figsize=(11.5, 4.3), constrained_layout=True
    )
    for ax in axes:
        ax.scatter(
            LT_div, T_div, s=18, color="0.25", marker="o",
            label="Diviner T7 (Williams et al. 2017)", zorder=3,
        )
        ax.plot(LT_model, Ts_h, color="#d62728", lw=1.6,
                label="Hayne χ-T³ (Phase 1 default)")
        ax.plot(LT_model, Ts_m, color="#1f77b4", lw=1.6,
                label="Martinez & Siegler K(T, ρ)")
        ax.grid(alpha=0.3)
        ax.set_xlabel("Local time (hours)", fontsize=11)
        ax.set_ylabel("Surface T (K)", fontsize=11)

    axes[0].set_title("Full diurnal cycle, 45° N highlands")
    axes[0].set_xlim(0, 24)
    axes[0].legend(loc="upper right", fontsize=9, framealpha=0.9)

    axes[1].set_title("Nighttime zoom (LT 16:00 – 08:00)")
    nightmask = (LT_model >= 16) | (LT_model <= 8)
    axes[1].set_xlim(16, 32)  # wrap LT axis: 16->8 = 16->24->32
    # Reflect the 0-8 wrap onto the 24-32 axis for visual continuity
    LT_wrap = np.where(LT_model <= 8, LT_model + 24, LT_model)
    order_n = np.argsort(LT_wrap[nightmask])
    axes[1].plot(LT_wrap[nightmask][order_n], Ts_h[nightmask][order_n],
                 color="#d62728", lw=1.6)
    axes[1].plot(LT_wrap[nightmask][order_n], Ts_m[nightmask][order_n],
                 color="#1f77b4", lw=1.6)
    LT_div_wrap = np.where(LT_div <= 8, LT_div + 24, LT_div)
    night_div = (LT_div >= 16) | (LT_div <= 8)
    axes[1].scatter(LT_div_wrap[night_div], T_div[night_div],
                    s=18, color="0.25", zorder=3)
    axes[1].set_xticks([16, 18, 20, 22, 24, 26, 28, 30, 32])
    axes[1].set_xticklabels(["16", "18", "20", "22", "00", "02", "04", "06", "08"])

    fig.suptitle(
        "Phase 2 Fig. 2 — 45° N highlands surface T: Hayne vs M&S vs Diviner",
        fontsize=12,
    )

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig2_diurnal_45N.pdf"
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=150)
    plt.close(fig)
    print(f"Saved {out_path.relative_to(_REPO_ROOT)}")

    # Summary stats — RMSE/bias of each model vs Diviner
    # Interpolate model surface T to Diviner LT bins for direct comparison.
    Ts_h_atDiv = np.interp(LT_div, LT_model, Ts_h)
    Ts_m_atDiv = np.interp(LT_div, LT_model, Ts_m)
    rmse_h = np.sqrt(np.mean((Ts_h_atDiv - T_div) ** 2))
    rmse_m = np.sqrt(np.mean((Ts_m_atDiv - T_div) ** 2))
    bias_h = np.mean(Ts_h_atDiv - T_div)
    bias_m = np.mean(Ts_m_atDiv - T_div)
    print(f"vs Diviner T7 (full diurnal, n={T_div.size}):")
    print(f"  Hayne     RMSE {rmse_h:5.1f} K, bias {bias_h:+5.1f} K")
    print(f"  Martinez  RMSE {rmse_m:5.1f} K, bias {bias_m:+5.1f} K")

    # Nighttime-only stats (where M&S is supposed to win)
    night_div = (LT_div >= 16) | (LT_div <= 8)
    rmse_h_n = np.sqrt(np.mean((Ts_h_atDiv[night_div] - T_div[night_div]) ** 2))
    rmse_m_n = np.sqrt(np.mean((Ts_m_atDiv[night_div] - T_div[night_div]) ** 2))
    print(f"Nighttime only (LT 16-08, n={night_div.sum()}):")
    print(f"  Hayne     RMSE {rmse_h_n:5.1f} K")
    print(f"  Martinez  RMSE {rmse_m_n:5.1f} K  (target: ~5 K lower than Hayne)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
