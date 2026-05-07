# Phase 2 — Martinez & Siegler (2021) Replication Plan

> **Status:** Scaffold drafted from MATLAB code release + LPSC 2022 abstract.
> Full JGR paper text not yet read (paywalled at AGU); a few quantitative
> targets are still tagged `NEEDS PAPER` below.
> **Branch:** `claude/cleanup-repo-organization-EcS3U`
> **Last updated:** 2026-05-07

This document is the work-of-record for replicating Martinez & Siegler
(2021), *A Global Thermal Conductivity Model for Lunar Regolith at Low
Temperatures*, JGR Planets 126, e2021JE006829.

## 1. Source provenance

| Source | Use | Location |
| --- | --- | --- |
| MATLAB code release (Zenodo `10.5281/zenodo.12586656`, GitHub `angelicam01/lunar1Dheat` v1.6) | Ground truth for equations, numerics, BC | `.scratch/lunar1Dheat/` (untracked) |
| LPSC 2022 abstract `#2754` (USRA, public) | Equation form, published constants, figure list, validation sites | `paper/refs/martinez_siegler_lpsc2022.pdf` |
| JGR Planets 126, e2021JE006829 | RMSE values, full latitude list, supplementary tables | **NOT YET OBTAINED** — paywalled |
| Phase 1 `lunar/properties.py:158-205`, `lunar/constants.py:147-162` | Existing Python implementation of K(T,ρ) | repo |

## 2. Model

### 2.1 Effective conductivity

Per the LPSC abstract Eq. (3) and `1DFunctions/updateRK.m`:

```
K_eff(T, ρ) = (A1·ρ - A2)·k_am(T) + (B1·ρ - B2)·T³        (Eq. 3)
```

with `k_am(T)` = the Woods-Robinson et al. (2019, JGR) Eq. 30 amorphous-solid
nine-term polynomial in `T^-4 ... T^4`. The first term is solid-conduction
(temperature-and-density dependent through the amorphous endmember); the
second term is radiative.

Sign convention note: the MATLAB code factors signs into the constants
(`A2 = -0.0051`, `B2 = -1.953e-10`) and writes `(A1·ρ + A2)·k_am + (B1·ρ + B2)·T³`.
This is algebraically identical to the abstract's form with positive
constants and explicit subtraction.

### 2.2 Density-scaling constants

| Constant | LPSC 2022 abstract | `updateRK.m` | Phase 1 `constants.py:147-162` | Decision |
| --- | --- | --- | --- | --- |
| `A1` | 5.0821e-6 | 5.0821e-6 | 5.0821e-6 | ✓ keep |
| `A2` | 5.1e-3 (sign: subtract) | -0.0051 | -0.0051 | ✓ keep (equivalent) |
| `B1` | **2.0022e-13** | **2.022e-13** | **2.022e-13** | ⚠ **escalate** — Phase 1 currently matches the code, NOT the published value. `derivk.m:4` uses `0.944·2.121e-13 ≈ 2.002e-13`, which is consistent with the published 2.0022e-13. The `updateRK.m` value is plausibly a typo (missing zero). Default: change Phase 1 to 2.0022e-13 after user confirmation. |
| `B2` | 1.953e-10 (sign: subtract) | -1.953e-10 | -1.953e-10 | ✓ keep (equivalent) |

### 2.3 Specific heat

Hayne (2017) Appendix A polynomial, unchanged from `1DFunctions/updateC.m`.
Phase 1 already has this in `lunar/properties.py` (verify).

### 2.4 Density profile

Hayne (2017) exponential, computed in `1DFunctions/makegrid.m:34-37`:

```
ρ(z) = ρ_d - (ρ_d - ρ_s)·exp(-z / H)
```

with `ρ_s = 1100`, `ρ_d = 1800` kg/m³.

### 2.5 H-parameter — site-dependent (NOT a single global value)

The LPSC abstract figures show H is fitted per site:

| Site | Standard model H | New (M&S) H |
| --- | --- | --- |
| 45° highlands (Fig 2) | 6.0 cm | 5.6 cm |
| Shoemaker PSR (Fig 4) | 6.9 cm | 5.6 cm |
| Global default in `heat1D.m` | — | 5.4 cm |

`NEEDS PAPER` to confirm the full per-latitude H table (Phase 1 currently
uses a single global H of 6 cm).

## 3. Numerics

From `Global/UpdatedModel/heat1D.m`:

| Parameter | Value | Phase 1 equivalent | Note |
| --- | --- | --- | --- |
| `dt` | 150 s | match | |
| `P` | 2.55024e6 s | match (synodic) | |
| `S` | 1361.0 W/m² | match | |
| `Q` (geothermal) | 0.018 W/m² (global) | site-specific (A15=21, A17=15 mW/m²) | M&S use a single value globally |
| `zmax` | 2.0 m | Phase 1 ~5 m | M&S shallower |
| `m`, `n` (grid params) | 20, 30 | geometric, ~80 layers | different parametrisation, both geometric |
| `ks` | 8.0e-4 W/m/K | 7.4e-4 (Hayne 2017) | M&S bumped up |
| `kd` | 3.8e-3 W/m/K | 3.4e-3 (Hayne 2017) | M&S bumped up |
| `ε` | 0.95 | match | |
| `σ` | 5.67051196e-8 | 5.6704e-8 | both pre-2018 CODATA |
| Spin-up tol | 1e-6 K | 0.01 K (CLAUDE.md) | M&S tighter by 4 orders of magnitude |

**Solver**: forward Euler explicit on a geometric grid; surface BC via
Newton iteration in `1DFunctions/Tsurface.m` (radiative balance with
T-dependent K); bottom BC `T_N = T_{N-1} + Q·dz_N/K_{N-1}` (geothermal flux,
identical to Phase 1's known-bug-fix form).

Phase 1 uses Crank-Nicolson, which is implicit and unconditionally stable —
this is *better*, not a bug, but means our Phase 2 results may differ from
M&S by O(numerical-scheme). Document but keep CN.

## 4. Insolation and albedo

### 4.1 Flat-surface insolation

`1DFunctions/insolationFeng2.m` — pure analytic flat-surface, no DEM, no
horizon, no slope. The model is fundamentally 1-D / flat for the global
case.

### 4.2 Albedo (Feng 2020 form)

```
albedo(θ) = A0 + (1 - cos(θ)^0.2752)
```

with `A0 = 0.12` highlands, `A0 = 0.07` mare. Note this is the Feng (2020)
form, not the Vasavada/Keihm form Phase 1 uses for Apollo. We must add
this as a switchable albedo model in `lunar/properties.py` or a new
`lunar/insolation.py` module.

### 4.3 Topography — what about DEM/shadowing?

The Global model is **flat-surface, no DEM**. The PSR Shoemaker case (LPSC
Fig 3-5) uses `1DFunctions/insolationcrater.m`, a closed-form bowl-crater
illumination with a single diameter parameter — **not** a Mazarico-style
LOLA horizon trace. This means:

- The user's earlier expectation that M&S includes DEM/shadowing is
  **incorrect** for the global model.
- The PSR Shoemaker analysis is a special-case bowl-crater geometry, not
  full-DEM ray-tracing.
- Phase 2 replication therefore does **not** require the LOLA/Mazarico
  pipeline that the original Phase-2 roadmap envisaged. That work moves
  to Phase 3 (or stays optional in Phase 2 as a "beyond-paper" extension).

## 5. Validation dataset (Diviner)

| Item | Source |
| --- | --- |
| Product | Diviner **Global Cumulative Products (GCP)**, NASA PDS |
| PDS reference | Paige, D. (2020), NASA PDS — `[4]` in LPSC abstract |
| Spatial resolution | 2 pixels per degree (~15 km) |
| Local time resolution | 0.25 h (96 LT bins per diurnal cycle) |
| Channel for low/mid-lat surface T | **T7** (25-41 µm; high SNR, rock-insensitive) |
| Channel for PSR surface T | **Channel 9** (longer wavelength; sees ultra-cold PSRs) |
| Filtering | <1% rock abundance, <1° slope (Lucey 2014, Paige 2017 PDS) |
| Latitude bin width | ±0.25° (per `extractdiv.m`) |

`NEEDS PAPER`: full list of validation latitudes. From the LPSC abstract we
know the paper covers at least: 45°N highlands (Fig 2), 60° mare (text),
80° highlands (text), and Shoemaker PSR at 87.91°S, 45.51°E (Fig 3-5).
Likely also covers equatorial latitudes (0°, 30°) for completeness — but
this is inference, not confirmed.

## 6. Figures to reproduce

From the LPSC 2022 abstract (the JGR paper likely has more — `NEEDS PAPER`
to confirm full list):

| # | Description | Inputs | Output |
| --- | --- | --- | --- |
| 1 | K vs T for ρ ∈ {1100,...,1700} kg/m³, standard (Hayne) vs new (M&S), T ∈ [0, 400] K | analytical | `output/figures/phase2_fig1_K_vs_T_multi_rho.pdf` |
| 2 | 45° highlands nighttime curve (LT 16:00-08:00), standard vs new vs Diviner T7 (45 ± 25° band), with H values labelled | thermal solver + Diviner GCP | `output/figures/phase2_fig2_45N_nighttime.pdf` |
| 3 | Shoemaker PSR (87.91°S, 45.51°E) surface T time series vs Diviner channel 9 | thermal solver + Diviner GCP ch9 | `output/figures/phase2_fig3_shoemaker_surface.pdf` |
| 4 | Shoemaker PSR T(z) profile, standard vs new model, depth -2 to 0 m | thermal solver | `output/figures/phase2_fig4_shoemaker_profile.pdf` |
| 5 | Shoemaker crater 4 m depth ΔT map (new − standard) | tile solver | `output/figures/phase2_fig5_shoemaker_4m_dT_map.pdf` |

**Quantitative targets from the abstract**:
- Global low-latitude diurnal: similar surface T to standard, slightly
  cooler at night.
- 60° mare: ~6 K warmer subsurface mean.
- 80° highlands: ~8 K warmer subsurface mean.
- Shoemaker PSR 4 m depth: up to **+30 K** vs standard (the headline result).
- Subsurface T at 2 m: up to **+15 K** in PSRs.

`NEEDS PAPER`: per-figure RMSE/bias values.

## 7. Implementation plan (sequenced)

1. **Diviner bootstrap script** — `scripts/download_diviner_gcp.py`
   - Targets PDS GCP files for T7 and ch9.
   - Caches to `data/diviner/gcp/` (gitignored).
   - Validation subset: latitude bands {0°, 30°, 45°, 60°, 80°} (each
     highlands + mare) plus a Shoemaker tile (~70 km × 50 km centred at
     87.91°S, 45.51°E).
   - Disk estimate: ≤ 5 GB. **Awaits user sign-off.**

2. **Insolation refactor** — extend `lunar/illumination.py` (or add a
   small module) with a `feng_albedo()` and `flat_insolation()` function
   so the Phase-2 driver can pick the M&S albedo model without disturbing
   Phase 1's Apollo runs.

3. **Driver script** — `lunar/martinez_driver.py` providing `run_site(latitude, surface, channel)`
   that wires Phase 1's Crank-Nicolson solver + M&S K(T,ρ) + Feng albedo +
   bottom geothermal flux of 18 mW/m². Returns T(z, t).

4. **Notebook** — `notebooks/phase2_martinez/01_martinez_replication.ipynb`
   walking from K(T) plot → 45° highlands → 60° mare → 80° highlands →
   Shoemaker PSR. Each section produces one of the five figures above.

5. **Tests** — `tests/test_martinez_phase2.py` checking K(T=100 K, ρ=1500
   kg/m³) against a hand-computed value; checking diurnal symmetry on a
   no-albedo synthetic case; smoke-testing the driver.

6. **Phase-1 letter wiring** — add a "Continuity to Phase 2" bullet in the
   letter's discussion section pointing at the new figures.

## 8. Open questions / `NEEDS PAPER` items

1. The B1 typo: paper value `2.0022e-13` vs code `2.022e-13`. **Decision needed before changing Phase 1 constants.**
2. Full list of validation latitudes (LPSC mentions 45°, 60°, 80° + PSR; paper presumably has more).
3. Per-latitude H values (LPSC shows 5.6 cm at 45°N highlands and Shoemaker; paper presumably tabulates more).
4. Quantitative RMSE/bias for each figure.
5. Time range of Diviner data used (full mission? subset?).
6. Whether the paper uses Diviner channel 8 anywhere (the abstract only mentions T7 and ch9).
7. Whether `kd = 3.8e-3` and `ks = 8.0e-4` are paper-justified or only in the code.

## 9. Connection to Phase 1

- Phase 1's `lunar/properties.py:158-205` already implements Eq. (3) — no
  re-implementation needed once the B1 question is settled.
- Phase 2 driver inherits Phase 1's solver, geometric grid, and bottom-BC
  geothermal-flux fix (all known-bug-fix-clean).
- Phase 1's Apollo 15/17 validation continues to use Hayne (2017)
  thermophysics for backwards compatibility with the published letter.
  Phase 2 adds Diviner-driven flat-site validation as an independent
  check.
- New continuity bullet to add in `paper/letter/letter.tex`: "The
  conductivity model used in this letter (Hayne 2017 χ-T³) is extended
  in companion Phase-2 work to the Martinez & Siegler (2021) low-T form;
  see `notebooks/phase2_martinez/`."

---

This plan replaces the prior "Phase 2 = DEM/illumination" roadmap. The
DEM/Mazarico/view-factor work moves to Phase 3.
