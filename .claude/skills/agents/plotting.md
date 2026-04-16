# Agent: Plotting — Publication-Quality Figures

## Role
You produce figures that are indistinguishable from those published in JGR: Planets, PSJ, Icarus, and Nature Astronomy. Every figure must meet journal submission standards on first output — no "draft quality" figures.

## Mandatory Style Rules

### Journal requirements (PSJ / Icarus / JGR)
- **Minimum font size**: 8 pt in the final printed figure (at column width)
- **Column width**: single = 3.35 in (85 mm), double = 7.0 in (178 mm)
- **Max height**: 9.0 in (229 mm)
- **DPI**: 300 for raster, vector (PDF/SVG) preferred
- **Font**: Helvetica, Arial, or sans-serif. NEVER serif in figures.
- **File formats**: PDF (preferred), PNG at 300 DPI, or EPS

### The Lunar-Clean style
All figures use this consistent visual language:

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

LUNAR_STYLE = {
    # Font
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    
    # Lines
    'lines.linewidth': 1.5,
    'lines.markersize': 5,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'xtick.minor.width': 0.5,
    'ytick.minor.width': 0.5,
    'xtick.major.size': 4,
    'ytick.major.size': 4,
    'xtick.minor.size': 2.5,
    'ytick.minor.size': 2.5,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.top': True,
    'ytick.right': True,
    
    # Grid
    'axes.grid': False,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.5,
    
    # Figure
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    
    # Legend
    'legend.frameon': True,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '0.8',
    'legend.fancybox': False,
    
    # Math
    'mathtext.default': 'regular',
}

def apply_lunar_style():
    """Apply Lunar-Clean publication style globally."""
    plt.rcParams.update(LUNAR_STYLE)
    # Ensure minor ticks on all axes
    mpl.rcParams['xtick.minor.visible'] = True
    mpl.rcParams['ytick.minor.visible'] = True
```

---

## Layout Rules — Preventing Overlap (MANDATORY)

These rules are **non-negotiable**. Every figure produced by this agent must
pass all of them. Overlapping text, legends, or labels are a submission
rejection risk.

### Rule L1 — Always use `constrained_layout`, never `tight_layout` alone

```python
# CORRECT — constrained_layout handles colorbars, multi-axis spacing, suptitle
fig, axes = plt.subplots(nrows, ncols, figsize=(...), constrained_layout=True)

# ALSO ACCEPTABLE for simple single-axis figures
fig, ax = plt.subplots(figsize=(...))
fig.tight_layout(pad=1.2)

# NEVER do this — tight_layout doesn't know about colorbars or suptitle
fig.suptitle("Title")
plt.tight_layout()   # suptitle will overlap the top axes
```

### Rule L2 — Legends must always be outside data axes

Legends are never allowed inside plotting rectangles. Use one of these two
patterns only:

```python
# Pattern A: outside-right (single axis)
ax.legend(
    loc='upper left',
    bbox_to_anchor=(1.02, 1.0),
    borderaxespad=0,
    frameon=True,
)

# Pattern B: figure-level legend above or below (multi-panel)
fig.legend(
    handles=handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 1.02),
    ncol=3,
    frameon=True,
)

# NEVER use ax.legend(loc='best')
# NEVER place legend in 'upper right'/'lower right' if inside axes
```

### Rule L3 — `fig.suptitle` must have explicit vertical clearance

```python
# CORRECT
fig.suptitle("Figure title", fontsize=12, fontweight='bold', y=1.01)
fig.tight_layout(rect=[0, 0, 1, 0.97])   # reserve 3% at top for suptitle

# WITH constrained_layout (preferred — no manual rect needed)
fig, axes = plt.subplots(1, 2, constrained_layout=True)
fig.suptitle("Title")   # constrained_layout auto-reserves space
```

### Rule L4 — Axis labels must not overlap tick labels

```python
# CORRECT — add padding to push label away from ticks
ax.set_xlabel('Temperature [K]', labelpad=8)
ax.set_ylabel('Depth [cm]',      labelpad=8)

# Rotated tick labels: increase bottom or left margin
fig.subplots_adjust(bottom=0.18)   # or use constrained_layout
```

### Rule L5 — In-axes text annotations must be offset and boxed

```python
# Annotation style: semi-transparent box so text is readable over any background
box_props = dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.75, edgecolor='none')
ax.text(0.05, 0.95, 'RMS = 2.1 K',
        transform=ax.transAxes,
        va='top', ha='left',
        fontsize=9,
        bbox=box_props)

# NEVER place text at a hard-coded data coordinate without a bbox
# ax.text(250, 30, 'label')   ← will overlap data if axis limits change
```

### Rule L6 — Multi-panel figures: share axes where appropriate

```python
# CORRECT — shared x-axis removes duplicate tick labels that clutter inter-panel space
fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True, constrained_layout=True)
# Only the bottom panel gets an x-axis label
axes[-1].set_xlabel('Days', labelpad=8)
# Other panels: suppress tick labels (sharex already hides them, but be explicit)
for ax in axes[:-1]:
    ax.tick_params(labelbottom=False)
```

### Rule L7 — Colorbars must never overlap data axes

```python
# CORRECT — create a dedicated side axis for colorbar (preferred)
from matplotlib import pyplot as plt

fig = plt.figure(figsize=(8, 4.5), constrained_layout=True)
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.05])
ax = fig.add_subplot(gs[0, 0])
cax = fig.add_subplot(gs[0, 1])

im = ax.imshow(data, cmap='magma')
cbar = fig.colorbar(im, cax=cax)
cbar.set_label('Temperature [K]', labelpad=8)

# Acceptable fallback for simple layouts (still external)
fig, ax = plt.subplots(constrained_layout=True)
im = ax.imshow(data, cmap='magma')
fig.colorbar(im, ax=ax, location='right', pad=0.03)

# NEVER place colorbar inside the plotting rectangle.
# NEVER allow colorbar to occlude lines, markers, or heatmap cells.
```

### Rule L8 — Check every figure before returning it

Run this mental checklist on every figure before saving or returning:

- [ ] Do any legend entries touch a line or scatter point?
- [ ] Does the suptitle overlap the top axis title?
- [ ] Do x/y-axis labels touch the tick labels?
- [ ] Do any in-axes text boxes cover data?
- [ ] Are colorbar labels cut off by the figure edge?
- [ ] On log-scale axes, do minor tick labels collide?

If any box is checked, fix it with the rules above before finishing.

---

### Color palettes

**Sequential (for temperature maps):**
```python
# Primary: custom thermal colormap (black → blue → white → yellow → red)
from matplotlib.colors import LinearSegmentedColormap
THERMAL_COLORS = ['#0d0221', '#1a0533', '#2d1b69', '#3d5a9e', 
                  '#4da6c9', '#7ec8a0', '#c8e550', '#f5d03b', 
                  '#f28c28', '#d94f30', '#a11a2d']
cmap_thermal = LinearSegmentedColormap.from_list('lunar_thermal', THERMAL_COLORS, N=256)

# Alternative: use 'magma' (perceptually uniform, good for T maps)
# Alternative: use 'coolwarm' (diverging, for ΔT difference maps)
```

**Categorical (for model comparison):**
```python
COLORS = {
    'hayne': '#2166ac',       # Blue
    'martinez': '#d6604d',    # Red-brown
    'burger': '#4dac26',      # Green
    'ice_coupled': '#7b3294', # Purple (your novel model)
    'diviner': '#1b7837',     # Dark green (observations)
    'apollo': '#e7298a',      # Pink (in situ data)
    'discrete': '#969696',    # Gray (retired model)
}
```

**PSR/ice maps:**
```python
# Ice stability: white (unstable) → light blue → dark blue (surface stable)
cmap_ice = LinearSegmentedColormap.from_list('ice_stability',
    ['#ffffff', '#d0e8ff', '#6baed6', '#2171b5', '#08306b'], N=256)
```

## Figure Templates

### Template 1: Depth-temperature profile
```python
def plot_temperature_profile(z, T_profiles, labels, colors, 
                             title=None, filename=None):
    """Publication-quality T(z) profile plot.
    
    Used for: Apollo validation, model comparison, ice stability depth.
    Depth on Y-axis (inverted), temperature on X-axis.
    """
    apply_lunar_style()
    fig, ax = plt.subplots(figsize=(3.35, 4.5))  # Single column
    
    for T, label, color in zip(T_profiles, labels, colors):
        ax.plot(T, z * 100, color=color, label=label)  # z in cm
    
    ax.set_xlabel('Temperature [K]')
    ax.set_ylabel('Depth [cm]')
    ax.invert_yaxis()
    ax.set_xlim(left=0)
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    
    if title:
        ax.set_title(title)
    
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')
    return fig, ax
```

### Template 2: Surface temperature map
```python
def plot_surface_temperature_map(x, y, T, title=None, filename=None,
                                 vmin=30, vmax=400, cmap='magma'):
    """Publication-quality 2D temperature map.
    
    Used for: spatial thermal maps, ice stability maps, illumination maps.
    """
    apply_lunar_style()
    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    
    im = ax.pcolormesh(x / 1000, y / 1000, T, 
                        cmap=cmap, vmin=vmin, vmax=vmax,
                        shading='auto', rasterized=True)
    
    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('Temperature [K]')
    cbar.ax.tick_params(labelsize=8)
    
    ax.set_xlabel('Easting [km]')
    ax.set_ylabel('Northing [km]')
    ax.set_aspect('equal')
    
    if title:
        ax.set_title(title, fontsize=10)
    
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')
    return fig, ax
```

### Template 3: Model comparison (multi-panel)
```python
def plot_model_comparison(z, T_hayne, T_martinez, T_ice, T_obs=None,
                          filename=None):
    """3-panel model comparison: Hayne vs Martinez vs Ice-coupled.
    
    Left: absolute profiles. Center: difference from Hayne. Right: ice fraction.
    """
    apply_lunar_style()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 4.0), sharey=True)
    
    z_cm = z * 100
    
    # Panel a: Absolute profiles
    ax = axes[0]
    ax.plot(T_hayne, z_cm, color=COLORS['hayne'], label='Hayne (2017)')
    ax.plot(T_martinez, z_cm, color=COLORS['martinez'], label='Martinez (2021)')
    ax.plot(T_ice, z_cm, color=COLORS['ice_coupled'], label='Ice-coupled')
    if T_obs is not None:
        ax.scatter(T_obs[:, 1], T_obs[:, 0] * 100, 
                   color=COLORS['apollo'], marker='s', s=30, 
                   zorder=5, label='Observed')
    ax.set_xlabel('Temperature [K]')
    ax.set_ylabel('Depth [cm]')
    ax.invert_yaxis()
    ax.legend(fontsize=7, loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    ax.text(0.02, 0.98, '(a)', transform=ax.transAxes, 
            fontweight='bold', va='top', fontsize=10)
    
    # Panel b: Difference from Hayne
    ax = axes[1]
    ax.axvline(0, color='gray', ls='--', lw=0.5)
    ax.plot(T_martinez - T_hayne, z_cm, color=COLORS['martinez'], 
            label='Martinez \u2212 Hayne')
    ax.plot(T_ice - T_hayne, z_cm, color=COLORS['ice_coupled'],
            label='Ice \u2212 Hayne')
    ax.set_xlabel('\u0394T [K]')
    ax.legend(fontsize=7, loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    ax.text(0.02, 0.98, '(b)', transform=ax.transAxes,
            fontweight='bold', va='top', fontsize=10)
    
    # Panel c: placeholder for ice fraction or other
    ax = axes[2]
    ax.set_xlabel('Ice volume fraction')
    ax.text(0.02, 0.98, '(c)', transform=ax.transAxes,
            fontweight='bold', va='top', fontsize=10)
    
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')
    return fig, axes
```

### Template 4: Diurnal curves
```python
def plot_diurnal_curves(local_time, T_surface, T_depths, depth_labels,
                        filename=None):
    """Temperature vs local solar time at multiple depths."""
    apply_lunar_style()
    fig, ax = plt.subplots(figsize=(5.0, 3.5))
    
    ax.plot(local_time, T_surface, 'k-', lw=2, label='Surface')
    cmap = plt.cm.viridis
    for i, (T, label) in enumerate(zip(T_depths, depth_labels)):
        color = cmap(i / len(T_depths))
        ax.plot(local_time, T, color=color, label=label)
    
    ax.set_xlabel('Local Solar Time [hours]')
    ax.set_ylabel('Temperature [K]')
    ax.set_xlim(0, 29.53 * 24)
    ax.set_xticks([0, 6*29.53, 12*29.53, 18*29.53, 24*29.53])
    ax.set_xticklabels(['0', '6', '12', '18', '24'])
    fig.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=True)
    
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')
    return fig, ax
```

### Template 5: Sensitivity analysis bar chart
```python
def plot_sensitivity_bars(param_names, delta_T_surface, delta_T_1m,
                          filename=None):
    """Horizontal grouped bar chart of parameter sensitivity."""
    apply_lunar_style()
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    
    y = np.arange(len(param_names))
    height = 0.35
    
    ax.barh(y - height/2, delta_T_surface, height, 
            label='Surface', color='#d6604d', alpha=0.85)
    ax.barh(y + height/2, delta_T_1m, height,
            label='1 m depth', color='#2166ac', alpha=0.85)
    
    ax.set_yticks(y)
    ax.set_yticklabels(param_names)
    ax.set_xlabel('\u0394T [K]')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
    ax.axvline(0, color='black', lw=0.5)
    
    plt.tight_layout()
    if filename:
        fig.savefig(filename, dpi=300, bbox_inches='tight')
    return fig, ax
```

## Interactive Figures (Plotly, optional)

Use Plotly for exploratory work and presentations, NOT for paper submission.

```python
import plotly.graph_objects as go

def interactive_thermal_map(x, y, T, title="Surface Temperature"):
    """Interactive 2D temperature map with hover info."""
    fig = go.Figure(data=go.Heatmap(
        z=T, x=x/1000, y=y/1000,
        colorscale='Magma', colorbar=dict(title='T [K]'),
        hoverongaps=False
    ))
    fig.update_layout(
        title=title,
        xaxis_title='Easting [km]',
        yaxis_title='Northing [km]',
        width=600, height=500
    )
    return fig
```

## Audit Checklist
- [ ] `apply_lunar_style()` called before every figure
- [ ] Font size ≥ 8 pt at final print size
- [ ] Axis labels include units in brackets: `'Temperature [K]'`
- [ ] Colorbars have labels with units
- [ ] Multi-panel figures have (a), (b), (c) labels
- [ ] DPI = 300 for saved figures
- [ ] Figures saved as PDF (preferred) or PNG
- [ ] Color-blind safe palette used (avoid red-green only distinctions)
- [ ] Depth axis inverted (surface at top) for subsurface profiles
- [ ] All text in figures uses sans-serif font
- [ ] No unnecessary gridlines (off by default)
- [ ] Minor ticks visible on all axes
- [ ] Tick marks point inward
- [ ] Rasterized=True for large pcolormesh/imshow to keep PDF file size manageable
- [ ] Figure width matches journal column width (single: 3.35 in, double: 7.0 in)
