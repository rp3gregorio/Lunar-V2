"""
SUPERSEDED -- not used by the current manuscript.

This schematic depicted a two-model architecture (Hayne vs. a
"Martinez & Siegler piecewise 3-layer" model) that was found to
mis-describe the genuine Martinez & Siegler (2021) conductivity model.
The figure was removed from the letter; the script is retained only
for history.  Do not regenerate or cite it.

Original description follows.

Model schematic for the letter (Fig. 1).

Three-panel layout designed at JGR:Planets full-width (190 mm = 7.48 in):
  (a)  Conceptual layer architecture: Hayne smooth-exponential vs.
       Martinez & Siegler piecewise 3-layer.
  (b)  K(z) profiles at T = 250 K (the SPICE-derived deep-T scale).
  (c)  K(T) at z = 30 cm (deep) showing the radiative multiplier
       1 + chi (T/T_ref)^3 — the temperature-dependent component
       responsible for the daytime conductivity rise.

Spacing tuned so the panel (a) header sits clear of the column
labels, panel (b) legend is in the upper-right where the data are
sparse, and panel (c) annotations fit inside the panel.
"""
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

# ── Hayne & MS parameters ─────────────────────────────────────────────────────
Ks_H, Kd_H, H_H = 7.4e-4, 3.4e-3, 0.06
Ks_M, Kd_M      = 1.0e-3, 6.3e-3
z1_M, z2_M      = 0.07, 0.20
chi, Tref       = 2.7, 350.0

T_plot = 250.0
rad_at = lambda T: 1.0 + chi * (T / Tref) ** 3
rad    = rad_at(T_plot)

def K_hayne(z, T=T_plot):
    Kc = Ks_H + (Kd_H - Ks_H) * (1.0 - np.exp(-np.asarray(z) / H_H))
    return Kc * rad_at(T)

def K_ms(z, T=T_plot):
    z = np.atleast_1d(np.asarray(z, float))
    base = np.where(z < z2_M,
                    Ks_M + (Kd_M - Ks_M) * (z / z2_M),
                    Kd_M)
    return base * rad_at(T)

z    = np.linspace(0, 0.32, 800)
z_cm = z * 100

# ── colours (unified with phase2_figures_v2.py palette) ──────────────────────
C_H,    C_H_BG = "#2A6478", "#7CA3B0"     # teal — same as C_HAYNE elsewhere
C_MS_S, C_MS_M, C_MS_D = "#F2C2A6", "#D7825A", "#9E2A1F"   # warm reds
C_TXT  = "#2A2520"

# ══════════════════════════════════════════════════════════════════════════════
# Figure layout — JGR:Planets full-width (190 mm = 7.48 in)
# Reserve a strip at the bottom for a SHARED legend (no in-axes legends).
# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.48, 8.9))
gs  = fig.add_gridspec(
    3, 1, height_ratios=[1.45, 1.10, 0.85], hspace=0.45,
    left=0.11, right=0.97, bottom=0.10, top=0.96,
)
ax0 = fig.add_subplot(gs[0])     # concept
ax1 = fig.add_subplot(gs[1])     # K(z)
ax2 = fig.add_subplot(gs[2])     # K(T) at deep

# ══════════════════════════════════════════════════════════════════════════════
# PANEL A — concept diagram
# ══════════════════════════════════════════════════════════════════════════════
ax0.set_xlim(0.5, 9.5)
ax0.set_ylim(34, -10)        # extra room above for headers
ax0.axis("off")
ax0.set_title("(a)  Conceptual model architecture",
              fontsize=13, fontweight="bold", loc="left", pad=8)

# column geometry
col_w = 1.8
hx, mx = 1.6, 6.1            # left edges of each column
hx_c, mx_c = hx + col_w/2, mx + col_w/2

# depth axis
for d in [0, 7, 20, 30]:
    ax0.plot([hx - 0.30, hx], [d, d], color="0.55", lw=0.9)
    ax0.text(hx - 0.45, d, f"{d}", ha="right", va="center",
             fontsize=10, color="0.30")
ax0.text(hx - 1.40, 15, "Depth (cm)", ha="center", va="center",
         fontsize=10.5, color="0.30", rotation=90)

# surface line
ax0.plot([hx - 0.3, mx + col_w + 0.3], [0, 0], color="0.30", lw=1.2)
ax0.text((hx + mx + col_w) / 2, -1.5, "surface  ($z = 0$)",
         ha="center", va="bottom", fontsize=10, color="0.30",
         style="italic")

# ─── Hayne column (smooth gradient fill) ─────────────────────────────────────
n_strips = 80
for i in range(n_strips):
    y0 = i * 30 / n_strips
    y1 = (i + 1) * 30 / n_strips
    alpha = 0.10 + 0.55 * (i / n_strips)
    ax0.add_patch(mpatches.Rectangle((hx, y0), col_w, y1 - y0,
                                     facecolor=C_H, alpha=alpha, lw=0))
ax0.add_patch(mpatches.Rectangle((hx, 0), col_w, 30,
                                 facecolor="none", edgecolor=C_H, lw=1.4))

# Hayne header — pushed up to clear the title above
ax0.text(hx_c, -7.5, "Hayne (2017)", ha="center", va="bottom",
         fontsize=12, fontweight="bold", color=C_H)
ax0.text(hx_c, -5.5, "smooth exponential",
         ha="center", va="bottom", fontsize=10, color=C_H, style="italic")

# K_s box (top of column)
ax0.text(hx_c, 3.5,
         fr"$K_s = {Ks_H*1e3:.2f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
         ha="center", va="center", fontsize=9.5, color=C_TXT,
         linespacing=1.3,
         bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                   edgecolor=C_H, lw=0.7, alpha=0.94))

# K_d box (bottom of column)
ax0.text(hx_c, 27.0,
         fr"$K_d = {Kd_H*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
         ha="center", va="center", fontsize=9.5, color="white",
         linespacing=1.3,
         bbox=dict(boxstyle="round,pad=0.22", facecolor=C_H,
                   edgecolor=C_H, lw=0.7))

# arrow for "K rises with depth"
ax0.annotate("", xy=(hx_c, 22), xytext=(hx_c, 8),
             arrowprops=dict(arrowstyle="->", color="white",
                             lw=2.4, alpha=0.95))

# H-parameter callout to the right of the column
ax0.annotate(
    fr"$H = 6$ cm" "\n" "(e-folding\ndepth)",
    xy=(hx + col_w, 6), xytext=(hx + col_w + 1.4, 12.5),
    fontsize=9.5, color=C_H, ha="center", va="center", linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_H, lw=0.9,
                    connectionstyle="arc3,rad=0.30"))

# ─── M&S column ───────────────────────────────────────────────────────────────
layers = [
    (0,  7,  C_MS_S, "Surface\nlayer",  C_TXT),
    (7,  20, C_MS_M, "Ramp\nzone",       C_TXT),
    (20, 30, C_MS_D, "Deep\nlayer",      "white"),
]
for (z0, z1, fc, lab, tc) in layers:
    ax0.add_patch(mpatches.Rectangle((mx, z0), col_w, z1 - z0,
                                     facecolor=fc, edgecolor=C_MS_D, lw=1.3))
    ax0.text(mx_c, (z0 + z1) / 2, lab, ha="center", va="center",
             fontsize=10, color=tc, linespacing=1.3, fontweight="semibold")

# M&S header
ax0.text(mx_c, -7.5, "Martinez & Siegler (2021)", ha="center", va="bottom",
         fontsize=12, fontweight="bold", color=C_MS_D)
ax0.text(mx_c, -5.5, "piecewise 3-layer",
         ha="center", va="bottom", fontsize=10, color=C_MS_D, style="italic")

# K_s and K_d callouts
ax0.annotate(
    fr"$K_s = {Ks_M*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
    xy=(mx + col_w, 3.5), xytext=(mx + col_w + 1.30, 1.5),
    fontsize=9.5, color=C_MS_D, ha="center", va="center", linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_MS_D, lw=1.0,
                    connectionstyle="arc3,rad=-0.20"))
ax0.annotate(
    fr"$K_d = {Kd_M*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
    xy=(mx + col_w, 25.0), xytext=(mx + col_w + 1.30, 27.0),
    fontsize=9.5, color=C_MS_D, ha="center", va="center", linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_MS_D, lw=1.0,
                    connectionstyle="arc3,rad=0.20"))

# breakpoint depth tags inside boxes
for z_break, lab in [(7, "7 cm"), (20, "20 cm")]:
    ax0.plot([mx, mx + col_w], [z_break, z_break],
             color="white", lw=1.0, ls="--", alpha=0.85)
    ax0.text(mx + col_w + 0.18, z_break, lab, ha="left", va="center",
             fontsize=10, color=C_MS_D,
             bbox=dict(boxstyle="round,pad=0.18",
                       facecolor="white", edgecolor=C_MS_D, lw=0.6))

# ══════════════════════════════════════════════════════════════════════════════
# PANEL B — K(z) at T = 250 K
# ══════════════════════════════════════════════════════════════════════════════
ax1.set_title(r"(b)  $K(z)$ at $T = 250$ K  "
              r"(with radiative multiplier $1+\chi (T/T_\mathrm{ref})^3$)",
              fontsize=12.5, fontweight="bold", loc="left", pad=8)

KH  = K_hayne(z) * 1e3
KMS = K_ms(z)    * 1e3

ax1.fill_betweenx(z_cm, KH, KMS, where=(KH < KMS),
                  facecolor=C_MS_D, alpha=0.10, label="M&S > Hayne region")
ax1.plot(KH,  z_cm, color=C_H,    lw=2.4,
         label="Hayne (2017) — smooth exponential")
ax1.plot(KMS, z_cm, color=C_MS_D, lw=2.4, ls="--",
         label="Martinez & Siegler (2021) — 3-layer")

for z_break, lab in [(7, "7 cm"), (20, "20 cm")]:
    ax1.axhline(z_break, color=C_MS_D, lw=0.9, ls=":", alpha=0.55)
    ax1.text(13.7, z_break - 0.3, lab, fontsize=9.5,
             color=C_MS_D, alpha=0.85, va="bottom", ha="right")

ax1.set_xlabel(r"Thermal conductivity $K$ (mW m$^{-1}$ K$^{-1}$)",
               fontsize=11)
ax1.set_ylabel("Depth (cm)", fontsize=11)
ax1.invert_yaxis()
ax1.set_ylim(33, -1)
ax1.set_xlim(0, 14)
ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.grid(color="0.90", lw=0.7)
ax1.tick_params(labelsize=10)
# (no in-axes legend — shared legend at the bottom of the figure)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL C — K(T) at z = 30 cm (deep)
# ══════════════════════════════════════════════════════════════════════════════
ax2.set_title(r"(c)  $K(T)$ at $z = 30$ cm "
              r"(deep limit; radiative multiplier dominates)",
              fontsize=12.5, fontweight="bold", loc="left", pad=8)

T_grid = np.linspace(80, 380, 200)
KH_T  = np.array([K_hayne(0.30, t) for t in T_grid]) * 1e3
KMS_T = np.array([K_ms(np.array([0.30]), t)[0] for t in T_grid]) * 1e3

ax2.plot(T_grid, KH_T,  color=C_H,    lw=2.4, label="Hayne (2017)")
ax2.plot(T_grid, KMS_T, color=C_MS_D, lw=2.4, ls="--",
         label="Martinez & Siegler (2021)")

# annotate the day/night reference points
for T_pt, lab, ha in [(110, "polar /\nnight", "left"),
                       (250, "annual\nmean", "center"),
                       (370, "daytime\npeak", "right")]:
    KMS_pt = K_ms(np.array([0.30]), T_pt)[0] * 1e3
    ax2.plot([T_pt, T_pt], [0, KMS_pt], color="0.6", lw=0.6, ls=":",
             alpha=0.6, zorder=0)
    x_off = {"left": 4, "center": 0, "right": -4}[ha]
    ax2.text(T_pt + x_off, 14.6, lab, fontsize=9, color="0.30",
             ha=ha, va="top", style="italic", linespacing=1.15)

ax2.set_xlabel(r"Temperature $T$ (K)", fontsize=11)
ax2.set_ylabel(r"$K$  (mW m$^{-1}$ K$^{-1}$)", fontsize=11)
ax2.set_xlim(80, 380)
ax2.set_ylim(0, 15)
ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator())
ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax2.grid(color="0.90", lw=0.7)
ax2.tick_params(labelsize=10)
# (no in-axes legend — shared legend at the bottom of the figure)

# ── shared legend BELOW all panels ────────────────────────────────────────────
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
legend_handles = [
    Line2D([0], [0], color=C_H, lw=2.4,
           label="Hayne (2017) — smooth exponential"),
    Line2D([0], [0], color=C_MS_D, lw=2.4, ls="--",
           label="Martinez & Siegler (2021) — piecewise 3-layer"),
    Patch(facecolor=C_MS_D, alpha=0.10,
          label="M\\&S $>$ Hayne region (panel b)"),
]
fig.legend(handles=legend_handles, loc="lower center",
           bbox_to_anchor=(0.5, 0.005), ncols=3, frameon=True,
           edgecolor="0.75", framealpha=0.97, fontsize=10,
           handlelength=2.2, borderpad=0.6, columnspacing=1.5)

# ── save ──────────────────────────────────────────────────────────────────────
out_pdf = "/tmp/fig_model_schematic.pdf"
out_png = "/tmp/fig_model_schematic.png"
fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
fig.savefig(out_png, dpi=180, bbox_inches="tight")
import os
print(f"Saved {out_pdf}  ({os.path.getsize(out_pdf)//1024} kB)")
