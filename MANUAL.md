# Lunar-Clean v2 — User Manual

**Owner**: Ramon III Palinguba Gregorio  
**Lab**: Kasai Laboratory, Institute of Science Tokyo  
**Version**: 0.1.0 (April 2026)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Downloading external data](#3-downloading-external-data)
4. [Package structure](#4-package-structure)
5. [Quick start](#5-quick-start)
6. [Module reference](#6-module-reference)
7. [Notebooks guide](#7-notebooks-guide)
8. [Running the tests](#8-running-the-tests)
9. [Scientific rules](#9-scientific-rules)
10. [Troubleshooting](#10-troubleshooting)

---

## 1 Overview

Lunar-Clean v2 is a 20 m/pixel 1-D subsurface thermal modeling pipeline for
the lunar south pole. It is the computational backbone of the TSUKIMI mission
preparation work at Kasai Lab (Institute of Science Tokyo).

The pipeline does four things in sequence:

```
LOLA DEM  ──▶  Illumination  ──▶  Thermal solver  ──▶  TSUKIMI RTM input
(20–80 m/px)   horizon + shadow   T(z,t) per pixel    brightness temperature
```

Key distinguishing features:
- **Hayne (2017) H-parameter** density model with pore-space conductivity.
- **Martinez & Siegler (2021)** conductivity with amorphous-ice polynomial
  (Woods-Robinson 2019) — no uniform grids.
- **Biele (2022) rational** specific-heat fit (4-parameter, valid 10–400 K).
- **Klinger (1980)** ice conductivity `K_ice = 567/T`.
- **Geometric depth grid** (forbidden: uniform grid).
- **Crank-Nicolson + Thomas** tridiagonal sweep (Numba JIT).
- **Mazarico (2011) ray-march** horizon tracer with Numba parallel `prange`.
- **NAIF SPICE / DE440** solar ephemeris via `spiceypy`.
- **10-lunation spin-up** with `max ΔT < 0.01 K` convergence check.

---

## 2 Installation

### Prerequisites

- Python ≥ 3.10
- A C compiler for Numba (GCC or Clang)

### Install the package

```bash
# Clone the repository
git clone https://github.com/rp3gregorio/Lunar-V2.git
cd Lunar-V2

# Core pipeline (solver, properties, grid, constants)
pip install -e .

# Add DEM / rasterio support
pip install -e ".[geo]"

# Add SPICE ephemeris support
pip install -e ".[spice]"

# Developer tools (pytest, ruff, mypy)
pip install -e ".[dev]"

# Everything at once
pip install -e ".[geo,spice,plot,dev]"
```

### Verify the installation

```bash
python -c "import lunar; print('OK')"
pytest tests/ -x -q
```

All tests that do not require external data files should pass immediately.
Tests requiring LOLA DEMs, SPICE kernels, or Apollo HFE data are skipped
automatically when those files are absent.

---

## 3 Downloading external data

All external data lives under `data/`. **None of it is tracked in git.**
See `data/README.md` for the complete manifest and download URLs.

### Quick-download script (requires `curl`)

```bash
# --- LOLA DEMs (south polar, 80/40/20 m per pixel) ---
mkdir -p data/dem
cd data/dem
curl -LO https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF  # 180 MB
curl -LO https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_40MPP_ADJ.TIF  # 670 MB
curl -LO https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF  # 2.5 GB
cd ../..

# --- SPICE kernels ---
mkdir -p data/spice
cd data/spice
BASE="https://naif.jpl.nasa.gov/pub/naif/generic_kernels"
curl -LO "$BASE/lsk/naif0012.tls"
curl -LO "$BASE/pck/pck00011.tpc"
curl -LO "$BASE/pck/moon_pa_de440_200625.bpc"
curl -LO "$BASE/fk/satellites/moon_de440_250416.tf"
curl -LO "$BASE/fk/satellites/moon_assoc_me.tf"
curl -LO "$BASE/spk/planets/de440s.bsp"
cd ../..

# --- Apollo 15/17 HFE ---
mkdir -p data/apollo/a15 data/apollo/a17 data/apollo/depth
cd data/apollo
BASE="https://pds-geosciences.wustl.edu/lunar/urn-nasa-pds-a15_17_hfe_concatenated/data"
for m in a15 a17; do
  curl -sL "$BASE/clean/$m/" | grep -oE 'href="[^"]*\.tab"' \
    | sed 's/href="//;s/"$//' | while read p; do
      curl -sLo "$m/$(basename $p)" "https://pds-geosciences.wustl.edu$p"
    done
done
for f in a15p1 a15p2 a17p1 a17p2; do
  curl -sLo "depth/${f}_depth.tab" "$BASE/depth/${f}_depth.tab"
done
cd ../..

# --- Diviner PCP (2 sample files) ---
mkdir -p data/diviner
cd data/diviner
BASE="https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/ltim/pols"
curl -LO "$BASE/pcp_avg_tbol_pols_sum_ltim13_240.tab"
curl -LO "$BASE/pcp_avg_tbol_pols_sum_ltim01_240.tab"
cd ../..
```

### Datasets not yet publicly available

| Dataset | Status | What to do |
|---|---|---|
| ChaSTE (Chandrayaan-3) | Login-gated (PRADAN, ISRO) | Download from https://pradan.issdc.gov.in/ch3/ when public; place as `data/chaste/chaste_profile.csv` |
| LCROSS volatiles | No machine-readable table | Transcribe Colaprete et al. (2010) Table 1 as `data/lcross/volatiles.csv` |

---

## 4 Package structure

```
lunar/
├── __init__.py          re-exports the main public API
├── constants.py         all physical/mission constants (cite in docstrings)
├── grid.py              geometric depth grid (make_geometric_grid)
├── properties.py        regolith/ice thermal property models
├── solver.py            Crank-Nicolson 1-D solver (solve_pixel)
├── illumination.py      DEM loader, Mazarico horizon tracer
├── ephem.py             SPICE solar ephemeris helper
├── validation.py        Apollo HFE, Diviner PCP loaders
├── ice_stability.py     ice stability depth predictor
├── rtm_coupling.py      TSUKIMI RTM interface scaffold
└── plotting/            publication-quality figure utilities

notebooks/
├── 00_quickstart.ipynb           5-minute demo of all major features
├── 01_apollo_validation.ipynb    compare solver to Apollo 15 HFE data
├── 02_equatorial_diurnal.ipynb   reproduce Hayne 2017 390/95 K benchmark
└── 03_spice_insolation.ipynb     full SPICE-driven pipeline at a real point

tests/
├── test_constants.py
├── test_grid.py
├── test_properties.py
├── test_solver.py
├── test_solver_assembly.py
├── test_illumination.py
├── test_ephem.py
└── test_validation.py
```

---

## 5 Quick start

### 5.1 Run the solver at one pixel

```python
import numpy as np
from lunar.grid import make_geometric_grid
from lunar.properties import conductivity_hayne, density_hayne, specific_heat
from lunar.constants import Q_B_SOUTH_POLAR, EMISSIVITY_DEFAULT
from lunar.solver import PixelInputs, solve_pixel

# 1. Geometric depth grid
grid = make_geometric_grid(z_max=3.0, dz0=0.003, growth=1.08)

# 2. One lunar sidereal period, 1-hour time steps
T_LUNAR = 27.321661 * 86400.0   # s
dt      = 3600.0
t_s     = np.arange(0.0, T_LUNAR, dt)

# 3. Sinusoidal insolation proxy (replace with SPICE for real runs)
S0    = 1361.0
phase = 2.0 * np.pi * t_s / T_LUNAR
S     = S0 * np.maximum(0.0, np.cos(phase))

# 4. Solver inputs
inputs = PixelInputs(
    grid=grid,
    t=t_s,
    bc_mode='radiative',
    insolation=S,
    albedo=0.12,
    emissivity=EMISSIVITY_DEFAULT,
    Q_b=Q_B_SOUTH_POLAR,        # 0.012 W m^-2
    n_lunations_spinup=10,
    spinup_tol_K=0.01,
)

# 5. Run
out = solve_pixel(inputs)
print(f"Surface T: {out.T[0].min():.1f}–{out.T[0].max():.1f} K")
print(f"Converged: {out.converged} ({out.n_spinup_cycles} lunations)")
```

### 5.2 Load a LOLA DEM and trace horizons

```python
from lunar.illumination import load_lola_dem, compute_horizon, azimuth_bin_centers

# Load the fast 80 MPP product
dem = load_lola_dem('data/dem/LDEM_80S_80MPP_ADJ.TIF', subsample=4)
print(f"DEM shape: {dem.elevation.shape}, pixel: {dem.dx:.0f} m")

# Trace horizons (n_azimuth=360 recommended)
horizon = compute_horizon(dem, n_azimuth=360)
print(f"Horizon shape: {horizon.shape}")  # (H, W, 360)
```

### 5.3 Compute solar geometry with SPICE

```python
from lunar import ephem
import numpy as np
from datetime import datetime, timedelta

times = [(datetime(2024, 1, 1) + timedelta(hours=4*i)).strftime('%Y-%m-%dT%H:%M:%S')
         for i in range(168)]                   # 28 days × 6/day

et          = ephem.et_from_iso(times)
elev, az    = ephem.solar_elevation_azimuth(et, lat_deg=-89.5, lon_deg=0.0)
S           = ephem.insolation_series(elev)
ephem.unload_kernels()

print(f"Peak elevation: {np.rad2deg(elev.max()):.2f} deg")
print(f"Peak insolation: {S.max():.1f} W m^-2")
```

---

## 6 Module reference

### `lunar.constants`

All physical constants are defined here. Never hard-code numerical values
elsewhere in the codebase; import from this module instead.

| Constant | Value | Source |
|---|---|---|
| `SIGMA_SB` | 5.670374419e-8 W m⁻² K⁻⁴ | CODATA 2018 |
| `EMISSIVITY_DEFAULT` | 0.95 | Hayne 2017 |
| `Q_B_SOUTH_POLAR` | 0.012 W m⁻² | Langseth 1976, polar |
| `Q_B_EQUATORIAL` | 0.018 W m⁻² | Langseth 1976, equatorial |
| `DZ0_DEFAULT` | 0.003 m | — |
| `GROWTH_DEFAULT` | 1.08 | — |
| `Z_MAX_DEFAULT` | 3.0 m | — |

### `lunar.grid`

```python
from lunar.grid import make_geometric_grid, DepthGrid

grid = make_geometric_grid(z_max=3.0, dz0=0.003, growth=1.08)
# grid.z_mid  — cell-center depths [m], shape (N,)
# grid.z_face — cell-face depths [m], shape (N+1,)
# grid.dz     — cell thicknesses [m], shape (N,)
# grid.n_layers — number of cells (int)
```

Geometric spacing: `dz[i] = dz0 * growth^i`. The diurnal skin depth for
nominal dry regolith is ~4 cm; `dz0=0.003 m` gives ~13 cells per skin depth.

### `lunar.properties`

```python
from lunar.properties import (
    density_hayne,       # ρ(z) = ρ_d + (ρ_s - ρ_d) * exp(-z/H)
    density_icy,         # mix with ice fraction φ
    conductivity_hayne,  # K(T, z) — Hayne 2017 with k_d=3.4e-3
    conductivity_martinez,  # Martinez & Siegler 2021 + Woods-Robinson 2019
    conductivity_icy,    # mix with Klinger 1980 K_ice=567/T
    specific_heat,       # model='hayne' | 'biele'
    specific_heat_icy,
    get_conductivity_model,  # returns callable by name string
)
```

**Critical constant**: `K_d = 3.4e-3 W m⁻¹ K⁻¹` (Hayne 2017). This was
wrong in earlier versions of the code — always verify this value.

### `lunar.solver`

```python
from lunar.solver import PixelInputs, PixelOutputs, solve_pixel

inputs = PixelInputs(
    grid,               # DepthGrid
    t,                  # time array [s]
    bc_mode,            # 'radiative' | 'dirichlet'
    insolation,         # [W m^-2], shape (N_t,) — radiative only
    albedo,             # default 0.12
    emissivity,         # default 0.95
    T_surface_forced,   # [K], shape (N_t,) — dirichlet only
    Q_b,                # geothermal flux [W m^-2]
    K_func,             # callable(T, z) → K
    rho_func,           # callable(z) → rho
    cp_func,            # callable(T) → cp
    T_init,             # initial T profile (optional)
    n_lunations_spinup, # default 10
    spinup_tol_K,       # default 0.01
)

out = solve_pixel(inputs)
# out.T          — shape (N_z, N_t) [K]
# out.z          — cell-center depths [m]
# out.t          — time array [s]
# out.converged  — bool
# out.n_spinup_cycles
```

### `lunar.illumination`

```python
from lunar.illumination import (
    DEM,
    load_lola_dem,       # rasterio-based GeoTIFF loader
    compute_horizon,     # Mazarico 2011 ray-march tracer
    azimuth_bin_centers, # [rad], clockwise from north
    is_illuminated,      # binary direct-illumination check
    synthetic_crater_dem,# unit-test fixture
)
```

`compute_horizon` returns shape `(H, W, n_azimuth)` in radians.
Uses Numba `@njit(parallel=True)` internally — first call triggers JIT
compilation (~5–30 s depending on hardware).

### `lunar.ephem`

```python
from lunar import ephem

et   = ephem.et_from_iso(['2024-01-01T00:00:00', ...])
elev, az = ephem.solar_elevation_azimuth(et, lat_deg=-89.5, lon_deg=0.0)
S    = ephem.insolation_series(elev)
ephem.unload_kernels()   # call at the end of a session
```

Kernels are loaded lazily on first call. Requires the 6 files in `data/spice/`.

### `lunar.validation`

```python
from lunar.validation import (
    load_apollo_hfe_temperature,   # returns HFERecord
    load_apollo_hfe_depth,         # returns structured ndarray
    load_diviner_pcp_polar,        # returns DivinerPCP
)

rec = load_apollo_hfe_temperature('a15', 'p1f1')
# rec.time_s, rec.T, rec.dT, rec.dT_corr, rec.flags

depths = load_apollo_hfe_depth('a15', 1)
# depths['time_iso'], depths['T'], depths['sensor'], depths['depth_cm'], depths['flags']

div = load_diviner_pcp_polar(local_time=13, season='sum', pole='pols')
# div.x, div.y, div.clon, div.clat, div.tbol
```

---

## 7 Notebooks guide

Open with `jupyter notebook notebooks/` or `jupyter lab notebooks/`.

| Notebook | Purpose | Prerequisites |
|---|---|---|
| `00_quickstart.ipynb` | 5-minute tour of all modules | None |
| `01_apollo_validation.ipynb` | Compare solver to Apollo 15 HFE | `data/apollo/` |
| `02_equatorial_diurnal.ipynb` | Reproduce Hayne 2017 390/95 K benchmark | None |
| `03_spice_insolation.ipynb` | Full SPICE-driven pipeline at Apollo 15 | `data/spice/` + spiceypy |

All notebooks use `matplotlib.use('Agg')` by default. To display plots
interactively, remove or change that line.

---

## 8 Running the tests

```bash
# All tests (skips those requiring missing data)
pytest tests/ -v

# Only the fast tests (no rasterio, no SPICE)
pytest tests/ -v -k "not lola and not spice and not ephem and not apollo and not diviner"

# With coverage report
pytest tests/ --cov=lunar --cov-report=term-missing
```

The test suite currently has **50 tests**. Tests that require external data
files skip gracefully when those files are not present.

### Expected output (minimal install)

```
tests/test_constants.py        PASSED (5)
tests/test_grid.py             PASSED (4)
tests/test_properties.py       PASSED (8)
tests/test_solver.py           PASSED (7)
tests/test_solver_assembly.py  PASSED (5)
tests/test_illumination.py     PASSED (3)  [LOLA test skipped]
tests/test_ephem.py            SKIPPED (3) [kernels missing]
tests/test_validation.py       SKIPPED (3) [data missing]
```

---

## 9 Scientific rules

These rules are enforced project-wide (see `CLAUDE.md` and `.claude/skills/SKILL.md`):

1. **Never fabricate numerical values.** Every constant must have a citation.
2. **Geometric depth grid only.** Uniform grids are forbidden.
3. **Bottom boundary condition = geothermal flux.** Not zero-flux.
4. **Spin-up ≥ 10 lunations** with `max ΔT < 0.01 K` convergence check.
5. **σ = 5.6704e-8 W m⁻² K⁻⁴** — verify every occurrence.
6. **K_d = 3.4e-3 W m⁻¹ K⁻¹** (Hayne 2017) — was wrong in older code.

---

## 10 Troubleshooting

### `ImportError: No module named 'numba'`

Numba is optional. The code falls back to pure NumPy. Install with:
```bash
pip install numba
```

### `ImportError: No module named 'rasterio'`

Required for `load_lola_dem`. Install the geo extra:
```bash
pip install -e ".[geo]"
# or: pip install rasterio
```

### `FileNotFoundError: Missing SPICE kernels`

Run the SPICE download script in section 3. Kernels must be in `data/spice/`.

### `SPICE(UNKNOWNFRAME): MOON_ME`

You have the binary PCK but not the frame kernels. Ensure all 6 files
listed in `data/README.md §2` are present, especially:
- `moon_de440_250416.tf`
- `moon_assoc_me.tf`

### Solver does not converge in 10 lunations

Increase `n_lunations_spinup` in `PixelInputs`. For deeply shadowed polar
pixels, convergence can require 15–20 lunations. Also check that `Q_b`
is not accidentally zero.

### Numba JIT compilation is slow on first run

Numba compiles `_horizon_grid` and the tridiagonal sweep on first call.
This is a one-time cost (~10–60 s). Subsequent calls use the cached
compiled code (stored in `__pycache__/`).

---

## References

- Hayne, P. O. et al. (2017), JGR Planets 122, 2371-2400. doi:10.1002/2017JE005387
- Martinez, G. M. & Siegler, M. A. (2021), JGR Planets 126, e2020JE006597.
- Biele, J. (2022), Planet. Space Sci. 218, 105501.
- Woods-Robinson, R. et al. (2019), PRB 100, 214108 (amorphous K polynomial).
- Klinger, J. (1980), Science 209, 271-272 (ice conductivity K=567/T).
- Mazarico, E. et al. (2011), Icarus 211, 1066-1081 (horizon tracer).
- Langseth, M. G. et al. (1976), Proc. Lunar Sci. Conf. 7th, 3143-3171 (Q_b).
- Nagihara, S. et al. (2018), Earth Space Sci. 5, 289-310 (Apollo HFE PDS).
- Williams, J.-P. et al. (2019), Icarus 326, 123-134 (Diviner PCP).
- Kopp, G. & Lean, J. L. (2011), GRL 38, L01706 (S0=1361 W m^-2).
- Barker, M. K. et al. (2023), PGDA product 90. doi:10.5067/LOLA/LDEM_80S_20MPP_ADJ_001
