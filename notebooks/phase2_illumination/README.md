# Phase 2 — Topographic Illumination

Add real topography to the forward model: DEM → slope + azimuth + horizon
profile per pixel → shadow-corrected insolation → tilted-surface solver.

| Notebook | Status |
|---|---|
| `04_illumination_shadows.ipynb` | ✅ Horizon tracer + LOLA DEM demo (synthetic crater validated). |

## Planned additions (feed into thesis Chapter 3)

* `05_ce4_chaste_slope_validation.ipynb` — re-run the ChaSTE 69 °S cell
  with the 6° local slope from Seth 2025 to close the −34 K bias seen
  in Phase 1 §10.
* Diviner-calibrated shadow masks at one polar latitude before extending
  to the full pole in Phase 3.

## Success criterion

ChaSTE surface T_peak residual drops from ~ −35 K (flat) to ≲ ±5 K once
the 6° slope is applied, matching the Murty 2025 / Seth 2025 reconciliation.
