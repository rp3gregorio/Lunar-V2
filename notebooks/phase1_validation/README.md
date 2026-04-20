# Phase 1 — Point-Source Validation

Benchmark the 1-D Crank-Nicolson solver against every in-situ lunar
thermal record currently available in the peer-reviewed literature.

| Notebook | Site(s) | Reference |
|---|---|---|
| `01_apollo_validation.ipynb` | Apollo 15 (26 °N) + Apollo 17 (20 °N) HFE, Chang'E-4 (45 °S), ChaSTE (69 °S) | Nagihara 2018; Huang 2022; Murty 2025 / Das 2025 / Seth 2025 |
| `02_equatorial_diurnal.ipynb` | Lunar equator — reference diurnal cycle comparing three conductivity models | Hayne 2017; Martinez & Siegler 2021 |
| `03_spice_insolation.ipynb` | Apollo 15 site driven by SPICE ephemeris vs sinusoidal proxy | NAIF DE440 |

## Supporting notes

* `APOLLO_DIURNAL_FIX_NOTES.md` — why the synodic (not sidereal) period is the
  correct phase basis for Apollo HFE folding.
* `SHALLOW_SENSOR_DIAGNOSIS.md` — the borestem heat-short artefact that
  forces RMSE evaluation to `z ≥ 80 cm`.

## Phase-1 success criteria

* Apollo 15 deep-sensor RMSE ≤ 1 K (Discrete Layer model), ≤ 1.5 K (Hayne 2017).
* Apollo 17 mean-T at 1 m within ±2 K of observed.
* CE-4 surface T_peak within order-unity of Huang 2022 (bias explained by
  sinusoidal-proxy vs SPA-basin topography).
* ChaSTE surface T_peak bias ≲ 40 K under flat-surface geometry — the
  remaining gap is the **motivation for Phase 2**, where a 6° local slope
  closes it.

## Data availability

* Apollo HFE — auto-downloaded from NASA PDS Geosciences Node (public).
* SPICE kernels — auto-downloaded from NAIF (public).
* CE-4 raw time-series — login-gated (CLPDS or author request); only the
  peer-reviewed scalar CSV ships. Manual-download recipe is embedded in
  the §9 markdown of `01_apollo_validation.ipynb`.
* ChaSTE raw profile — login-gated (ISRO PRADAN); only the peer-reviewed
  scalar CSV ships. Manual-download recipe is embedded in the §10 markdown
  of `01_apollo_validation.ipynb`.
