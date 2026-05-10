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
- Vasavada (2012) angle-dependent Bond albedo
  A(i) = A0 + 0.06 i^3 + 0.25 i^8, A0=0.12 highlands, baked into the
  insolation array (PixelInputs.albedo=0) so the angular dependence
  matches the radiative BC without solver changes
- 80-lunation spin-up with the top-only convergence criterion:
  surface-cell delta T < 0.01 K (deep cells equilibrate over centuries,
  irrelevant for diurnal validation; see solver.py spinup_depth_m)

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

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import (
    EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SOLAR_CONSTANT,
)
from lunar.diviner import load_gcp_band, select_diurnal_curve
from lunar.phase2_plotting import (
    COLORS, apply_phase2_style, legend_below, savefig_pair,
)
from lunar.grid import make_geometric_grid
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

# Lunar synodic period [s]: 29.530589 days x 86400 s/day.
T_LUNAR = 29.530589 * 86400.0  # 2551443.84 s
LATITUDE_DEG = 45.0
A0_HIGHLANDS = 0.12           # Hayne 2017 small-i Bond albedo (highlands)
N_LUNATIONS = 1               # report one lunation of output
DT = 300.0                    # 5-minute timesteps
SPINUP_LUNATIONS = 80
SPINUP_TOL_K = 0.01           # surface-cell convergence target
SPINUP_DEPTH_M = 0.10         # diurnal skin depth at lunar K, rho-cp
T_INIT_GUESS = 220.0          # near steady-state mean for 45 deg N


def vasavada_albedo(cos_i: np.ndarray, A0: float = A0_HIGHLANDS) -> np.ndarray:
    """Vasavada (2012) angle-dependent Bond albedo, clamped at 0.5.

    A(i) = A0 + 0.06 i^3 + 0.25 i^8, with the incidence angle i in
    radians. Diverges past i ~ 80 deg; clamping at 0.5 is the standard
    upper bound used in lunar thermal modelling.
    """
    i = np.arccos(np.clip(cos_i, 0.0, 1.0))
    return np.minimum(0.5, A0 + 0.06 * i ** 3 + 0.25 * i ** 8)


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
        insolation=insolation,        # already (1-A_Vasavada) * S0 * cos i
        albedo=0.0,                   # angle-dep A is baked into insolation
        emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL,
        K_func=K_func,
        rho_func=lambda z: rho_z,
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=SPINUP_LUNATIONS,
        spinup_tol_K=SPINUP_TOL_K,
        spinup_depth_m=SPINUP_DEPTH_M,
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
    # Time array, insolation, and angle-dep albedo absorption.
    # t=0 == solar noon; cos_zenith = cos(lat) * cos(2 pi t / T_lunar).
    n_t = int(N_LUNATIONS * T_LUNAR / DT) + 1
    t = np.linspace(0.0, N_LUNATIONS * T_LUNAR, n_t)
    phase = 2.0 * np.pi * t / T_LUNAR
    cos_lat = np.cos(np.deg2rad(LATITUDE_DEG))
    cos_zenith = np.maximum(0.0, cos_lat * np.cos(phase))
    A_of_t = vasavada_albedo(cos_zenith, A0=A0_HIGHLANDS)
    # Bake (1-A) into the absorbed-insolation array so the solver's
    # scalar-albedo BC (with albedo=0) reproduces the angle-dep result.
    insolation = (1.0 - A_of_t) * SOLAR_CONSTANT * cos_zenith
    print(
        f"Grid points: {n_t}, "
        f"peak cos_zenith = {cos_zenith.max():.3f} "
        f"(=> noon A = {A_of_t[cos_zenith.argmax()]:.3f}), "
        f"peak absorbed = {insolation.max():.0f} W/m^2"
    )

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
    apply_phase2_style()
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for ax in axes:
        ax.scatter(
            LT_div, T_div, s=18, color=COLORS["diviner"], marker="o",
            label="Diviner T7 (Williams et al. 2017)", zorder=3,
        )
        ax.plot(LT_model, Ts_h, color=COLORS["hayne"], lw=1.7,
                label="Hayne χ-T³ (Phase 1 default)")
        ax.plot(LT_model, Ts_m, color=COLORS["ms"], lw=1.7,
                label="Martinez & Siegler K(T, ρ)")
        ax.set_xlabel("Local time (hours)")
        ax.set_ylabel("Surface T (K)")

    axes[0].set_title("Full diurnal cycle, 45° N highlands")
    axes[0].set_xlim(0, 24)

    axes[1].set_title("Nighttime zoom (LT 16:00 – 08:00)")
    nightmask = (LT_model >= 16) | (LT_model <= 8)
    axes[1].set_xlim(16, 32)
    LT_wrap = np.where(LT_model <= 8, LT_model + 24, LT_model)
    order_n = np.argsort(LT_wrap[nightmask])
    axes[1].plot(LT_wrap[nightmask][order_n], Ts_h[nightmask][order_n],
                 color=COLORS["hayne"], lw=1.7)
    axes[1].plot(LT_wrap[nightmask][order_n], Ts_m[nightmask][order_n],
                 color=COLORS["ms"], lw=1.7)
    LT_div_wrap = np.where(LT_div <= 8, LT_div + 24, LT_div)
    night_div = (LT_div >= 16) | (LT_div <= 8)
    axes[1].scatter(LT_div_wrap[night_div], T_div[night_div],
                    s=18, color=COLORS["diviner"], zorder=3)
    axes[1].set_xticks([16, 18, 20, 22, 24, 26, 28, 30, 32])
    axes[1].set_xticklabels(["16", "18", "20", "22", "00", "02", "04", "06", "08"])

    fig.suptitle(
        "45° N highlands surface T: Hayne vs M&S vs Diviner  (Fig 5a of M&S 2021)",
        fontsize=12, y=0.99,
    )

    legend_below(axes[0], ncol=3, pad=0.20)

    out_dir = _REPO_ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase2_fig2_diurnal_45N.pdf"
    savefig_pair(fig, out_path)
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
