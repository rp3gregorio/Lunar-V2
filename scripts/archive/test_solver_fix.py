"""Verify solver fixes: T_surface output and no drop-off at t=0."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from lunar.solver import PixelInputs, solve_pixel
from lunar.grid import make_geometric_grid
import numpy as np

grid = make_geometric_grid(z_max=3.0, dz0=0.002, growth=0.08)
print(f'Grid: {grid.n_layers} layers')

T_LUNAR = 27.321661 * 86400.0
N_t = int(T_LUNAR / 3600.0) + 1
t = np.linspace(0.0, T_LUNAR, N_t)
Q = 1361.0 * np.maximum(0.0, np.cos(2*np.pi*t/T_LUNAR))

inp = PixelInputs(grid=grid, t=t, bc_mode='radiative', insolation=Q,
                  n_lunations_spinup=5, spinup_tol_K=0.05)
out = solve_pixel(inp)

print(f'T_surface: peak={out.T_surface.max():.1f} K, min={out.T_surface.min():.1f} K')
print(f'T[0,:]:    peak={out.T[0,:].max():.1f} K, min={out.T[0,:].min():.1f} K')
print(f'Delta (true surface vs cell-0): peak={out.T_surface.max()-out.T[0,:].max():.1f} K')

# Check no drop-off at t=0
d01 = abs(out.T[0,1] - out.T[0,0])
print(f'T[0,0]={out.T[0,0]:.1f}, T[0,1]={out.T[0,1]:.1f}, diff={d01:.1f} K')
print(f'Drop-off check: {"PASS (no drop-off)" if d01 < 5.0 else "FAIL (drop-off still present)"}')

# Check convergence
print(f'Converged: {out.converged}, cycles: {out.n_spinup_cycles}')
print(f'Last cycle max dT: {out.diagnostics.get("last_cycle_max_dT", "N/A")}')
