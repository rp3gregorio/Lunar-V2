# Agent: Illumination — Shadow Modeling & Secondary Radiation

## Role
You handle DEM processing, horizon computation, solar geometry, direct illumination, and secondary illumination (scattered visible + thermal IR via view factors).

## DEM Data

### Primary product
- **LDEM_80S_20MPP_ADJ.TIF** — 20 m/pixel, 80–90°S, 2.6 GB
- Source: pgda.gsfc.nasa.gov/products/90 (Barker et al. 2023)
- Format: GeoTIFF, polar stereographic projection, elevation in meters
- Load with: `rasterio`, `rioxarray`, or GDAL

### Alternatives
- 10 m/pixel: LDEM_83S_10MPP_ADJ.TIF (4.8 GB, 83–90°S)
- 5 m/pixel: site-specific DEMs (16×16 km, 27 Artemis candidate sites)
- SLDEM2015: 60 m merged LOLA+Kaguya (±60° only — NOT for polar work)

### Preprocessing
```bash
# Extract study area subset
gdal_translate -projwin xmin ymax xmax ymin input.tif subset.tif

# Compute slope and aspect
gdaldem slope subset.tif slope.tif
gdaldem aspect subset.tif aspect.tif
```

## Horizon-Based Illumination

### Algorithm (Mazarico et al. 2011)
For each pixel (i, j):
1. Trace rays in N azimuthal directions (≥360, preferably 720)
2. Along each ray, compute elevation angle β = arctan(Δh / D)
3. Track maximum β → this is the horizon elevation in that direction
4. Store horizon profile: β_max(azimuth) for each pixel

### Nested grid approach (for efficiency at 20 m)
- 0–5 km: use 20 m DEM (full resolution)
- 5–50 km: use 80 m DEM (downsampled or separate file)
- 50–200 km: use 240 m DEM
- Critical at south pole where distant crater rims cast shadows >100 km

### Solar position
Use SPICE (via `spiceypy`) or JPL HORIZONS for proper:
- Lunar obliquity (1.54°)
- 18.6-year nodal precession cycle
- Sub-solar latitude variation (±1.54°)
- Hourly timesteps over at least one full lunation (29.53 days)
- For full seasonal coverage: simulate one draconic year (346.6 days)

### Illumination check per timestep
```python
def is_illuminated(solar_elev, solar_azimuth, horizon_profile, az_angles):
    """Check if pixel is directly illuminated.
    solar_elev: solar elevation angle [rad]
    solar_azimuth: solar azimuth [rad]
    horizon_profile: max elevation angles per azimuth [rad]
    """
    if solar_elev <= 0:
        return False
    idx = np.searchsorted(az_angles, solar_azimuth) % len(az_angles)
    return solar_elev > horizon_profile[idx]
```

## Secondary Illumination (View Factors)

### Physics
PSRs receive energy from two sources:
1. **Scattered visible**: sunlit walls reflect portion of solar flux into PSR
2. **Thermal IR**: warm sunlit walls emit thermal radiation into PSR

Both depend on view factors F_ij between pixel pairs.

### View factor between flat facets
```
F_ij = (cos θ_i · cos θ_j) / (π · r²_ij) · ΔA_j · V_ij
```
where θ_i, θ_j are angles from surface normals to line-of-sight, r_ij is distance, ΔA_j is facet area, V_ij is mutual visibility (0 or 1).

### Implementation strategy (phased)
**Phase 1**: Sparse view factors — only compute F_ij between PSR pixels (i) and sunlit pixels (j). With ~10% PSR area, this is ~100× smaller than the full N² matrix.

**Phase 2**: Distance cutoff at ~2–3 km (F drops as ~1/r², distant facets contribute negligibly).

**Phase 3** (optional): HODLR compression (Potter et al. 2023) for full radiosity if needed.

### Energy balance with scattering
```python
Q_scattered_vis = sum(F_ij * albedo_j * S * cos(theta_z_j) * is_sunlit_j)
Q_thermal_ir = sum(F_ij * emissivity_j * sigma * T_j**4)
Q_total = Q_direct + Q_scattered_vis + Q_thermal_ir
```

### Reference implementation
Schorghofer's Planetary-Code-Collection (github.com/nschorgh/Planetary-Code-Collection):
- `Topo3D/fieldofview.f90` — view factor computation
- `Topo3D/shadows.f90` — shadow casting
- `Topo3D/topo3d_module.f90` — main driver

## Computational Estimates (20 m, 10×10 km patch)
- Pixels: 500 × 500 = 250,000
- Horizon profiles (720 azimuths): ~700 MB
- Sparse view-factor matrix (PSR-to-sunlit): ~800 MB
- Time per pixel (horizon): ~0.1 s with Numba → ~7 hours total (parallelizable)
- Time per pixel (thermal solver, 10 lunations): ~10–100 s → significant, use Fourier method or limit spin-up

## Audit Checklist
- [ ] DEM is 20 m south pole, not SLDEM2015 (which stops at ±60°)
- [ ] Azimuths ≥ 360 (preferably 720)
- [ ] Nested grid for far-field horizons
- [ ] SPICE ephemeris, not simplified analytical solar geometry
- [ ] Secondary illumination includes BOTH scattered visible AND thermal IR
- [ ] View factors obey reciprocity: A_i · F_ij = A_j · F_ji
- [ ] Total view factor from any pixel ≤ 1 (energy conservation)
