# Notebooks — Phase Layout

Jupyter notebooks implementing the Lunar-V2 thermal modeling pipeline.
Each notebook is self-installing (click **Run All**); it puts the repo
root on `sys.path`, installs missing Python packages into the current
kernel, and auto-downloads (or verifies) any required data. All outputs
land in `output/figures/` and `output/gifs/`.

Work is organised by **mission phase** — each folder is one cohesive
slice of the TSUKIMI pipeline, with its own README.

## Folders

| Folder | Status | Purpose |
|---|---|---|
| `phase0_quickstart/` | ✅ shipped | Library tour. Grid, properties, analytical wave — confirms `lunar` imports cleanly on a fresh clone. |
| `phase1_validation/` | ✅ shipped | **Point-source validation.** Apollo 15/17 HFE, Chang'E-4, ChaSTE, equatorial Hayne reference, SPICE vs sinusoidal proxy. |
| `phase2_illumination/` | 🚧 in progress | Topographic coupling. DEM + horizon tracing + shadow-corrected insolation, then slope-corrected re-runs of ChaSTE (69°S). |
| `phase3_polar_maps/` | ⏳ planned | Diviner bolometric map validation over one pole + ice-stability depths. |
| `phase4_manuscript/` | ⏳ planned | Thesis / paper figure bundles, LaTeX integration. |

## Dependencies

* **Core** (every notebook): `numpy`, `scipy`, `numba`, `matplotlib`.
* **Phase 1**: `spiceypy` (notebooks 01 and 03).
* **Phase 2**: `rasterio`, `spiceypy`, `Pillow` (GIFs).

Everything is pip-installed by the bootstrap cell on first run.

## Output structure

```
output/
├── figures/    # Publication-quality PDF + PNG (300 DPI)
├── gifs/       # Animated GIFs of thermal evolution
├── data/       # Exported numerical data
└── tables/     # Summary tables
```
