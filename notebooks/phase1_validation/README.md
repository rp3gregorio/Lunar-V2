# Phase 1 — Point-Source Apollo Validation

Benchmark the 1-D Crank-Nicolson solver at the Apollo 15 and 17 HFE
sites against the only in-situ lunar subsurface temperature records
publicly available. This phase is strictly one-point-at-a-time — the
deliverable is an apples-to-apples comparison between the **Hayne
2017** model (as shipped in `phayne/heat1d`, vendored under
`third_party/heat1d/`) and the **Discrete Layer Model** (Apollo-
calibrated three-slab alternative) evaluated on the stabilised-window
deep sensors (`z ≥ 80 cm`).

| Notebook | Site(s) | Reference |
|---|---|---|
| `01_apollo_validation.ipynb` | Apollo 15 (26 °N) + Apollo 17 (20 °N) HFE | Nagihara et al. 2018, 2019 |
| `02_equatorial_diurnal.ipynb` | Lunar equator — reference diurnal cycle, Hayne vs Martinez vs Discrete | Hayne 2017; Martinez & Siegler 2021 |
| `03_spice_insolation.ipynb` | Apollo 15 driven by SPICE ephemeris vs sinusoidal proxy | NAIF DE440 |

## Supporting notes

* `APOLLO_DIURNAL_FIX_NOTES.md` — why the synodic (not sidereal) period
  is the correct phase basis for HFE folding.
* `SHALLOW_SENSOR_DIAGNOSIS.md` — the borestem heat-short artefact
  that forces RMSE evaluation to `z ≥ 80 cm`.

## Phase-1 success criteria

* Apollo 15 deep-sensor RMSE ≤ 1 K (Discrete Layer), ≤ 1.5 K (Hayne 2017).
* Apollo 17 mean-T at 1 m within ±2 K of observed.
* Hayne Figure 4 reproduced at the Apollo 15 site (T vs depth at
  multiple local times, overlaid with HFE stabilised-window deep
  sensors).
* Hayne-style summary statistics table (bias, RMSE, skill score)
  written into `output/tables/apollo_stats.csv`.

## Data availability

* Apollo HFE — auto-downloaded from NASA PDS Geosciences Node (public,
  ~40 MB total; cached locally after first run).
* SPICE kernels — auto-downloaded from NAIF (public, ~46 MB; cached).

## Scope note — what is NOT in Phase 1

* Chang'E-4 and ChaSTE in-situ probe comparisons are **out of scope**
  for this thesis (the raw time-series are login-gated and add no
  information beyond the Apollo benchmark).
* Global maps, latitude-dependent H-parameter, rock-abundance mixing,
  Martinez-Siegler cold-region correction, Burger microphysics, and
  DEM/horizon shadowing move to **Phase 2** (improved Hayne model).
