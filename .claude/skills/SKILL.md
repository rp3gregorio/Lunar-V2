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
**Target journal:** Planetary Science Journal (PSJ)

### What this pipeline does

**Four-phase build.** See `paper/pipeline/lunarv2_pipeline.tex` (the
canonical roadmap PDF) for the full specification. In short:

1. **Phase 1 — Point validation.** Benchmark the Hayne 2017 solver (as
   shipped in `phayne/heat1d`, vendored under `third_party/heat1d/`)
   plus the Discrete Layer alternative against Apollo 15/17 HFE
   stabilised-window deep sensors. Reproduce Hayne 2017 Figure 4.
2. **Phase 2 — Improved Hayne 2017 global model.** One merged model
   adding the Hayne 2017 appendix-only products that never landed in
   his GitHub (H-parameter latitude map, rock-abundance mixing,
   bolometric emissivity) plus Martinez & Siegler (2021) cold-region
   conductivity, Bürger (2024) microphysical scaling, and LOLA-DEM
   horizon + shadow-mask + sky-view factor.
3. **Phase 3 — RTM coupling, Jacobian, ice-stability.** Two-stream
   regolith radiative transfer, finite-difference Jacobian of emerging
   brightness-T w.r.t. retrieval state, and an ice-stability index map.
4. **Phase 4 — Thesis integration.** Figure/table bundling + LaTeX
   integration; scoping of post-thesis extensions (roughness,
   time-dependent ice retreat, Mars port, in-flight retrieval harness).

**Scope boundaries.** Chang'E-4 and ChaSTE in-situ probe validations are
explicitly out of scope — removed from the codebase in Phase 1.

### Repository structure
```
Lunar-V2/
├── .claude/skills/              # THIS SKILL LIVES HERE
├── lunar/                       # Python package
│   ├── _bootstrap.py            # Auto-install + auto-download
│   ├── solver.py                # 1-D Crank-Nicolson integrator
│   ├── properties.py            # K(T,z), ρ(z), c_p(T), albedo_angle(i)
│   ├── illumination.py          # DEM + horizon + shadow (Phase 2)
│   ├── constants.py             # Every number, cited
│   └── validation.py            # Apollo HFE + Diviner PCP loaders
├── notebooks/
│   ├── phase0_quickstart/       # Library smoke test
│   ├── phase1_validation/       # Apollo + Hayne Fig 4 (THIS PHASE)
│   ├── phase2_improved_hayne/   # Global model upgrade
│   ├── phase3_rtm_ice/          # RTM + Jacobian + ice stability
│   └── phase4_thesis/           # Thesis figure/table bundling
├── third_party/heat1d/          # Vendored phayne/heat1d (Hayne 2017 reference)
├── paper/pipeline/              # lunarv2_pipeline.tex — canonical roadmap
├── archive/                     # Retired scripts + legacy docs (committed)
├── data/                        # External datasets (gitignored, auto-download)
├── tests/
├── pyproject.toml
└── README.md
```

## Agent System

This skill uses **5 specialized agents**. Claude should automatically route to the appropriate agent based on the task. If a task spans multiple agents, invoke them in sequence.

| Agent | File | Trigger keywords |
|-------|------|-----------------|
| **Physics** | `agents/physics.md` | solver, heat equation, conductivity, density, boundary condition, H-parameter, properties, temperature, thermal, regolith, ice coupling |
| **Illumination** | `agents/illumination.md` | shadow, DEM, LOLA, horizon, ray-trace, view factor, illumination, PSR, scattered, albedo, solar, ephemeris |
| **Data** | `agents/data.md` | Diviner, Apollo, validation, RMSE, download, PDS, PGDA, LISTER, calibration, comparison |
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
- **Phase 1 reference solver = vendored `phayne/heat1d`** under `third_party/heat1d/`. The in-repo `lunar.*` model mirrors its formulas exactly (K(T,z) with χ(T/350)³, ρ(z) exponential, A(i) Eq A.1, Hayne cp polynomial).
- **Phase 1 primary validation = Apollo 15/17 HFE deep sensors** (z ≥ 80 cm). Diviner becomes primary validation in Phase 2.
- **Chang'E-4 and ChaSTE in-situ probe validations are out of scope.** Removed from the codebase.
- Discrete 3-layer model: kept as an Apollo-calibrated alternative for comparison in Phase 1. Not used in Phase 2+ pipeline.
- Grid: ALWAYS geometric. Δz₀ ≈ 2 mm, growth ~0.1–0.2, ~55 layers to 3 m.
- Bottom BC: geothermal flux Q_b. Default 0.018 W/m² (equatorial). NOT zero-flux. Use Q_b = 0.021 W/m² for Apollo 15 (Langseth 1976), Q_b = 0.015 W/m² for Apollo 17 (Nagihara 2018 reprocessed).
- Spin-up: ≥10 lunations. Check convergence (max ΔT < 0.01 K between last two cycles).
- σ = 5.6704×10⁻⁸ W·m⁻²·K⁻⁴. Verify every occurrence.
- The novel contribution is (a) ice-coupled thermal properties with self-consistent feedback AND (b) the improved-Hayne global model (Phase 2).

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
