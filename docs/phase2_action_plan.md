# Phase 2 — action plan after reading the full Martinez & Siegler 2021 paper

> Last updated: 2026-05-11. Branch: `claude/cleanup-repo-organization-EcS3U`

## What the paper actually contains (11 figures)

| # | Subject | Replicated? | Script |
| --- | --- | --- | --- |
| 1 | K(T) at ρ=1300, 3 models (Woods-Robinson, Hayne, Vasavada top-layer) | ❌ | Trivial — 3-curve plot at fixed ρ |
| 2 | NU-LHT-2M lab data, scaled ρ=1100→1800 | ❌ | Needs Zhong et al. 2016 lab data |
| 3 | Hayne vs M&S K(T,ρ), 8 densities | ✅ | `global/fig1_K_vs_T.py` (mislabeled fig1, same plot) |
| 4 | 0° equator: 4-panel (T_s diurnal, T_z, ΔT_s, ΔT_z) | ✅ | `global/fig4_equator_reference.py` |
| 5 | Nighttime at 4 lats: 45°H, 70°H, 30°M, 60°M vs Diviner | ✅ | `global/fig5_multilat_diurnal.py` |
| 6 | T(z) gradients at same 4 lats | ✅ | `global/fig6_multilat_gradient.py` |
| 7 | T_mean vs latitude, highlands AND mare, with Apollo 15/17 | ✅ | `global/fig7_latitude_sweep.py` |
| 8 | Crater min/max T, D=5,8,16, 75°-89.9° | ✅ | `craters/fig89_crater_sweep.py` |
| 9 | Crater ΔT subsurface, D=5,8,16, at 1m and 2m | ✅ | `craters/fig89_crater_sweep.py` |
| 10 | Shoemaker T_s vs Diviner ch9 | ✅ | `psr_shoemaker/fig3_diurnal.py` |
| 11 | Shoemaker T(z) | ✅ | `psr_shoemaker/figs45_subsurface.py` |

**Score: 9 of 11 fully replicated.** Remaining: paper-Fig 1 (3-model
K(T) overlay at fixed ρ=1300; trivial extension of `fig1_K_vs_T.py`) and
paper-Fig 2 (Zhong 2016 NU-LHT lab data — needs external download).

---

## Priority list — what to build next, in order

### Tier 1: high-leverage, no new data needed — ✅ ALL BUILT (2026-05-11)

1. ✅ **Fig 7 — latitude sweep** → `scripts/phase2/global/fig7_latitude_sweep.py`
   - 0-80° in 5° steps, both K models, highlands + mare
   - Apollo 15/17 HFE markers overlaid; ProcessPoolExecutor parallelism
   - Run: `python3 scripts/phase2/global/fig7_latitude_sweep.py`

2. ✅ **Figs 8 & 9 — crater sweep** → `scripts/phase2/craters/fig89_crater_sweep.py`
   - D = 5, 8, 16; lat 75°-89.9° in 1° steps
   - Uses `crater_floor_insolation()` from `lunar/illumination.py`
   - Run: `python3 scripts/phase2/craters/fig89_crater_sweep.py`

3. ✅ **Fig 4 — 0° equator reference** → `scripts/phase2/global/fig4_equator_reference.py`
   - 4-panel: T_s diurnal, T(z) noon/midnight, ΔT_s(LT), ΔT(z)
   - Run: `python3 scripts/phase2/global/fig4_equator_reference.py`

4. ✅ **Figs 5 + 6 — multi-latitude** → split into two scripts
   - `scripts/phase2/global/fig5_multilat_diurnal.py` — nighttime T_s at 4 sites
   - `scripts/phase2/global/fig6_multilat_gradient.py` — midnight T(z) at same sites
   - Diviner T7 overlay per panel; graceful fallback when a band isn't on disk

### Tier 2: needs data downloads (you do these)

1. **LOLA 1064-nm normal albedo map** (Lucey et al. 2014). Used in
   M&S Eq. 4 (Bond albedo with angular dependence). Currently we use a
   constant per-region (mare = 0.07, highlands = 0.12).
   - Source: PDS Geosciences Node, search "LOLA albedo".
   - Needed for: Fig 7 to vary albedo per pixel rather than per region.
   - Optional for Tier 1 #1 — using constants is fine for the headline.

2. **Zhong et al. 2016 NU-LHT-2M lab data**. K(T) measurements from 15-205 K
   that the M&S fit is built on.
   - Source: Zhong et al. 2016 *Icarus* 255, 50-58 (paywalled, but check
     if supplementary data is on Mendeley / Zenodo).
   - Needed for: Fig 2 (just a data-overlay plot).
   - Optional — Fig 2 is the least scientifically important of the 11.

3. **LOLA south-polar DEM** (PGDA Product 90). Already automated:
   `python3 scripts/phase2/global/download_lola_dem.py` (80MPP, 225 MB).
   - Needed for: south-polar DEM map demo, future per-pixel illumination,
     PSR catalog.
   - Run this whenever you want the DEM map.

### Tier 3: new physics (multi-day, post-tier-1)

1. **Per-pixel illumination map for the south pole.** Use the existing
   `lunar/illumination.py` `compute_horizon()` to generate
   shoemakerIllumination.mat-equivalents for every pixel in the LOLA DEM
   tile.
   - Required for: M&S Fig 9 reconstruction as a true 2-D map (currently
     1-D proxy in our Fig 5).
   - Required for: any global thermal map at high latitudes.
   - Effort: ~2-3 days. Need to validate against the upstream
     `shoemakerIllumination.mat` time series at the Shoemaker tile (sanity
     check: our compute_horizon-derived Q_total should match upstream
     within ~10 %).

2. **2-D global model: lat × lon T_mean(z) maps.**
   - Build a coarse lat-lon grid (e.g., 1° x 1°), run thermal solver per
     pixel, store T(z) profiles, render as Mercator + polar-stereographic.
   - Cold-trap stability map: count pixels with T(z=4m) < 110 K (water-ice
     stability threshold).
   - Effort: ~1 week. The big tasks are (a) parallelizing the solver over
     pixels, (b) integrating LOLA albedo + slope + horizon into the
     per-pixel BC, (c) rendering at thesis-publication quality.

---

## What's needed *from you* now

1. **Run the Tier-1 sweeps on your Mac.** All scripts exist and are
   parallelised with ProcessPoolExecutor. Wall-clock estimates:
   - `python3 scripts/phase2/global/fig7_latitude_sweep.py` — ~22 min on
     M-series Mac (17 lats × 2 K × 2 terrains, 68 calls, pool size = CPU).
   - `python3 scripts/phase2/craters/fig89_crater_sweep.py` — ~1-3 h.
   - `python3 scripts/phase2/global/fig4_equator_reference.py` — ~3 min.
   - `python3 scripts/phase2/global/fig5_multilat_diurnal.py` — ~10 min.
   - `python3 scripts/phase2/global/fig6_multilat_gradient.py` — ~10 min.

2. **(Optional) Download missing Diviner bands** for the multi-latitude
   reference overlays. `python3 scripts/download_diviner_gcp.py --all-bands`.
   Scripts gracefully skip any band not on disk.

3. **Decide on the global model scope (Tier 3).** Three options:
   - **A. Flat-terrain only** — solver per pixel, no horizon/shadow. Fast
     (~hours), captures M&S K-model effect at all latitudes. Misses PSRs.
   - **B. Flat-terrain + Shoemaker-style PSR overrides.** Use the upstream
     `.mat` for Shoemaker; flat-terrain for everywhere else. Compromise.
   - **C. Full per-pixel illumination** with `compute_horizon()`. Closest
     to the paper's Fig 9 but ~1-2 weeks of work + downloads.

4. **(Optional) Tell me which target journal.** If GRL/JGR Planets, the
   figures need polish (axis labels, font sizes, legend placement, units)
   already substantially done with `phase2_plotting.py`.

---

## Session log

**2026-05-11 (Tier-1 completion):**
- Built fig4_equator_reference.py, fig5_multilat_diurnal.py,
  fig6_multilat_gradient.py, fig7_latitude_sweep.py (with multiprocessing),
  and fig89_crater_sweep.py.
- Fixed `_REPO_ROOT = parents[2]` bug → `parents[3]` in all phase2 scripts
  (previously caused silent writes to `scripts/output/figures/`).
- Updated fig3 to use real upstream shoemakerIllumination.mat (697-day run).
- Merged 01_global/02_craters/03_psr_shoemaker into one phase2.ipynb with
  all outputs embedded.
- All `python` invocations in docs/scripts switched to `python3` for Mac
  (zsh) compatibility.

**2026-05-10 (foundation):**
- Read full M&S 2021 JGR paper.
- Built `lunar/phase2_plotting.py` (unified style + `legend_below()`).
- Re-styled the 5 existing scripts (Figs 1, 2, 3, 4, 5).
- Added `crater_floor_insolation()` and `load_shoemaker_illumination()`
  to `lunar/illumination.py`.
- Added `download_lola_dem.py` and `fig_southpolar_dem_map.py`.

## Status summary

**Complete:** 9 of 11 paper figures replicated.
**Remaining:** paper-Fig 1 (3-K-model overlay at fixed ρ=1300; trivial)
and paper-Fig 2 (Zhong 2016 NU-LHT lab data, needs external download).
**Blocking on you:** run the Tier-1 sweeps; Tier-3 scope decision.
