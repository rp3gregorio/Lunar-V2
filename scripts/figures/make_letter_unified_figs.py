"""
Regenerate the three letter figures previously produced by the
01_apollo_validation notebook, using the same palette and style
helpers as phase2_figures_v2.py so all six letter figures share a
single visual identity.

Outputs (overwriting the old notebook versions):
  paper/letter/figures/fig2_apollo_mean_T_profile.pdf
  paper/letter/figures/apollo_amplitude_vs_depth.pdf
  paper/letter/figures/fig5_kd_sweep.pdf
"""
from __future__ import annotations
import json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from copy import deepcopy

sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2")
sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2/scripts")

from lunar import _bootstrap as boot
boot.ensure_lunar(extra=("spiceypy", "scipy"))
boot.ensure_apollo_hfe(mission="a15",
                       probes=("p1f1","p1f2","p1f3","p1f4",
                               "p2f1","p2f2","p2f3","p2f4"))
boot.ensure_apollo_hfe(mission="a17", probes=())

from lunar.grid import make_geometric_grid
from lunar.properties import conductivity_hayne, specific_heat
from lunar.constants import (
    K_SURFACE, K_DEEP, H_PARAMETER, CHI_RADIATIVE, T_REFERENCE, LUNATION_SECONDS,
)
from lunar.solver import PixelInputs, solve_pixel
from lunar.apollo_helpers import extract_sensor_stability

# Pull the unified rcParams + palette from the phase-2 figure module.
from phase2_figures_v2 import (   # type: ignore
    JGR_FULL,
    FS_TITLE, FS_LABEL, FS_TICK, FS_LEGEND,
    C_HAYNE, C_MS, C_A15, C_A17, C_CHAR, C_DIM, C_GRID,
    fmt_axis,
)

# Configurations that match kd_sweep.py and the validation notebook
S0           = 1361.0
T_LUNAR      = LUNATION_SECONDS
DT_STEP      = 3600.0
N_LUN_FAST   = 30
TOL_FAST     = 0.05
GRID         = dict(z_max=5.0, dz0=0.002, growth=0.08)

HAYNE = dict(K_S=K_SURFACE, K_D=K_DEEP, H=H_PARAMETER, CHI=CHI_RADIATIVE)
MS_K_S, MS_K_D, MS_Z1, MS_Z2 = 1.0e-3, 6.3e-3, 0.07, 0.20

SITES = {
    "A15": dict(label="Apollo 15", lat=26.13, lon=3.63,
                albedo=0.131, emissivity=0.95, Q_BASAL=0.021,
                T_MEAN_EFF=250.0, MIN_DEPTH_CM=80, mission="a15"),
    "A17": dict(label="Apollo 17", lat=20.19, lon=30.77,
                albedo=0.137, emissivity=0.95, Q_BASAL=0.015,
                T_MEAN_EFF=256.5, MIN_DEPTH_CM=80, mission="a17"),
}

LETTER_FIGS = pathlib.Path("/Users/rp3gregorio/Lunar-V2/paper/letter/figures")
PHASE_A     = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase_a_results.json")


# ── Solver ────────────────────────────────────────────────────────────────────
def k_func_hayne(kd, h=HAYNE["H"]):
    def f(T, z):
        return conductivity_hayne(T, z, Ks=HAYNE["K_S"], Kd=kd,
                                  H=h, chi=HAYNE["CHI"])
    return f


def k_func_ms():
    """3-layer M&S K(z) with the same radiative multiplier."""
    def f(T, z):
        z_arr = np.atleast_1d(np.asarray(z))
        T_arr = np.atleast_1d(np.asarray(T))
        if T_arr.shape != z_arr.shape:
            T_arr = np.broadcast_to(T_arr, z_arr.shape).copy()
        Kc = np.where(z_arr < MS_Z2,
                      MS_K_S + (MS_K_D - MS_K_S) * (z_arr / MS_Z2),
                      MS_K_D)
        return Kc * (1.0 + HAYNE["CHI"] * (T_arr / T_REFERENCE) ** 3)
    return f


def run_pixel(site_cfg, *, kfunc):
    site = deepcopy(site_cfg)
    grid_  = make_geometric_grid(**GRID)
    z_mid  = grid_.z_mid
    N_t    = int(T_LUNAR / DT_STEP) + 1
    t_s    = np.linspace(0.0, T_LUNAR, N_t)
    cos_lat = np.cos(np.deg2rad(site["lat"]))
    phase   = 2.0 * np.pi * t_s / T_LUNAR
    insol   = S0 * cos_lat * np.maximum(0.0, np.cos(phase))
    K_init = kfunc(np.full_like(z_mid, site["T_MEAN_EFF"]), z_mid)
    T_init = site["T_MEAN_EFF"] + site["Q_BASAL"] * np.cumsum(grid_.dz / K_init)
    out = solve_pixel(PixelInputs(
        grid=grid_, t=t_s, bc_mode="radiative",
        insolation=insol, albedo=site["albedo"],
        emissivity=site["emissivity"], Q_b=site["Q_BASAL"], T_init=T_init,
        n_lunations_spinup=N_LUN_FAST, spinup_tol_K=TOL_FAST,
        K_func=kfunc, cp_func=lambda T: specific_heat(T, model="hayne"),
    ))
    return z_mid, out.T, t_s


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Annual-mean subsurface T profile
# ══════════════════════════════════════════════════════════════════════════════
def fig_mean_T_profile():
    fig, axes = plt.subplots(1, 2, figsize=(JGR_FULL, 5.0),
                             gridspec_kw={"wspace": 0.28})
    fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.20)

    for ax, name in zip(axes, ["A15", "A17"]):
        cfg = SITES[name]
        # observations
        obs = extract_sensor_stability(cfg["mission"], cfg["MIN_DEPTH_CM"])
        z_obs = np.array(obs["depth_cm_all"]) / 100.0
        T_obs = np.array(obs["T_eq_all"])
        T_std = np.array(obs["T_std_all"])
        deep  = np.array(obs["deep_mask"], dtype=bool)
        stype = np.array(obs["stype_all"])

        # model: Hayne reference + M&S 3-layer
        z_mid, T_mat_H, _  = run_pixel(cfg, kfunc=k_func_hayne(HAYNE["K_D"]))
        z_mid, T_mat_MS, _ = run_pixel(cfg, kfunc=k_func_ms())
        T_H  = T_mat_H.mean(axis=1)
        T_MS = T_mat_MS.mean(axis=1)

        # plot
        ax.plot(T_H,  z_mid * 100, "-",  color=C_HAYNE, lw=2.0,
                label="Hayne (2017) — smooth exponential")
        ax.plot(T_MS, z_mid * 100, "--", color=C_MS, lw=2.0,
                label="Martinez & Siegler (2021) — 3-layer")

        # observed sensors
        col_TG = C_CHAR
        col_TR = C_DIM
        for is_tg in (True, False):
            mask = (stype == ("TG" if is_tg else "TR"))
            ax.errorbar(T_obs[mask & deep], z_obs[mask & deep] * 100,
                        xerr=T_std[mask & deep], fmt="o",
                        color=col_TG if is_tg else col_TR,
                        mec="white", mew=0.7, markersize=7, capsize=2,
                        label=("TG (deep)" if is_tg else "TR (deep)") if name == "A15" else None)
            ax.errorbar(T_obs[mask & ~deep], z_obs[mask & ~deep] * 100,
                        xerr=T_std[mask & ~deep], fmt="o", mfc="none",
                        color=col_TG if is_tg else col_TR,
                        mew=0.9, markersize=7, capsize=2,
                        label=("TG (shallow, excluded)" if is_tg else "TR (shallow, excluded)") if name == "A15" else None)

        # borestem zone shading
        ax.axhspan(0, 80, color="0.85", alpha=0.35, zorder=0)
        ax.text(ax.get_xlim()[0] + 1, 12, "borestem zone\n(z < 80 cm)",
                fontsize=FS_TICK, color=C_DIM, va="center", style="italic")

        fmt_axis(ax,
                 xlabel="Annual-mean temperature (K)",
                 ylabel="Depth (cm)" if name == "A15" else "",
                 title=f"({['a','b'][['A15','A17'].index(name)]})  {cfg['label']}")
        ax.invert_yaxis()
        ax.set_ylim(250, 0)

    # shared legend below
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, 0.005),
               ncols=3, frameon=True, edgecolor=C_GRID, framealpha=0.97,
               fontsize=FS_LEGEND, handlelength=2.2, borderpad=0.6,
               columnspacing=1.6)

    out = LETTER_FIGS / "fig2_apollo_mean_T_profile.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Diurnal amplitude vs depth (borestem signature)
# ══════════════════════════════════════════════════════════════════════════════
def fig_amplitude_vs_depth():
    fig, axes = plt.subplots(1, 2, figsize=(JGR_FULL, 4.6),
                             gridspec_kw={"wspace": 0.28})
    fig.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.22)

    for ax, name in zip(axes, ["A15", "A17"]):
        cfg = SITES[name]
        obs = extract_sensor_stability(cfg["mission"], cfg["MIN_DEPTH_CM"])
        # Per-sensor diurnal amplitude has to be computed from the raw
        # data via SPICE LST folding; we approximate it here by the
        # within-window standard deviation of the Apollo HFE record,
        # which is dominated by the diurnal cycle for shallow sensors.
        z_obs = np.array(obs["depth_cm_all"])
        T_std = np.array(obs["T_std_all"])
        # Diurnal amplitude ≈ √2 × σ for a sinusoidal signal.
        amp_obs = np.sqrt(2.0) * T_std

        # Modelled regolith attenuation curve (analytical, both models).
        z_grid = np.linspace(0.0, 250.0, 400)   # cm
        # diurnal skin depth: δ = √(2 κ / ω); κ = K/(ρ c_p)
        # at the surface for the Hayne reference at T~250 K
        kappa_H  = HAYNE["K_D"]      / (1500.0 * 850.0)
        kappa_MS = MS_K_D            / (1500.0 * 850.0)
        omega    = 2 * np.pi / T_LUNAR
        delta_H  = np.sqrt(2 * kappa_H  / omega) * 100  # cm
        delta_MS = np.sqrt(2 * kappa_MS / omega) * 100  # cm
        amp_H  = 100 * np.exp(-z_grid / delta_H)
        amp_MS = 100 * np.exp(-z_grid / delta_MS)

        ax.semilogx(amp_H,  z_grid, "-",  color=C_HAYNE, lw=2.0,
                    label="Hayne (2017) — smooth exponential")
        ax.semilogx(amp_MS, z_grid, "--", color=C_MS, lw=2.0,
                    label="Martinez & Siegler (2021) — 3-layer")
        ax.semilogx(amp_obs, z_obs, "o", color=C_CHAR,
                    mec="white", mew=0.7, markersize=7,
                    label="Apollo HFE  (obs.)")

        # borestem zone
        ax.axhspan(0, 80, color="0.85", alpha=0.35, zorder=0)
        ax.text(2e-3, 12, "borestem zone (z < 80 cm)",
                fontsize=FS_TICK, color=C_DIM, va="center", style="italic")

        fmt_axis(ax,
                 xlabel=r"Diurnal amplitude  (K)",
                 ylabel="Depth (cm)" if name == "A15" else "",
                 title=f"({['a','b'][['A15','A17'].index(name)]})  {cfg['label']}")
        ax.invert_yaxis()
        ax.set_ylim(220, 0)
        ax.set_xlim(1e-3, 200)

    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, 0.005),
               ncols=3, frameon=True, edgecolor=C_GRID, framealpha=0.97,
               fontsize=FS_LEGEND, handlelength=2.2, borderpad=0.6)

    out = LETTER_FIGS / "apollo_amplitude_vs_depth.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — K_d sweep (the central retrieval figure)
# ══════════════════════════════════════════════════════════════════════════════
def fig_kd_sweep():
    """Reads Phase-A results and plots the K_d sweep curves with the
    unified palette (A15 = forest green, A17 = coral) and a shared
    legend below."""
    d = json.loads(PHASE_A.read_text())

    fig, ax = plt.subplots(figsize=(JGR_FULL, 5.0))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.30)

    from scipy.interpolate import CubicSpline
    for name, color in [("A15", C_A15), ("A17", C_A17)]:
        s   = d[name]
        kdg = np.array(s["kd_grid"]) * 1e3
        rmse = np.array(s["rmse_curve"])
        cs  = CubicSpline(kdg, rmse)
        kdf = np.linspace(kdg[0], kdg[-1], 400)

        b = s["bootstrap"]
        lo, hi = b["ci_lo"]*1e3, b["ci_hi"]*1e3
        # CI band along the curve
        in_ci = (kdf >= lo) & (kdf <= hi)
        ax.fill_between(kdf[in_ci], 0, cs(kdf[in_ci]),
                        color=color, alpha=0.10, zorder=0)

        ax.plot(kdf, cs(kdf), "-", color=color, lw=2.4,
                label=f"{name}  $K_d^{{*}} = {s['kd_star']*1e3:.2f}$  "
                      f"[{lo:.2f}, {hi:.2f}]")
        ax.plot(kdg, rmse, "o", color=color, markersize=4.0,
                mec="white", mew=0.5, zorder=3)
        ax.plot(s["kd_star"]*1e3, s["rmse_star"], "*", color=color,
                markersize=20, mec="white", mew=1.4, zorder=5)

    # vertical reference lines
    ax.axvline(3.4, color=C_HAYNE, ls="--", lw=1.2, alpha=0.7,
               label="Hayne 2017  $K_d = 3.4$")
    ax.axvline(6.3, color=C_MS, ls=":", lw=1.2, alpha=0.7,
               label="Martinez & Siegler 2021  $K_d = 6.3$")

    fmt_axis(ax,
             xlabel=r"Deep conductivity  $K_d$  (mW m$^{-1}$ K$^{-1}$)",
             ylabel=r"Deep-sensor RMSE  (K)",
             title="Per-site $K_d$ retrieval under the Hayne 2017 functional form")
    ax.set_xlim(0, 26)
    ax.set_ylim(0, 6)

    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, 0.005),
               ncols=2, frameon=True, edgecolor=C_GRID, framealpha=0.97,
               fontsize=FS_LEGEND, handlelength=2.2, borderpad=0.6,
               title="Sites:  $K_d^{*}$  [95% bootstrap CI]   and reference values",
               title_fontsize=FS_LABEL)

    out = LETTER_FIGS / "fig5_kd_sweep.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  → {out}")


def main():
    print("Regenerating letter figures with unified palette:")
    fig_mean_T_profile()
    fig_amplitude_vs_depth()
    fig_kd_sweep()
    print("done.")


if __name__ == "__main__":
    main()
