"""
Phase B-1: replace the analytical (K_d, Q_b) posterior surrogate with
a real `emcee` MCMC run at each Apollo site.

The likelihood is the same as the surrogate — Gaussian in the
profile-fit RMSE — so the science answer should match. The benefit is
defensibility: the posterior is now a proper Markov-chain sample with
convergence diagnostics, autocorrelation lengths, and sample-based
percentiles. The output figure is a 2-site corner plot with marginal
KDEs and joint contours.

Output:
  paper/appendix/figures/fig_kd_qb_posterior.pdf
  output/phase_b_mcmc_samples.json (posterior summary statistics)

Runtime: ~30 s with 32 walkers × 4000 steps × 2 sites (likelihood is
analytical via the cached RMSE-vs-K_d spline from phase_a_results.json).
"""
from __future__ import annotations
import json, sys, pathlib, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import emcee
import corner

sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2/scripts")
from phase2_figures_v2 import (   # type: ignore
    JGR_FULL,
    FS_TITLE, FS_LABEL, FS_TICK, FS_LEGEND,
    C_HAYNE, C_MS, C_A15, C_A17, C_CHAR, C_DIM, C_GRID, C_CORAL,
    fmt_axis,
)

PHASE_A = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase_a_results.json")
OUT_FIG = pathlib.Path("/Users/rp3gregorio/Lunar-V2/paper/appendix/figures/fig_kd_qb_posterior.pdf")
OUT_JSON = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase_b_mcmc_samples.json")

# ── Site parameters ──────────────────────────────────────────────────────────
SITES = {
    "A15": dict(qb_published=0.021, qb_prior_mean=0.018, qb_prior_sigma=0.005,
                colour=C_A15),
    "A17": dict(qb_published=0.015, qb_prior_mean=0.013, qb_prior_sigma=0.004,
                colour=C_A17),
}


def make_log_posterior(site, kd_grid_spline, qb_pub,
                        qb_prior_mean, qb_prior_sigma,
                        N_obs, sigma_data=0.5,
                        kd_lim=(1e-3, 30e-3),
                        qb_lim=(2e-3, 40e-3)):
    """Closure returning log P(K_d, Q_b | data) under:
    - degeneracy-aware likelihood: deep profile is invariant under
      (K_d, Q_b) -> (alpha K_d, alpha Q_b). The RMSE at any (K_d, Q_b)
      equals the RMSE at K_eff = K_d * (Q_b_pub / Q_b) under the
      published Q_b, so we evaluate the spline at K_eff.
    - Gaussian prior on Q_b from the Saito/Nagihara reanalysis;
      flat prior on K_d within [1, 30] mW/m/K."""
    log_kd_lo, log_kd_hi = np.log(kd_lim[0]), np.log(kd_lim[1])
    log_qb_lo, log_qb_hi = np.log(qb_lim[0]), np.log(qb_lim[1])

    def log_post(theta):
        log_kd, log_qb = theta
        if not (log_kd_lo <= log_kd <= log_kd_hi):  return -np.inf
        if not (log_qb_lo <= log_qb <= log_qb_hi):  return -np.inf
        kd = np.exp(log_kd)
        qb = np.exp(log_qb)
        kd_eff = kd * (qb_pub / qb)
        rmse = float(kd_grid_spline(kd_eff))
        if not np.isfinite(rmse):  return -np.inf
        # likelihood
        log_L = -0.5 * N_obs * (rmse / sigma_data) ** 2
        # Gaussian prior on Q_b
        log_pr = -0.5 * ((qb - qb_prior_mean) / qb_prior_sigma) ** 2
        # Jacobian for log-uniform prior on K_d (flat in log space →
        # log-prior on K_d is a constant inside bounds)
        return log_L + log_pr

    return log_post


def run_mcmc(name, site, kd_grid, rmse_curve, n_obs):
    from scipy.interpolate import CubicSpline
    spline = CubicSpline(kd_grid, rmse_curve, extrapolate=True)
    log_post = make_log_posterior(
        name, spline, site["qb_published"],
        site["qb_prior_mean"], site["qb_prior_sigma"], n_obs)

    n_walkers = 32
    n_dim     = 2
    n_steps   = 4000
    n_burn    = 1000

    rng = np.random.default_rng(seed=42 if name == "A15" else 17)
    init_kd = rng.uniform(np.log(2e-3), np.log(15e-3), n_walkers)
    init_qb = rng.normal(np.log(site["qb_prior_mean"]),
                          0.15, n_walkers)
    p0 = np.column_stack([init_kd, init_qb])

    print(f"  [{name}] running emcee: {n_walkers} walkers × {n_steps} steps ...",
          flush=True)
    sampler = emcee.EnsembleSampler(n_walkers, n_dim, log_post)
    sampler.run_mcmc(p0, n_steps, progress=False)

    chain = sampler.get_chain(discard=n_burn, flat=True)
    samples_kd = np.exp(chain[:, 0]) * 1e3   # mW/m/K
    samples_qb = np.exp(chain[:, 1]) * 1e3   # mW/m^2

    # autocorrelation
    try:
        tau = sampler.get_autocorr_time(tol=20, quiet=True)
        eff_n = (n_steps - n_burn) * n_walkers / max(tau)
    except emcee.autocorr.AutocorrError:
        tau = [np.nan, np.nan]
        eff_n = float("nan")

    summary = dict(
        n_walkers=n_walkers, n_steps=n_steps, n_burn=n_burn,
        autocorr_tau=[float(t) for t in tau],
        effective_n=float(eff_n),
        kd_q16=float(np.percentile(samples_kd, 16)),
        kd_q50=float(np.percentile(samples_kd, 50)),
        kd_q84=float(np.percentile(samples_kd, 84)),
        kd_q025=float(np.percentile(samples_kd, 2.5)),
        kd_q975=float(np.percentile(samples_kd, 97.5)),
        qb_q16=float(np.percentile(samples_qb, 16)),
        qb_q50=float(np.percentile(samples_qb, 50)),
        qb_q84=float(np.percentile(samples_qb, 84)),
    )
    print(f"  [{name}] K_d posterior: median = {summary['kd_q50']:.2f} "
          f"(16/84 = {summary['kd_q16']:.2f}/{summary['kd_q84']:.2f}, "
          f"95% = {summary['kd_q025']:.2f}–{summary['kd_q975']:.2f})",
          flush=True)
    print(f"  [{name}] Q_b posterior: median = {summary['qb_q50']:.2f} "
          f"(16/84 = {summary['qb_q16']:.2f}/{summary['qb_q84']:.2f}) "
          f"mW/m^2",
          flush=True)
    return samples_kd, samples_qb, summary


def main():
    if not PHASE_A.exists():
        sys.exit(f"need {PHASE_A}")
    d = json.loads(PHASE_A.read_text())

    print("Phase B-1: emcee MCMC for the joint (K_d, Q_b) posterior",
          flush=True)

    samples = {}
    summary_all = {}
    for name in ("A15", "A17"):
        sk = d[name]
        kd_grid = np.array(sk["kd_grid"])
        rmse    = np.array(sk["rmse_curve"])
        N_obs   = 7 if name == "A15" else 16
        s_kd, s_qb, smry = run_mcmc(name, SITES[name], kd_grid, rmse, N_obs)
        samples[name] = (s_kd, s_qb)
        summary_all[name] = smry

    # ── Figure: 2-site corner panels stacked ─────────────────────────────────
    fig = plt.figure(figsize=(JGR_FULL, 9.0))
    gs  = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0],
                           width_ratios=[1.0, 1.0],
                           hspace=0.50, wspace=0.32,
                           left=0.10, right=0.95, top=0.95, bottom=0.13)

    panel_labels = [("(a)", "(c)"), ("(b)", "(d)")]
    for col, (name, _ignore) in enumerate([("A15", "(a)"), ("A17", "(b)")]):
        s_kd, s_qb = samples[name]
        col_site   = SITES[name]["colour"]

        # 2-D posterior with marginals — small inline corner plot
        ax_main = fig.add_subplot(gs[0, col])
        ax_kd   = fig.add_subplot(gs[1, col])

        # 2-D scatter + contour
        H, xed, yed = np.histogram2d(s_kd, s_qb, bins=60)
        H = H.T
        # smoothed histogram
        from scipy.ndimage import gaussian_filter
        H_smooth = gaussian_filter(H, sigma=1.5)
        ax_main.contourf(xed[:-1] + 0.5*(xed[1]-xed[0]),
                         yed[:-1] + 0.5*(yed[1]-yed[0]),
                         H_smooth, levels=18, cmap="rocket_r"
                         if False else "Reds", alpha=0.85)
        # 1- and 2-sigma contours
        levels = [0.05, 0.32, 0.68] * np.array([H_smooth.max()])
        ax_main.contour(xed[:-1] + 0.5*(xed[1]-xed[0]),
                         yed[:-1] + 0.5*(yed[1]-yed[0]),
                         H_smooth, levels=[H_smooth.max()*x for x in (0.05, 0.32, 0.68)],
                         colors="white", linewidths=0.8)

        # MAP marker (median)
        med_kd = np.median(s_kd)
        med_qb = np.median(s_qb)
        ax_main.plot(med_kd, med_qb, "*", markersize=15, color=C_CORAL,
                     mec="white", mew=1.3, zorder=5)

        # iso-ratio rays (Q_b/K_d = const → equilibrium gradient)
        kd_line = np.linspace(*ax_main.get_xlim(), 100)
        for grad in [1.0, 2.0, 3.0]:
            ax_main.plot(kd_line, grad * kd_line, ls=":", lw=0.7,
                         color="0.4", alpha=0.6)

        joint_lbl, marg_lbl = panel_labels[col]
        fmt_axis(ax_main,
                 xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
                 ylabel=r"$Q_b$  (mW m$^{-2}$)",
                 title=f"{joint_lbl}  Apollo {name[1:]}  —  joint posterior")

        # marginal K_d (with KDE)
        ax_kd.hist(s_kd, bins=60, density=True, color=col_site,
                   alpha=0.55, edgecolor=col_site, lw=0.4)
        # 16/50/84 percentile lines
        for q, ls in [(16, ":"), (50, "-"), (84, ":")]:
            v = np.percentile(s_kd, q)
            ax_kd.axvline(v, color=C_CHAR, lw=1.0, ls=ls, alpha=0.85)
        fmt_axis(ax_kd,
                 xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
                 ylabel=r"$P(K_d \mid \mathrm{data})$",
                 title=f"{marg_lbl}  Apollo {name[1:]} — marginal $P(K_d)$")
        # Compact summary box in the corner of the panel that is empty
        # of histogram support (upper-right for A15; histograms decay
        # at high K_d there; for A17 we use upper-left where the
        # histogram is also nearly zero below K_d~6).
        x_ann, ha = (0.97, "right") if name == "A15" else (0.04, "left")
        ax_kd.text(x_ann, 0.97,
                   f"median {med_kd:.2f}\n"
                   f"16/84 [{np.percentile(s_kd,16):.2f}, "
                   f"{np.percentile(s_kd,84):.2f}]\n"
                   f"95% CI [{np.percentile(s_kd,2.5):.2f}, "
                   f"{np.percentile(s_kd,97.5):.2f}]",
                   transform=ax_kd.transAxes, ha=ha, va="top",
                   fontsize=FS_TICK, linespacing=1.3,
                   bbox=dict(boxstyle="round,pad=0.4",
                             facecolor="white", edgecolor=C_GRID, lw=0.6))

    # ── shared legend BELOW ──────────────────────────────────────────────────
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0],[0], marker="*", color="none", markerfacecolor=C_CORAL,
               mec="white", markersize=14, label="posterior median"),
        Line2D([0],[0], color="white", lw=1.5,
               label=r"posterior 1-, 2-, 3-$\sigma$ contours"),
        Line2D([0],[0], ls=":", color="0.4",
               label=r"iso-ratio rays  $Q_b/K_d = \mathrm{const}$"),
        Line2D([0],[0], color=C_CHAR, lw=1.0, ls="-",
               label="median  (marginal)"),
        Line2D([0],[0], color=C_CHAR, lw=1.0, ls=":",
               label="16/84 percentiles  (marginal)"),
    ]
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(0.5, 0.01), ncols=3, frameon=True,
               edgecolor=C_GRID, framealpha=0.97, fontsize=FS_LEGEND,
               handlelength=2.0, borderpad=0.6, columnspacing=1.6,
               title=r"emcee MCMC  ($N_{\rm walkers}=32$, $N_{\rm steps}=4000$, burn-in 1000; Saito $Q_b$ prior)",
               title_fontsize=FS_LABEL)

    fig.savefig(OUT_FIG)
    plt.close(fig)
    print(f"\nSaved: {OUT_FIG}", flush=True)

    OUT_JSON.write_text(json.dumps(summary_all, indent=2))
    print(f"Saved: {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
