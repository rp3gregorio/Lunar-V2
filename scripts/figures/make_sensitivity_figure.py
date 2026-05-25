#!/usr/bin/env python3
"""Two-panel density-profile sensitivity figure for the letter.

Panel (a)  Bulk-density profile shapes rho(z) covered by the sweep.
           For each value of the deep bulk density rho_d in
           {1700, 1750, ..., 2000} kg/m^3 (the Apollo-core range;
           Mitchell+ 1973; Carrier 1991) we plot the corresponding
           this-work 3-layer rho(z), against the Hayne (2017)
           smooth-exponential profile for comparison.
Panel (b)  Retrieved deep conductivity K_d* as a function of rho_d,
           per site. A dashed horizontal reference at the Hayne (2017)
           global K_d = 3.4 mW/m/K shows how far the per-site
           retrieval sits from the global baseline across the sweep.

Input JSON: output/rho_d_sensitivity.json
(written by scripts/pipeline/compute_rho_d_sensitivity.py).

Run from the repo root after the sensitivity run is complete:
  python scripts/figures/make_sensitivity_figure.py
"""
from __future__ import annotations
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# shared design tokens (match the rest of the letter figures)
JGR_FULL = 7.48
C_TEAL    = "#2A6478"
C_CORAL   = "#B85B3A"
C_FOREST  = "#3D6E4A"
C_CHAR    = "#2A2520"
C_DIM     = "#6E6862"
C_GRID    = "#E8E5E0"
C_PAPER   = "#FBFAF8"
FS_LABEL  = 10.5
FS_TICK   = 9.5
FS_TITLE  = 11.0
HAYNE_KD  = 3.4    # mW m^-1 K^-1

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Latin Modern Roman", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "axes.edgecolor": C_DIM,
    "axes.labelcolor": C_CHAR,
    "text.color": C_CHAR,
    "xtick.color": C_CHAR,
    "ytick.color": C_CHAR,
    "axes.linewidth": 0.8,
})

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT  = ROOT / "paper" / "letter" / "figures"

# ── this-work 3-layer density profile (same constants as the manuscript) ─
RHO_S        = 1100.0    # surface bulk density (kg/m^3)
TL_Z1, TL_Z2 = 0.02, 0.20    # surface-layer and transition-base depths (m)
HAYNE_RHO_D  = 1800.0    # Hayne nominal deep density
HAYNE_H      = 0.06      # Hayne e-folding depth (m)


def rho_three_layer(z, rho_d):
    """Discrete 3-layer rho(z): flat surface layer, linear compaction
    transition, flat deep layer at rho_d."""
    z = np.asarray(z, float)
    out = np.empty_like(z)
    out[z < TL_Z1] = RHO_S
    ramp = (z >= TL_Z1) & (z < TL_Z2)
    out[ramp] = RHO_S + (rho_d - RHO_S) * \
        (z[ramp] - TL_Z1) / (TL_Z2 - TL_Z1)
    out[z >= TL_Z2] = rho_d
    return out


def rho_hayne(z):
    """Hayne (2017) smooth-exponential rho(z)."""
    return HAYNE_RHO_D - (HAYNE_RHO_D - RHO_S) * np.exp(-z / HAYNE_H)


def main():
    rho_j = json.loads((ROOT / "output" /
                        "rho_d_sensitivity.json").read_text())
    rho_grid = np.array(rho_j["rho_deep_kg_m3"])
    kd15 = np.array(rho_j["A15"])
    kd17 = np.array(rho_j["A17"])

    # Wider bottom margin to hold the shared legend with no overlap into
    # the panel area; figure slightly taller for breathing room.
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(JGR_FULL, 4.6))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.34,
                        wspace=0.30)

    # ── panel (a): the rho(z) profile shapes the sweep covers ──────────────
    axA.set_facecolor(C_PAPER)
    z_cm = np.linspace(0.0, 60.0, 400)        # depth axis, cm
    z_m  = z_cm / 100.0

    # one rho(z) curve per rho_d, colour-graded light->dark with rho_d
    cmap = plt.get_cmap("YlOrBr")
    n = len(rho_grid)
    # Plot all sweep curves but label only the three reference rho_d in the
    # shared legend (1700, mid, 2000). Order-preserving: a single proxy
    # entry "this work, 3-layer (sweep)" is added separately to the legend
    # via a Line2D handle so the dense bundle of warm curves reads as one
    # entry instead of seven.
    from matplotlib.lines import Line2D
    for k, rho_d in enumerate(rho_grid):
        col = cmap(0.30 + 0.55 * k / max(n - 1, 1))
        axA.plot(rho_three_layer(z_m, rho_d), z_cm,
                 color=col, lw=1.8, alpha=0.95, zorder=3)
    # Hayne smooth-exponential reference
    axA.plot(rho_hayne(z_m), z_cm, color=C_TEAL, lw=2.4, ls="--",
             zorder=4)

    # 3-layer boundaries -- short dotted lines + tiny inline labels in
    # the clear left margin so they don't clutter the legend. Labels are
    # placed BELOW the boundary line (va="top") so the z=2 cm label stays
    # inside the panel rather than running off the top edge.
    for zb_cm, name in ((TL_Z1 * 100, "2 cm"), (TL_Z2 * 100, "20 cm")):
        axA.axhline(zb_cm, color=C_DIM, lw=0.7, ls=(0, (1, 2)),
                    alpha=0.6, zorder=0)
        axA.text(1080, zb_cm + 0.8, name, fontsize=FS_TICK - 2,
                 color=C_DIM, style="italic", va="top", ha="left")

    axA.set_xlabel(r"Bulk density  $\rho$  (kg m$^{-3}$)",
                   fontsize=FS_LABEL)
    axA.set_ylabel("Depth  (cm)", fontsize=FS_LABEL)
    axA.set_title(r"(a)  3-layer $\rho(z)$ shapes swept "
                  r"over the Apollo-core range",
                  fontsize=FS_TITLE, fontweight="bold", pad=6)
    axA.set_ylim(60, 0)
    axA.set_xlim(1050, 2050)
    axA.tick_params(labelsize=FS_TICK)
    axA.grid(color=C_GRID, lw=0.5)
    axA.set_axisbelow(True)

    # ── panel (b): K_d* response to rho_d ───────────────────────────────────
    axB.set_facecolor(C_PAPER)
    axB.axhline(HAYNE_KD, color=C_TEAL, ls="--", lw=1.4, alpha=0.85,
                zorder=2)
    axB.plot(rho_grid, kd15, "o-", color=C_FOREST, lw=2.0, ms=7,
             mec="white", mew=1.0, zorder=4)
    axB.plot(rho_grid, kd17, "s-", color=C_CORAL, lw=2.0, ms=7,
             mec="white", mew=1.0, zorder=4)
    # shade the Apollo-core range explicitly
    axB.axvspan(1700, 2000, color=C_DIM, alpha=0.06, zorder=0)
    axB.set_xlabel(r"Deep bulk density  $\rho_d$  (kg m$^{-3}$)",
                   fontsize=FS_LABEL)
    axB.set_ylabel(r"Retrieved $K_d^{*}$  (mW m$^{-1}$ K$^{-1}$)",
                   fontsize=FS_LABEL)
    axB.set_title(r"(b)  $K_d^{*}$ response across the same range",
                  fontsize=FS_TITLE, fontweight="bold", pad=6)
    axB.set_xlim(rho_grid.min() - 25, rho_grid.max() + 25)
    axB.tick_params(labelsize=FS_TICK)
    axB.grid(color=C_GRID, lw=0.5)
    axB.set_axisbelow(True)

    # ── single shared legend BELOW the figure (no in-panel legends) ─────────
    # Hand-built handles so the seven warm rho(z) curves collapse into one
    # entry with a representative mid-tone swatch, plus two endpoint
    # swatches that visually convey the swept range.
    mid_col = cmap(0.30 + 0.55 * 0.5)
    sweep_handle = Line2D([0], [0], color=mid_col, lw=2.4,
                          label=r"This work 3-layer, $\rho(z)$ "
                                r"swept 1700--2000 kg m$^{-3}$")
    hayne_handle = Line2D([0], [0], color=C_TEAL, lw=2.0, ls="--",
                          label=f"Hayne (2017) reference "
                                f"(panel a profile; "
                                f"panel b global $K_d={HAYNE_KD}$)")
    a15_handle = Line2D([0], [0], marker="o", color=C_FOREST, lw=2.0,
                        ms=7, mec="white", mew=1.0,
                        label=r"A15 retrieved $K_d^{*}$ (panel b)")
    a17_handle = Line2D([0], [0], marker="s", color=C_CORAL, lw=2.0,
                        ms=7, mec="white", mew=1.0,
                        label=r"A17 retrieved $K_d^{*}$ (panel b)")
    fig.legend(handles=[sweep_handle, hayne_handle, a15_handle, a17_handle],
               loc="lower center", bbox_to_anchor=(0.5, 0.01),
               ncols=2, frameon=True,
               edgecolor=C_GRID, framealpha=0.97, fontsize=FS_TICK,
               handlelength=2.4, columnspacing=2.4, borderpad=0.6)

    out = OUT / "fig_sensitivity.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
