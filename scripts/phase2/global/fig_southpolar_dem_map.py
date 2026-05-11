"""South-polar LOLA DEM map — foundation for global Phase 2 work.

Plots the LDEM_80S DEM (PGDA Product 90) in the native polar-stereographic
projection (Moon 2015 sphere, lon0 = 0, lat0 = -90), overlays the Shoemaker
PSR tile (87.91 deg S, 45.51 deg E) used for Figs 3-5, and adds latitude
gridlines at -80, -85, -88, -89.

This is the same DEM Martinez & Siegler (2021) implicitly use through their
Paige+2010 ray-tracer; getting it loaded and visualized in our pipeline is
a prerequisite for:
  * Per-pixel illumination maps (replace the constant Q in fig3 for sites
    other than Shoemaker, and for the global Fig 7 latitude sweep).
  * The 2-D 4-m ΔT map (M&S Fig 9) reconstruction.
  * PSR cataloguing for cold-trap stability (Williams et al. 2019).

Usage
-----
    python3 scripts/phase2/global/fig_southpolar_dem_map.py           # 80MPP (default)
    python3 scripts/phase2/global/fig_southpolar_dem_map.py --mpp 40  # finer detail

Run ``python3 scripts/phase2/global/download_lola_dem.py`` first.

Output: ``output/figures/phase2_fig_lola_southpolar.{pdf,png}``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.illumination import load_lola_dem
from lunar.phase2_plotting import COLORS, apply_phase2_style, savefig_pair

# Lunar constants — Moon 2015 sphere
R_MOON = 1737.4e3   # m

# Highlight target (Shoemaker tile used in Phase 2 Figs 3, 4, 5)
SHOEMAKER_LAT = -87.9102
SHOEMAKER_LON = 45.5073


def latlon_to_polarxy(lat_deg: np.ndarray, lon_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """South-polar stereographic from -90 deg with lon0=0.

    Returns (x, y) in metres, matching the convention the PGDA DEM uses.
    """
    lat = np.deg2rad(lat_deg)
    lon = np.deg2rad(lon_deg)
    # Standard south-polar stereographic projection
    rho = 2.0 * R_MOON * np.tan(np.pi / 4.0 + lat / 2.0)  # for south pole, lat<0 => rho>0
    x = rho * np.sin(lon)
    y = -rho * np.cos(lon)
    return x, y


def add_lat_circles(ax, lats=(-80, -85, -88, -89)) -> None:
    theta = np.linspace(0, 2 * np.pi, 360)
    lon_grid = np.rad2deg(theta)
    for lat in lats:
        x, y = latlon_to_polarxy(np.full_like(lon_grid, lat), lon_grid)
        ax.plot(x, y, color="0.4", lw=0.6, ls=":", alpha=0.7)
        # Label at lon = 90 deg
        x_lab, y_lab = latlon_to_polarxy(np.array([lat]), np.array([90.0]))
        ax.annotate(
            f"{lat}°", xy=(x_lab[0], y_lab[0]),
            fontsize=8, color="0.35", ha="left", va="center",
        )


def add_lon_radials(ax, r_outer: float, lons=(0, 45, 90, 135, 180, 225, 270, 315)) -> None:
    for lon in lons:
        x_in, y_in = latlon_to_polarxy(np.array([-80.0]), np.array([lon]))
        x_out, y_out = latlon_to_polarxy(np.array([-90.0]), np.array([lon]))
        # Reverse: from -90 outward to -80
        ax.plot([x_out[0], x_in[0]], [y_out[0], y_in[0]],
                color="0.4", lw=0.5, ls=":", alpha=0.6)
        # Outer label at lat=-80
        ax.annotate(
            f"{lon}°E", xy=(x_in[0], y_in[0]),
            fontsize=8, color="0.35", ha="center", va="center",
            xytext=(0, -10), textcoords="offset points",
        )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mpp", type=int, choices=(80, 40, 20), default=80)
    p.add_argument(
        "--subsample", type=int, default=4,
        help="On-load subsampling stride to keep RAM use low (default 4)",
    )
    args = p.parse_args()

    dem_path = _REPO_ROOT / "data" / "lola" / f"LDEM_80S_{args.mpp}MPP_ADJ.TIF"
    if not dem_path.exists():
        raise SystemExit(
            f"\nDEM not found: {dem_path}\n"
            f"Run scripts/phase2/global/download_lola_dem.py first.\n"
        )

    print(f"Loading {dem_path.name} (subsample={args.subsample})...")
    dem = load_lola_dem(dem_path, subsample=args.subsample)
    print(
        f"  shape = {dem.elevation.shape}, "
        f"x range [{dem.x.min()/1e3:.0f}, {dem.x.max()/1e3:.0f}] km, "
        f"y range [{dem.y.min()/1e3:.0f}, {dem.y.max()/1e3:.0f}] km\n"
        f"  elev range [{np.nanmin(dem.elevation)/1e3:+.2f}, "
        f"{np.nanmax(dem.elevation)/1e3:+.2f}] km"
    )

    # Plot
    apply_phase2_style()
    fig, ax = plt.subplots(figsize=(9.0, 9.0))

    # Mask values outside the DEM circle
    XX, YY = np.meshgrid(dem.x, dem.y)
    rho = np.sqrt(XX ** 2 + YY ** 2)
    rho_outer, _ = latlon_to_polarxy(np.array([-80.0]), np.array([0.0]))
    rho_outer = float(abs(rho_outer[0]))
    elev = np.where(rho <= rho_outer * 1.02, dem.elevation, np.nan)

    # Symmetric colour scale around 0 elevation
    elev_km = elev / 1000.0
    vmax = np.nanpercentile(np.abs(elev_km), 99)
    im = ax.pcolormesh(
        dem.x, dem.y, elev_km,
        cmap="terrain", vmin=-vmax, vmax=vmax,
        shading="auto", rasterized=True,
    )

    # Lat/lon graticule
    add_lat_circles(ax)
    add_lon_radials(ax, r_outer=rho_outer)

    # Highlight Shoemaker
    sh_x, sh_y = latlon_to_polarxy(
        np.array([SHOEMAKER_LAT]), np.array([SHOEMAKER_LON]),
    )
    ax.scatter(
        sh_x, sh_y, s=120, marker="*", color=COLORS["highlight"],
        edgecolor="black", linewidth=0.8, zorder=5,
        label=f"Shoemaker tile  ({SHOEMAKER_LAT:.2f}°, {SHOEMAKER_LON:.2f}°E)",
    )

    ax.set_aspect("equal")
    ax.set_xlim(-rho_outer * 1.05, rho_outer * 1.05)
    ax.set_ylim(-rho_outer * 1.05, rho_outer * 1.05)
    ax.set_xlabel("x  (m, polar-stereographic)")
    ax.set_ylabel("y  (m, polar-stereographic)")
    ax.set_title(
        f"LOLA south-polar DEM (PGDA product 90, {args.mpp} m/px native)\n"
        f"Reference for Phase 2 PSR work; 80°S - 90°S cap"
    )

    # Colourbar — kept compact, on the side
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label("Elevation (km, relative to lunar reference sphere R = 1737.4 km)")

    # Star marker legend at bottom
    handles, labels = ax.get_legend_handles_labels()
    fig.subplots_adjust(bottom=0.10)
    fig.legend(
        handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02),
        frameon=True, edgecolor="0.6",
    )

    out_path = _REPO_ROOT / "output" / "figures" / "phase2_fig_lola_southpolar.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    savefig_pair(fig, out_path)
    plt.close(fig)
    print(f"Saved {out_path.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
