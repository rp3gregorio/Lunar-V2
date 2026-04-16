"""Quick consistency check: verify all constants and property models
against their published reference values."""
import numpy as np
from lunar.constants import (
    SIGMA_SB, K_SURFACE, K_DEEP, H_PARAMETER, CHI_RADIATIVE,
    Q_B_EQUATORIAL, Q_B_SOUTH_POLAR, RHO_SURFACE, RHO_DEEP,
)
from lunar.properties import (
    conductivity_hayne, conductivity_martinez, conductivity_icy,
    density_hayne, specific_heat,
)

print("=" * 60)
print("Model Consistency Check — Reference Values")
print("=" * 60)

# 1. Stefan-Boltzmann
assert abs(SIGMA_SB - 5.670374419e-8) < 1e-15
print(f"[OK] sigma = {SIGMA_SB:.10e} W m^-2 K^-4")

# 2. Conductivity constants
assert K_SURFACE == 7.4e-4
assert K_DEEP == 3.4e-3
assert H_PARAMETER == 0.06
assert CHI_RADIATIVE == 2.7
print(f"[OK] K_s={K_SURFACE}, K_d={K_DEEP}, H={H_PARAMETER}, chi={CHI_RADIATIVE}")

# 3. Density endpoints
z0 = np.array([0.0])
z_deep = np.array([10.0])
assert abs(density_hayne(z0)[0] - RHO_SURFACE) < 1.0
assert abs(density_hayne(z_deep)[0] - RHO_DEEP) < 1.0
print(f"[OK] rho(0)={density_hayne(z0)[0]:.0f}, rho(10m)={density_hayne(z_deep)[0]:.0f}")

# 4. Bottom BC
assert Q_B_EQUATORIAL == 0.018
assert Q_B_SOUTH_POLAR == 0.012
print(f"[OK] Q_b eq={Q_B_EQUATORIAL}, Q_b polar={Q_B_SOUTH_POLAR}")

# 5. Specific heat
cp300_h = specific_heat(np.array([300.0]), model="hayne")[0]
cp300_b = specific_heat(np.array([300.0]), model="biele")[0]
assert 600 < cp300_h < 900, f"cp_hayne(300K) = {cp300_h}"
assert 600 < cp300_b < 900, f"cp_biele(300K) = {cp300_b}"
print(f"[OK] cp(300K): hayne={cp300_h:.1f}, biele={cp300_b:.1f} J/kg/K")

# 6. Low-T conductivity comparison
T_low = np.array([50.0, 80.0, 100.0, 150.0, 300.0])
z_zero = np.zeros_like(T_low)
K_h = conductivity_hayne(T_low, z_zero)
K_m = conductivity_martinez(T_low, z_zero)
print("\nLow-T conductivity (surface):")
for T, kh, km in zip(T_low, K_h, K_m):
    r = km / kh if kh > 0 else float("inf")
    print(f"  T={T:5.0f} K: Hayne={kh:.6f}, Martinez={km:.6f}, ratio={r:.3f}")

# 7. Ice conductivity check
phi = np.full_like(T_low, 0.3)
K_ice = conductivity_icy(T_low, z_zero, phi_ice=phi)
print("\nIce-coupled K (phi=0.3, surface):")
for T, ki in zip(T_low, K_ice):
    print(f"  T={T:5.0f} K: K_icy={ki:.4f} (K_ice_pure ~ {567.0 / T:.2f})")

print("\n" + "=" * 60)
print("ALL CHECKS PASSED")
print("=" * 60)
