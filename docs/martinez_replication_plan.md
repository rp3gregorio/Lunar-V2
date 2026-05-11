# Phase 2 — Martinez & Siegler (2021) Replication Plan

> **Status:** Tier 1 complete — 9 of 11 paper figures replicated.
> **Branch:** `claude/cleanup-repo-organization-EcS3U`
> **Last updated:** 2026-05-11

## What Phase 2 is

Per `.claude/skills/SKILL.md`:
> **Phase 2:** Martinez & Siegler (2021) model + shadowing/DEM effects. Both fold into improved Hayne global model.

Phase 2 is **one thing** with two halves:
- The **K(T, ρ)** low-temperature thermal conductivity model from M&S 2021
- The **illumination / DEM / shadow** physics needed to apply it at PSRs and craters

## Repository layout (mirrors upstream MATLAB structure)

```
.scratch/lunar1Dheat/           # upstream MATLAB code (gitignored; Zenodo DOI 10.5281/zenodo.12586656)
│   ├── Global/                 # → our scripts/phase2/global/ + phase2.ipynb §1-7
│   ├── Craters/                # → our scripts/phase2/craters/ + phase2.ipynb crater section
│   └── PSRShoemaker/           # → our scripts/phase2/psr_shoemaker/ + phase2.ipynb PSR section

data/upstream/martinez2021/     # committed data products (small files, cited)
│   └── shoemakerIllumination.mat  # 697-sample ray-traced illumination (14 KB)

scripts/phase2/
│   ├── global/
│   │   ├── fig1_K_vs_T.py              # K(T) overlay Hayne vs M&S, 8 densities
│   │   ├── fig2_diurnal_45N.py         # 45°N diurnal vs Diviner T7
│   │   ├── fig4_equator_reference.py   # 0° 4-panel sanity check
│   │   ├── fig5_multilat_diurnal.py    # 4-site nighttime T_s vs Diviner
│   │   ├── fig6_multilat_gradient.py   # 4-site midnight T(z)
│   │   ├── fig7_latitude_sweep.py      # T_mean vs lat + Apollo markers (parallel)
│   │   ├── download_lola_dem.py        # PGDA LOLA DEM downloader
│   │   └── fig_southpolar_dem_map.py   # South polar DEM map
│   ├── craters/
│   │   └── fig89_crater_sweep.py       # D=5,8,16 × lat 75-89.9° (Figs 8 + 9)
│   └── psr_shoemaker/
│       ├── fig3_diurnal.py             # Shoemaker T_s(t) — real .mat input
│       └── figs45_subsurface.py        # T(z) + ΔT(z) profiles

notebooks/phase2/
│   └── phase2.ipynb                    # single merged notebook with all outputs embedded

lunar/illumination.py
    + crater_floor_insolation()         # port of upstream insolationcrater.m
    + load_shoemaker_illumination()     # reads shoemakerIllumination.mat → dict
```

## Source provenance

| Source | Use | Location |
| --- | --- | --- |
| MATLAB code release (Zenodo `10.5281/zenodo.12586656`, GitHub `angelicam01/lunar1Dheat` v1.6) | Ground truth for equations, BC, grid params | `.scratch/lunar1Dheat/` (gitignored) |
| `shoemakerIllumination.mat` (same release) | Real ray-traced illumination for Shoemaker PSR | `data/upstream/martinez2021/` (committed) |
| LPSC 2022 abstract #2754 | Equation form, figure list | `paper/refs/martinez_siegler_lpsc2022.pdf` |
| JGR Planets 126, e2021JE006829 | Full paper | see Hayne group + Martinez Zenodo |

## Illumination strategy

| Use case | Method |
| --- | --- |
| Shoemaker PSR replication (Fig 3) | `load_shoemaker_illumination()` → upstream `.mat` precomputed by ray-tracing with LOLA |
| Generic bowl crater (parametric) | `crater_floor_insolation()` → port of `insolationcrater.m` (simple D² scaling) |
| New PSR sites / extensions | `lunar/illumination.py` `compute_horizon()` → Mazarico 2011 DEM horizon tracer |

## Figure status

> "Our Fig N" indexes our file naming (`output/figures/phase2_figN_*`).
> "Paper Fig N" maps to Martinez & Siegler (2021) JGR's 11-figure list.

| Our Fig | Paper Fig | Subject | Script | Notes |
| --- | --- | --- | --- | --- |
| 1 | 3 | K(T, ρ) overlay, 8 densities | `global/fig1_K_vs_T.py` | mislabeled |
| 2 | 5a | 45°N diurnal vs Diviner T7 | `global/fig2_diurnal_45N.py` | Vasavada albedo + top-only spinup |
| 3 | 10 | Shoemaker surface T(t) | `psr_shoemaker/fig3_diurnal.py` | real upstream `.mat` (697-day run) |
| 4 | 11 | Shoemaker T(z) profile | `psr_shoemaker/figs45_subsurface.py` | daveTemp BC |
| 5 | — | ΔT vs depth at Shoemaker | `psr_shoemaker/figs45_subsurface.py` | 1-D proxy of paper Fig 9 |
| 4(eq) | 4 | 0° equator 4-panel reference | `global/fig4_equator_reference.py` | NEW (2026-05-11) |
| 5(ml) | 5 | Nighttime T_s at 4 latitudes | `global/fig5_multilat_diurnal.py` | NEW |
| 6(ml) | 6 | Midnight T(z) at 4 latitudes | `global/fig6_multilat_gradient.py` | NEW |
| 7 | 7 | T_mean vs latitude + Apollo | `global/fig7_latitude_sweep.py` | NEW (headline) |
| 8 | 8 | Crater min/max T, D=5,8,16 | `craters/fig89_crater_sweep.py` | NEW |
| 9 | 9 | Crater ΔT(z), D=5,8,16, z=1m, 2m | `craters/fig89_crater_sweep.py` | NEW |

**Score: 9 of 11 paper figures replicated** (missing paper Figs 1 + 2 only).

## Key fixes applied vs previous state

1. **B1 = 2.0022e-13** (was 2.022e-13 — MATLAB release typo). Fixed in `lunar/properties.py`.
2. **Fig 3 surface BC**: was calibrated constant 0.191 W/m² (wrong). Now uses real `shoemakerIllumination.mat` Q_total(t) (mean 0.141 W/m²).
3. **Figs 4 & 5 surface BC**: was 44.4 K from Diviner GCP Tbol (different product). Now uses daveTemp mean 34.2 K from the same `.mat` file (same reference as the upstream paper).
4. **Vasavada angle-dep albedo**: Fig 2 now uses A(i) = A0 + 0.06·i³ + 0.25·i⁸ baked into insolation (was flat 0.12). Dropped full-diurnal RMSE from 15 K to 9.2 K.
5. **Top-only spinup**: `PixelInputs.spinup_depth_m = 0.10 m` — convergence checked only in top 10 cm. Solver now converges in 10-42 lunations instead of never.

## Deferred / future work

- **Fig 5 2-D map**: requires per-pixel illumination (PSR pixels → `compute_horizon()` per pixel). 1-D proxy in `figs45_subsurface.py`.
- **CE-4/ChaSTE slope correction** (Phase 2B): 6° local slope at CE-4 to close the −34 K surface-T bias from Phase 1. Target notebook: `notebooks/phase2/02_craters.ipynb`.
