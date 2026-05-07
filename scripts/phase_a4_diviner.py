"""
Phase A-4: Diviner surface-temperature closure at the Apollo 15 and 17
landing sites.

What this script does
─────────────────────
1. Downloads the Diviner GCP (Global Cumulative Product) latitude bands
   that cover the Apollo 15 (lat ≈ 26°N) and Apollo 17 (lat ≈ 20°N)
   sites, from the NASA PDS Geosciences node.  The download is cached
   so re-runs are cheap.

2. For each site, extracts the Diviner-observed diurnal temperature
   cycle T(LST) at the closest grid pixel.

3. Runs the Phase-1 1-D Crank-Nicolson solver at the same site with
   the per-site retrieved K_d from output/phase_a_results.json,
   producing the *modelled* surface-T trace over one lunation.

4. Generates a 2-panel comparison figure
   (paper/appendix/figures/fig_diviner_closure.pdf) that overlays the
   two on the same SPICE LST axis at A15 and A17.

5. Reports the surface-T RMSE and bias at each site to
   output/phase_a4_results.json.

How to run
──────────
  cd /Users/rp3gregorio/Lunar-V2
  python3 scripts/phase_a4_diviner.py

The PDS files are ~156 MB each; budget ~5-10 minutes for the first
run (network-bound).  Subsequent runs reuse the cache under
data/diviner/gcp/.

If your network blocks the urlopen approach the script uses, an
equivalent curl one-liner per band is printed at the start.
"""
from __future__ import annotations
import json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2")
from lunar import _bootstrap as boot
boot.ensure_lunar(extra=("spiceypy", "scipy"))

from lunar.diviner import (
    download_gcp_band, load_gcp_band, select_diurnal_curve,
    gcp_band_for_latitude, gcp_band_filename, GCP_DIR_URL,
)

# Re-use the publication style + solver wrapper from earlier scripts
sys.path.insert(0, "/Users/rp3gregorio/Lunar-V2/scripts")
from phase2_figures_v2 import (   # type: ignore
    C_A15, C_A17, C_HAYNE, C_TEAL, C_CHAR, C_DIM, C_GRID,
    FS_LABEL, FS_TICK, FS_LEGEND, fmt_axis,
)
from phase_a_pipeline import run_with, SITES, T_LUNAR, DT_STEP   # type: ignore

DATA_DIR  = pathlib.Path("/Users/rp3gregorio/Lunar-V2/data/diviner/gcp")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS   = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase_a_results.json")
OUT_JSON  = pathlib.Path("/Users/rp3gregorio/Lunar-V2/output/phase_a4_results.json")
OUT_FIG   = pathlib.Path("/Users/rp3gregorio/Lunar-V2/paper/appendix/figures/fig_diviner_closure.pdf")


def print_curl_equivalent(lat_min: int, lat_max: int) -> None:
    """Print the equivalent curl command for users who can't urlopen."""
    fname = gcp_band_filename(lat_min, lat_max)
    url   = f"{GCP_DIR_URL}/{fname}"
    print(f"  curl --user-agent 'Lunar-V2/phase-a4' "
          f"-L -o {DATA_DIR / fname} '{url}'")


def fetch_band(lat: float) -> tuple[int, int]:
    """Download via curl — bypasses Python's SSL certificate setup,
    which is often broken on macOS Python.org installs."""
    import subprocess
    lat_min, lat_max = gcp_band_for_latitude(lat)
    fname = gcp_band_filename(lat_min, lat_max)
    dest  = DATA_DIR / fname
    if dest.exists() and dest.stat().st_size > 100_000_000:
        print(f"  cached: {dest}", flush=True)
        return lat_min, lat_max
    url = f"{GCP_DIR_URL}/{fname}"
    print(f"  downloading {fname} (~156 MB) via curl ...", flush=True)
    cmd = [
        "curl", "-L", "--fail", "--silent", "--show-error",
        "--user-agent", "Lunar-V2/phase-a4",
        "-o", str(dest), url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"curl failed: {res.stderr}\n"
                 f"manual command:\n  {' '.join(cmd)}")
    print(f"  downloaded {dest.stat().st_size/1e6:.1f} MB → {dest}", flush=True)
    return lat_min, lat_max


def diviner_diurnal_at(site_cfg, lat_min: int, lat_max: int
                        ) -> tuple[np.ndarray, np.ndarray]:
    """Return (LST_hours, T_kelvin) for the Diviner GCP pixel(s) closest
    to the site, averaged over a ±1° longitude window."""
    band = load_gcp_band(lat_min, lat_max, cache_dir=DATA_DIR,
                         columns=("t7", "tbol"))
    lon = site_cfg["lon"]
    lst, T = select_diurnal_curve(
        band, latitude=site_cfg["lat"],
        channel="tbol",
        half_width_deg=0.5,
        longitude_range=(lon - 1.0, lon + 1.0),
    )
    return lst, T


def model_surface_diurnal(site_cfg, kd) -> tuple[np.ndarray, np.ndarray]:
    """Run the Phase-1 solver at the given K_d and return (LST_hours, T_surface)."""
    # The existing run_with averages over the analysis lunation; here we
    # need the time-resolved surface trace, so we re-implement minimally.
    from copy import deepcopy
    from lunar.grid import make_geometric_grid
    from lunar.properties import conductivity_hayne, specific_heat
    from lunar.constants import K_SURFACE, H_PARAMETER, CHI_RADIATIVE, T_REFERENCE
    from lunar.solver import PixelInputs, solve_pixel
    GRID = dict(z_max=5.0, dz0=0.002, growth=0.08)
    HAYNE = dict(K_S=K_SURFACE, H=H_PARAMETER, CHI=CHI_RADIATIVE, T_REF=T_REFERENCE)
    S0 = 1361.0
    site = deepcopy(site_cfg)
    grid_  = make_geometric_grid(**GRID)
    z_mid  = grid_.z_mid
    N_t    = int(T_LUNAR / DT_STEP) + 1
    t_s    = np.linspace(0.0, T_LUNAR, N_t)
    cos_lat = np.cos(np.deg2rad(site["lat"]))
    phase   = 2.0 * np.pi * t_s / T_LUNAR
    insol   = S0 * cos_lat * np.maximum(0.0, np.cos(phase))
    def k_func(T, z):
        return conductivity_hayne(T, z, Ks=HAYNE["K_S"], Kd=kd,
                                  H=HAYNE["H"], chi=HAYNE["CHI"])
    def cp_func(T):
        return specific_heat(T, model="hayne")
    K_init = k_func(np.full_like(z_mid, site["T_MEAN_EFF"]), z_mid)
    T_init = site["T_MEAN_EFF"] + site["Q_BASAL"] * np.cumsum(grid_.dz / K_init)
    out = solve_pixel(PixelInputs(
        grid=grid_, t=t_s, bc_mode="radiative",
        insolation=insol, albedo=site["albedo"],
        emissivity=site["emissivity"], Q_b=site["Q_BASAL"], T_init=T_init,
        n_lunations_spinup=30, spinup_tol_K=0.05,
        K_func=k_func, cp_func=cp_func,
    ))
    # Map analysis-lunation time to local solar time (LST in hours).
    # Our SPICE phase = 2π t / T_LUNAR; LST=12 at noon (max insolation),
    # which is t=0 in the wave we used. So LST = 12 + 24 * t / T_LUNAR
    # mod 24.
    lst = (12.0 + 24.0 * t_s / T_LUNAR) % 24.0
    T_surf = out.T[0, :]   # surface trace
    # sort by LST so the comparison plot is monotonic
    order = np.argsort(lst)
    return lst[order], T_surf[order]


def main():
    if not RESULTS.exists():
        sys.exit(f"need {RESULTS} from phase_a_pipeline.py first")
    phase_a = json.loads(RESULTS.read_text())

    print("Phase A-4: Diviner surface-T closure", flush=True)
    print(f"Cache directory: {DATA_DIR}", flush=True)
    print()

    out = {}
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6),
                             gridspec_kw={"wspace": 0.30})
    fig.subplots_adjust(left=0.07, right=0.97, top=0.86, bottom=0.16)

    for ax, name in zip(axes, ["A15", "A17"]):
        cfg = SITES[name]
        kd  = phase_a[name]["kd_star"]
        print(f"=== {name}  ({cfg['label']}, lat = {cfg['lat']:.2f}°) ===",
              flush=True)
        lat_min, lat_max = fetch_band(cfg["lat"])
        print(f"   reading band {lat_min:+d}–{lat_max:+d}° N ... ", flush=True)
        lst_div, T_div = diviner_diurnal_at(cfg, lat_min, lat_max)
        print(f"   running solver at K_d* = {kd*1e3:.2f} mW/m/K ...", flush=True)
        lst_mod, T_mod = model_surface_diurnal(cfg, kd)

        # Resample model onto the Diviner LST bins for residual stats
        T_mod_at_div = np.interp(lst_div, lst_mod, T_mod)
        rmse = float(np.sqrt(np.nanmean((T_mod_at_div - T_div) ** 2)))
        bias = float(np.nanmean(T_mod_at_div - T_div))
        print(f"   RMSE = {rmse:.2f} K,  bias = {bias:+.2f} K", flush=True)
        out[name] = dict(kd_used=kd, rmse_K=rmse, bias_K=bias,
                         n_diviner_bins=int(np.sum(np.isfinite(T_div))))

        # plot
        col = C_A15 if name == "A15" else C_A17
        ax.plot(lst_div, T_div, "o", markersize=4.5, color=col, alpha=0.55,
                mec="white", mew=0.4, label="Diviner (GCP)")
        ax.plot(lst_mod, T_mod, "-", color=col, lw=2.0,
                label=f"Model  ($K_d^{{*}} = {kd*1e3:.2f}$)")
        fmt_axis(ax,
                 xlabel="Local solar time  (hours)",
                 ylabel="Surface temperature  (K)",
                 title=f"({['a','b'][['A15','A17'].index(name)]})  {name}    "
                       f"RMSE = {rmse:.1f} K,  bias = {bias:+.1f} K")
        ax.set_xlim(0, 24)
        ax.legend(loc="upper left", borderpad=0.6)

    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {OUT_JSON}", flush=True)
    fig.savefig(OUT_FIG)
    plt.close(fig)
    print(f"Saved: {OUT_FIG}", flush=True)


if __name__ == "__main__":
    main()
