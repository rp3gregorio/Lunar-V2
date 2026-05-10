# Phase 2 — Martinez & Siegler (2021) Replication Plan

> **Status:** Consolidation complete. Phase 2 is now a single directory.
> **Branch:** `claude/cleanup-repo-organization-EcS3U`
> **Last updated:** 2026-05-10

## What Phase 2 is

Per `.claude/skills/SKILL.md`:
> **Phase 2:** Martinez & Siegler (2021) model + shadowing/DEM effects. Both fold into improved Hayne global model.

Phase 2 is **one thing** with two halves:
- The **K(T, ρ)** low-temperature thermal conductivity model from M&S 2021
- The **illumination / DEM / shadow** physics needed to apply it at PSRs and craters

## Repository layout (mirrors upstream MATLAB structure)

```
.scratch/lunar1Dheat/           # upstream MATLAB code (gitignored; Zenodo DOI 10.5281/zenodo.12586656)
│   ├── Global/                 # → our notebooks/phase2/01_global.ipynb
│   ├── Craters/                # → our notebooks/phase2/02_craters.ipynb
│   └── PSRShoemaker/           # → our notebooks/phase2/03_psr_shoemaker.ipynb

data/upstream/martinez2021/     # committed data products (small files, cited)
│   └── shoemakerIllumination.mat  # 697-sample ray-traced illumination (14 KB)

scripts/phase2/
│   ├── global/
│   │   ├── fig1_K_vs_T.py              # Fig 1: K(T) overlay Hayne vs M&S
│   │   └── fig2_diurnal_45N.py         # Fig 2: 45°N diurnal vs Diviner T7
│   ├── craters/                        # (parametric bowl-crater; populated when needed)
│   └── psr_shoemaker/
│       ├── fig3_diurnal.py             # Fig 3: Shoemaker T_s(t) vs daveTemp
│       └── figs45_subsurface.py        # Figs 4 & 5: T(z), ΔT(z)

notebooks/phase2/
│   ├── 01_global.ipynb                 # Figs 1, 2 — run in <1 s (cached) or ~3 min (RERUN)
│   ├── 02_craters.ipynb                # crater_floor_insolation demo + horizon tracer API
│   └── 03_psr_shoemaker.ipynb          # Figs 3, 4, 5 — real upstream illumination data

lunar/illumination.py
    + crater_floor_insolation()         # port of upstream insolationcrater.m (8-line formula)
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

| Fig | Subject | Script | Status |
| --- | --- | --- | --- |
| 1 | K(T, ρ) overlay, 6 densities | `global/fig1_K_vs_T.py` | ✅ Complete |
| 2 | 45°N diurnal vs Diviner T7 | `global/fig2_diurnal_45N.py` | ✅ Complete (Vasavada albedo, top-only spinup) |
| 3 | Shoemaker surface T(t) | `psr_shoemaker/fig3_diurnal.py` | ✅ Complete (real upstream illumination data) |
| 4 | Shoemaker T(z) profile | `psr_shoemaker/figs45_subsurface.py` | ✅ Complete |
| 5 | ΔT vs depth (1-D proxy) | `psr_shoemaker/figs45_subsurface.py` | ✅ Complete |

## Key fixes applied vs previous state

1. **B1 = 2.0022e-13** (was 2.022e-13 — MATLAB release typo). Fixed in `lunar/properties.py`.
2. **Fig 3 surface BC**: was calibrated constant 0.191 W/m² (wrong). Now uses real `shoemakerIllumination.mat` Q_total(t) (mean 0.141 W/m²).
3. **Figs 4 & 5 surface BC**: was 44.4 K from Diviner GCP Tbol (different product). Now uses daveTemp mean 34.2 K from the same `.mat` file (same reference as the upstream paper).
4. **Vasavada angle-dep albedo**: Fig 2 now uses A(i) = A0 + 0.06·i³ + 0.25·i⁸ baked into insolation (was flat 0.12). Dropped full-diurnal RMSE from 15 K to 9.2 K.
5. **Top-only spinup**: `PixelInputs.spinup_depth_m = 0.10 m` — convergence checked only in top 10 cm. Solver now converges in 10-42 lunations instead of never.

## Deferred / future work

- **Fig 5 2-D map**: requires per-pixel illumination (PSR pixels → `compute_horizon()` per pixel). 1-D proxy in `figs45_subsurface.py`.
- **CE-4/ChaSTE slope correction** (Phase 2B): 6° local slope at CE-4 to close the −34 K surface-T bias from Phase 1. Target notebook: `notebooks/phase2/02_craters.ipynb`.
