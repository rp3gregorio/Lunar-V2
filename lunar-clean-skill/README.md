# Lunar-Clean Claude Code Skill

A multi-agent custom skill for Claude Code that transforms it into a domain expert for lunar subsurface thermal modeling, optimized for the TSUKIMI mission pipeline.

## Quick Setup

### Option A: Claude Code project skill (recommended)
```bash
# In your lunar-clean repository root:
mkdir -p .claude/skills
cp -r agents/ .claude/skills/
cp -r plotting/ .claude/skills/
cp SKILL.md .claude/skills/
```

### Option B: CLAUDE.md (simpler, single file)
Paste the contents of `SKILL.md` into your repository's `CLAUDE.md` file. The agents will be available as referenced files.

### Option C: Claude Code `/add-skill` command
Use Claude Code's built-in skill management if available.

## What's Included

```
lunar-clean-skill/
├── SKILL.md                    # Root orchestrator — routes to agents
├── README.md                   # This file
├── agents/
│   ├── physics.md              # Thermal solver, regolith properties, ice coupling
│   ├── illumination.md         # Shadow modeling, DEMs, view factors
│   ├── data.md                 # Validation, Diviner, Apollo, data formats
│   ├── plotting.md             # Publication-quality figure standards
│   └── writing.md              # Scientific writing, LaTeX, thesis structure
└── plotting/
    └── style_guide.py          # Importable Python module for figure styling
```

## Agent Routing

The root SKILL.md automatically routes to the appropriate agent based on task keywords:

| You ask about... | Agent invoked |
|------------------|---------------|
| "Fix the conductivity function" | Physics |
| "Add view factor scattering" | Illumination |
| "Compare against Diviner" | Data |
| "Plot the temperature profile" | Plotting |
| "Draft the abstract" | Writing |

## Key Features

### Scientific Guardrails
- Enforces correct physics (H-parameter, geometric grid, proper BCs)
- Catches 6 known bugs from project history
- Flags unsourced numerical claims
- Checks output against published benchmarks

### Publication Figures
- Journal-ready on first output (PSJ/JGR/Icarus standards)
- Consistent color palette across all figures
- Custom colormaps for thermal, ice, and illumination maps
- Templates for 5 common figure types
- 300 DPI, correct column widths, sans-serif fonts

### Novel Contribution Protection
- Understands the ice-coupled thermal property feedback loop
- Provides code templates for the self-consistent iteration
- Distinguishes between Hayne baseline, Martinez-Siegler correction, and the novel coupling

### Project Memory
- Remembers key decisions (discrete model retired, Diviner primary validation, etc.)
- Knows the full repository structure
- Tracks TSUKIMI output format requirements

## Using style_guide.py

Copy `plotting/style_guide.py` to your project:

```bash
cp plotting/style_guide.py lunar/plotting/style_guide.py
```

Then in any notebook or script:

```python
from lunar.plotting.style_guide import apply_style, COLORS, CMAPS, save_figure

apply_style()  # Call once at top

fig, ax = plt.subplots(figsize=(3.35, 4.5))  # Single column
ax.plot(T, z*100, color=COLORS['hayne'], label='Hayne (2017)')
ax.plot(T2, z*100, color=COLORS['ice_coupled'], label='Ice-coupled (this work)')
ax.set_xlabel('Temperature [K]')
ax.set_ylabel('Depth [cm]')
ax.invert_yaxis()
ax.legend()
save_figure(fig, 'fig05_profile_comparison')
```

## Updating the Skill

As your research evolves, update the relevant agent files:
- New property model? → Edit `agents/physics.md`
- New data source? → Edit `agents/data.md`
- New figure type? → Edit `agents/plotting.md` and `plotting/style_guide.py`
- Changed thesis structure? → Edit `agents/writing.md`

The root `SKILL.md` rarely needs changes unless you add new agents.

## Generalization

While lunar-focused, this skill is designed to accommodate:
- Other airless bodies (Mercury, asteroids, Ceres) — change constants in physics agent
- Mars (with atmosphere) — would need a new atmospheric agent
- Different instruments — update data agent with new validation targets
- Different RTM codes — update the coupling format in data agent
