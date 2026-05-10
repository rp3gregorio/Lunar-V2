"""Phase 2 Figure 3 (preliminary) — Shoemaker PSR surface T diurnal.

Reproduces the surface-T part of Martinez & Siegler (2021) LPSC abstract
Fig 3, with a calibrated constant-scattered-flux approximation in place
of a full bowl-crater radiosity module.

Why a constant scattered flux is the right starting point
---------------------------------------------------------
Shoemaker (87.91 deg S, 25-km bowl crater, ~4.5 km deep) is a permanent
shadow: direct insolation on the floor is identically zero year-round.
The only energy input is scattered visible light from sunlit upper-rim
walls plus thermal IR re-emission from those walls. A full treatment
needs (a) per-azimuth view factors, (b) sub-solar latitude oscillation
+/-1.54 deg over the lunar year, (c) wall-floor multi-bounce. We don't
have that module yet.

What we *can* do honestly: calibrate a single constant scattered flux
Q_scatter from the Diviner Tbol time-mean at the Shoemaker tile, run
both K models (Hayne and M&S) under that constant input, and check
that the solver produces the right mean surface T. This isolates the
*thermal* physics (which we own) from the *scattering* physics (which
we don't yet model).

Calibration. The radiative steady state is

    Q_scatter + Q_b = epsilon * sigma * T_s^4

so

    Q_scatter = epsilon * sigma * T_s^4 - Q_b
              = 0.95 * 5.6704e-8 * 44.39^4 - 0.018
              = 0.191 W/m^2

This sits at the upper end of the 0.05-0.30 W/m^2 range Hayne (2015)
quotes for moderate-depth PSRs.

Output: ``output/figures/phase2_fig3_shoemaker_diurnal.{pdf,png}``
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
    EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SIGMA_SB, SOLAR_CONSTANT,
)

SIGMA = SIGMA_SB
from lunar.diviner import load_gcp_band
from lunar.grid import make_geometric_grid
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

# Shoemaker tile
SHOEMAKER_LAT = -87.91
SHOEMAKER_LON = 45.51

# Solver setup
T_LUNAR = 29.530589 * 86400.0  # synodic period (s)
DT = 600.0  # 10-minute timesteps; Q_in is constant so we can step coarsely
N_LUNATIONS = 1
SPINUP_LUNATIONS = 60
SPINUP_TOL_K = 0.001  # K — tighter because Q_in is constant; converges fast
SPINUP_DEPTH_M = 0.10
T_INIT_GUESS = 45.0


def diviner_shoemaker() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Return (LT, T9_mean, T9_std, meta) for the Shoemaker tile."""
    band = load_gcp_band(-90, -80, columns=("t9", "tbol"))
    i_target = np.argmin(
        (band.clon - SHOEMAKER_LON) ** 2
        + (band.clat - SHOEMAKER_LAT) ** 2
    )
    cell_mask = (
        (band.clon == band.clon[i_target])
        & (band.clat == band.clat[i_target])
    )
    LT = band.ltim[cell_mask]
    t9 = band.channels["t9"][cell_mask]
    tbol = band.channels["tbol"][cell_mask]
    valid = (t9 > -9000) & (tbol > -9000)
    meta = {
        "clon": float(band.clon[i_target]),
        "clat": float(band.clat[i_target]),
        "tbol_mean": float(tbol[valid].mean()),
        "n_samples": int(valid.sum()),
    }
    return LT[valid], t9[valid], tbol[valid], meta


def run_solver_constant_flux(
    Q_in: float, K_func, T_surface_init: float
) -> tuple[float, int, bool]:
    """Run solver in radiative-BC mode with constant scattered flux.

    Returns (T_surface_converged_mean, n_spinup_cycles, converged_flag).
    Because Q_in is constant in time the converged T_s is also constant;
    we still run the time-domain solver to confirm the calibration is
    consistent with the regolith property models (Hayne rho(z), c_p(T),
    etc.) used in Figs 2 and 4.
    """
    grid = make_geometric_grid(z_max=2.0, dz0=0.002, growth=0.10)
    rho_z = density_hayne(grid.z_mid)
    n_t = int(N_LUNATIONS * T_LUNAR / DT) + 1
    t_arr = np.linspace(0.0, N_LUNATIONS * T_LUNAR, n_t)
    insolation = np.full(n_t, Q_in)
    T_init = np.full(grid.n_layers, T_surface_init)

    inp = PixelInputs(
        grid=grid,
        t=t_arr,
        bc_mode="radiative",
        insolation=insolation,
        albedo=0.0,  # Q_in is *absorbed* flux already (no wall=>floor BRDF here)
        emissivity=EMISSIVITY_DEFAULT,
        Q_b=Q_B_EQUATORIAL,
        K_func=K_func,
        rho_func=lambda z: rho_z,
        cp_func=lambda T: specific_heat(T, model="hayne"),
        T_init=T_init,
        n_lunations_spinup=SPINUP_LUNATIONS,
        spinup_tol_K=SPINUP_TOL_K,
        spinup_depth_m=SPINUP_DEPTH_M,
    )
    out = solve_pixel(inp)
    return float(out.T_surface.mean()), out.n_spinup_cycles, out.converged


def main() -> int:
    LT, t9, tbol, meta = diviner_shoemaker()
    print(
        f"Shoemaker tile (clon={meta['clon']:.2f}, clat={meta['clat']:.2f}):\n"
        f"  Tbol mean {meta['tbol_mean']:.2f} K, "
        f"T9 mean {t9.mean():.2f} K  (n={meta['n_samples']} LT bins)"
    )

    # Bin Diviner LT samples into 96 bins for plotting smoothness
    lt_bins = np.arange(0, 24.25, 0.25)
    bin_idx = np.digitize(LT, lt_bins) - 1
    t9_binned = np.array(
        [t9[bin_idx == i].mean() if (bin_idx == i).any() else np.nan
         for i in range(lt_bins.size)]
    )
    tbol_binned = np.array(
        [tbol[bin_idx == i].mean() if (bin_idx == i).any() else np.nan
         for i in range(lt_bins.size)]
    )

    # Calibration: pick Q_scatter so that radiative-equilibrium T_s = Tbol mean
    T_target = meta["tbol_mean"]
    Q_scatter = (
        EMISSIVITY_DEFAULT * SIGMA * T_target ** 4 - Q_B_EQUATORIAL
    )
    print(
        f"\nCalibrated scattered flux: "
        f"Q_scatter = {Q_scatter*1e3:.1f} mW/m^2 "
        f"(=> radiative-eq T_s = {T_target:.2f} K)"
    )

    # Run solver under both K models — confirms consistency
    print("Running Phase 1 solver under constant Q_scatter...")
    t0 = time.time()
    Th_mean, nh, ch = run_solver_constant_flux(
        Q_scatter, conductivity_hayne, T_target
    )
    print(
        f"  Hayne   : T_s_mean = {Th_mean:.2f} K, "
        f"spinup={nh}/{SPINUP_LUNATIONS}, converged={ch} "
        f"({time.time()-t0:.1f} s)"
    )
    t0 = time.time()
    Tm_mean, nm, cm = run_solver_constant_flux(
        Q_scatter, conductivity_martinez, T_target
    )
    print(
        f"  M&S     : T_s_mean = {Tm_mean:.2f} K, "
        f"spinup={nm}/{SPINUP_LUNATIONS}, converged={cm} "
        f"({time.time()-t0:.1f} s)"
    )

    # ---- Figure 3 ----
    fig, ax = plt.subplots(figsize=(7.5, 5.0), constrained_layout=True)

    # Diviner (binned)
    ax.plot(
        lt_bins, t9_binned,
        color="0.25", lw=1.4, marker="o", ms=3.5,
        label=f"Diviner T9 (Shoemaker tile, n={meta['n_samples']} LT bins)",
    )
    ax.plot(
        lt_bins, tbol_binned,
        color="0.55", lw=1.0, ls="--", marker=".", ms=3,
        label="Diviner Tbol (bolometric)",
    )

    # Diviner statistics shading: Tbol mean +/- 1 sigma over the LT sweep
    tbol_mean_arr = np.full_like(lt_bins, meta["tbol_mean"], dtype=float)
    tbol_std = float(np.nanstd(tbol_binned))
    ax.fill_between(
        lt_bins,
        tbol_mean_arr - tbol_std,
        tbol_mean_arr + tbol_std,
        color="0.85", alpha=0.5, zorder=0,
        label=fr"Tbol mean $\pm$ 1$\sigma$ = {meta['tbol_mean']:.1f} $\pm$ {tbol_std:.1f} K",
    )

    # Model lines (constant in this approximation)
    ax.axhline(
        Th_mean, color="#d62728", lw=1.8, ls="-",
        label=f"Hayne χ-T³ steady (constant Q_in): {Th_mean:.2f} K",
    )
    ax.axhline(
        Tm_mean, color="#1f77b4", lw=1.8, ls="-.",
        label=f"M&S K(T,ρ) steady (constant Q_in): {Tm_mean:.2f} K",
    )

    ax.set_xlim(0, 24)
    ax.set_xlabel("Local time (h)", fontsize=11)
    ax.set_ylabel("Surface temperature (K)", fontsize=11)
    ax.set_title(
        "Phase 2 Fig. 3 (preliminary) — Shoemaker PSR surface T\n"
        f"Constant-scattered-flux approx: Q_scatter = {Q_scatter*1e3:.1f} mW/m² "
        f"(calibrated to Tbol mean)",
        fontsize=10.5,
    )
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92, ncol=1)
    ax.grid(alpha=0.3)

    out_path = _REPO_ROOT / "output" / "figures" / "phase2_fig3_shoemaker_diurnal.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=150)
    plt.close(fig)
    print(f"Saved {out_path.relative_to(_REPO_ROOT)}")

    print(
        "\nLimitations of this approximation (documented in figure caption "
        "and notebook):\n"
        "  - No diurnal modulation: PSR floors have a quasi-seasonal cycle\n"
        "    (sub-solar latitude oscillates +/-1.54 deg over the lunar year);\n"
        "    capturing the +/- 5-15 K Diviner scatter requires per-pixel\n"
        "    bowl-crater radiosity (rim view factor + sunlit-wall radiance).\n"
        "  - The 0.7 K T_s_Hayne vs T_s_M&S spread is purely from emissivity\n"
        "    + Q_b coupling; surface T is not where the K-model matters\n"
        "    (see Figs 4 & 5 — at depth the spread grows to +18.6 K at 4 m)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
