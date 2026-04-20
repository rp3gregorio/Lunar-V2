# Phase 3 — Polar Maps & Ice Stability (planned)

Use the horizon + view-factor pipeline from Phase 2 at every pixel of
a polar DEM, solve the 1-D regolith column at each, and compare the
modelled bolometric surface temperatures against Diviner polar
cumulative products. Derive ice-stability depths from the resulting
T(z) maps.

## Planned notebooks

| Notebook | Purpose |
|---|---|
| `06_diviner_polar_validation.ipynb` | Model vs Diviner PCP bolometric T maps at one pole (coarse grid first). |
| `07_polar_t_min_map.ipynb` | Annual-minimum / annual-mean T maps at 0 cm, 10 cm, 1 m. |
| `08_ice_stability_depth.ipynb` | H2O / CO2 ice stability depth maps per Schorghofer 2008 criterion. |

## Data dependencies

* `boot.ensure_lola_dem_80mpp()` — 80 m/pixel polar DEM (auto-download).
* Diviner PCP tables — `lunar.validation.load_diviner_pcp_polar()` already
  exists; PDS bundle fetch needs to be wired into `_bootstrap.py`.

## Success criterion

Bolometric-T residual (model − Diviner) RMS ≤ 8 K at one pole over a
quasi-polar-stereographic coarse grid, matching published latitude-dependent
Diviner error envelopes.
