"""Quick test of grid fix and solver T_surface output."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from lunar.solver import PixelInputs, solve_pixel
from lunar.grid import make_geometric_grid
import numpy as np

# Correct grid (growth=0.08 → dz *= 1.08 each layer)
grid = make_geometric_grid(z_max=3.0, dz0=0.002, growth=0.08)
print(f'Correct grid: {grid.n_layers} layers, z[0]={grid.z_mid[0]*100:.3f} cm, z[-1]={grid.z_mid[-1]:.2f} m')

# Buggy grid (growth=1.08 → dz *= 2.08 each layer!)
grid_bug = make_geometric_grid(z_max=10.0, dz0=0.003, growth=1.08)
print(f'Buggy grid:   {grid_bug.n_layers} layers, z[0]={grid_bug.z_mid[0]*100:.3f} cm, z[-1]={grid_bug.z_mid[-1]:.2f} m')

# Quick solver test with correct grid
T_LUNAR = 27.321661 * 86400.0
N_t = int(T_LUNAR / 600.0) + 1
t = np.linspace(0.0, T_LUNAR, N_t)
phase = 2.0 * np.pi * t / T_LUNAR
Q = 1361.0 * np.maximum(0.0, np.cos(phase))

inp = PixelInputs(grid=grid, t=t, bc_mode='radiative', insolation=Q,
                  n_lunations_spinup=3, spinup_tol_K=0.1)
out = solve_pixel(inp)
print(f'\nT_surface shape: {out.T_surface.shape}')
print(f'T_surface peak: {out.T_surface.max():.1f} K, min: {out.T_surface.min():.1f} K')
print(f'T[0,:] peak:    {out.T[0,:].max():.1f} K, min: {out.T[0,:].min():.1f} K')
print(f'ΔT (true surface vs cell-0): {abs(out.T_surface.max()-out.T[0,:].max()):.1f} K')
print('\nALL OK')
