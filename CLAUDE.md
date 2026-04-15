# Claude Code — Lunar-Clean v2

This repository has a domain-expert skill installed under
`.claude/skills/`. The skill turns Claude Code into a planetary
subsurface thermal modeling assistant specialized for the TSUKIMI
mission pipeline.

**Read first:** `.claude/skills/SKILL.md` — the root orchestrator. It
contains the project-wide rules (SI units, scientific-integrity rules,
known-bug checklist, output benchmarks) and routes tasks to the
appropriate agent.

## Agents

| Agent | File | When to invoke |
| --- | --- | --- |
| Physics | `.claude/skills/agents/physics.md` | Heat equation, regolith properties, ice coupling, numerical methods |
| Illumination | `.claude/skills/agents/illumination.md` | DEMs, horizons, shadows, view factors, solar geometry |
| Data | `.claude/skills/agents/data.md` | Diviner, Apollo HFE, Chang'E, ChaSTE, validation workflows |
| Plotting | `.claude/skills/agents/plotting.md` | Publication-quality figures (PSJ / JGR / Icarus standards) |
| Writing | `.claude/skills/agents/writing.md` | LaTeX manuscript, thesis chapters, abstracts |

## Hard rules (see SKILL.md for the full list)

1. **Never fabricate numerical values.** Cite every constant.
2. **Geometric depth grid only** — uniform grids are forbidden.
3. **Bottom boundary condition = geothermal flux**, not zero-flux.
4. **Spin-up ≥ 10 lunations** with convergence check `max ΔT < 0.01 K`.
5. **σ = 5.6704e-8 W m⁻² K⁻⁴** — verify every occurrence.
6. **K_d = 3.4e-3 W m⁻¹ K⁻¹** (Hayne 2017) — previously wrong in code.

## Development branch

All work on this session happens on
`claude/thermal-lunar-profile-repo-ZF4Mm`. Do not push to `main` without
explicit approval.
