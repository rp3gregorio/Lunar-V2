# Phase 2 — Improved Hayne 2017 Global Model

Phase 1 validated the unmodified Hayne 2017 forward solver (as shipped
in `third_party/heat1d/`) at the Apollo 15 and 17 sites. Phase 2 takes
that solver and lifts it to a *global* model that is quantitatively
better than the published Hayne 2017 pipeline. All improvements land
in a single merged model so the thesis has **one** forward operator to
report, not a tower of separate corrections.

## Planned notebooks

| Notebook | Status | Purpose |
|---|---|---|
| `04_illumination_shadows.ipynb` | ✅ scaffolding | Horizon tracer + LOLA DEM demo (synthetic crater validated). Kept from prior scope; now Phase-2 entry point. |
| `05_hayne_global_ingredients.ipynb` | ⏳ planned | Add appendix-only products that never made it into `phayne/heat1d`: latitude-dependent H-parameter (Hayne 2017 §5.2 / Eq A.9), rock-abundance anisothermal mixture (Bandfield et al. 2011), and wavelength-dependent bolometric emissivity. |
| `06_martinez_cold_regions.ipynb` | ⏳ planned | Swap in the Martinez & Siegler (2021) density-dependent conductivity for the PSR/cold-region regime where the Hayne K(T,z) form breaks down below ~80 K. Cross-validates against Siegler 2015 polar PSR Diviner brightness temperatures. |
| `07_burger_microphysics.ipynb` | ⏳ planned | Bürger et al. (2024, *JGR Planets*) microphysical thermal model — add the latitudinal dependence of the radiative contact-conductivity coupling. Tests whether the global H-parameter map collapses into the Burger microphysical parameters. |
| `08_diviner_global_validation.ipynb` | ⏳ planned | Global bolometric-T map, coarse polar-stereographic first, compared against Diviner PCP products. Closes the loop that Hayne 2017 §6 opened. |

## What "improved" means, concretely

| Hayne 2017 as-published (and as in `phayne/heat1d`) | Phase 2 upgrade |
|---|---|
| Scalar H = 0.07 m | H(φ) from Eq A.9 (pyshtools polynomial fit) |
| No rock abundance | Bandfield 2011 anisothermal two-component T-field |
| A(i) polynomial (Keihm 1984) | unchanged — already in Hayne's GitHub |
| ε = 0.95 scalar | Wavelength-dependent spectral ε → bolometric |
| K(T,z) = Kc(z)·[1 + χ(T/350)³] | Martinez-Siegler form below ~80 K, Hayne above |
| — | Burger microphysical radiative coupling scaling |
| No shadowing | LOLA DEM + horizon tracer + sky-view factor |

## Data dependencies

* `boot.ensure_lola_dem_80mpp()` — 80 m/pixel polar DEM (auto-download).
* `boot.ensure_diviner_pcp()` — PDS bulk-fetcher for Diviner Polar
  Cumulative Products (staged dormant in Phase 1; turned on here).
* Hayne 2017 supplementary global H-parameter map — for validation
  overlay, pulled from the paper's supporting-info section.

## Success criterion

Global bolometric-T residual (model − Diviner PCP) RMS ≤ 6 K at one
pole over a polar-stereographic coarse grid (goal: beat the published
Hayne 2017 ~8 K envelope by incorporating the Martinez-Siegler and
Burger improvements plus DEM shadowing).
