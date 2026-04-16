# Continuation Prompt for Lunar-V2

**Copy-paste this entire block into a new Claude session to continue the work.**

---

## Who I Am

I'm Ramon III Palinguba Gregorio, a graduate student at Kasai Laboratory, Institute of Science Tokyo. My thesis deadline is September 2026 and I'm targeting the Planetary Science Journal (PSJ) for publication.

## What This Repository Is

Lunar-V2 (`https://github.com/rp3gregorio/Lunar-V2`, branch `claude/thermal-lunar-profile-repo-ZF4Mm`) is a 20 m/pixel 1-D subsurface thermal modeling pipeline for the lunar south pole. It feeds into the TSUKIMI terahertz radiometer mission.

The pipeline does:
1. LOLA DEM ingestion → horizon ray-tracing (Mazarico 2011) → shadow-corrected insolation
2. 1-D Crank-Nicolson thermal solver per pixel with Numba JIT
3. T(z, t) profiles at ~55 geometric depth nodes from surface to 3 m
4. Ice stability depth mapping (Schorghofer & Taylor 2007)
5. Output format for TSUKIMI RTM coupling

**My novel contribution** is the ice-coupled thermal property feedback loop: ice presence changes K and c_p, which changes T(z), which changes where ice is stable. This positive feedback has not been published for the Moon.

## Current State of the Repository

### What's Complete and Working (57 tests pass)
- **`lunar/constants.py`** — All physical constants with citations (Hayne 2017, CODATA, Apollo HFE)
- **`lunar/grid.py`** — Geometric depth grid (uniform grids forbidden). Default: dz0=2 mm, growth=0.15, z_max=3 m
- **`lunar/properties.py`** — Three conductivity models (Hayne 2017, Martinez-Siegler 2021, ice-coupled) + two specific heat models (Hayne polynomial, Biele 2022 rational)
- **`lunar/solver.py`** — Crank-Nicolson + Thomas tridiagonal, radiative BC with Newton iteration, spin-up with convergence check (max dT < 0.01 K), T_surface tracking
- **`lunar/illumination.py`** — Mazarico ray-march horizon tracer (Numba parallel), bilinear DEM sampling, load_lola_dem via rasterio, is_illuminated binary check
- **`lunar/ephem.py`** — SPICE solar ephemeris (MOON_ME frame, DE440), lazy kernel loading, solar elevation/azimuth/insolation
- **`lunar/validation.py`** — Apollo HFE loader (multi-format), Diviner PCP loader
- **`lunar/ice_stability.py`** — Murphy & Koop (2005) saturation vapor pressure, Hertz-Knudsen sublimation, z_star finder with log-linear interpolation, 2-D map helper
- **`lunar/plotting/`** — Publication-quality styling (PSJ/JGR/Icarus standards), animation utilities for GIFs
- **`lunar/_bootstrap.py`** — Auto-installs packages and downloads data when notebooks are opened

### What's Still a Scaffold (NotImplementedError)
- **`lunar/illumination.py::compute_view_factors`** — Sparse PSR-to-sunlit view-factor matrix. Reference: Schorghofer Planetary-Code-Collection `Topo3D/fieldofview.f90`. Needs reciprocity check (A_i·F_ij = A_j·F_ji) and energy conservation (sum_j F_ij <= 1).
- **`lunar/pipeline.py`** — Top-level orchestrator: DEM → horizon → solver (pixel-parallel) → ice_stability → NetCDF output. Wire after individual modules are validated.
- **`lunar/rtm_coupling.py`** — TSUKIMI NetCDF serializer. Schema is locked (`TsukimiPixelRecord` dataclass), but writer is blocked on final format confirmation with the TSUKIMI team.

### Notebooks (all self-installing, click Run All)
- `00_quickstart.ipynb` — Grid, properties, analytical wave validation, radiative pixel run, synthetic crater
- `01_apollo_validation.ipynb` — Apollo 15 HFE comparison, three K-models vs buried sensors
- `02_equatorial_diurnal.ipynb` — K-model intercomparison (Hayne/Martinez/ice-coupled), 80°S polar case, GIFs
- `03_spice_insolation.ipynb` — SPICE-driven pipeline at Apollo 15 site
- `04_illumination_shadows.ipynb` — Phase 2: synthetic crater horizon + shadow-corrected thermal run, real LOLA DEM section

### External Data (in `data/`, gitignored)
- `data/dem/LDEM_80S_80MPP_ADJ.TIF` — 80 m/pixel south polar DEM (180 MB, auto-downloaded)
- `data/spice/` — 6 NAIF kernels (46 MB, auto-downloaded)
- `data/apollo/` — Apollo 15/17 HFE probe timeseries + depth tables (auto-downloaded)
- `data/diviner/` — 2 Diviner PCP files (noon + midnight, 400 MB)
- ChaSTE (Chandrayaan-3) — login-gated at PRADAN, not available
- LCROSS — no machine-readable public table

## Scientific Rules (MUST enforce)

1. **Never fabricate numerical values.** Every constant must have a paper citation.
2. **Geometric depth grid only.** Uniform grids are forbidden.
3. **Bottom BC = geothermal flux** (Q_b), not zero-flux. Equatorial: 0.018 W/m², polar: 0.012 W/m².
4. **Spin-up >= 10 lunations** with max dT < 0.01 K convergence check.
5. **sigma = 5.6704e-8 W m^-2 K^-4** — verify every occurrence.
6. **K_d = 3.4e-3 W m^-1 K^-1** (Hayne 2017) — was wrong in old code.
7. **H-parameter = 0.06 m** (global mean from Hayne 2017).
8. **Ice conductivity: K_ice = 567/T** (Klinger 1980, crystalline Ih).
9. SI units internally. Convert only at I/O boundaries.
10. The discrete 3-layer model is RETIRED. It lives only as a comparison figure.

## Known Past Mistakes to Avoid
- Bottom BC bug: `T[N-1] = T[N-2]` is zero-flux, NOT geothermal. Correct: `T[N-1] = T[N-2] + Q_b*dz/K`.
- Apollo probe material: fiberglass borestems, NOT aluminum.
- Spin-up: 5 cycles is not enough for polar latitudes. Use >= 10.
- Hayne c_p polynomial: some sources give volumetric (rho*c_p), not specific (c_p). Ours is specific.

## Key Benchmarks
- Equatorial surface: peak ~390 K, minimum ~95 K (Hayne 2017)
- Apollo 15 subsurface at 1 m: ~252 K mean
- PSR surface: 30-100 K depending on geometry
- Ice stability threshold: 1 mm/Gyr loss rate (Schorghofer & Taylor 2007)
- Ice at 110 K: sublimation rate ~few mm/Gyr (marginal stability)

## What I Need Done Next (Priority Order)

### Priority 1 — Validate ice_stability against Diviner
- Take the spin-up T(z,t) output from notebook 02 (80°S case)
- Compute annual-mean T_mean(z) and feed into `ice_stability_depth()`
- Compare the predicted z_star against Hayne et al. (2021) Figure 3 micro cold trap depths
- Add this as a new section in notebook 02 or a new notebook 05_ice_stability.ipynb

### Priority 2 — View Factors (Phase 1 sparse)
- Implement `compute_view_factors()` in illumination.py
- Only PSR pixels as receivers (sparse), sunlit pixels as emitters
- Distance cutoff at 2-3 km (1/r^2 falloff makes farther terms negligible)
- Must pass reciprocity check: A_i * F_ij == A_j * F_ji
- Must pass energy conservation: sum_j F_ij <= 1
- Reference: Schorghofer Planetary-Code-Collection Topo3D/fieldofview.f90

### Priority 3 — Real DEM Pipeline
- Take the 80 MPP LOLA DEM, extract a ~10 km x 10 km patch near Shackleton crater
- Run horizon tracing on that patch
- Run the thermal solver pixel-by-pixel (with Numba parallelism or multiprocessing)
- Produce a spatial map of T_surface, T_mean(1m), and z_star
- Compare surface T against Diviner PCP at same local time

### Priority 4 — Ice-Coupled Feedback Loop
- This is my novel contribution:
  1. Start with dry-regolith T(z,t) from solver
  2. Compute z_star from `ice_stability_depth()`
  3. Set phi_ice > 0 for z > z_star (initial guess: 3% volume fraction)
  4. Recompute K and c_p using ice-coupled models
  5. Re-run solver with new properties
  6. Recompute z_star from new T(z,t)
  7. Iterate until z_star converges (tolerance 1 mm)
  8. Show this loop in a notebook with convergence plots

### Priority 5 — Pipeline Orchestrator
- Wire `pipeline.py::run_pipeline()` to connect all modules
- Accept a DEM path + config, iterate over all pixels, write NetCDF output
- The `TsukimiPixelRecord` schema in rtm_coupling.py is the output format

### Priority 6 — Paper Figures
- Target: PSJ single-column (3.35 in) and double-column (7.0 in) figures
- Figure 1: Regolith property comparison (3 K-models)
- Figure 2: Equatorial diurnal benchmark vs Hayne 2017
- Figure 3: Apollo 15 HFE validation
- Figure 4: South polar illumination + shadow map
- Figure 5: Ice stability depth map with/without ice-coupled feedback
- Figure 6: T(z) profiles at key PSR sites (Shackleton, Haworth, Faustini)
- Follow the layout rules in `.claude/skills/agents/plotting.md`

## Key References
- Hayne et al. (2017), JGR Planets 122, 2371-2400 — H-parameter model
- Martinez & Siegler (2021), JGR Planets 126, e2021JE006829 — low-T conductivity
- Biele (2022), Planet. Space Sci. 218, 105501 — rational c_p fit
- Woods-Robinson et al. (2019), PRB 100, 214108 — amorphous K polynomial
- Klinger (1980), Science 209, 271-272 — ice conductivity K=567/T
- Mazarico et al. (2011), Icarus 211, 1066-1081 — horizon tracer
- Murphy & Koop (2005), QJRMS 131, 1539-1565 — ice saturation pressure
- Schorghofer & Taylor (2007), JGR 112, E02010 — ice stability threshold
- Hayne et al. (2021), Nat. Astron. 5, 169-175 — micro cold traps
- Nagihara et al. (2018), Earth Space Sci. 5, 289-310 — Apollo HFE PDS
- Williams et al. (2019), JGR Planets 124, 2505-2521 — Diviner PCP
- Feng, Siegler & Hayne (2020), JGR Planets 125, e2019JE006130 — polar Q_b
- Barker et al. (2023), PGDA product 90 — LOLA DEMs

## How to Start a New Session

```
git clone https://github.com/rp3gregorio/Lunar-V2.git
cd Lunar-V2
git checkout claude/thermal-lunar-profile-repo-ZF4Mm
```

Read these files first:
1. `CLAUDE.md` — project rules
2. `MANUAL.md` — full API reference
3. `Lunar Files/LUNAR_THERMAL_SKILL.md` — domain expert instructions
4. This file (`CONTINUATION_PROMPT.md`)

Then run `pytest tests/ -v` to confirm everything passes, and open the relevant notebook to continue.
