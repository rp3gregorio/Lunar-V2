#!/usr/bin/env python3
"""Two introduction figures for the letter, in the Anthropic design idiom.

  fig_intro_models.pdf   -- the three conductivity models compared:
                            (a) bulk-density profile rho(z),
                            (b) thermal-conductivity profile K(z).
  fig_intro_probe.pdf    -- schematic of an Apollo HFE borestem and its
                            gradient- and ring-bridge sensors in the
                            regolith column.

Both are vector PDFs sized for the JGR single-column text width and use
the shared warm palette of the other letter figures. Self-contained:
no pipeline data required.

Run from the repo root:
  python scripts/figures/make_intro_figures.py
"""
from __future__ import annotations
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

# ── shared design tokens (match phase2_figures_v2.py) ────────────────────────
JGR_FULL = 7.48
C_CORAL  = "#B85B3A"
C_CORAL_L= "#E5A88A"
C_TEAL   = "#2A6478"
C_TEAL_L = "#7CA3B0"
C_FOREST = "#3D6E4A"
C_FOREST_L="#94B89C"
C_CHAR   = "#2A2520"
C_DIM    = "#6E6862"
C_GRID   = "#E8E5E0"
C_PAPER  = "#FBFAF8"     # warm near-white panel background
FS_LABEL = 10.5
FS_TICK  = 9.5
FS_TITLE = 11.0

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

OUT = pathlib.Path(__file__).resolve().parents[2] / "paper" / "letter" / "figures"

# ── regolith model parameters (Hayne 2017; this-work 3-layer) ────────────────
RHO_S, RHO_D = 1100.0, 1800.0      # Hayne surface / deep bulk density
H_PARAM      = 0.06                 # Hayne e-folding depth (m)
RHO_D_SITE   = {"A15": 1825.0, "A17": 1960.0}   # 3-layer per-site deep density
TL_Z1, TL_Z2 = 0.02, 0.20           # 3-layer boundaries (m)


def rho_hayne(z):
    """Hayne (2017) exponential density profile."""
    return RHO_D - (RHO_D - RHO_S) * np.exp(-z / H_PARAM)


def rho_three_layer(z, rho_deep):
    """This-work discrete 3-layer density profile: a loose surface layer,
    a compaction ramp, and a compacted deep layer at rho_deep."""
    z = np.asarray(z, float)
    rho_mid = 0.5 * (RHO_S + rho_deep)
    out = np.empty_like(z)
    out[z < TL_Z1] = RHO_S
    ramp = (z >= TL_Z1) & (z < TL_Z2)
    frac = (z[ramp] - TL_Z1) / (TL_Z2 - TL_Z1)
    out[ramp] = RHO_S + (rho_deep - RHO_S) * frac
    out[z >= TL_Z2] = rho_deep
    _ = rho_mid
    return out


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 of intro -- conductivity-model comparison
# ════════════════════════════════════════════════════════════════════════════
def fig_intro_models():
    z = np.linspace(0.0, 2.0, 400)            # depth, m
    z_cm = z * 100.0

    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(JGR_FULL, 3.7))
    fig.subplots_adjust(left=0.085, right=0.975, top=0.86, bottom=0.30,
                        wspace=0.30)

    # ── panel (a): bulk-density profiles ────────────────────────────────────
    # y-axis limited to the top 60 cm, where the three models actually
    # differ; below 20 cm every profile is flat, so plotting to 200 cm
    # just wastes the panel and crowds the layer labels.
    axA.set_facecolor(C_PAPER)
    axA.plot(rho_hayne(z), z_cm, color=C_TEAL, lw=2.6,
             label="Hayne (2017): smooth exponential")
    axA.plot(rho_three_layer(z, RHO_D_SITE["A15"]), z_cm,
             color=C_FOREST, lw=2.4, ls="--",
             label=r"This work, 3-layer: A15 ($\rho_d=1825$)")
    axA.plot(rho_three_layer(z, RHO_D_SITE["A17"]), z_cm,
             color=C_CORAL, lw=2.4, ls=":",
             label=r"This work, 3-layer: A17 ($\rho_d=1960$)")

    # mark the 3-layer boundaries and label the three layers in clear space
    for zb in (TL_Z1, TL_Z2):
        axA.axhline(zb * 100, color=C_DIM, lw=0.7, ls=(0, (1, 2)),
                    alpha=0.7, zorder=0)
    axA.text(1960, TL_Z1 * 50, "surface\nlayer", fontsize=FS_TICK - 1.5,
             color=C_DIM, style="italic", va="center", ha="right",
             linespacing=0.95)
    axA.text(1960, (TL_Z1 + TL_Z2) * 50, "compaction\ntransition",
             fontsize=FS_TICK - 1.5, color=C_DIM, style="italic",
             va="center", ha="right", linespacing=0.95)
    axA.text(1960, 44, "compacted\ndeep layer", fontsize=FS_TICK - 1.5,
             color=C_DIM, style="italic", va="center", ha="right",
             linespacing=0.95)

    axA.set_xlabel(r"Bulk density $\rho$  (kg m$^{-3}$)", fontsize=FS_LABEL)
    axA.set_ylabel("Depth  (cm)", fontsize=FS_LABEL)
    axA.set_title("(a)  Density profile", fontsize=FS_TITLE,
                  fontweight="bold", pad=6)
    axA.set_ylim(60, 0)
    axA.set_xlim(1050, 2000)
    axA.tick_params(labelsize=FS_TICK)
    axA.grid(color=C_GRID, lw=0.5)
    axA.set_axisbelow(True)

    # ── panel (b): conductivity profiles (schematic, room-T) ────────────────
    # K(z) shapes only -- absolute scale is the retrieval target, so we show
    # normalised shape: surface K_s to a deep K_d, same two architectures.
    axB.set_facecolor(C_PAPER)
    Ks, Kd = 0.0074, 0.034            # representative W/m/K (x10^-3 shown)
    K_hayne = (Kd - (Kd - Ks) * np.exp(-z / H_PARAM)) * 1e3
    # 3-layer K(z): flat-ramp-flat, same boundaries
    def K_three(zz):
        zz = np.asarray(zz, float)
        out = np.empty_like(zz)
        out[zz < TL_Z1] = Ks
        ramp = (zz >= TL_Z1) & (zz < TL_Z2)
        frac = (zz[ramp] - TL_Z1) / (TL_Z2 - TL_Z1)
        out[ramp] = Ks + (Kd - Ks) * frac
        out[zz >= TL_Z2] = Kd
        return out * 1e3
    # panel (b) shows the two K(z) architectures (shape, not the
    # site-specific retrieved value); labels live in the shared legend.
    axB.plot(K_hayne, z_cm, color=C_TEAL, lw=2.6)
    axB.plot(K_three(z), z_cm, color=C_CHAR, lw=2.4, ls="--")
    axB.text(36, 6, "smooth\nexponential", fontsize=FS_TICK - 1.5,
             color=C_TEAL, ha="right", va="center", style="italic",
             linespacing=0.95)
    axB.text(20, 40, "discrete\n3-layer", fontsize=FS_TICK - 1.5,
             color=C_CHAR, ha="center", va="center", style="italic",
             linespacing=0.95)

    axB.set_xlabel(r"Thermal conductivity $K$  (mW m$^{-1}$ K$^{-1}$)",
                   fontsize=FS_LABEL)
    axB.set_ylabel("Depth  (cm)", fontsize=FS_LABEL)
    axB.set_title("(b)  Conductivity architecture", fontsize=FS_TITLE,
                  fontweight="bold", pad=6)
    axB.set_ylim(60, 0)
    axB.set_xlim(0, 40)
    axB.tick_params(labelsize=FS_TICK)
    axB.grid(color=C_GRID, lw=0.5)
    axB.set_axisbelow(True)

    # shared legend below -- only the three density-panel curves
    handles, labels = axA.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center",
               bbox_to_anchor=(0.5, 0.005), ncols=3, frameon=True,
               edgecolor=C_GRID, framealpha=0.97, fontsize=FS_TICK - 1,
               handlelength=2.2, columnspacing=1.6, borderpad=0.6)

    out = OUT / "fig_intro_models.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  -> {out}")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 of intro -- Apollo HFE probe schematic
# ════════════════════════════════════════════════════════════════════════════
def fig_intro_probe():
    fig, ax = plt.subplots(figsize=(JGR_FULL, 4.6))
    fig.subplots_adjust(left=0.04, right=0.78, top=0.92, bottom=0.06)

    # depth axis runs 0 (surface) downward to 250 cm
    z_top, z_bot = -18.0, 250.0
    ax.set_xlim(0, 100)
    ax.set_ylim(z_bot, z_top)
    ax.axis("off")

    # ── sky / surface / regolith bands ──────────────────────────────────────
    ax.add_patch(Rectangle((0, z_top), 100, -z_top, facecolor="#F4F1EC",
                           edgecolor="none", zorder=0))                # space
    # regolith: a continuous depth gradient (many thin slices, no gaps),
    # darkening smoothly with depth to suggest increasing compaction
    n_slice = 120
    edges = np.linspace(0.0, z_bot, n_slice + 1)
    for k in range(n_slice):
        f = k / (n_slice - 1)                       # 0 at surface, 1 deep
        shade = 0.93 - 0.16 * f
        ax.add_patch(Rectangle((0, edges[k]), 100, edges[k + 1] - edges[k],
                               facecolor=(shade, shade - 0.045,
                                          shade - 0.10),
                               edgecolor="none", zorder=0))
    # surface line
    ax.plot([0, 100], [0, 0], color=C_CHAR, lw=1.6, zorder=3)
    ax.text(2, -8, "Lunar surface", fontsize=FS_TICK, color=C_CHAR,
            style="italic", va="center")
    ax.text(2, 230, "compacted deep regolith", fontsize=FS_TICK - 1,
            color="#FBFAF8", style="italic", va="center", alpha=0.95,
            zorder=3)

    # ── the borestem (fibreglass tube the probe sits in) ────────────────────
    stem_x, stem_w = 33.0, 5.0
    ax.add_patch(FancyBboxPatch((stem_x, 2), stem_w, 224,
                 boxstyle="round,pad=0,rounding_size=1.2",
                 facecolor="#D9D2C6", edgecolor=C_DIM, lw=1.0, zorder=2))
    # the borestem protrudes slightly above the surface
    ax.add_patch(Rectangle((stem_x, -14), stem_w, 16,
                 facecolor="#D9D2C6", edgecolor=C_DIM, lw=1.0, zorder=2))
    ax.text(stem_x + stem_w / 2, -16, "borestem",
            fontsize=FS_TICK - 1, color=C_DIM, ha="center", va="bottom")

    # borestem-affected zone (upper 80 cm) -- the part excluded from retrieval
    ax.add_patch(Rectangle((0, 0), 100, 80, facecolor=C_CORAL,
                           alpha=0.10, edgecolor="none", zorder=1))
    ax.plot([0, 100], [80, 80], color=C_CORAL, lw=1.1, ls="--", zorder=3)
    ax.text(98, 40, "borestem-affected zone\n(z < 80 cm, excluded)",
            fontsize=FS_TICK - 1, color=C_CORAL, ha="right", va="center",
            style="italic")

    # ── the sensor positions (representative Apollo-15 Probe-1 depths) ──────
    # gradient-bridge (TG) and ring-bridge (TR) sensors
    sensors = [
        (35, "TR11A", "shallow", True),
        (45, "TR11A'", "shallow", True),
        (84, "TG11B", "deep",    False),
        (91, "TG12A", "deep",    False),
        (101,"TR12A", "deep",    False),
        (129,"TR12B", "deep",    False),
        (139,"TG12B", "deep",    False),
    ]
    cx = stem_x + stem_w / 2
    for depth, name, kind, excluded in sensors:
        col = C_DIM if excluded else C_TEAL
        # sensor: a small filled rounded marker on the stem
        ax.add_patch(FancyBboxPatch((cx - 3.4, depth - 2.0), 6.8, 4.0,
                     boxstyle="round,pad=0,rounding_size=0.8",
                     facecolor=col, edgecolor="white", lw=0.9, zorder=4))
        # leader line + label to the right
        ax.annotate(f"{name}  ({depth} cm)",
                    xy=(cx + 3.4, depth), xytext=(62, depth),
                    fontsize=FS_TICK - 1,
                    color=(C_DIM if excluded else C_CHAR),
                    va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", color=C_DIM, lw=0.7,
                                    shrinkA=0, shrinkB=2))

    # depth scale on the left (a clean vertical axis line + ticks)
    ax.plot([10, 10], [0, z_bot], color=C_CHAR, lw=0.9, zorder=3)
    for zt in (0, 50, 100, 150, 200, 250):
        ax.plot([8.0, 10], [zt, zt], color=C_CHAR, lw=0.9, zorder=3)
        ax.text(6.8, zt, f"{zt}", fontsize=FS_TICK - 1, ha="right",
                va="center", color=C_CHAR)
    ax.text(3.2, 125, "Depth  (cm)", fontsize=FS_TICK, ha="center",
            va="center", color=C_CHAR, rotation=90)

    # ── legend for sensor types (in the clear lower-right margin) ───────────
    lx, ly = 80.0, 178.0
    ax.add_patch(FancyBboxPatch((lx - 3, ly - 12), 42, 56,
                 boxstyle="round,pad=0,rounding_size=2.0",
                 facecolor="#FBFAF8", edgecolor=C_GRID, lw=1.0, zorder=5,
                 clip_on=False))
    ax.add_patch(FancyBboxPatch((lx, ly), 6.8, 4.0,
                 boxstyle="round,pad=0,rounding_size=0.8",
                 facecolor=C_TEAL, edgecolor="white", lw=0.9, zorder=6))
    ax.text(lx + 9.5, ly + 2, "deep sensor\n(used in retrieval)",
            fontsize=FS_TICK - 1.5, va="center", color=C_CHAR, zorder=6,
            linespacing=1.0)
    ax.add_patch(FancyBboxPatch((lx, ly + 22), 6.8, 4.0,
                 boxstyle="round,pad=0,rounding_size=0.8",
                 facecolor=C_DIM, edgecolor="white", lw=0.9, zorder=6))
    ax.text(lx + 9.5, ly + 24, "shallow sensor\n(borestem-affected,\nexcluded)",
            fontsize=FS_TICK - 1.5, va="center", color=C_CHAR, zorder=6,
            linespacing=1.0)

    ax.set_title("Apollo Heat-Flow Experiment: probe configuration",
                 fontsize=FS_TITLE, fontweight="bold", pad=8)

    out = OUT / "fig_intro_probe.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  -> {out}")


if __name__ == "__main__":
    print("Generating introduction figures:")
    fig_intro_models()
    fig_intro_probe()
    print("Done.")
