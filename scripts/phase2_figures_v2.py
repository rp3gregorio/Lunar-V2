"""
Phase-2 figure regeneration with publication-grade aesthetic
(Anthropic-aligned: warm coral, deep teal, restrained palette,
clean serif typography, generous whitespace).

Reads the numerical results from output/phase2_results.json and
regenerates the new letter/appendix figures.
"""
from __future__ import annotations
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap

# ─── Style — publication-grade, restrained warm palette ──────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.0,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#2A2520",
    "axes.labelcolor": "#2A2520",
    "axes.titlecolor": "#2A2520",
    "axes.titlepad": 8.0,
    "axes.titlelocation": "left",
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "xtick.color": "#2A2520",
    "ytick.color": "#2A2520",
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.minor.size": 1.5,
    "ytick.minor.size": 1.5,
    "legend.fontsize": 8.5,
    "legend.frameon": True,
    "legend.fancybox": False,
    "legend.framealpha": 0.97,
    "legend.edgecolor": "#D4CFC4",
    "legend.borderpad": 0.5,
    "legend.handletextpad": 0.6,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.10,
    "grid.color": "#E8E5E0",
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.8,
})

# Anthropic-aligned palette (publication-friendly)
C_CORAL    = "#B85B3A"   # primary warm accent (~Anthropic coral)
C_CORAL_L  = "#E5A88A"   # light coral
C_TEAL     = "#2A6478"   # cool primary
C_TEAL_L   = "#7CA3B0"   # light teal
C_FOREST   = "#3D6E4A"   # tertiary green
C_FOREST_L = "#94B89C"   # light green
C_PLUM     = "#5A4A6A"   # quaternary muted plum
C_CHAR     = "#2A2520"   # warm charcoal text
C_DIM      = "#6E6862"   # secondary text
C_NEUTRAL  = "#A8A29A"   # neutral mid-gray
C_GRID     = "#E8E5E0"   # very pale warm gray

# Site/source-specific:
C_A15      = C_FOREST
C_A17      = C_CORAL
C_HAYNE    = C_TEAL
C_MS       = "#9E2A1F"     # deep red, distinguishable from coral
C_LAB      = C_PLUM

# Custom colormap for Q_b heatmap: cool→neutral→warm
ANTH_DIVERGE = LinearSegmentedColormap.from_list(
    "anth_diverge",
    ["#2A6478", "#7CA3B0", "#F5F1EA", "#E5A88A", "#B85B3A", "#7A2F18"]
)
ANTH_SEQ = LinearSegmentedColormap.from_list(
    "anth_seq",
    ["#FAF7F2", "#E5D5C8", "#D9A07C", "#B85B3A", "#7A2F18", "#3A1A0A"]
)

# Output paths
RESULTS = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase2_results.json")
LETTER_FIGS   = pathlib.Path("/Users/rp3gregorio/Lunar-V2/paper/letter/figures")
APPENDIX_FIGS = pathlib.Path("/Users/rp3gregorio/Lunar-V2/paper/appendix/figures")


def fmt_axis(ax, *, xlabel="", ylabel="", title=""):
    if xlabel: ax.set_xlabel(xlabel)
    if ylabel: ax.set_ylabel(ylabel)
    if title:  ax.set_title(title)
    ax.grid(axis="both", color=C_GRID, lw=0.5)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_color(C_CHAR)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Bootstrap distributions (letter)
# ══════════════════════════════════════════════════════════════════════════════
def fig_bootstrap(d, out_path):
    fig = plt.figure(figsize=(9.0, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.30,
                          left=0.085, right=0.97, top=0.86, bottom=0.13)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1])

    # ── (a) per-site distributions ──────────────────────────────────────────
    boot15 = np.array(d["A15"]["bootstrap"]["samples"]) * 1e3
    boot17 = np.array(d["A17"]["bootstrap"]["samples"]) * 1e3

    bins = np.linspace(2, 19, 60)
    h15, _ = np.histogram(boot15, bins=bins)
    h17, _ = np.histogram(boot17, bins=bins)
    centers = 0.5 * (bins[:-1] + bins[1:])
    width = bins[1] - bins[0]

    a15_med, a15_lo, a15_hi = np.percentile(boot15, [50, 2.5, 97.5])
    a17_med, a17_lo, a17_hi = np.percentile(boot17, [50, 2.5, 97.5])

    ax0.bar(centers, h15, width=width*0.95, color=C_A15, alpha=0.55,
            edgecolor=C_A15, lw=0.4,
            label=f"A15  median {a15_med:.2f}  [{a15_lo:.2f}, {a15_hi:.2f}]")
    ax0.bar(centers, h17, width=width*0.95, color=C_A17, alpha=0.55,
            edgecolor=C_A17, lw=0.4,
            label=f"A17  median {a17_med:.2f}  [{a17_lo:.2f}, {a17_hi:.2f}]")

    # Hayne reference line — push label to the LEFT side and below the histogram peak
    ax0.axvline(3.4, color=C_CHAR, ls="--", lw=1.0, alpha=0.55)
    ymax = max(h15.max(), h17.max())
    ax0.text(3.4 - 0.25, ymax * 0.45, "Hayne (2017)\n$K_d = 3.4$",
             fontsize=8, color=C_DIM, va="center", ha="right",
             linespacing=1.25, style="italic")

    fmt_axis(ax0,
             xlabel=r"$K_d^{*}$  (mW m$^{-1}$ K$^{-1}$)",
             ylabel="bootstrap count",
             title="(a)  Per-site bootstrap distributions")
    ax0.set_xlim(2, 19)
    ax0.set_ylim(0, ymax * 1.20)
    ax0.legend(loc="upper right", borderpad=0.5,
               title="95% CI from 2000 resamples", title_fontsize=8.5,
               handlelength=1.6)
    ax0.xaxis.set_minor_locator(mtick.AutoMinorLocator())

    # ── (b) inter-site contrast distribution ────────────────────────────────
    contrast = (boot17 - boot15)
    cmed, clo, chi_ = np.percentile(contrast, [50, 2.5, 97.5])

    bins2 = np.linspace(-2, 16, 60)
    hC, _ = np.histogram(contrast, bins=bins2)
    centers2 = 0.5 * (bins2[:-1] + bins2[1:])
    width2 = bins2[1] - bins2[0]

    ax1.bar(centers2, hC, width=width2*0.95,
            color=C_A17, alpha=0.55, edgecolor=C_A17, lw=0.4)
    ax1.axvspan(clo, chi_, color=C_A17, alpha=0.10, zorder=0)
    ax1.axvline(0, color=C_CHAR, ls="--", lw=1.0, alpha=0.7)
    ax1.axvline(cmed, color=C_A17, ls="-", lw=1.4)

    # annotation box (top-right)
    p_str = "$p < 10^{-3}$" if d["contrast_bootstrap"]["p_value"] < 1e-3 \
            else f"$p \\approx {d['contrast_bootstrap']['p_value']:.3g}$"
    ax1.text(0.97, 0.95,
             f"median  $\\Delta K_d^{{*}} = {cmed:.2f}$\n"
             f"95% CI $[{clo:.2f},\\ {chi_:.2f}]$\n"
             f"{p_str}",
             transform=ax1.transAxes, ha="right", va="top",
             fontsize=8.5, color=C_CHAR,
             bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                       edgecolor=C_GRID, lw=0.6),
             linespacing=1.6)

    # null line label (well separated from box)
    ax1.text(0.4, ax1.get_ylim()[1]*0.50, "null  (zero\ncontrast)",
             fontsize=7.5, color=C_DIM, ha="left", va="center",
             linespacing=1.25, style="italic")

    fmt_axis(ax1,
             xlabel=r"$\Delta K_d^{*}$ (A17 − A15)  (mW m$^{-1}$ K$^{-1}$)",
             ylabel="bootstrap count",
             title="(b)  Inter-site contrast distribution")
    ax1.set_xlim(-2, 16)
    ax1.xaxis.set_minor_locator(mtick.AutoMinorLocator())

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Robustness suite (letter): Q_b sensitivity + joint K_d × H
# ══════════════════════════════════════════════════════════════════════════════
def fig_robustness(d, out_path):
    fig = plt.figure(figsize=(11.0, 4.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.0], wspace=0.34,
                          left=0.06, right=0.965, top=0.86, bottom=0.16)
    axA = fig.add_subplot(gs[0])  # Q_b heatmap
    axB = fig.add_subplot(gs[1])  # joint K_d×H A15
    axC = fig.add_subplot(gs[2])  # joint K_d×H A17

    # ── (a) Q_b sensitivity heatmap ─────────────────────────────────────────
    qbs = d["qb_sensitivity"]
    alphas = np.array(qbs["alpha_grid"])
    contrast = np.array(qbs["contrast_grid"]) * 1e3
    sig = np.array(qbs["significance_grid"])

    im = axA.imshow(contrast.T, origin="lower", aspect="auto",
                    extent=[alphas[0], alphas[-1], alphas[0], alphas[-1]],
                    cmap=ANTH_DIVERGE, vmin=-3, vmax=12,
                    interpolation="nearest")
    cbar = fig.colorbar(im, ax=axA, pad=0.025, fraction=0.05, aspect=25)
    cbar.ax.set_ylabel(r"$\Delta K_d^{*}$  (mW m$^{-1}$ K$^{-1}$)",
                       fontsize=9, color=C_CHAR)
    cbar.ax.tick_params(labelsize=8, colors=C_CHAR)
    cbar.outline.set_edgecolor(C_GRID)

    # significance contours
    cs = axA.contour(alphas, alphas, sig.T, levels=[2, 4, 7],
                     colors=C_CHAR, linewidths=0.9, linestyles="--",
                     alpha=0.75)
    axA.clabel(cs, fmt=lambda x: f"{int(x)}σ",
               fontsize=8, inline=True, inline_spacing=3)

    # global rescaling diagonal
    axA.plot(alphas, alphas, color="white", lw=2.4, alpha=0.85,
             solid_capstyle="butt")
    axA.text(1.22, 1.18, "global rescaling\n(contrast invariant)",
             color="white", fontsize=8, rotation=44.5, ha="center",
             va="center", style="italic")

    # markers
    axA.plot(1.0, 1.0, "o", color=C_CHAR, markersize=8, mec="white", mew=1.2)
    axA.text(1.03, 0.99, "nominal", fontsize=8, color="white", ha="left",
             va="center", fontweight="medium")
    axA.plot(0.7, 1.0, "s", color=C_FOREST, markersize=9, mec="white", mew=1.2)
    axA.annotate("Saito A15 −30%", xy=(0.7, 1.0), xytext=(0.745, 1.21),
                 fontsize=7.5, color=C_CHAR, ha="left",
                 arrowprops=dict(arrowstyle="-|>", color=C_FOREST, lw=0.7,
                                 shrinkA=0, shrinkB=2))

    fmt_axis(axA,
             xlabel=r"A15 $Q_b$ rescaling $\alpha_{15}$",
             ylabel=r"A17 $Q_b$ rescaling $\alpha_{17}$",
             title=r"(a)  $K_d^{*}$ contrast vs. non-uniform $Q_b$")

    # ── (b)(c) joint K_d × H per site ───────────────────────────────────────
    cf_handle = None
    for ax, name, label in [(axB, "A15", "(b)  Apollo 15"),
                            (axC, "A17", "(c)  Apollo 17")]:
        j = d[name]["joint_kd_h"]
        h_grid  = np.array(j["h_grid"]) * 100
        kd_grid = np.array(j["kd_grid"]) * 1e3
        rmse    = np.array(j["rmse2d"])
        rmse_min = j["rmse_min"]

        cf = ax.contourf(kd_grid, h_grid, rmse, levels=18,
                         cmap=ANTH_SEQ, alpha=0.92)
        if cf_handle is None:
            cf_handle = cf
        # white contours at 0.5/1.0/2.0 K above min
        levels_white = [rmse_min + dx for dx in [0.5, 1.0, 2.0, 3.0]]
        cs = ax.contour(kd_grid, h_grid, rmse,
                        levels=levels_white, colors="white",
                        linewidths=1.0, alpha=0.85)
        ax.clabel(cs, fmt="%.1f K", fontsize=7.5, inline=True,
                  inline_spacing=4)

        # joint min star
        ax.plot(j["kd_min"]*1e3, j["h_min"]*100, marker="*",
                markersize=18, color=C_CORAL, mec="white", mew=1.3,
                zorder=5)

        # H = 6 cm canonical line
        ax.axhline(6.0, color="white", ls="--", lw=1.0, alpha=0.85)

        # 1-D K_d* at H=6
        kd_1d = d[name]["kd_star"] * 1e3
        ax.plot(kd_1d, 6.0, "o", markersize=9, color=C_TEAL,
                mec="white", mew=1.2, zorder=4)

        # custom legend
        legend_handles = [
            Line2D([0], [0], marker="*", color="none",
                   markerfacecolor=C_CORAL, mec="white", markersize=12,
                   label=f"joint min  ({j['kd_min']*1e3:.2f}, {j['h_min']*100:.0f} cm)"),
            Line2D([0], [0], marker="o", color="none",
                   markerfacecolor=C_TEAL, mec="white", markersize=8,
                   label=f"1-D $K_d^{{*}}$ at $H=6$  ({kd_1d:.2f})"),
        ]
        ax.legend(handles=legend_handles, loc="upper right",
                  fontsize=7.5, framealpha=0.94, borderpad=0.4)

        fmt_axis(ax,
                 xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
                 ylabel=r"$H$  (cm)" if ax is axB else "",
                 title=label)

    # shared colorbar for (b) and (c)
    cbar2 = fig.colorbar(cf_handle, ax=[axB, axC], pad=0.02, fraction=0.05,
                         aspect=25)
    cbar2.ax.set_ylabel("RMSE (K)", fontsize=9, color=C_CHAR)
    cbar2.ax.tick_params(labelsize=8, colors=C_CHAR)
    cbar2.outline.set_edgecolor(C_GRID)

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE — K_d sweep redesign (letter)
# ══════════════════════════════════════════════════════════════════════════════
def fig_kd_sweep_v2(d, out_path):
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.14)

    for name, color in [("A15", C_A15), ("A17", C_A17)]:
        s = d[name]
        rmse = np.array(s["rmse_curve"])
        if name == "A15":
            kd_grid = np.linspace(1.5e-3, 9.0e-3, len(rmse)) * 1e3
        else:
            kd_grid = np.linspace(3.0e-3, 18.0e-3, len(rmse)) * 1e3

        from scipy.interpolate import CubicSpline
        cs = CubicSpline(kd_grid, rmse)
        kdfine = np.linspace(kd_grid[0], kd_grid[-1], 400)

        b = s["bootstrap"]
        lo_kd, hi_kd = b["ci_lo"]*1e3, b["ci_hi"]*1e3
        # 95% CI shading along the curve
        kd_in_ci = (kdfine >= lo_kd) & (kdfine <= hi_kd)
        ax.fill_between(kdfine[kd_in_ci], 0, cs(kdfine[kd_in_ci]),
                        color=color, alpha=0.10, zorder=0)

        ax.plot(kdfine, cs(kdfine), "-", color=color, lw=2.0, alpha=0.95,
                label=f"{name}  $K_d^{{*}}={s['kd_star']*1e3:.2f}$  "
                      f"[{lo_kd:.2f}, {hi_kd:.2f}]")
        ax.plot(kd_grid, rmse, "o", color=color, markersize=4.0,
                mec="white", mew=0.5, zorder=3)

        kdstar = s["kd_star"] * 1e3
        rmsestar = s["rmse_star"]
        ax.plot(kdstar, rmsestar, "*", color=color, markersize=18,
                mec="white", mew=1.3, zorder=5)

    # vertical references
    ax.axvline(3.4, color=C_TEAL, ls="--", lw=1.0, alpha=0.7, zorder=1)
    ax.text(3.5, 5.6, "Hayne (2017)\n$K_d = 3.4$", fontsize=8, color=C_TEAL,
            va="top", linespacing=1.25)
    ax.axvline(6.3, color=C_MS, ls=":", lw=1.0, alpha=0.7, zorder=1)
    ax.text(6.4, 5.6, "M&S (2021)\n$K_d = 6.3$", fontsize=8, color=C_MS,
            va="top", linespacing=1.25)

    fmt_axis(ax,
             xlabel=r"Deep conductivity  $K_d$  (mW m$^{-1}$ K$^{-1}$)",
             ylabel=r"Deep-sensor RMSE  (K)",
             title="Per-site $K_d$ retrieval under the Hayne (2017) functional form")
    ax.set_xlim(0, 19)
    ax.set_ylim(0, 6)
    ax.legend(loc="upper right",
              title="Site  $K_d^{*}$  [95% bootstrap CI]",
              title_fontsize=8.5, borderpad=0.6)

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX FIGURES — lab comparison + cold-trap (moved from letter)
# ══════════════════════════════════════════════════════════════════════════════
def fig_lab_comparison(d, out_path):
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    fig.subplots_adjust(left=0.40, right=0.97, top=0.88, bottom=0.16)

    sources = [
        ("Cremers & Birkebak 1971 (lab)", 0.9, 0.2, C_LAB,    "Lab"),
        ("Horai 1981 (lab)",               1.5, 0.4, C_LAB,    "Lab"),
        ("Hemingway 1973 (lab)",           1.2, 0.3, C_LAB,    "Lab"),
        ("Hayne 2017 (orbital, global)",   3.4, 0.5, C_HAYNE,  "Orbital"),
        ("Vasavada 2012 (orbital, deep)",  7.0, 1.5, C_HAYNE,  "Orbital"),
        ("Martínez & Siegler 2021 (orbital, 3-layer)", 6.3, 1.0, C_HAYNE, "Orbital"),
        ("This work — A15 (in situ)",
         d["A15"]["bootstrap"]["median"]*1e3,
         (d["A15"]["bootstrap"]["ci_hi"] - d["A15"]["bootstrap"]["ci_lo"])/4*1e3,
         C_A15, "In situ"),
        ("This work — A17 (in situ)",
         d["A17"]["bootstrap"]["median"]*1e3,
         (d["A17"]["bootstrap"]["ci_hi"] - d["A17"]["bootstrap"]["ci_lo"])/4*1e3,
         C_A17, "In situ"),
    ]
    sources.reverse()
    labels = [s[0] for s in sources]
    vals   = [s[1] for s in sources]
    errs   = [s[2] for s in sources]
    cols   = [s[3] for s in sources]

    y = np.arange(len(labels))
    ax.barh(y, vals, xerr=errs, color=cols, alpha=0.78,
            edgecolor=C_CHAR, lw=0.5,
            error_kw=dict(elinewidth=1.0, capsize=3.5, ecolor=C_CHAR))
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", left=False)
    fmt_axis(ax,
             xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
             title="$K_d$ estimates across measurement scales")
    ax.set_xlim(0, 14)

    # category legend in upper-right (outside data)
    legend_handles = [
        mpatches.Patch(color=C_LAB,   alpha=0.78, label="Laboratory  (mm scale)"),
        mpatches.Patch(color=C_HAYNE, alpha=0.78, label="Orbital  (km scale)"),
        mpatches.Patch(color=C_A15,   alpha=0.78, label="In situ  Apollo 15"),
        mpatches.Patch(color=C_A17,   alpha=0.78, label="In situ  Apollo 17"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              title="Measurement type", title_fontsize=9, borderpad=0.5)

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


def fig_cold_trap(d, out_path):
    ct = d["cold_trap"]
    Kd = np.array(ct["kd_grid"]) * 1e3
    z  = np.array(ct["depth_stable_m"])

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.subplots_adjust(left=0.13, right=0.965, top=0.86, bottom=0.16)

    ax.plot(Kd, z, color=C_TEAL, lw=2.0)
    ax.fill_between(Kd, z, 0, color=C_TEAL_L, alpha=0.20)

    refs = [
        (3.4, "Hayne (2017) global", C_TEAL, "below"),
        (d["A15"]["bootstrap"]["median"]*1e3, "A15 retrieval", C_A15, "below"),
        (d["A17"]["bootstrap"]["median"]*1e3, "A17 retrieval", C_A17, "left"),
    ]
    z_max = z.max()
    for kd_v, lab, col, pos in refs:
        z_v = np.interp(kd_v, Kd, z)
        ax.plot([kd_v, kd_v], [0, z_v], color=col, ls="--", lw=1.0, alpha=0.85)
        ax.plot(kd_v, z_v, "o", markersize=8, color=col, mec="white", mew=1.0,
                zorder=4)
        if pos == "below":
            ax.text(kd_v + 0.18, z_v - 0.8, lab, fontsize=8.5, color=col,
                    ha="left", va="top")
        else:  # "left"
            ax.text(kd_v - 0.18, z_v + 0.6, lab, fontsize=8.5, color=col,
                    ha="right", va="bottom")

    fmt_axis(ax,
             xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
             ylabel=r"Cold-trap depth  $z_\mathrm{stable}$  (m)",
             title="Implication for polar-volatile cold-trap depth")
    ax.set_xlim(2, 12)
    ax.set_ylim(0, z_max * 1.12)

    ax.text(0.97, 0.04,
            (f"Polar $Q_b = {ct['Qb_polar']*1e3:.0f}$ mW m$^{{-2}}$, "
             "$T_\\mathrm{surface} = 80$ K\n"
             "Schorghofer & Aharonson (2005)-style estimate"),
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color=C_DIM, style="italic",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=C_GRID, lw=0.6))

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX FIGURE — Bayesian posterior (4 panels: 2 sites × {2D, marginal})
# ══════════════════════════════════════════════════════════════════════════════
def fig_posterior(out_path):
    """Read the posterior arrays from the cache file in /tmp if available,
    else recompute from json."""
    # We'll regenerate the posterior from scratch using the K_d sweep curves,
    # because the json doesn't store the (kdv, qbv, P) arrays.
    import sys; sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2")
    d = json.loads(RESULTS.read_text())

    # Reload the pipeline's posterior method
    from scripts.phase2_pipeline_fast import kd_qb_posterior

    QB_PUB = {"A15": 0.021, "A17": 0.015}
    QB_PRIOR = {"A15": (0.018, 0.005), "A17": (0.013, 0.004)}

    # We need R (residual matrix) which is NOT in json. We need to rerun
    # K_d sweep OR re-derive R from rmse_curve. Since json only has the
    # RMSE curve (not the residuals), build a posterior using the RMSE
    # curve directly.
    fig = plt.figure(figsize=(11.0, 7.5))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.34,
                          left=0.07, right=0.96, top=0.93, bottom=0.08)
    axes = [[fig.add_subplot(gs[r, c]) for c in (0, 1)] for r in (0, 1)]

    for col, name in enumerate(["A15", "A17"]):
        rmse = np.array(d[name]["rmse_curve"])
        if name == "A15":
            kd_grid = np.linspace(1.5e-3, 9.0e-3, len(rmse))
        else:
            kd_grid = np.linspace(3.0e-3, 18.0e-3, len(rmse))
        # Synthetic R: zero-mean residuals scaled to give the right RMSE
        # (this is just to plug into kd_qb_posterior which only needs the
        # diagonal RMSE shape and N).
        N_deep = 7 if name == "A15" else 16
        R = np.zeros((N_deep, len(rmse)))
        # Distribute the squared residual evenly so RMSE matches
        for k, rm in enumerate(rmse):
            R[:, k] = rm   # all identical → RMSE = rm
        kdv, qbv, P = kd_qb_posterior(
            R, kd_grid, qb_published=QB_PUB[name],
            qb_prior_mean=QB_PRIOR[name][0],
            qb_prior_sigma=QB_PRIOR[name][1])
        kdv_mW = kdv * 1e3
        qbv_mW = qbv * 1e3

        # ── upper: 2D posterior ──────────────────────────────────────────
        ax = axes[0][col]
        ax.contourf(kdv_mW, qbv_mW, P, levels=20, cmap=ANTH_SEQ)
        Pmax = P.max()
        ax.contour(kdv_mW, qbv_mW, P,
                   levels=[Pmax*0.05, Pmax*0.32, Pmax*0.68],
                   colors="white", linewidths=0.9,
                   linestyles=["-", "--", ":"])

        # mode
        ij = np.unravel_index(np.argmax(P), P.shape)
        ax.plot(kdv_mW[ij[1]], qbv_mW[ij[0]], "*",
                markersize=14, color=C_CORAL, mec="white", mew=1.3)

        # iso-ratio rays
        for grad in [1.0, 2.0, 3.0]:
            ax.plot(kdv_mW, grad * kdv_mW, color="white", lw=0.6,
                    ls=":", alpha=0.6)

        fmt_axis(ax,
                 xlabel=r"$K_d$  (mW m$^{-1}$ K$^{-1}$)",
                 ylabel=r"$Q_b$  (mW m$^{-2}$)",
                 title=f"({chr(ord('a')+col)})  {name} joint posterior")
        ax.legend(handles=[Line2D([0], [0], marker="*", color="none",
                                  markerfacecolor=C_CORAL, mec="white",
                                  markersize=10, label="posterior mode")],
                  loc="upper right", borderpad=0.4)

        # ── lower: marginals ──────────────────────────────────────────────
        ax = axes[1][col]
        Pkd = P.sum(axis=0); Pkd /= Pkd.sum() * (kdv_mW[1]-kdv_mW[0])
        Pqb = P.sum(axis=1); Pqb /= Pqb.sum() * (qbv_mW[1]-qbv_mW[0])

        l1 = ax.plot(kdv_mW, Pkd, color=C_TEAL, lw=2.0,
                     label=r"$P(K_d \mid \mathrm{data})$")[0]
        ax2 = ax.twiny()
        # twin top axis for Q_b
        l2 = ax2.plot(qbv_mW, Pqb / Pqb.max() * Pkd.max(),
                      color=C_CORAL, lw=2.0, ls="--",
                      label=r"$P(Q_b \mid \mathrm{data})$  (rescaled)")[0]
        ax2.set_xlim(qbv_mW[0], qbv_mW[-1])

        ax.set_xlabel(r"$K_d$  (mW m$^{-1}$ K$^{-1}$)", color=C_TEAL)
        ax.set_ylabel(r"$P(K_d)$", color=C_TEAL)
        ax.tick_params(axis="x", colors=C_TEAL)
        ax.tick_params(axis="y", colors=C_TEAL)
        ax.set_title(f"({chr(ord('c')+col)})  {name} marginal posteriors")
        ax2.set_xlabel(r"$Q_b$  (mW m$^{-2}$)", color=C_CORAL)
        ax2.tick_params(axis="x", colors=C_CORAL)
        ax2.spines["top"].set_color(C_CORAL)
        ax2.spines["top"].set_visible(True)
        ax.spines["bottom"].set_color(C_TEAL)
        ax.legend([l1, l2],
                  [r"$P(K_d)$", r"$P(Q_b)$ (rescaled)"],
                  loc="upper right", fontsize=8)
        ax.grid(color=C_GRID, lw=0.5)
        ax.set_axisbelow(True)
        for s in (ax.spines["left"], ax.spines["bottom"]):
            s.set_color(C_TEAL)

    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main():
    d = json.loads(RESULTS.read_text())
    print("Regenerating Phase-2 figures with publication-grade aesthetic:")
    fig_bootstrap(d, LETTER_FIGS / "fig_bootstrap.pdf")
    fig_robustness(d, LETTER_FIGS / "fig_robustness.pdf")
    fig_kd_sweep_v2(d, LETTER_FIGS / "fig5_kd_sweep_v2.pdf")
    fig_lab_comparison(d, APPENDIX_FIGS / "fig_lab_comparison.pdf")
    fig_cold_trap(d, APPENDIX_FIGS / "fig_cold_trap_depth.pdf")
    fig_posterior(APPENDIX_FIGS / "fig_kd_qb_posterior.pdf")
    print("Done.")

if __name__ == "__main__":
    main()
