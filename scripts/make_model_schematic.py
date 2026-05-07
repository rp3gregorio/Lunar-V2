"""
Publication-quality schematic comparing the Hayne (2017) smooth exponential
K(z) profile with the Martinez & Siegler (2021) piecewise 3-layer profile.

Stacked layout (two rows): top row = panel A (concept diagram),
bottom row = panel B (K(z) curves). This avoids horizontal label collisions
that plagued the side-by-side layout.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

# ── parameters ────────────────────────────────────────────────────────────────
Ks_H, Kd_H, H_H = 7.4e-4, 3.4e-3, 0.06
Ks_M, Kd_M      = 1.0e-3, 6.3e-3
z1_M, z2_M      = 0.07, 0.20
chi, Tref       = 2.7, 350.0
T_plot          = 250.0
rad             = 1.0 + chi * (T_plot / Tref) ** 3

def K_hayne(z):
    Kc = Ks_H + (Kd_H - Ks_H) * (1.0 - np.exp(-np.asarray(z) / H_H))
    return Kc * rad

def K_ms(z):
    z = np.atleast_1d(np.asarray(z, float))
    return rad * np.where(z < z2_M,
                          Ks_M + (Kd_M - Ks_M) * (z / z2_M),
                          Kd_M)

z    = np.linspace(0, 0.32, 800)
z_cm = z * 100

C_H, C_H_BG = "#1F538F", "#9FBBDC"
C_MS_S, C_MS_M, C_MS_D = "#F2C2A6", "#D7825A", "#9E2A1F"
C_TXT = "#222222"

# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(11.5, 7.6))
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.0],
                      left=0.10, right=0.78, bottom=0.10, top=0.93, hspace=0.16)
ax0 = fig.add_subplot(gs[0])   # panel A: concept
ax1 = fig.add_subplot(gs[1])   # panel B: K(z)

# ── PANEL A — concept diagram (depth on Y, two columns side-by-side) ──────────
ax0.set_xlim(0.5, 9.5)
ax0.set_ylim(33, -5)
ax0.axis("off")
ax0.set_title("(a)  Conceptual model architecture",
              fontsize=14, fontweight="bold", loc="left", pad=12)

# column geometry
col_w = 1.6
hx, mx = 1.4, 6.4    # left edges
hx_c, mx_c = hx + col_w/2, mx + col_w/2  # centres

# ── shared depth axis (left only) ────────────────────────────────────────────
for d in [0, 7, 20, 30]:
    ax0.plot([hx - 0.30, hx], [d, d], color="0.55", lw=0.9)
    ax0.text(hx - 0.45, d, f"{d}", ha="right", va="center",
             fontsize=11, color="0.30")
ax0.text(hx - 1.35, 15, "Depth (cm)", ha="center", va="center",
         fontsize=12, color="0.30", rotation=90)

# surface line
ax0.plot([hx - 0.3, mx + col_w + 0.3], [0, 0], color="0.30", lw=1.2)
ax0.text((hx + mx + col_w) / 2, -1.5, "surface  ($z = 0$)",
         ha="center", va="bottom", fontsize=11, color="0.30", style="italic")

# ── HAYNE column ─────────────────────────────────────────────────────────────
n_strips = 80
for i in range(n_strips):
    y0 = i * 30 / n_strips
    y1 = (i + 1) * 30 / n_strips
    alpha = 0.10 + 0.55 * (i / n_strips)
    ax0.add_patch(mpatches.Rectangle((hx, y0), col_w, y1 - y0,
                                     facecolor=C_H, alpha=alpha, lw=0))
ax0.add_patch(mpatches.Rectangle((hx, 0), col_w, 30,
                                 facecolor="none", edgecolor=C_H, lw=1.4))

# Header (top)
ax0.text(hx_c, -5.0, "Hayne (2017)", ha="center", va="bottom",
         fontsize=13, fontweight="bold", color=C_H)
ax0.text(hx_c, -3.7, "smooth exponential",
         ha="center", va="bottom", fontsize=11, color=C_H, style="italic")

# K_s box (top of column)
ax0.text(hx_c, 3.0,
         fr"$K_s = {Ks_H*1e3:.2f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
         ha="center", va="center", fontsize=10, color=C_TXT,
         linespacing=1.3,
         bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                   edgecolor=C_H, lw=0.7, alpha=0.94))

# K_d box (bottom of column)
ax0.text(hx_c, 27.0,
         fr"$K_d = {Kd_H*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
         ha="center", va="center", fontsize=10, color="white",
         linespacing=1.3,
         bbox=dict(boxstyle="round,pad=0.22", facecolor=C_H,
                   edgecolor=C_H, lw=0.7))

# arrow showing K increases with depth
ax0.annotate("", xy=(hx_c, 22), xytext=(hx_c, 8),
             arrowprops=dict(arrowstyle="->", color="white",
                             lw=2.4, alpha=0.95))

# H-parameter callout to the right of the column
ax0.annotate(
    fr"$H = 6$ cm" "\n" "(e-folding\ndepth)",
    xy=(hx + col_w, 6), xytext=(hx + col_w + 1.5, 12.5),
    fontsize=10, color=C_H, ha="center", va="center",
    linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_H, lw=0.9,
                    connectionstyle="arc3,rad=0.30"))

# ── M&S column ───────────────────────────────────────────────────────────────
layers = [
    (0,  7,  C_MS_S, "Surface\nlayer",  C_TXT),
    (7,  20, C_MS_M, "Ramp\nzone",       C_TXT),
    (20, 30, C_MS_D, "Deep\nlayer",      "white"),
]
for (z0, z1, fc, lab, tc) in layers:
    ax0.add_patch(mpatches.Rectangle((mx, z0), col_w, z1 - z0,
                                     facecolor=fc, edgecolor=C_MS_D, lw=1.3))
    ax0.text(mx_c, (z0 + z1) / 2, lab, ha="center", va="center",
             fontsize=11, color=tc, linespacing=1.3, fontweight="semibold")

# Header
ax0.text(mx_c, -5.0, "Martinez & Siegler (2021)", ha="center", va="bottom",
         fontsize=13, fontweight="bold", color=C_MS_D)
ax0.text(mx_c, -3.7, "piecewise 3-layer",
         ha="center", va="bottom", fontsize=11, color=C_MS_D, style="italic")

# K_s callout — RIGHT of M&S column at top (don't conflict with the headers)
ax0.annotate(
    fr"$K_s = {Ks_M*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
    xy=(mx + col_w, 3.5), xytext=(mx + col_w + 1.3, 1.5),
    fontsize=10, color=C_MS_D, ha="center", va="center", linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_MS_D, lw=1.0,
                    connectionstyle="arc3,rad=-0.20"))

# K_d callout — RIGHT of M&S column at bottom
ax0.annotate(
    fr"$K_d = {Kd_M*1e3:.1f}$" "\n" r"mW m$^{-1}$ K$^{-1}$",
    xy=(mx + col_w, 25.0), xytext=(mx + col_w + 1.3, 27.5),
    fontsize=10, color=C_MS_D, ha="center", va="center", linespacing=1.3,
    arrowprops=dict(arrowstyle="-|>", color=C_MS_D, lw=1.0,
                    connectionstyle="arc3,rad=0.20"))

# breakpoint tags (right side)
for z_break, lab in [(7, "7 cm"), (20, "20 cm")]:
    ax0.plot([mx, mx + col_w], [z_break, z_break],
             color="white", lw=1.0, ls="--", alpha=0.85)
    ax0.text(mx + col_w + 0.18, z_break, lab, ha="left", va="center",
             fontsize=10, color=C_MS_D,
             bbox=dict(boxstyle="round,pad=0.18",
                       facecolor="white", edgecolor=C_MS_D, lw=0.6))

# ══════════════════════════════════════════════════════════════════════════════
# PANEL B — K(z) curves
# ══════════════════════════════════════════════════════════════════════════════
ax1.set_title(fr"(b)  $K(z)$ at $T = 250$ K  "
              r"(includes radiative multiplier $1+\chi(T/T_\mathrm{ref})^3$)",
              fontsize=14, fontweight="bold", loc="left", pad=10)

KH  = K_hayne(z) * 1e3
KMS = K_ms(z)    * 1e3

ax1.fill_betweenx(z_cm, KH, KMS, where=(KH < KMS),
                  facecolor=C_MS_D, alpha=0.10, label="M&S > Hayne region")
ax1.plot(KH,  z_cm, color=C_H,    lw=2.4,
         label="Hayne (2017) — smooth exponential")
ax1.plot(KMS, z_cm, color=C_MS_D, lw=2.4, ls="--",
         label="Martinez & Siegler (2021) — 3-layer")

for z_break, lab in [(7, "7 cm"), (20, "20 cm")]:
    ax1.axhline(z_break, color=C_MS_D, lw=0.9, ls=":", alpha=0.6)
    ax1.text(13.6, z_break + 0.2, lab, fontsize=10,
             color=C_MS_D, alpha=0.85, va="top", ha="right")

# right-side endpoint labels
ax1.annotate(r"Hayne  $K_d = 3.4$",
             xy=(KH[-1], z_cm[-1]), xytext=(7.5, 31.5),
             fontsize=11, color=C_H,
             arrowprops=dict(arrowstyle="-|>", color=C_H, lw=0.9,
                             connectionstyle="arc3,rad=-0.18"))
ax1.annotate(r"M&S  $K_d = 6.3$",
             xy=(KMS[-1], z_cm[-1]), xytext=(11.0, 31.5),
             fontsize=11, color=C_MS_D,
             arrowprops=dict(arrowstyle="-|>", color=C_MS_D, lw=0.9,
                             connectionstyle="arc3,rad=-0.20"))

ax1.set_xlabel(r"Thermal conductivity $K$ (mW m$^{-1}$ K$^{-1}$)", fontsize=12)
ax1.set_ylabel("Depth (cm)", fontsize=12)
ax1.invert_yaxis()
ax1.set_ylim(33, -1)
ax1.set_xlim(0, 14)
ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax1.grid(color="0.90", lw=0.7)
ax1.tick_params(labelsize=11)
ax1.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0.0, fontsize=11, framealpha=0.96, edgecolor="0.75")

# ── save ──────────────────────────────────────────────────────────────────────
out_pdf = "/tmp/fig_model_schematic.pdf"
out_png = "/tmp/fig_model_schematic.png"
fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
fig.savefig(out_png, dpi=180, bbox_inches="tight")
import os
print(f"Saved {out_pdf}  ({os.path.getsize(out_pdf)//1024} kB)")
