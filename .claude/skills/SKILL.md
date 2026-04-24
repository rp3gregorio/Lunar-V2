---
name: Lunar-Clean: Planetary Thermal Modeling
description: This skill transforms Claude Code into a specialized assistant for planetary subsurface thermal modeling, with primary focus on lunar science and the TSUKIMI mission pipeline. It provides domain-expert auditing, publication-quality figure generation, and modular agents for different aspects of the research workflow.
---
# Lunar-Clean: Planetary Thermal Modeling Skill

## Overview

This skill transforms Claude Code into a specialized assistant for planetary subsurface thermal modeling, with primary focus on lunar science and the TSUKIMI mission pipeline. It provides domain-expert auditing, publication-quality figure generation, and modular agents for different aspects of the research workflow.

## Project: Lunar-Clean v2

**Owner:** Ramon III Palinguba Gregorio, Kasai Laboratory, Institute of Science Tokyo
**Supervisors:** Prof. Yasuko Kasai, Prof. Arihiro Kamada
**Mission affiliation:** TSUKIMI (Tohoku Univ., NICT, UTokyo, IST)
**Thesis deadline:** September 2026
**Target journal (Phase 1 letter):** Geophysical Research Letters (GRL) via ESS Open Archive preprint

### What this pipeline does
1. Ingests LOLA DEMs → computes illumination with topographic shadow and secondary scattering
2. Runs a 1D finite-difference thermal solver (Crank-Nicolson, Numba JIT) per pixel at 20 m resolution
3. Outputs T(z, t) at ~55 geometric depth nodes (0–3 m) per pixel
4. Feeds thermal profiles into TSUKIMI's terahertz RTM via Jacobian coupling
5. Produces ice survivability maps as integrated downstream products
6. Novel contribution: self-consistent ice-coupled thermal properties (feedback loop)

### Repository structure
```
lunar-clean/
├── .claude/
│   └── skills/              # THIS SKILL LIVES HERE
│       ├── SKILL.md          # This file (root orchestrator)
│       ├── agents/
│       │   ├── physics.md    # Thermal physics & solver agent
│       │   ├── illumination.md  # Shadow & illumination agent
│       │   ├── data.md       # Data processing & validation agent
│       │   ├── plotting.md   # Publication figure agent
│       │   └── writing.md    # Scientific writing agent
│       ├── plotting/
│       │   └── style_guide.md   # Figure style standards
│       └── templates/
│           └── figure_templates.py  # Reusable plotting code
├── lunar/
│   ├── __init__.py
│   ├── solver.py
│   ├── properties.py
│   ├── illumination.py
│   ├── pipeline.py
│   ├── ice_stability.py
│   ├── rtm_coupling.py
│   └── constants.py
├── notebooks/
├── tests/
├── paper/
├── pyproject.toml
└── README.md
```

## Agent System

This skill uses **5 specialized agents**. Claude should automatically route to the appropriate agent based on the task. If a task spans multiple agents, invoke them in sequence.

| Agent | File | Trigger keywords |
|-------|------|-----------------|
| **Physics** | `agents/physics.md` | solver, heat equation, conductivity, density, boundary condition, H-parameter, properties, temperature, thermal, regolith, ice coupling |
| **Illumination** | `agents/illumination.md` | shadow, DEM, LOLA, horizon, ray-trace, view factor, illumination, PSR, scattered, albedo, solar, ephemeris |
| **Data** | `agents/data.md` | Diviner, Apollo, validation, RMSE, download, PDS, PGDA, Chang'E, ChaSTE, LISTER, calibration, comparison |
| **Plotting** | `agents/plotting.md` | figure, plot, graph, map, colorbar, colormap, axis, label, publication, visualization |
| **Writing** | `agents/writing.md` | paper, manuscript, LaTeX, abstract, section, draft, thesis, PSJ, Icarus, reference, citation |

## Global Rules (Apply to ALL agents)

### Code standards
- Python 3.10+. NumPy, SciPy, Numba for numerics. Matplotlib + optional Plotly for plotting.
- `@njit(cache=True)` for all hot loops. Type hints on all public functions.
- Docstrings with units: `"""Compute density. Parameters: z (float): depth [m]"""`
- SI units internally. Convert only at I/O boundaries.
- pytest for all new functions. Test against known analytical or published solutions.

### Scientific integrity
- **NEVER fabricate numerical values.** If a value is needed and not known, say "I need to verify this against [specific paper]."
- **ALWAYS cite the source** for any physical constant, parameter value, or equation.
- **Flag any hardcoded number** that doesn't have a comment with its source.
- When in doubt, be conservative: state uncertainty, don't hide it.

### Key decisions (memory)
- **Phase 1 scope:** Single-point validation at Apollo 15 + 17 only. No CE-4/ChaSTE in Phase 1.
- **Discrete 3-layer model:** Kept as Phase-1 comparison against Hayne. Will be dropped in Phase 2+ pipeline.
- **Primary deep-sensor threshold:** 80 cm. Sensors z < 80 cm shown but excluded from RMSE (borestem artefact).
- **Insolation:** Sinusoidal proxy at site latitude — adequate for flat-terrain A15/A17.
- **Phase 2:** Martinez & Siegler (2021) model + shadowing/DEM effects. Both fold into improved Hayne global model.
- Grid: ALWAYS geometric. Δz₀ ≈ 2 mm, growth ~0.08, ~80 layers to 5 m.
- Bottom BC: geothermal flux Q_b. NOT zero-flux. A15 = 21 mW m⁻², A17 = 15 mW m⁻².
- Spin-up: 100 lunations (equatorial). Check convergence (max ΔT < 0.01 K).
- σ = 5.6704×10⁻⁸ W·m⁻²·K⁻⁴. Verify every occurrence.
- Synodic period = 29.530589 d. Use LUNATION_SECONDS from constants.py (not sidereal 27.32 d).

### Known bugs to catch
1. Bottom BC: `T[N-1] = T[N-2]` is WRONG (zero-flux). Correct: `T[N-1] = T[N-2] + Q_b * dz[-1] / k[-1]`
2. K_d value must match Hayne (2017): 3.4×10⁻³ W/m/K. Previously was wrong in code.
3. Spin-up < 10 cycles: insufficient for polar latitudes. Flag and fix.
4. Uniform grid spacing: ALWAYS flag. Must be geometric.
5. Missing radiative term in conductivity: K must include BOTH K_c (contact) AND χ·(T/350)³ (radiative).
6. Apollo probe material: fiberglass borestems, NOT aluminum.

### Output benchmarks (sanity checks)
- Equatorial: T_max ≈ 390 K, T_min ≈ 95 K
- Apollo 15 subsurface 1 m: ~252 K mean
- Apollo 17 subsurface 1 m: ~255 K mean
- PSR surface: 30–100 K depending on crater depth and secondary illumination
- Thermal inertia: global mean ~55 J·m⁻²·K⁻¹·s⁻¹/²
- Surface K: ~7.4×10⁻⁴ W/m/K; deep K: ~3.4×10⁻³ W/m/K
