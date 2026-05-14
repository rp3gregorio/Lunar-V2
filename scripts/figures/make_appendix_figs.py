"""
Three pedagogical figures for the SI appendix:
  Fig 1: Apollo HFE instrument schematic (borehole + sensors + borestem)
  Fig 2: Diurnal skin-depth attenuation (intuitive)
  Fig 3: K_d / Q_b degeneracy (level curves of equilibrium gradient)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import matplotlib.ticker as ticker
import os

OUT = "/tmp/letter_zip/appendix/figures"
os.makedirs(OUT, exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Apollo HFE instrument schematic
# ═════════════════════════════════════════════════════════════════════════════
def make_instrument():
    fig, ax = plt.subplots(figsize=(8.0, 6.5))
    ax.set_xlim(-3.5, 4.2)
    ax.set_ylim(-2.7, 0.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── regolith background ──────────────────────────────────────────────────
    # surface
    ax.fill_between([-3.5, 4.2], -2.7, 0, color="#D6BB94", alpha=0.35)
    # hatched surface texture
    for x in np.linspace(-3.4, 4.1, 40):
        ax.plot([x, x + 0.1], [0.04, 0.10], color="#8C7041", lw=0.6, alpha=0.4)
    ax.axhline(0, color="#5C4426", lw=1.4)
    ax.text(-3.3, 0.18, "lunar surface  $z = 0$",
            color="#5C4426", fontsize=9, style="italic")

    # ── borestem (fibreglass tube) ───────────────────────────────────────────
    bs_x, bs_w = -0.10, 0.30
    bs_top, bs_bot = 0.05, -2.50
    ax.add_patch(mpatches.Rectangle(
        (bs_x, bs_bot), bs_w, bs_top - bs_bot,
        facecolor="#F5F5F5", edgecolor="#777", lw=1.0))
    ax.text(bs_x + bs_w + 0.10, -0.30, "fibreglass\nborestem",
            ha="left", va="center", fontsize=10.5, color="#444",
            linespacing=1.2)

    # ── ALSEP enclosure on the surface ───────────────────────────────────────
    al_x, al_y, al_w, al_h = 0.6, 0.05, 1.5, 0.35
    ax.add_patch(FancyBboxPatch(
        (al_x, al_y), al_w, al_h, boxstyle="round,pad=0.02",
        facecolor="#C7CDD3", edgecolor="#444", lw=1.0))
    ax.text(al_x + al_w / 2, al_y + al_h / 2, "ALSEP electronics",
            ha="center", va="center", fontsize=10, color="#222")
    # cable from ALSEP to borestem
    ax.plot([al_x, bs_x + bs_w], [al_y + 0.05, 0.10],
            color="#444", lw=0.8)

    # ── thermometer probe inside the borestem ────────────────────────────────
    # 4 sensor pairs at depths (cm):
    sensors = [
        ( -0.30, "TG / TR", "shallow (borestem-contaminated)", "#D14848"),
        ( -0.80, "TG / TR", "shallow", "#D14848"),
        ( -1.40, "TG / TR", "deep — used in retrieval", "#1E5A99"),
        ( -2.00, "TG / TR", "deep — used in retrieval", "#1E5A99"),
    ]
    for (z, lab, sub, col) in sensors:
        ax.plot([bs_x + 0.04, bs_x + bs_w - 0.04], [z, z],
                color=col, lw=1.6)
        ax.plot([bs_x + 0.07, bs_x + 0.07], [z + 0.05, z - 0.05],
                color=col, lw=2.5, solid_capstyle="round")
        ax.plot([bs_x + bs_w - 0.07, bs_x + bs_w - 0.07],
                [z + 0.05, z - 0.05], color=col, lw=2.5,
                solid_capstyle="round")
        ax.text(bs_x + bs_w + 0.10, z, f"{abs(z*100):.0f} cm",
                ha="left", va="center", fontsize=9.5, color=col)

    # bracket showing borestem contamination zone (top 80 cm)
    ax.annotate("", xy=(-1.10, -0.80), xytext=(-1.10, 0),
                arrowprops=dict(arrowstyle="<->", color="#D14848", lw=1.5))
    ax.text(-1.18, -0.40,
            "contaminated\n(borestem heat-short)\n$z < 80$ cm",
            ha="right", va="center", color="#D14848", fontsize=10,
            linespacing=1.25, style="italic")

    # bracket showing retrieval zone
    ax.annotate("", xy=(-1.10, -2.40), xytext=(-1.10, -0.80),
                arrowprops=dict(arrowstyle="<->", color="#1E5A99", lw=1.5))
    ax.text(-1.18, -1.60,
            "deep-sensor zone\nused for $K_d$ retrieval\n$z \\geq 80$ cm",
            ha="right", va="center", color="#1E5A99", fontsize=10,
            linespacing=1.25, style="italic")

    # ── heat-flow arrows (ambient + borestem heat-short) ─────────────────────
    # solar flux from above
    for x in [-2.5, 1.8, 3.2]:
        ax.annotate("", xy=(x, 0.05), xytext=(x, 0.45),
                    arrowprops=dict(arrowstyle="->", color="#E08020",
                                    lw=1.4))
    ax.text(2.5, 0.50, "diurnal $T$ swing $\\sim$ 100 K",
            color="#E08020", fontsize=10, ha="center", style="italic")

    # heat-short arrow down the borestem (top)
    ax.annotate("", xy=(bs_x + bs_w / 2, -0.55),
                xytext=(bs_x + bs_w / 2, -0.05),
                arrowprops=dict(arrowstyle="->", color="#A14040", lw=2.0,
                                alpha=0.85))

    # geothermal flux from below
    for x in [-2.5, 0.8, 3.2]:
        ax.annotate("", xy=(x, -2.40), xytext=(x, -2.66),
                    arrowprops=dict(arrowstyle="->", color="#B03020",
                                    lw=1.4))
    ax.text(2.5, -2.66, "$Q_b$ from interior",
            color="#B03020", fontsize=10, ha="center", style="italic")

    # title
    ax.set_title("Apollo Heat-Flow Experiment — instrument geometry",
                 fontsize=14, fontweight="bold", pad=4)

    fig.tight_layout()
    out = f"{OUT}/fig_instrument_schematic.pdf"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"  → {out}")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Diurnal skin-depth attenuation
# ═════════════════════════════════════════════════════════════════════════════
def make_skin_depth():
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.0),
                             gridspec_kw={"width_ratios": [1.6, 1.0]})
    fig.subplots_adjust(left=0.06, right=0.97, bottom=0.27, top=0.92,
                        wspace=0.27)

    # surface temperature wave (a synthetic 100-K diurnal swing)
    P = 29.53          # lunation in days
    omega = 2 * np.pi / (P * 86400)
    delta = 0.04       # 4 cm skin depth (representative)
    Tmean = 240
    Tamp  = 100

    t = np.linspace(0, 2 * P, 1500)   # two lunations
    # depth slices
    depths_cm = [0, 2, 5, 10, 20, 40, 80]
    depths    = np.array(depths_cm) / 100.0

    ax = axes[0]
    cmap = plt.get_cmap("viridis_r")
    for i, (z, lab) in enumerate(zip(depths, depths_cm)):
        attn  = np.exp(-z / delta)
        phase = z / delta
        T = Tmean + Tamp * attn * np.cos(omega * t * 86400 - phase)
        col = cmap(i / (len(depths) - 1))
        ax.plot(t, T, color=col, lw=1.8, label=f"{lab} cm")
    ax.set_xlabel("Time (Earth days)", fontsize=12)
    ax.set_ylabel("Temperature (K)", fontsize=12)
    ax.set_title("(a)  Diurnal wave penetrating the regolith",
                 fontsize=14, fontweight="bold", loc="left", pad=4)
    ax.grid(color="0.90", lw=0.7)
    ax.legend(bbox_to_anchor=(0.5, -0.18), loc="upper center",
              borderaxespad=0.0, fontsize=11, framealpha=0.97,
              title="Sensor depth", title_fontsize=12,
              handlelength=1.8, borderpad=0.7, ncols=7)
    ax.set_xlim(0, 2 * P)
    ax.tick_params(labelsize=11)

    # right panel: attenuation factor vs depth
    ax = axes[1]
    z_plot = np.linspace(0, 1.20, 600)
    attn = np.exp(-z_plot / delta)
    ax.fill_betweenx(z_plot * 100, attn, 1, color="#FDE6D5", alpha=0.5)
    ax.plot(attn, z_plot * 100, color="#9E2A1F", lw=2.4)

    # mark e-folding depth
    ax.axhline(delta * 100, color="0.40", ls="--", lw=1.0)
    ax.text(1e-8, delta * 100 + 1.5,
            r"$\delta \approx 4$ cm",
            fontsize=10.5, color="0.30", va="top", ha="left")

    # mark borestem zone
    ax.axhline(80, color="#1E5A99", ls=":", lw=1.4, alpha=0.8)
    ax.text(1e-8, 80 - 2,
            r"$z = 80$ cm  (borestem cut)" "\n"
            r"  amplitude $\sim 10^{-9}$ K",
            fontsize=10, color="#1E5A99", va="bottom", ha="left",
            linespacing=1.3)

    ax.set_xscale("log")
    ax.set_xlim(1e-15, 2)
    ax.invert_yaxis()
    ax.set_ylim(120, 0)
    ax.set_xlabel("Diurnal amplitude / surface amplitude", fontsize=12)
    ax.set_ylabel("Depth (cm)", fontsize=12)
    ax.set_title("(b)  Exponential attenuation",
                 fontsize=14, fontweight="bold", loc="left", pad=4)
    ax.grid(color="0.90", lw=0.7, which="both")
    ax.tick_params(labelsize=11)

    out = f"{OUT}/fig_skin_depth.pdf"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"  → {out}")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — K_d / Q_b degeneracy
# ═════════════════════════════════════════════════════════════════════════════
def make_degeneracy():
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    fig.subplots_adjust(left=0.085, right=0.66, top=0.92, bottom=0.12)

    Kd = np.linspace(2, 16, 400)        # mW/m/K
    Qb = np.linspace(5, 30, 400)        # mW/m^2
    KK, QQ = np.meshgrid(Kd, Qb)

    # equilibrium deep gradient |dT/dz| = Q_b / K_d  (K/m)
    grad = QQ / KK   # mW/m^2 ÷ mW/m/K = K/m

    # contour set
    levels = [1, 2, 3, 4, 5, 6, 8]
    cs = ax.contour(KK, QQ, grad, levels=levels, colors="0.40", linewidths=0.9)
    ax.clabel(cs, inline=True, fontsize=10, fmt="%g K/m")

    # shaded ridge at the A17 retrieval value (gradient = 15/11.23 = 1.34 K/m)
    grad_A17 = 15 / 11.23
    cs1 = ax.contourf(KK, QQ, grad,
                      levels=[grad_A17 - 0.02, grad_A17 + 0.02],
                      colors=["#9E2A1F"], alpha=0.35)

    # marker: nominal A17
    ax.plot(11.23, 15, marker="*", markersize=18, color="#9E2A1F",
            mec="white", mew=1.5, label="A17 nominal\n($K_d=11.2$, $Q_b=15$)")

    # marker: re-analysis A17 ($Q_b ~ 10$, then $K_d ~ 7.5$)
    ax.plot(7.5, 10, marker="o", markersize=12, color="#1E5A99",
            mec="white", mew=1.2,
            label="A17 with $Q_b=10$\n(degenerate ridge)")

    # marker: A15 nominal
    ax.plot(4.85, 21, marker="s", markersize=12, color="#2D7A2D",
            mec="white", mew=1.2,
            label="A15 nominal\n($K_d=4.85$, $Q_b=21$)")

    # rescaling arrow connecting two A17 points (along ridge)
    ax.annotate("", xy=(7.5, 10), xytext=(11.23, 15),
                arrowprops=dict(arrowstyle="-|>", color="#9E2A1F",
                                lw=1.6, alpha=0.7,
                                connectionstyle="arc3,rad=0.2"))
    ax.text(9.0, 11.5, "rescaling\n$\\alpha=2/3$",
            fontsize=10.5, color="#9E2A1F", style="italic", ha="center")

    # axes
    ax.set_xlabel(r"Deep conductivity $K_d$  (mW m$^{-1}$ K$^{-1}$)",
                  fontsize=12)
    ax.set_ylabel(r"Basal heat flux $Q_b$  (mW m$^{-2}$)", fontsize=12)
    ax.set_title(r"$K_d / Q_b$ degeneracy:  contours of constant deep gradient "
                 r"$|\partial_z T| = Q_b / K_d$",
                 fontsize=14, fontweight="bold", pad=4)
    ax.grid(color="0.90", lw=0.7)
    ax.legend(bbox_to_anchor=(1.02, 1.0), loc="upper left",
              borderaxespad=0.0, fontsize=11, framealpha=0.97,
              edgecolor="0.75",
              title="Reference points", title_fontsize=12,
              handlelength=1.8, borderpad=0.7)
    ax.tick_params(labelsize=11)
    ax.set_xlim(2, 16)
    ax.set_ylim(5, 30)

    out = f"{OUT}/fig_kd_qb_degeneracy.pdf"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"  → {out}")
    plt.close(fig)

# ── run all ───────────────────────────────────────────────────────────────────
print("Generating appendix figures:")
make_instrument()
make_skin_depth()
make_degeneracy()
print("done.")
