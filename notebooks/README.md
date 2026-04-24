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
| `phase1_validation/` | ✅ shipped | **Point-source Apollo validation.** Apollo 15/17 HFE only. Hayne 2017 (as in `third_party/heat1d/`) vs Discrete Layer vs observation. |
| `phase2_improved_hayne/` | 🚧 in progress | **Improved Hayne 2017 global model.** H-lat map + rock-abundance mix + Martinez-Siegler cold-region correction + Burger microphysics + DEM/horizon shadowing + Diviner PDS validation. |
| `phase3_rtm_ice/` | ⏳ planned | RTM coupling, Jacobian, ice-stability index (supports TSUKIMI retrieval). |
| `phase4_thesis/` | ⏳ planned | Thesis figure bundles + paper LaTeX integration. |

## Dependencies

* **Core** (every notebook): `numpy`, `scipy`, `numba`, `matplotlib`.
* **Phase 1**: `spiceypy` (notebooks 01 and 03).
* **Phase 2**: `rasterio`, `spiceypy`, `Pillow`, `pyshtools` (for
  H-parameter latitude fit).

Everything is pip-installed by the bootstrap cell on first run.

## Output structure

```
output/
├── figures/    # Publication-quality PDF + PNG (300 DPI)
├── gifs/       # Animated GIFs of thermal evolution
├── data/       # Exported numerical data
└── tables/     # Summary tables
```
