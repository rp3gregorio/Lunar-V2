# Phase 2 — action plan after reading the full Martinez & Siegler 2021 paper

> Last updated: 2026-05-10. Branch: `claude/cleanup-repo-organization-EcS3U`

## What the paper actually contains (11 figures)

| # | Subject | Replicated? | Comment |
| --- | --- | --- | --- |
| 1 | K(T) at ρ=1300, 3 models (Woods-Robinson, Hayne, Vasavada top-layer) | ❌ | Trivial to add — just plot 3 curves |
| 2 | NU-LHT-2M lab data, scaled ρ=1100→1800 | ❌ | Need Zhong et al. 2016 lab data |
| 3 | Hayne vs M&S K(T,ρ), 8 densities | ✅ | Built (mislabeled as "fig1" — same plot) |
| 4 | 0° equator: 4-panel (T_s diurnal, T_z, ΔT_s, ΔT_z) | ❌ | Easy: re-run solver at 0° |
| 5 | Nighttime at 4 lats: 45°H, 70°H, 30°M, 60°M vs Diviner | ⚠️ 1 of 4 | Have 45°H; need 70°H, 30°M, 60°M |
| 6 | T(z) gradients at same 4 lats | ❌ | Drops out of Fig 5 runs |
| 7 | T_mean vs latitude, highlands AND mare, with Apollo 15/17 | ❌ | **Headline figure** — need lat sweep |
| 8 | Crater min/max T, D=5,8,16, 75°-89.9° | ❌ | Use `crater_floor_insolation()` already in `lunar/illumination.py` |
| 9 | Crater ΔT subsurface, D=5,8,16, at 1m and 2m | ❌ | Same sweep as Fig 8 |
| 10 | Shoemaker T_s vs Diviner ch9 | ✅ | Built |
| 11 | Shoemaker T(z) | ✅ | Built |

**Score: 3 of 11 fully replicated, 1 partial.**

---

## Priority list — what to build next, in order

### Tier 1: high-leverage, no new data needed (this week)

1. **Fig 7 — latitude sweep (the global punchline)**.
   Loop solver over latitude 0° → 80° in 5° steps, both K models, both
   highlands and mare. Plot mean surface T and mean T at z=1m vs latitude,
   with Apollo 15/17 markers.
   - Runtime: ~15 min/latitude × 16 lats × 2 K models = ~8 hours.
     Easy to parallelize: 1 hr on a quad-core if we use multiprocessing.
   - Implementation: new script `scripts/phase2/global/fig7_latitude_sweep.py`.
   - Required data: only Diviner GCP (already downloaded) + LOLA 1064-nm
     albedo map (see Tier 2 #1 below — for now use the per-latitude default
     from the paper: 0.07 mare, 0.12 highlands).

2. **Figs 8 & 9 — crater sweep**. Loop over D=5, 8, 16 and lat 75-89.9°
   in 1° steps. Use `crater_floor_insolation()` (already ported).
   - Runtime: ~10 min/case × 3 D × 16 lats × 2 K models = ~16 hr.
     Use coarser timestepping for shadowed cases — the input doesn't
     change minute-to-minute. Realistic: 2-3 hours.
   - Implementation: new script `scripts/phase2/craters/fig89_crater_sweep.py`.

3. **Fig 4 — 0° equator reference**. The cleanest sanity check that
   our two K models reproduce the published agreement at low latitude.
   - Runtime: ~3 min total (just one location, one K-model pair).
   - Implementation: new script `scripts/phase2/global/fig4_equator_reference.py`.

4. **Fig 5 four-panel + Fig 6 gradients**. Run Fig 2's pipeline at the
   four published latitudes and stack into a 2×2 panel. Fig 6 falls out
   of the same converged solver runs.
   - Runtime: 4× Fig 2 ~= 12 min total.
   - Implementation: extend existing `fig2_diurnal_45N.py` into
     `fig5_multilat_diurnal.py` + `fig6_multilat_gradient.py`.

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
   `python scripts/phase2/global/download_lola_dem.py` (80MPP, 225 MB).
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

## What's needed *from you* before tier-1 work can run

In rough order of urgency:

1. **Pick a runtime budget.** Tier 1 #1 (Fig 7) is the punchline but takes
   ~1-8 hours wall time even on a multi-core machine. Tell me how long you
   want to spend.

2. **Confirm whether the Diviner GCP data on your Mac is sufficient.**
   I have the polar 80-90 S band downloaded. Fig 7 needs the 0-90 N + S
   bands. Re-run `python scripts/download_diviner_gcp.py --all-bands` if
   you haven't.

3. **Decide on the global model scope.** Three options:
   - **A. Flat-terrain only** — solver per pixel, no horizon/shadow. Fast
     (~hours), captures M&S K-model effect at all latitudes. Misses PSRs.
   - **B. Flat-terrain + Shoemaker-style PSR overrides.** Use the upstream
     `.mat` for Shoemaker; flat-terrain for everywhere else. Compromise.
   - **C. Full per-pixel illumination** with `compute_horizon()`. Closest
     to the paper's Fig 9 but ~1-2 weeks of work + downloads.

4. **(Optional) Tell me which target journal.** If GRL/JGR Planets, the
   figures need polish (axis labels, font sizes, legend placement, units)
   that's already partly done with the new `phase2_plotting.py` style; if
   thesis-only, less polish needed.

---

## What I'm doing in this session (already on the branch)

- ✅ Read the full M&S 2021 JGR paper.
- ✅ Built `lunar/phase2_plotting.py`: unified style + `legend_below()`
  helper that places legends in a separate box below the axes.
- ✅ Re-styled the 5 existing scripts (Figs 1, 2, 3, 4, 5) to use the new
  helper. Legend never overlaps data.
- ✅ Added `crater_floor_insolation()` and `load_shoemaker_illumination()`
  to `lunar/illumination.py` for Tier-1 work.
- ✅ Added `download_lola_dem.py` (80 / 40 / 20 MPP options) and
  `fig_southpolar_dem_map.py` for Tier-2 #3 / Tier-3 work.
- ✅ Wrote this action plan.

## Status summary

**Complete:** 3 of 11 paper figures + foundation work for the rest.
**Blocking on you:** scope decision (3.A/B/C above), runtime budget.
**Blocking on data:** Zhong 2016 lab data (non-critical), LOLA albedo
(non-critical for tier 1), full Diviner GCP set (run downloader).
