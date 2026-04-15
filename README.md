# Lunar-Clean v2

A 20 m/pixel subsurface thermal modeling pipeline for the lunar south pole,
with topographic shadow and secondary illumination, self-consistent
ice-coupled regolith properties, and coupling to the TSUKIMI terahertz
radiative-transfer model.

> Successor to the original "Thermal Lunar Profile" study. Redesigned around
> a continuous H-parameter regolith model, a geometric depth grid, and the
> novel ice-coupled conductivity feedback loop.

## Project

| | |
| --- | --- |
| **Owner** | Ramon III Palinguba Gregorio |
| **Lab** | Kasai Laboratory, Institute of Science Tokyo |
| **Supervisors** | Prof. Yasuko Kasai, Prof. Arihiro Kamada |
| **Mission affiliation** | TSUKIMI (Tohoku Univ., NICT, UTokyo, IST) |
| **Thesis deadline** | September 2026 |
| **Target journal** | Planetary Science Journal (PSJ) |

## What the pipeline does

1. Ingests LOLA DEMs and computes illumination with topographic shadow and
   secondary scattering (visible + thermal IR).
2. Runs a 1D finite-difference thermal solver (Crank-Nicolson, Numba JIT)
   per pixel at 20 m resolution.
3. Emits `T(z, t)` at ~55 geometric depth nodes from 0 to 3 m per pixel.
4. Feeds thermal profiles into TSUKIMI's terahertz RTM via Jacobian coupling.
5. Produces ice survivability maps as the integrated downstream product.
6. **Novel contribution**: self-consistent ice-coupled thermal properties
   with a convergent feedback loop on ice stability depth.

## Repository layout

```
Lunar-V2/
├── .claude/skills/       # Lunar-Clean domain expert skill for Claude Code
│   ├── SKILL.md          # Root orchestrator with project rules
│   ├── agents/           # Physics / illumination / data / plotting / writing
│   └── plotting/         # Publication figure style guide
├── lunar/                # Python package (installable)
│   ├── constants.py      # SI physical constants with citations
│   ├── grid.py           # Geometric depth grid
│   ├── properties.py     # Hayne, Martinez-Siegler, ice-coupled models
│   ├── solver.py         # 1D Crank-Nicolson thermal solver
│   ├── illumination.py   # DEM processing, horizons, view factors
│   ├── ice_stability.py  # Sublimation rates and z_star
│   ├── rtm_coupling.py   # TSUKIMI output schema
│   ├── pipeline.py       # Top-level orchestrator
│   └── plotting/         # Mirror of the skill's style_guide.py
├── tests/                # pytest suite (grid, properties, constants, solver)
├── notebooks/            # Jupyter exploration (non-authoritative)
├── paper/                # LaTeX manuscript sources (PSJ target)
└── outputs/              # Run artifacts (gitignored)
```

## Quick start

```bash
git clone https://github.com/rp3gregorio/Lunar-V2.git
cd Lunar-V2
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,geo,spice]"
pytest
```

The test suite currently exercises `lunar.constants`, `lunar.grid`,
`lunar.properties`, and the tridiagonal assembly in `lunar.solver`.
The full solver, horizon tracer, and view-factor computation are
scaffolded but not yet wired (see "Status" below).

## Status

| Module | Status | Notes |
| --- | --- | --- |
| `constants` | Implemented | All values cited against Hayne 2017 / CODATA / Apollo HFE |
| `grid` | Implemented | Geometric only — uniform grids are rejected |
| `properties` | Partially implemented | Hayne K and rho; Martinez and ice-coupled placeholders flagged; `specific_heat` intentionally raises until verified against heat1d |
| `solver` | Scaffold | Tridiagonal assembly works; non-linear surface BC and spin-up loop pending |
| `illumination` | Scaffold | Function signatures; Mazarico tracer not yet written |
| `ice_stability` | Scaffold | Awaiting solver output and a choice of saturation-pressure fit |
| `rtm_coupling` | Schema only | NetCDF serializer blocked on schema lock-in with TSUKIMI team |
| `pipeline` | Scaffold | Top-level driver wired last |

## Scientific integrity rules

These are enforced by the Claude Code skill at `.claude/skills/SKILL.md` and
by code review:

- **Never fabricate numerical values.** If a value is needed and not known,
  say so explicitly.
- **Always cite the source** for any physical constant, parameter value, or
  equation.
- **Flag any hardcoded number** that does not have a comment with its source.
- **Never the zero-flux bottom BC.** Use a geothermal-flux bottom BC.
- **Never a uniform depth grid.** Always geometric, with ≥10 points in the
  diurnal skin depth.

## License

MIT. See `LICENSE` (to be added).
