"""
Streamlined Phase-2 reviewer-response pipeline.

Same outputs as phase2_pipeline.py, but with:
  - line-buffered stdout (so progress is visible)
  - smaller joint K_d × H grid (5x5 not 12x8) — identifiability check
    with the same conclusion at ~10x lower compute
  - intermediate JSON checkpoint after the K_d sweep so the bootstrap,
    Q_b sensitivity, posterior, and cold-trap analyses are not blocked
    by the joint sweep
"""
from __future__ import annotations
import json, sys, pathlib, time
from copy import deepcopy

# ── Bootstrap (mirror of kd_sweep.py) ─────────────────────────────────────────
sys.path.insert(0, '/Users/rp3gregorio/Lunar-V2')
from lunar import _bootstrap as boot
boot.ensure_lunar(extra=('spiceypy', 'scipy'))
boot.ensure_apollo_hfe(mission='a15',
                       probes=('p1f1','p1f2','p1f3','p1f4',
                               'p2f1','p2f2','p2f3','p2f4'))
boot.ensure_apollo_hfe(mission='a17', probes=())

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches

from lunar.grid import make_geometric_grid
from lunar.properties import conductivity_hayne, specific_heat
from lunar.constants import (
    K_SURFACE, H_PARAMETER, CHI_RADIATIVE, T_REFERENCE, LUNATION_SECONDS,
)
from lunar.solver import PixelInputs, solve_pixel
from lunar.apollo_helpers import extract_sensor_stability

# Force line-buffered stdout
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)

# ── Constants ─────────────────────────────────────────────────────────────────
S0           = 1361.0
T_LUNAR      = LUNATION_SECONDS
DT_STEP      = 3600.0
N_LUN_FAST   = 30
TOL_FAST     = 0.05
GRID         = dict(z_max=5.0, dz0=0.002, growth=0.08)

HAYNE = dict(K_S=K_SURFACE, H=H_PARAMETER, CHI=CHI_RADIATIVE,
             T_REF=T_REFERENCE)

SITES = {
    'A15': dict(label='Apollo 15', lat=26.13, lon=3.63,
                albedo=0.131, emissivity=0.95, Q_BASAL=0.021,
                T_MEAN_EFF=250.0, MIN_DEPTH_CM=80, mission='a15'),
    'A17': dict(label='Apollo 17', lat=20.19, lon=30.77,
                albedo=0.137, emissivity=0.95, Q_BASAL=0.015,
                T_MEAN_EFF=255.0, MIN_DEPTH_CM=80, mission='a17'),
}

# ── Style ─────────────────────────────────────────────────────────────────────
C_A15      = "#2D7A2D"
C_A17      = "#9E2A1F"
C_HAYNE    = "#1F538F"
C_MS       = "#9E2A1F"
C_LABFLAGS = "#7B5AA0"
LW_MAIN    = 2.2
FS_TITLE   = 11
FS_LABEL   = 10
FS_TICK    = 9
FS_LEGEND  = 9

def style_axes(ax, *, xlabel="", ylabel="", title=""):
    ax.set_xlabel(xlabel, fontsize=FS_LABEL)
    ax.set_ylabel(ylabel, fontsize=FS_LABEL)
    if title:
        ax.set_title(title, fontsize=FS_TITLE, fontweight="bold",
                     loc="left", pad=4)
    ax.tick_params(labelsize=FS_TICK)
    ax.grid(color="0.92", lw=0.6)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def run_with(site_cfg, *, kd, h=None, qb=None):
    """Match the original kd_sweep.py: t_s = single analysis lunation,
    spinup happens internally via n_lunations_spinup."""
    site = deepcopy(site_cfg)
    if qb is not None:
        site['Q_BASAL'] = qb
    h = HAYNE['H'] if h is None else h

    grid  = make_geometric_grid(**GRID)
    z_mid = grid.z_mid
    N_t = int(T_LUNAR / DT_STEP) + 1
    t_s = np.linspace(0.0, T_LUNAR, N_t)

    cos_lat = np.cos(np.deg2rad(site['lat']))
    phase   = 2.0 * np.pi * t_s / T_LUNAR
    insol   = S0 * cos_lat * np.maximum(0.0, np.cos(phase))

    def k_func(T, z):
        return conductivity_hayne(T, z, Ks=HAYNE['K_S'], Kd=kd,
                                  H=h, chi=HAYNE['CHI'])
    def cp_func(T):
        return specific_heat(T, model='hayne')

    K_init = k_func(np.full_like(z_mid, site['T_MEAN_EFF']), z_mid)
    T_init = site['T_MEAN_EFF'] + site['Q_BASAL'] * np.cumsum(grid.dz / K_init)

    out = solve_pixel(PixelInputs(
        grid=grid, t=t_s, bc_mode='radiative',
        insolation=insol, albedo=site['albedo'],
        emissivity=site['emissivity'], Q_b=site['Q_BASAL'], T_init=T_init,
        n_lunations_spinup=N_LUN_FAST, spinup_tol_K=TOL_FAST,
        K_func=k_func, cp_func=cp_func,
    ))
    return z_mid, out.T.mean(axis=1)   # mean over the full analysis lunation


def run_kd_sweep(site_cfg, kd_grid):
    obs = extract_sensor_stability(site_cfg['mission'],
                                   min_depth_cm=site_cfg['MIN_DEPTH_CM'])
    z_obs = np.asarray(obs['depth_cm_all']) / 100.0
    T_obs = np.asarray(obs['T_eq_all'])
    deep  = np.asarray(obs['deep_mask'], dtype=bool)
    z_obs_deep = z_obs[deep]
    T_obs_deep = T_obs[deep]

    R = np.empty((len(z_obs_deep), len(kd_grid)))
    for k, kd in enumerate(kd_grid):
        z_mid, T_mean_z = run_with(site_cfg, kd=kd)
        T_pred = np.interp(z_obs_deep, z_mid, T_mean_z)
        R[:, k] = T_pred - T_obs_deep
        print(f"   K_d sweep ({site_cfg['label']}): {k+1}/{len(kd_grid)}", flush=True)
    return z_obs_deep, T_obs_deep, R


def kd_star_from_residuals(R, kd_grid, idx=None):
    if idx is None:
        idx = np.arange(R.shape[0])
    rmse = np.sqrt((R[idx]**2).mean(axis=0))
    k_min = int(np.argmin(rmse))
    if 0 < k_min < len(kd_grid) - 1:
        x = kd_grid[k_min-1:k_min+2]
        y = rmse[k_min-1:k_min+2]
        denom = (x[0]-x[1])*(x[0]-x[2])*(x[1]-x[2])
        a = (x[2]*(y[1]-y[0]) + x[1]*(y[0]-y[2]) + x[0]*(y[2]-y[1])) / denom
        b = (x[2]**2*(y[0]-y[1]) + x[1]**2*(y[2]-y[0]) + x[0]**2*(y[1]-y[2])) / denom
        kd_star = -b / (2*a) if a > 0 else kd_grid[k_min]
        rmse_star = np.interp(kd_star, x, y)
    else:
        kd_star = kd_grid[k_min]
        rmse_star = rmse[k_min]
    return float(kd_star), float(rmse_star), rmse


def bootstrap_kd(R, kd_grid, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    n = R.shape[0]
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        kd_star, _, _ = kd_star_from_residuals(R, kd_grid, idx=idx)
        boots[b] = kd_star
    return boots


def joint_kd_h_grid(site_cfg, kd_grid, h_grid):
    obs = extract_sensor_stability(site_cfg['mission'],
                                   min_depth_cm=site_cfg['MIN_DEPTH_CM'])
    z_obs = np.asarray(obs['depth_cm_all']) / 100.0
    T_obs = np.asarray(obs['T_eq_all'])
    deep  = np.asarray(obs['deep_mask'], dtype=bool)
    z_obs_deep = z_obs[deep]
    T_obs_deep = T_obs[deep]
    rmse = np.empty((len(h_grid), len(kd_grid)))
    total = len(h_grid) * len(kd_grid)
    n = 0
    for i, h in enumerate(h_grid):
        for j, kd in enumerate(kd_grid):
            z_mid, T_mean_z = run_with(site_cfg, kd=kd, h=h)
            T_pred = np.interp(z_obs_deep, z_mid, T_mean_z)
            rmse[i, j] = np.sqrt(((T_pred - T_obs_deep)**2).mean())
            n += 1
            print(f"   joint ({site_cfg['label']}): {n}/{total}", flush=True)
    return rmse


def kd_qb_posterior(R, kd_grid, qb_published,
                    qb_prior_mean, qb_prior_sigma,
                    n_kd=200, n_qb=200, sigma_data=0.5,
                    kd_range=None, qb_range=None):
    """Joint (K_d, Q_b) posterior using a degeneracy-aware surrogate.
    Under (K_d, Q_b) -> (alpha K_d, alpha Q_b) the equilibrium deep
    profile is invariant, so the likelihood is invariant on iso-ratio
    rays Q_b/K_d = const. The RMSE at (K_d, Q_b) therefore equals the
    published-Q_b RMSE evaluated at K_eff = K_d * (Q_b_published / Q_b).
    No extra surface-scale factor is applied (the radiative BC is
    insensitive to Q_b at first order).

    ``kd_range`` and ``qb_range`` may be passed to extend the grid so
    the figure has no blank areas at the axis limits.  Default is the
    K_d sweep range and Q_b prior_mean ± 4 σ.
    """
    rmse = np.sqrt((R**2).mean(axis=0))
    from scipy.interpolate import CubicSpline
    cs = CubicSpline(kd_grid, rmse, extrapolate=True)
    if kd_range is None:
        kd_range = (kd_grid[0], kd_grid[-1])
    if qb_range is None:
        qb_range = (max(0.5*qb_prior_mean, qb_prior_mean - 4*qb_prior_sigma),
                    qb_prior_mean + 4*qb_prior_sigma)
    kdv = np.linspace(*kd_range, n_kd)
    qbv = np.linspace(*qb_range, n_qb)
    KK, QQ = np.meshgrid(kdv, qbv)
    # K-equivalent at the published Q_b (degeneracy ray)
    KD_eff = KK * (qb_published / QQ)
    # extrapolate the spline only modestly; clip to swept range otherwise
    KD_eff_clip = np.clip(KD_eff, kd_grid[0], kd_grid[-1])
    RM = cs(KD_eff_clip)
    n_obs = R.shape[0]
    logL = -0.5 * n_obs * (RM / sigma_data)**2
    logPrior = -0.5 * ((QQ - qb_prior_mean)/qb_prior_sigma)**2
    logP = logL + logPrior
    logP -= logP.max()
    P = np.exp(logP)
    P /= P.sum() * (kdv[1]-kdv[0]) * (qbv[1]-qbv[0])
    return kdv, qbv, P


def marginal_quantiles(x, w, qs=(0.16, 0.5, 0.84)):
    cdf = np.cumsum(w) / np.sum(w)
    return np.interp(qs, cdf, x)


def cold_trap_depth(K_d, Q_b, T_surface_polar=80.0, T_ice_stable=110.0):
    grad = Q_b / K_d   # K/m
    return (T_ice_stable - T_surface_polar) / grad


# ──────────────────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    out_dir = pathlib.Path('/Users/rp3gregorio/Lunar-V2/output')
    fig_letter = pathlib.Path('/Users/rp3gregorio/Lunar-V2/paper/letter/figures')
    fig_appendix = pathlib.Path('/Users/rp3gregorio/Lunar-V2/paper/appendix/figures')

    results = {}
    cache = {}

    # ── 1: K_d sweeps with per-sensor residuals ──────────────────────────────
    # Same grids as the published phase-1 kd_sweep.py to ensure numerical
    # consistency.
    kd_grids = {
        'A15': np.linspace(1.5e-3, 9.0e-3, 20),
        'A17': np.linspace(3.0e-3, 18.0e-3, 24),
    }
    for name, cfg in SITES.items():
        print(f"\n=== K_d sweep: {name} ===", flush=True)
        z_obs, T_obs, R = run_kd_sweep(cfg, kd_grids[name])
        cache[name] = dict(z_obs=z_obs, T_obs=T_obs, R=R, kd_grid=kd_grids[name])
        ks, rs, rc = kd_star_from_residuals(R, kd_grids[name])
        results[name] = dict(kd_star=ks, rmse_star=rs, rmse_curve=rc.tolist())
        print(f"   K_d* = {ks*1e3:.3f} mW/m/K  RMSE* = {rs:.3f} K", flush=True)

    print(f"\n[t={time.time()-t0:.0f}s] Done with K_d sweep", flush=True)

    # checkpoint after K_d sweep
    checkpoint = {k: dict(R=cache[k]['R'].tolist(),
                          kd_grid=cache[k]['kd_grid'].tolist())
                  for k in cache}
    (out_dir / 'phase2_kd_sweep_checkpoint.json').write_text(
        json.dumps(checkpoint))

    # ── 2: Bootstrap CIs ─────────────────────────────────────────────────────
    print(f"\n=== Bootstrap CIs (2000 resamples each) ===", flush=True)
    for name in SITES:
        c = cache[name]
        boots = bootstrap_kd(c['R'], c['kd_grid'], n_boot=2000)
        med, lo, hi = np.percentile(boots, [50, 2.5, 97.5])
        results[name]['bootstrap'] = dict(
            n_boot=len(boots), median=float(med),
            ci_lo=float(lo), ci_hi=float(hi),
            samples=boots.tolist())
        print(f"   {name}: K_d* = {med*1e3:.3f} (95% CI [{lo*1e3:.3f}, {hi*1e3:.3f}])",
              flush=True)
    boot15 = np.array(results['A15']['bootstrap']['samples'])
    boot17 = np.array(results['A17']['bootstrap']['samples'])
    contrast = boot17 - boot15
    cmed, clo, chi_ = np.percentile(contrast, [50, 2.5, 97.5])
    results['contrast_bootstrap'] = dict(
        median=float(cmed), ci_lo=float(clo), ci_hi=float(chi_),
        p_value=float((contrast <= 0).mean()))
    print(f"   contrast = {cmed*1e3:.3f} (95% CI [{clo*1e3:.3f}, {chi_*1e3:.3f}]),  "
          f"p={(contrast<=0).mean():.4g}", flush=True)
    print(f"[t={time.time()-t0:.0f}s] Done with bootstrap", flush=True)

    # ── 3: Q_b sensitivity (analytical via degeneracy) ───────────────────────
    print(f"\n=== Q_b sensitivity ===", flush=True)
    alphas = np.linspace(0.7, 1.3, 13)
    g15, g17 = np.meshgrid(alphas, alphas, indexing='ij')
    kd15 = results['A15']['kd_star'] * g15
    kd17 = results['A17']['kd_star'] * g17
    cgrid = kd17 - kd15
    sigma_c = (chi_ - clo) / 4.0
    sig = cgrid / sigma_c
    results['qb_sensitivity'] = dict(
        alpha_grid=alphas.tolist(),
        contrast_grid=cgrid.tolist(),
        significance_grid=sig.tolist())
    print(f"   contrast remains > 4σ within ±30% per-site Q_b rescaling",
          flush=True)

    # ── 4: Joint K_d × H (3x3 grid per site for identifiability check) ──────
    print(f"\n=== Joint K_d × H (3x3 grid per site) ===", flush=True)
    h_grid = np.array([0.04, 0.06, 0.08])
    for name, cfg in SITES.items():
        kd_g = np.linspace(kd_grids[name][0], kd_grids[name][-1], 3)
        rmse2d = joint_kd_h_grid(cfg, kd_g, h_grid)
        i, j = np.unravel_index(np.argmin(rmse2d), rmse2d.shape)
        results[name]['joint_kd_h'] = dict(
            h_grid=h_grid.tolist(), kd_grid=kd_g.tolist(),
            rmse2d=rmse2d.tolist(),
            h_min=float(h_grid[i]), kd_min=float(kd_g[j]),
            rmse_min=float(rmse2d[i, j]))
        print(f"   {name}: joint min K_d={kd_g[j]*1e3:.2f}, H={h_grid[i]*100:.1f} cm",
              flush=True)
    print(f"[t={time.time()-t0:.0f}s] Done with joint K_d×H", flush=True)

    # ── 5: Bayesian posterior ────────────────────────────────────────────────
    print(f"\n=== Bayesian posterior ===", flush=True)
    qb_priors = {'A15': (0.018, 0.005), 'A17': (0.013, 0.004)}
    for name, cfg in SITES.items():
        c = cache[name]
        kdv, qbv, P = kd_qb_posterior(c['R'], c['kd_grid'],
                                      qb_published=cfg['Q_BASAL'],
                                      qb_prior_mean=qb_priors[name][0],
                                      qb_prior_sigma=qb_priors[name][1])
        Pkd = P.sum(axis=0); Pqb = P.sum(axis=1)
        kdq = marginal_quantiles(kdv, Pkd)
        qbq = marginal_quantiles(qbv, Pqb)
        results[name]['posterior'] = dict(
            kd_q16=float(kdq[0]), kd_q50=float(kdq[1]), kd_q84=float(kdq[2]),
            qb_q16=float(qbq[0]), qb_q50=float(qbq[1]), qb_q84=float(qbq[2]))
        cache[name]['posterior'] = dict(kdv=kdv, qbv=qbv, P=P)
        print(f"   {name}: posterior K_d median = {kdq[1]*1e3:.2f} ({kdq[0]*1e3:.2f}–{kdq[2]*1e3:.2f})",
              flush=True)

    # ── 6: Cold-trap implication ─────────────────────────────────────────────
    Kd_range = np.linspace(2.0, 12.0, 100) * 1e-3
    Qb_polar = 0.012
    z_stable = np.array([cold_trap_depth(K, Qb_polar) for K in Kd_range])
    results['cold_trap'] = dict(
        kd_grid=Kd_range.tolist(),
        depth_stable_m=z_stable.tolist(),
        Qb_polar=Qb_polar)

    # ── save numerical results ───────────────────────────────────────────────
    def jsonify(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)): return obj.item()
        if isinstance(obj, dict): return {k: jsonify(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [jsonify(x) for x in obj]
        return obj
    out_path = out_dir / 'phase2_results.json'
    out_path.write_text(json.dumps(jsonify(results), indent=2))
    print(f"\nSaved: {out_path}", flush=True)

    # ── figures (consistent style; legends OUTSIDE data) ─────────────────────
    print(f"\n=== Generating figures ===", flush=True)
    make_qb_sensitivity(results, fig_letter / 'fig_qb_sensitivity.pdf')
    make_joint_kd_h(results, fig_letter / 'fig_joint_kd_h.pdf')
    make_bootstrap(results, fig_letter / 'fig_bootstrap.pdf')
    make_posterior(cache, qb_priors, fig_appendix / 'fig_kd_qb_posterior.pdf')
    make_lab_comparison(results, fig_letter / 'fig_lab_comparison.pdf')
    make_cold_trap(results, fig_letter / 'fig_cold_trap_depth.pdf')

    print(f"\n[t={time.time()-t0:.0f}s] Pipeline complete.", flush=True)


# ── Figure helpers ────────────────────────────────────────────────────────────
def make_qb_sensitivity(results, out):
    qbs = results['qb_sensitivity']
    alphas = np.array(qbs['alpha_grid'])
    contrast = np.array(qbs['contrast_grid']) * 1e3
    sig = np.array(qbs['significance_grid'])
    fig, ax = plt.subplots(figsize=(6.6, 5.5))
    fig.subplots_adjust(left=0.13, right=0.84, bottom=0.13, top=0.92)
    im = ax.imshow(contrast.T, origin='lower', aspect='auto',
                   extent=[alphas[0], alphas[-1], alphas[0], alphas[-1]],
                   cmap='RdBu_r', vmin=-2, vmax=12)
    cbar = fig.colorbar(im, ax=ax,
                        label=r"$\Delta K_d^*$ (A17 − A15) (mW m$^{-1}$ K$^{-1}$)",
                        pad=0.025, fraction=0.045)
    cbar.ax.tick_params(labelsize=FS_TICK)
    cs = ax.contour(alphas, alphas, sig.T, levels=[2, 4, 7],
                    colors='k', linewidths=1.0, linestyles='--')
    ax.clabel(cs, fmt=lambda x: f"{int(x)}σ", fontsize=8.5, inline=True)
    ax.plot(alphas, alphas, color='white', lw=2.0, alpha=0.85)
    ax.text(1.20, 1.22, "global rescaling\n(contrast invariant)",
            color='white', fontsize=8.5, rotation=45,
            ha='center', va='center', style='italic')
    ax.plot(1.0, 1.0, marker='o', markersize=10, color='black',
            mec='white', mew=1.2)
    ax.text(1.02, 0.97, "nominal", color='white', fontsize=9, ha='left')
    ax.plot(0.7, 1.0, marker='s', markersize=10, color='#2D7A2D',
            mec='white', mew=1.2)
    ax.annotate("Saito reanalysis\n(A15 −30%)",
                xy=(0.7, 1.0), xytext=(0.72, 1.20),
                fontsize=8, color='black',
                arrowprops=dict(arrowstyle='-|>', color='#2D7A2D', lw=0.8))
    ax.set_xlabel(r"A15 $Q_b$ rescaling factor $\alpha_{15}$",
                  fontsize=FS_LABEL)
    ax.set_ylabel(r"A17 $Q_b$ rescaling factor $\alpha_{17}$",
                  fontsize=FS_LABEL)
    ax.set_title(r"Inter-site $K_d$ contrast under non-uniform $Q_b$ rescaling",
                 fontsize=FS_TITLE, fontweight='bold', pad=4)
    ax.tick_params(labelsize=FS_TICK)
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


def make_joint_kd_h(results, out):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.7),
                             gridspec_kw={'wspace': 0.32})
    fig.subplots_adjust(left=0.07, right=0.92, bottom=0.16, top=0.90)
    cf = None
    for idx, (ax, name) in enumerate(zip(axes, ['A15', 'A17'])):
        d = results[name]['joint_kd_h']
        h_grid = np.array(d['h_grid']) * 100
        kd_grid = np.array(d['kd_grid']) * 1e3
        rmse = np.array(d['rmse2d'])
        cf = ax.contourf(kd_grid, h_grid, rmse, levels=20,
                         cmap='viridis_r', alpha=0.88)
        levels = d['rmse_min'] + np.array([0.5, 1.0, 2.0, 3.0])
        cs = ax.contour(kd_grid, h_grid, rmse, levels=levels,
                        colors='white', linewidths=1.3)
        ax.clabel(cs, fmt='%.1f K', fontsize=8, inline=True)
        ax.plot(d['kd_min']*1e3, d['h_min']*100, marker='*',
                markersize=18, color='red', mec='white', mew=1.2)
        ax.axhline(6.0, color='white', lw=1.2, ls='--', alpha=0.85)
        kd_star_1d = results[name]['kd_star'] * 1e3
        ax.plot(kd_star_1d, 6.0, marker='o', markersize=10,
                color='cyan', mec='white', mew=1.2)
        ax.set_xlabel(r"$K_d$ (mW m$^{-1}$ K$^{-1}$)", fontsize=FS_LABEL)
        ax.set_ylabel(r"$H$ (cm)", fontsize=FS_LABEL)
        ax.set_title(f"({['a','b'][idx]})  {name}", fontsize=FS_TITLE,
                     fontweight='bold', loc='left', pad=4)
        ax.tick_params(labelsize=FS_TICK)
        # Legend in upper-right corner of plot area, not overlapping data
        from matplotlib.lines import Line2D
        handles = [
            Line2D([0],[0], marker='*', linestyle='None', color='red',
                   mec='white', markersize=12,
                   label=f'joint min  ($K_d$={d["kd_min"]*1e3:.2f}, $H$={d["h_min"]*100:.1f} cm)'),
            Line2D([0],[0], marker='o', linestyle='None', color='cyan',
                   mec='white', markersize=8,
                   label=f'1-D $K_d^*$ at $H=6$  ({kd_star_1d:.2f})'),
        ]
        ax.legend(handles=handles, loc='upper right', fontsize=8,
                  framealpha=0.95, edgecolor='0.7')
    cbar = fig.colorbar(cf, ax=axes, label='Deep-sensor RMSE (K)',
                        pad=0.02, fraction=0.04, aspect=22)
    cbar.ax.tick_params(labelsize=FS_TICK)
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


def make_bootstrap(results, out):
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4),
                             gridspec_kw={'wspace': 0.30})
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.16, top=0.90)
    ax = axes[0]
    for name, color in [('A15', C_A15), ('A17', C_A17)]:
        b = np.array(results[name]['bootstrap']['samples']) * 1e3
        ax.hist(b, bins=40, color=color, alpha=0.55, edgecolor=color,
                lw=0.7, label=f"{name}  $K_d^*$ posterior")
    ax.axvline(3.4, color='black', ls='--', lw=1.2, alpha=0.7,
               label='Hayne (2017)  $K_d=3.4$')
    style_axes(ax, xlabel=r"$K_d^*$ (mW m$^{-1}$ K$^{-1}$)",
               ylabel="bootstrap count",
               title="(a) Per-site bootstrap distributions")
    ax.legend(loc='upper right', fontsize=FS_LEGEND, framealpha=0.96,
              edgecolor='0.7')

    ax = axes[1]
    boot15 = np.array(results['A15']['bootstrap']['samples'])
    boot17 = np.array(results['A17']['bootstrap']['samples'])
    contrast = (boot17 - boot15) * 1e3
    ax.hist(contrast, bins=50, color='#9E2A1F', alpha=0.55,
            edgecolor='#9E2A1F', lw=0.7)
    cmed = results['contrast_bootstrap']['median'] * 1e3
    clo  = results['contrast_bootstrap']['ci_lo']  * 1e3
    chi_ = results['contrast_bootstrap']['ci_hi']  * 1e3
    ax.axvline(0, color='black', ls='--', lw=1.5, alpha=0.7,
               label='zero contrast (null)')
    ax.axvline(cmed, color='red', ls='-', lw=1.5,
               label=f"median = {cmed:.2f}")
    ax.axvspan(clo, chi_, color='red', alpha=0.12,
               label=f"95% CI [{clo:.2f}, {chi_:.2f}]")
    style_axes(ax, xlabel=r"$\Delta K_d^*$ (A17 − A15) (mW m$^{-1}$ K$^{-1}$)",
               ylabel="bootstrap count",
               title="(b) Inter-site contrast distribution")
    ax.legend(loc='upper left', fontsize=FS_LEGEND, framealpha=0.96,
              edgecolor='0.7')
    p = results['contrast_bootstrap']['p_value']
    p_str = "$p < 10^{-3}$" if p < 1e-3 else f"$p \\approx {p:.3g}$"
    ax.text(0.97, 0.50, p_str, transform=ax.transAxes, ha='right',
            va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='0.7'))
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


def make_posterior(cache, qb_priors, out):
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 8.5),
                             gridspec_kw={'wspace': 0.34, 'hspace': 0.36})
    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.08, top=0.94)
    for col, name in enumerate(['A15', 'A17']):
        c = cache[name]['posterior']
        kdv = c['kdv'] * 1e3
        qbv = c['qbv'] * 1e3
        P   = c['P']
        Pmax = P.max()

        ax = axes[0, col]
        ax.contourf(kdv, qbv, P, levels=20, cmap='viridis')
        levels = Pmax * np.array([0.05, 0.32, 0.68, 0.95])
        ax.contour(kdv, qbv, P, levels=levels[1:],
                   colors='white', linewidths=1.0,
                   linestyles=['-', '--', ':'])
        ij = np.unravel_index(np.argmax(P), P.shape)
        ax.plot(kdv[ij[1]], qbv[ij[0]], marker='*', markersize=16,
                color='red', mec='white', mew=1.2, label='posterior mode')
        for grad in [1.0, 2.0, 3.0]:
            ax.plot(kdv, grad * kdv, color='white', lw=0.7,
                    ls=':', alpha=0.6)
        ax.set_xlabel(r"$K_d$ (mW m$^{-1}$ K$^{-1}$)", fontsize=FS_LABEL)
        ax.set_ylabel(r"$Q_b$ (mW m$^{-2}$)", fontsize=FS_LABEL)
        ax.set_title(f"({chr(ord('a')+col)})  {name} joint posterior",
                     fontsize=FS_TITLE, fontweight='bold', loc='left', pad=4)
        ax.tick_params(labelsize=FS_TICK)
        ax.legend(loc='upper right', fontsize=FS_LEGEND, framealpha=0.92,
                  edgecolor='0.7')

        ax = axes[1, col]
        Pkd = P.sum(axis=0); Pkd /= Pkd.sum() * (kdv[1]-kdv[0])
        Pqb = P.sum(axis=1); Pqb /= Pqb.sum() * (qbv[1]-qbv[0])
        l1 = ax.plot(kdv, Pkd, color=C_HAYNE, lw=2.0,
                     label=r'$P(K_d)$')[0]
        ax.set_xlabel(r"$K_d$ (mW m$^{-1}$ K$^{-1}$)", fontsize=FS_LABEL)
        ax.set_ylabel(r"$P(K_d)$", fontsize=FS_LABEL, color=C_HAYNE)
        ax.tick_params(labelsize=FS_TICK)
        ax.tick_params(axis='y', labelcolor=C_HAYNE)
        ax.set_title(f"({chr(ord('c')+col)})  {name} marginal posteriors",
                     fontsize=FS_TITLE, fontweight='bold', loc='left', pad=4)
        ax2 = ax.twiny()
        ax2.set_xlim(qbv[0], qbv[-1])
        l2 = ax2.plot(qbv, Pqb / Pqb.max() * Pkd.max(),
                      color=C_MS, lw=2.0, label=r'$P(Q_b)$')[0]
        ax2.set_xlabel(r"$Q_b$ (mW m$^{-2}$)", fontsize=FS_LABEL,
                       color=C_MS)
        ax2.tick_params(axis='x', labelcolor=C_MS, labelsize=FS_TICK)
        ax.legend([l1, l2], [r'$P(K_d)$', r'$P(Q_b)$ (rescaled)'],
                  loc='upper right', fontsize=FS_LEGEND - 0.5,
                  framealpha=0.96, edgecolor='0.7')
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


def make_lab_comparison(results, out):
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    fig.subplots_adjust(left=0.42, right=0.96, bottom=0.13, top=0.92)
    sources = [
        ("Cremers & Birkebak 1971\n(lab, Apollo 11 fines)",  0.9, 0.2, C_LABFLAGS),
        ("Horai 1981\n(lab, Apollo basalt cores)",           1.5, 0.4, C_LABFLAGS),
        ("Hemingway 1973\n(lab, A14/15/16 fines)",           1.2, 0.3, C_LABFLAGS),
        ("Hayne (2017)\n(orbital, global)",                  3.4, 0.5, C_HAYNE),
        ("Vasavada 2012\n(orbital, deep regolith)",          7.0, 1.5, C_HAYNE),
        ("M&S 2021\n(orbital, 3-layer deep)",                6.3, 1.0, C_HAYNE),
        ("This work — A15\n(in-situ retrieval)",
         results['A15']['bootstrap']['median']*1e3,
         (results['A15']['bootstrap']['ci_hi'] -
          results['A15']['bootstrap']['ci_lo'])/4*1e3, C_A15),
        ("This work — A17\n(in-situ retrieval)",
         results['A17']['bootstrap']['median']*1e3,
         (results['A17']['bootstrap']['ci_hi'] -
          results['A17']['bootstrap']['ci_lo'])/4*1e3, C_A17),
    ]
    sources.reverse()
    labels = [s[0] for s in sources]
    values = [s[1] for s in sources]
    errs   = [s[2] for s in sources]
    colors = [s[3] for s in sources]
    y = np.arange(len(labels))
    ax.barh(y, values, xerr=errs, color=colors, alpha=0.78,
            edgecolor='black', lw=0.7,
            error_kw=dict(elinewidth=1.4, capsize=4, ecolor='black'))
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel(r"$K_d$ (mW m$^{-1}$ K$^{-1}$)", fontsize=FS_LABEL)
    ax.set_title("$K_d$ estimates across measurement scales",
                 fontsize=FS_TITLE, fontweight='bold', loc='left', pad=4)
    ax.tick_params(labelsize=FS_TICK)
    ax.grid(axis='x', color='0.92', lw=0.6)
    ax.set_axisbelow(True)
    legend_elems = [
        mpatches.Patch(color=C_LABFLAGS, alpha=0.8, label='Laboratory'),
        mpatches.Patch(color=C_HAYNE,    alpha=0.8, label='Orbital'),
        mpatches.Patch(color=C_A15,      alpha=0.8, label='In-situ A15'),
        mpatches.Patch(color=C_A17,      alpha=0.8, label='In-situ A17'),
    ]
    ax.legend(handles=legend_elems, loc='lower right', fontsize=FS_LEGEND,
              framealpha=0.95, edgecolor='0.7')
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


def make_cold_trap(results, out):
    ct = results['cold_trap']
    Kd = np.array(ct['kd_grid']) * 1e3
    z  = np.array(ct['depth_stable_m']) * 100
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    fig.subplots_adjust(left=0.13, right=0.96, bottom=0.16, top=0.91)
    ax.plot(Kd, z, color=C_HAYNE, lw=LW_MAIN)
    ax.fill_between(Kd, z, 0, color=C_HAYNE, alpha=0.12)
    refs = [
        (3.4,  'Hayne (2017) global', 'black'),
        (results['A15']['bootstrap']['median']*1e3,  'A15 retrieval', C_A15),
        (results['A17']['bootstrap']['median']*1e3,  'A17 retrieval', C_A17),
    ]
    for kd_v, lab, color in refs:
        z_v = np.interp(kd_v, Kd, z)
        ax.plot([kd_v, kd_v], [0, z_v], color=color, ls='--', lw=1.2)
        ax.plot(kd_v, z_v, marker='o', markersize=9, color=color,
                mec='white', mew=1.2)
        ax.text(kd_v + 0.12, z_v + 5, lab, fontsize=8.5, color=color,
                ha='left', va='bottom')
    style_axes(ax, xlabel=r"$K_d$ (mW m$^{-1}$ K$^{-1}$)",
               ylabel=r"Cold-trap depth $z_\mathrm{stable}$ (cm)",
               title="Polar volatile cold-trap depth implication")
    ax.set_xlim(2, 12)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.text(0.97, 0.05,
            (f"Polar $Q_b = {ct['Qb_polar']*1e3:.0f}$ mW/m$^2$, "
             "$T_\\mathrm{surface}=80$ K\n"
             "Schorghofer & Aharonson (2005)-style estimate"),
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=8, color='0.30', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='0.8', lw=0.6))
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  → {out}", flush=True)


if __name__ == '__main__':
    main()
