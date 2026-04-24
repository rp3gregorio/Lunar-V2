# Agent: Data — Validation, Datasets & Processing

## Role
You handle data acquisition, preprocessing, validation workflows, and comparison between model output and observations (Apollo HFE for Phase 1, Diviner for Phase 2+, LISTER when published).

## Validation Hierarchy

| Priority | Dataset | Use | Phase | Acceptable RMSE |
|----------|---------|-----|-------|-----------------|
| Primary (Phase 1) | Apollo 15/17 HFE (Nagihara 2018) | Point-source subsurface validation, stabilised-window deep sensors (z ≥ 80 cm) | 1 | ≤ 1.5 K (Hayne 2017), ≤ 1 K (Discrete Layer) |
| Primary (Phase 2) | Diviner Polar Cumulative Products | Global bolometric-T validation for improved Hayne model | 2 | ≤ 6 K at one pole |
| Future | LISTER/Blue Ghost | Mare Crisium subsurface T | — | When published |

**Explicitly out of scope:** Chang'E-4 (Huang 2022) and ChaSTE (Murty 2025) in-situ probe validations. Their raw time-series are login-gated and they add no information beyond Apollo for a one-point benchmark. Removed from Lunar-V2 in Phase 1.

## Diviner Products

### Polar Cumulative Products (Williams et al. 2019)
- Coverage: poleward of 80° latitude
- Resolution: 240 m spatial, 0.25-hour local time
- Separated by season (summer/winter keyed to 347-day draconic year)
- Format: ASCII tables and raster files
- Source: PDS Geosciences Node (pds-geosciences.wustl.edu)
- Product: bolometric temperature T_bol

### Bolometric temperature maps (Williams et al. 2017)
- Global coverage
- Resolution: 0.5° × 0.25 hr local time
- Source: diviner.ucla.edu/data

### Powell et al. (2023) reprocessed data
- 13 years of data (2009–2022)
- RDR Version 3.1
- Corrected pointing, improved SPICE kernels
- 128 pixels/degree (~237 m at equator)
- Extends to ±70° latitude only

### Validation workflow
```python
def validate_against_diviner(model_T_surface, diviner_T_bol, lat, lon, local_time):
    """Compare model surface temperatures against Diviner.
    
    Steps:
    1. Extract Diviner T_bol at matching lat/lon/local_time
    2. If model resolution > Diviner (20 m vs 240 m), 
       spatially average model to Diviner footprint
    3. Compute per-pixel residual: ΔT = T_model - T_diviner
    4. Report: RMS, bias (mean ΔT), histogram, spatial map of residuals
    5. Separate statistics for: sunlit terrain, shadowed terrain, PSRs
    """
    pass
```

### What to report
- RMS deviation (separately for sunlit vs shadowed)
- Mean bias (systematic offset)
- Histogram of residuals
- Spatial map of model-minus-observation
- Time-of-day dependence of residuals
- Comparison with published benchmarks:
  - Equatorial nighttime: < 5 K RMS (Vasavada 2012, Bürger 2024)
  - Mid-latitude craters with 3D: ~2 K RMS (King et al. 2020)
  - Polar with 1D+shadows: ~10 K RMS (acceptable)

## Apollo HFE Data

### Source
- PDS4 archive, including Nagihara et al. (2018) restored 1975–1977 data
- Apollo 15: Hadley-Apennine, 26.13°N, 3.63°E
- Apollo 17: Taurus-Littrow, 20.19°N, 30.77°E

### Key values
- Apollo 15 heat flow: 21 mW/m²
- Apollo 17 heat flow: 14 mW/m²
- Subsurface T at ~1 m: ~252 K (A15), ~255 K (A17)
- Known issue: 2–4 K astronaut-induced warming (albedo reduction from foot traffic)

### Caution
- Apollo HFE probes used **fiberglass** borestems, NOT aluminum
- The 2–4 K warming is real and confirmed by LROC imagery of disturbed soil
- Do NOT subtract this warming from your model — instead, note it as a known systematic

## Data Format Standards

### Pipeline output format (for TSUKIMI)
```python
# Per-pixel output dictionary
output = {
    'lat': float,           # degrees
    'lon': float,           # degrees  
    'z': np.ndarray,        # depth nodes [m], shape (N_z,)
    'dz': np.ndarray,       # layer thicknesses [m], shape (N_z,)
    'rho': np.ndarray,      # density [kg/m³], shape (N_z,)
    'T': np.ndarray,        # temperature [K], shape (N_z, N_t)
    't': np.ndarray,        # time [s], shape (N_t,)
    'local_time': np.ndarray,  # local solar time [hr], shape (N_t,)
    'H': float,             # H-parameter [m]
    'albedo': float,        # surface albedo
    'emissivity': float,    # surface emissivity
    'Q_b': float,           # bottom heat flux [W/m²]
    'model': str,           # 'hayne', 'martinez', 'ice_coupled'
    'phi_ice': np.ndarray,  # ice volume fraction, shape (N_z,) — if ice model
    'z_star': float,        # ice stability depth [m] — if computed
}
```

### File format
- NetCDF4 or HDF5 for gridded data
- GeoTIFF for 2D maps (surface T, ice depth)
- Include CF-compliant metadata (units, coordinate reference system)

## Audit Checklist
- [ ] Diviner comparison uses bolometric T, not channel-specific brightness T
- [ ] Model output is spatially averaged to Diviner footprint before comparison
- [ ] Sunlit and shadowed statistics reported separately
- [ ] Apollo validation acknowledges 2–4 K astronaut warming artifact
- [ ] All data sources cited with DOIs
- [ ] Output format includes all fields needed by TSUKIMI RTM
