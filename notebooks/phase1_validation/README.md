# Phase 1 — Point-Source Thermal Validation

Single-point (1-D) benchmark of the Lunar-V2 Crank-Nicolson thermal solver
against the Apollo 15 and 17 Heat Flow Experiment (HFE).

## Notebook

| File | Contents |
|---|---|
| `01_apollo_validation.ipynb` | Full Phase-1 pipeline: model verification, solver runs, Figs 1–4, statistics |

## Key figures produced

| Figure | Description |
|---|---|
| **Fig 1** — `hayne_model_properties.{png,pdf}` | Hayne (2017) K(z), K(T), ρ(z), c_p(T) — confirms exact Appendix A implementation |
| **Fig 2** — `apollo_mean_T_profile.{png,pdf}` | Annual-mean T(z) at A15 + A17: Hayne vs Discrete vs Apollo HFE |
| **Fig 3** — `a15_diurnal_sensor_grid.{png,pdf}` | Per-sensor diurnal cycles at A15 — SPICE LST, peak-aligned |
| **Fig 4** — `a17_diurnal_sensor_grid.{png,pdf}` | Per-sensor diurnal cycles at A17 — SPICE LST, peak-aligned |

## Models compared

| Model | K(T,z) form | Calibration anchor |
|---|---|---|
| **Hayne (2017)** | H-parameter exponential + χ(T/350)³ | Diviner surface brightness T |
| **Discrete 3-layer** | Sharp layers (0-7, 7-20, >20 cm) + same χ(T/350)³ | Apollo HFE subsurface gradient |

Both share: same Crank-Nicolson solver, same geothermal flux BC, same Hayne (2017)
c_p(T) polynomial (Ledlow 1992 / Hemingway 1981).

## Validation sites

| Mission | Site | Coords | Q_b | Min. depth for RMSE |
|---|---|---|---|---|
| Apollo 15 | Hadley-Apennine | 26.13°N 3.63°E | 21 mW m⁻² (Langseth 1976) | 80 cm |
| Apollo 17 | Taurus-Littrow | 20.19°N 30.77°E | 15 mW m⁻² (Nagihara 2018) | 80 cm |

## Phase-1 success criteria

- Apollo 15 deep-sensor RMSE ≤ 2 K (both models)
- Apollo 17 deep-sensor RMSE ≤ 2 K (both models)
- No free-parameter tuning — all Hayne (2017) constants are as published

## Why shallow sensors (z < 80 cm) are excluded from RMSE

The fibreglass borestem axially conducts surface heat to the sensor cavity,
producing apparent diurnal swings of ~5 K at z = 35 cm even though the
regolith skin depth is only ~3-5 cm. This is a documented hardware artefact
(Langseth et al. 1977; Grott et al. 2010; Nagihara et al. 2018 §3.2).
Panels for z < 80 cm are shown to demonstrate the artefact, not scored.

## Archived notebooks

| File | Reason archived |
|---|---|
| `../../archive/phase1_legacy/02_equatorial_diurnal.ipynb` | K-model equatorial comparison moved to Phase 2 |
| `../../archive/phase1_legacy/03_spice_insolation.ipynb` | SPICE vs sinusoidal pedagogical; SPICE LST now integrated in 01 |

## Target publication

**Phase 1 results are scoped for a short letter** (~3000 words, 4 figures).

Recommended venue: **Geophysical Research Letters (GRL)** — 4-figure limit,
3500-word limit, high visibility, preprint via [ESS Open Archive](https://essopenarchive.org)
(free, immediate, indexed). Alternative: **Earth and Space Science (ESS)** — open
access, longer format if referee comments require expansion.

**Not recommended:** Annales Geophysicae — its scope is solar-terrestrial physics
and Earth's upper atmosphere, not planetary subsurface thermophysics.

## Data sources (auto-downloaded)

- Apollo 15/17 HFE — NASA PDS Geosciences Node (Nagihara et al. 2018 / 2019)
- SPICE kernels — NAIF generic kernels (DE440, PCK, LSK, MOON_ME)
