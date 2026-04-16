# Notebooks

Jupyter notebooks implementing the Lunar-V2 thermal modeling pipeline.
Each notebook is self-installing (click "Run All") and produces publication-
quality figures in `output/figures/` plus animated GIFs in `output/gifs/`.

## Run order

| # | Notebook | Purpose | Key outputs |
|---|----------|---------|-------------|
| 00 | `00_quickstart.ipynb` | Grid, properties, analytical wave validation | Sanity checks |
| 01 | `01_apollo_validation.ipynb` | Apollo 15 HFE data comparison | Time series, mean T, amplitude vs depth |
| 02 | `02_equatorial_diurnal.ipynb` | **K-model comparison** (Hayne vs Martinez vs ice) + 80°S polar | Surface T curves, ΔT maps, property profiles, GIFs |
| 03 | `03_spice_insolation.ipynb` | SPICE ephemeris → insolation → thermal solver at Apollo 15 | SPICE vs proxy, subsurface T at sensor depths |
| 04 | `04_illumination_shadows.ipynb` | **Phase 2**: Horizon tracing, shadow-corrected insolation, DEM | Crater validation, illumination maps, shadow GIFs |

## Output structure

```
output/
├── figures/    # Publication-quality PDF + PNG (300 DPI)
├── gifs/       # Animated GIFs of thermal evolution
├── data/       # Exported numerical data
└── tables/     # Summary tables
```

## Dependencies

Core: `numpy`, `scipy`, `numba`, `matplotlib`
Optional: `spiceypy` (NB03), `rasterio` (NB04), `Pillow` (GIFs)
