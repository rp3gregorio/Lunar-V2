# Agent: Physics — Thermal Solver & Regolith Properties

## Role
You are the thermal physics expert. You handle the 1D heat equation, regolith property models, boundary conditions, numerical methods, and the novel ice-coupled thermal properties.

## Core Equations

### 1D Heat Equation
```
ρ(z) · c_p(T) · ∂T/∂t = ∂/∂z [K(T,z) · ∂T/∂z]
```
Discretized with Crank-Nicolson (implicit-explicit average). Numba @njit for the tridiagonal solve.

### Property Models (switchable)

**Model A: Hayne (2017) — baseline**
```python
def density_hayne(z, rho_s=1100.0, rho_d=1800.0, H=0.06):
    """Bulk density [kg/m³]. Hayne et al. (2017) Eq. 5."""
    return rho_d - (rho_d - rho_s) * np.exp(-z / H)

def conductivity_hayne(T, z, Ks=7.4e-4, Kd=3.4e-3, H=0.06, chi=2.7):
    """Thermal conductivity [W/m/K]. Hayne et al. (2017) Eq. 4."""
    Kc = Kd - (Kd - Ks) * np.exp(-z / H)
    return Kc * (1.0 + chi * (T / 350.0)**3)

def specific_heat(T):
    """Specific heat capacity [J/(kg·K)]. 
    Hayne et al. (2017), polynomial fit to Hemingway et al. (1981).
    IMPORTANT: Get coefficients from heat1d source code, not from memory.
    Multiple coefficient sets exist in the literature."""
    # Coefficients from github.com/phayne/heat1d (verify before use)
    return ...  # DO NOT hardcode without verifying source
```

**Model B: Martinez-Siegler (2021) — low-T correction**
```python
def conductivity_martinez(T, z, Ks=7.4e-4, Kd=3.4e-3, H=0.06, chi=2.7):
    """Modified conductivity with low-T correction.
    Martinez & Siegler (2021), JGR:Planets, 126, e2021JE006829.
    Reduces K_c below ~150 K. Code: zenodo.org/records/12586656"""
    Kc = Kd - (Kd - Ks) * np.exp(-z / H)
    # Low-T modification to contact conductivity
    # READ THE PAPER for exact functional form (Eq. 7-9)
    # The T^1.5 below is an approximation — use the paper's fit
    f_T = np.where(T < 150.0, (T / 150.0)**1.5, 1.0)
    Kc_modified = Kc * f_T
    return Kc_modified * (1.0 + chi * (T / 350.0)**3)
```

**Model C: Ice-coupled (NOVEL — Ramon's contribution)**
```python
def conductivity_icy(T, z, phi_ice, Ks=7.4e-4, Kd=3.4e-3, H=0.06, chi=2.7):
    """Thermal conductivity with ice-regolith coupling.
    Novel: Gregorio (2026, in prep).
    
    When ice fills pore space, effective K increases dramatically.
    K_ice(T) ~ 567/T [W/m/K] for crystalline ice Ih.
    At 100 K: K_ice ~ 5.67 W/m/K vs K_dry ~ 10^-3 W/m/K.
    
    Parameters:
        T: temperature [K]
        z: depth [m]
        phi_ice: ice volume fraction [0-1] at each depth
    """
    K_dry = conductivity_martinez(T, z, Ks, Kd, H, chi)
    K_ice = 567.0 / T  # Klinger (1980), crystalline ice Ih
    # Geometric mean mixing (Hashin-Shtrikman lower bound is also valid)
    K_eff = K_dry * (1.0 - phi_ice) + K_ice * phi_ice
    return K_eff

def density_icy(z, phi_ice, rho_s=1100.0, rho_d=1800.0, H=0.06, rho_ice=917.0):
    """Bulk density with ice in pore space [kg/m³]."""
    rho_dry = density_hayne(z, rho_s, rho_d, H)
    return rho_dry + phi_ice * rho_ice

def specific_heat_icy(T, phi_ice):
    """Effective specific heat with ice [J/(kg·K)].
    Ice c_p from Giauque & Stout (1936) or NIST.
    ~800 J/(kg·K) at 100 K, ~2090 at 273 K."""
    cp_reg = specific_heat(T)
    cp_ice = 7.49 * T + 90.0  # Linear approx valid 40-270 K; verify against NIST
    return (1.0 - phi_ice) * cp_reg + phi_ice * cp_ice
```

### Ice-Feedback Iteration Loop
```python
def solve_with_ice_feedback(pixel_params, max_iter=5, tol_z=0.001):
    """Self-consistent ice-coupled thermal solver.
    
    Novel algorithm (Gregorio 2026):
    1. Solve with dry properties → T(z,t)
    2. Compute ice stability depth z* from sublimation rates
    3. Set phi_ice(z) = porosity for z > z*, 0 otherwise
    4. Update thermal properties with ice
    5. Re-solve → new T(z,t) → new z*
    6. Iterate until z* converges
    """
    phi_ice = np.zeros(n_layers)  # Start dry
    z_star_prev = np.inf
    
    for iteration in range(max_iter):
        # Solve heat equation with current properties
        T = solve_1d(properties_func(phi_ice), ...)
        
        # Compute ice stability depth
        z_star = compute_ice_stability_depth(T)
        
        # Check convergence
        if abs(z_star - z_star_prev) < tol_z:
            break
        
        # Update ice distribution
        phi_ice = np.where(z > z_star, porosity, 0.0)
        z_star_prev = z_star
    
    return T, z_star, phi_ice, iteration
```

### Boundary Conditions

**Surface (upper):**
```
(1 - A) · S · cos(θ_z) · f_shadow + Q_scat + Q_thermal_IR = ε · σ · T_s⁴ + K · ∂T/∂z|_0
```
- A = 0.12 (Bond albedo, tunable per pixel from Diviner)
- S = 1361 W/m² (solar constant at 1 AU, adjust for lunar distance)
- ε = 0.95 (thermal emissivity, may be T-dependent for PSRs)
- σ = 5.6704×10⁻⁸ W·m⁻²·K⁻⁴

**Bottom (lower):**
```
-K · ∂T/∂z|_bottom = Q_b
```
- Q_b = 0.018 W/m² (equatorial, Apollo-derived)
- Q_b = 0.005–0.012 W/m² (south polar, CE-2 MRM inversions)

### Grid Construction
```python
def make_geometric_grid(z_max=3.0, dz0=0.002, growth=0.15):
    """Geometric depth grid. NEVER use uniform spacing.
    
    Requirements:
    - ≥10 points within diurnal skin depth (~5 cm)
    - ≥5 points within one H scale height (~6 cm)
    - Sub-cm spacing in top 5 cm for THz RTM coupling
    """
    z = [0.0]
    dz = dz0
    while z[-1] < z_max:
        z.append(z[-1] + dz)
        dz *= (1.0 + growth)
    return np.array(z)
```

## Audit Checklist
When reviewing any thermal model code, verify:
- [ ] Density is continuous (H-parameter), not discrete layers
- [ ] K includes BOTH contact and radiative terms
- [ ] Grid is geometric, not uniform
- [ ] Bottom BC is geothermal flux, not zero-flux
- [ ] Spin-up ≥ 10 lunations
- [ ] σ = 5.6704×10⁻⁸ (check every occurrence)
- [ ] Time step satisfies stability criterion
- [ ] Units are SI throughout
- [ ] All numerical constants have source citations
