"""Phase 2 Figure 3 — Shoemaker PSR surface T driven by real ray-traced illumination.

This is a faithful replication: drives the Phase 1 thermal solver with the
*same* time-varying scattered-illumination input that Martinez & Siegler
(2021) used for the published Shoemaker figures.

Inputs
------
``data/upstream/martinez2021/shoemakerIllumination.mat`` — 697 time samples
at the Shoemaker tile (-87.91, 45.51), bit-for-bit copy from Zenodo DOI
10.5281/zenodo.12586656. Fields:
  * ``IRillumination`` (W/m^2): thermal-IR re-emission from sunlit walls
  * ``visibleillumination`` (W/m^2): scattered visible from sunlit walls
  * ``daveTemp`` (K): Dave-Paige Diviner reference T from mosaicking
  * ``juliandate``: time stamps

Q_total = IRillumination + visibleillumination is what the upstream
``PSRShoemaker/UpdatedModel/heat1DShoemaker.m`` driver feeds into the
heat solver as the radiative-BC input flux.

Method
------
1. Load the .mat illumination time series.
2. Resample to a uniform grid for the solver (5-min steps over the 697-d
   span). 3. Spin up under the Q_total time series until the seasonal cycle
   stabilises (typically <30 cycles of the input series, shorter than
   30 lunations). Use top-only convergence at one diurnal skin depth.
4. Run both K models (Hayne chi-T^3 and M&S K(T,rho)).
5. Compare model T_surface(t) to ``daveTemp(t)``.

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

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.constants import EMISSIVITY_DEFAULT, Q_B_EQUATORIAL, SIGMA_SB
from lunar.grid import make_geometric_grid
from lunar.illumination import load_shoemaker_illumination
from lunar.phase2_plotting import (
    COLORS, apply_phase2_style, legend_below, savefig_pair,
)
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, density_hayne, specific_heat,
)
from lunar.solver import PixelInputs, solve_pixel

# Sub-sample step within the 697-day input span (10-min)
DT = 600.0
SPINUP_LUNATIONS = 30   # input span ~23 months, so 30 lunation-equivalents is plenty
SPINUP_TOL_K = 0.05     # K — looser than diurnal because the input is seasonal-scale
SPINUP_DEPTH_M = 0.10
T_INIT_GUESS = 40.0


def run_solver_real_illumination(
    Q_t: np.ndarray, t_arr: np.ndarray, K_func,
) -> tuple[np.ndarray, int, bool, float]:
    """Run Phase 1 solver with the real Q_total(t) time series."""
    grid = make_geometric_grid(z_max=2.0, dz0=0.002, growth=0.10)
    rho_z = density_hayne(grid.z_mid)
    T_init = np.full(grid.n_layers, T_INIT_GUESS)

    # Re-use the existing radiative BC. Q_t is *absorbed* flux (already
    # accounts for albedo since the upstream pipeline used these as
    # absorbed inputs to their solver), so we set albedo=0.
    inp = PixelInputs(
        grid=grid,
        t=t_arr,
        bc_mode="radiative",
        insolation=Q_t,
        albedo=0.0,
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
    return out.T_surface, out.n_spinup_cycles, out.converged, float(out.T_surface.mean())


def main() -> int:
    # 1. Load the real upstream illumination data
    sh = load_shoemaker_illumination()
    Q_total_input = sh["Q_total"]    # W/m^2
    T_ref = sh["T_reference"]        # K (Dave-Paige Diviner)
    t_jd = sh["t_jd"]                # Julian dates
    print(
        f"Upstream Shoemaker illumination ({len(Q_total_input)} samples, "
        f"lat={sh['latitude']:.2f}, lon={sh['longitude']:.2f}):\n"
        f"  Q_total: mean = {Q_total_input.mean():.4f} W/m^2, "
        f"peak = {Q_total_input.max():.4f}\n"
        f"  T_ref (Dave-Paige):  mean = {T_ref.mean():.2f} K, "
        f"range = {T_ref.min():.1f} - {T_ref.max():.1f} K"
    )

    # 2. Resample input to uniform DT seconds for the solver
    t_input_s = (t_jd - t_jd[0]) * 86400.0  # seconds since first sample
    span_s = t_input_s[-1]
    n_t = int(span_s / DT) + 1
    t_arr = np.linspace(0.0, span_s, n_t)
    Q_t = np.interp(t_arr, t_input_s, Q_total_input)
    print(
        f"Resampled to {n_t} solver steps (DT={DT/60:.1f} min, "
        f"span={span_s/86400:.1f} d)"
    )

    # 3. Run both K models
    print("Running Phase 1 solver with real Q_total(t) input...")
    t0 = time.time()
    Th_t, nh, ch, Th_mean = run_solver_real_illumination(
        Q_t, t_arr, conductivity_hayne,
    )
    print(
        f"  Hayne   : T_s(t) mean = {Th_mean:.2f} K, "
        f"range = {Th_t.min():.1f} - {Th_t.max():.1f} K, "
        f"spinup = {nh}/{SPINUP_LUNATIONS}, converged = {ch} "
        f"({time.time()-t0:.1f} s)"
    )
    t0 = time.time()
    Tm_t, nm, cm, Tm_mean = run_solver_real_illumination(
        Q_t, t_arr, conductivity_martinez,
    )
    print(
        f"  M&S     : T_s(t) mean = {Tm_mean:.2f} K, "
        f"range = {Tm_t.min():.1f} - {Tm_t.max():.1f} K, "
        f"spinup = {nm}/{SPINUP_LUNATIONS}, converged = {cm} "
        f"({time.time()-t0:.1f} s)"
    )

    # 4. Resample model T(t) back to the original input cadence to compare
    Th_at_ref = np.interp(t_input_s, t_arr, Th_t)
    Tm_at_ref = np.interp(t_input_s, t_arr, Tm_t)
    rmse_h = float(np.sqrt(np.mean((Th_at_ref - T_ref) ** 2)))
    rmse_m = float(np.sqrt(np.mean((Tm_at_ref - T_ref) ** 2)))
    bias_h = float(np.mean(Th_at_ref - T_ref))
    bias_m = float(np.mean(Tm_at_ref - T_ref))
    print(
        f"\nFit vs Dave-Paige reference T (n={len(T_ref)} samples):\n"
        f"  Hayne    RMSE = {rmse_h:.2f} K, bias = {bias_h:+.2f} K\n"
        f"  M&S      RMSE = {rmse_m:.2f} K, bias = {bias_m:+.2f} K"
    )

    # 5. Plot
    apply_phase2_style()
    days = (t_input_s - t_input_s[0]) / 86400.0
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    ax.plot(
        days, T_ref,
        color=COLORS["diviner"], lw=1.2, marker=".", ms=2.5,
        label="Diviner ch9 / Dave-Paige reference (daveTemp)",
    )
    ax.plot(
        days, Th_at_ref,
        color=COLORS["hayne"], lw=1.7,
        label=f"Hayne χ-T³  (RMSE {rmse_h:.1f} K, bias {bias_h:+.1f} K)",
    )
    ax.plot(
        days, Tm_at_ref,
        color=COLORS["ms"], lw=1.7, ls="--",
        label=f"M&S K(T,ρ)  (RMSE {rmse_m:.1f} K, bias {bias_m:+.1f} K)",
    )
    ax.set_xlabel("Days since first sample  (697-day span ≈ 23 lunations)")
    ax.set_ylabel("Surface temperature (K)")
    ax.set_title(
        "Shoemaker PSR surface T, real ray-traced illumination  (Fig 10 of M&S 2021)\n"
        f"Q_total = vis + IR from upstream shoemakerIllumination.mat "
        f"(mean {Q_total_input.mean():.3f} W/m²)"
    )
    legend_below(ax, ncol=3, pad=0.18)

    out_path = _REPO_ROOT / "output" / "figures" / "phase2_fig3_shoemaker_diurnal.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"\nSaved {out_path.relative_to(_REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
