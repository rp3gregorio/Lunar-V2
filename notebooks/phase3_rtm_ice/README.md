# Phase 3 — RTM Coupling, Jacobian, Ice-Stability Index (planned)

With the improved global Hayne model locked (Phase 2), couple the
surface-T field to a radiative transfer model, derive a forward-operator
Jacobian suitable for TSUKIMI retrieval, and produce a mission-ready
ice-stability index map.

## Planned notebooks

| Notebook | Purpose |
|---|---|
| `09_rtm_coupling.ipynb` | Forward-couple T(z) to a two-stream regolith radiative-transfer model → emerging brightness-T spectra at Diviner / LRO bands and at TSUKIMI's thermal band. |
| `10_jacobian_forward.ipynb` | Finite-difference Jacobian of emerging brightness-T w.r.t. (H-parameter, rock abundance, surface density, volumetric ice fraction). Cross-check against adjoint-state estimate. |
| `11_ice_stability_index.ipynb` | H2O / CO2 ice stability depth maps (Schorghofer 2008 criterion) with uncertainty bars propagated from Phase 2 residuals. |

## Data dependencies

* Diviner spectral-channel tables (L1b, per-channel — beyond PCP).
* LOLA rock-abundance map (Bandfield et al. 2011).

## Success criterion

Jacobian condition number ≤ 1e4 for the TSUKIMI retrieval state vector
on the polar-stereographic grid. Ice-stability map agrees with
Schorghofer 2008 published extents at the 90% level.
