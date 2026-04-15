"""1D subsurface heat-equation solver.

This module hosts the per-pixel thermal solver. It solves

    rho(z) * c_p(T) * dT/dt = d/dz ( K(T, z) * dT/dz )

on a geometric depth grid with a non-linear radiative surface boundary
and a geothermal-flux bottom boundary.

Status
------
The numerical scaffolding (Crank-Nicolson tridiagonal assembly) is in
place, but the non-linear surface coupling and the property-update
cycle with :mod:`lunar.properties` still need to be wired in before the
solver can produce publishable temperatures. A Numba ``@njit`` fast path
will replace the NumPy reference implementation once the math is
validated against the Apollo 15/17 benchmarks
(``T_mean(1 m) ~ 252 / 255 K``, see SKILL.md).

The public entry point is :func:`solve_pixel`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .constants import EMISSIVITY_DEFAULT, Q_B_SOUTH_POLAR, SIGMA_SB
from .grid import DepthGrid


@dataclass
class PixelInputs:
    """All inputs required to run the 1D solver at one DEM pixel."""

    grid: DepthGrid
    insolation: np.ndarray  # net downward solar flux [W m^-2], shape (N_t,)
    t: np.ndarray  # time samples [s], shape (N_t,)
    albedo: float
    emissivity: float = EMISSIVITY_DEFAULT
    Q_b: float = Q_B_SOUTH_POLAR
    conductivity: Callable[..., np.ndarray] | None = None
    density: Callable[..., np.ndarray] | None = None
    specific_heat: Callable[..., np.ndarray] | None = None
    phi_ice: np.ndarray | None = None  # shape (N_z,) if ice-coupled model


@dataclass
class PixelOutputs:
    """Solver output for one DEM pixel (matches TSUKIMI coupling format)."""

    T: np.ndarray  # shape (N_z, N_t) [K]
    z: np.ndarray  # shape (N_z,) [m]
    t: np.ndarray  # shape (N_t,) [s]
    iterations: int = 0
    diagnostics: dict = field(default_factory=dict)


def surface_energy_balance_residual(
    T_s: float,
    insolation: float,
    albedo: float,
    emissivity: float,
    K_surf: float,
    dz_surf: float,
    T_subsurf: float,
) -> float:
    """Residual of the non-linear surface energy balance.

    Solve :math:`R(T_s) = 0` where

    .. math::

        R(T_s) = (1-A)\\,S_{\\mathrm{net}}
                 - \\varepsilon \\sigma T_s^4
                 - K \\frac{T_s - T_{\\mathrm{sub}}}{\\Delta z / 2}

    This is a convenience helper that :func:`solve_pixel` uses inside
    a Newton iteration at each time step. Units: SI throughout.
    """
    radiative_in = (1.0 - albedo) * insolation
    radiative_out = emissivity * SIGMA_SB * T_s**4
    conductive = K_surf * (T_s - T_subsurf) / (0.5 * dz_surf)
    return radiative_in - radiative_out - conductive


def _assemble_tridiagonal(
    grid: DepthGrid,
    K: np.ndarray,
    rho_cp: np.ndarray,
    dt: float,
    theta: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the Crank-Nicolson tridiagonal matrix (a, b, c).

    Implements the finite-volume discretisation of
    ``rho * c_p * dT/dt = d/dz (K dT/dz)`` on non-uniform cell-centered
    grid :attr:`DepthGrid.z_mid` with face conductivities at
    :attr:`DepthGrid.z_face`. Face conductivities are taken as the
    harmonic mean of the two adjacent cell values.

    Returns
    -------
    (a, b, c) : tuple of np.ndarray
        Sub-, main-, and super-diagonal of the implicit operator
        ``(I + theta * dt * L)``. The corresponding explicit operator
        ``(I - (1-theta) * dt * L)`` uses the same weights with sign
        flipped on the off-diagonals; we let the caller apply it.
    """
    n = grid.n_layers
    dz = grid.dz
    z_face = grid.z_face

    # Harmonic-mean face conductivities between adjacent cells.
    K_face = np.empty(n + 1)
    K_face[0] = K[0]
    K_face[-1] = K[-1]
    for i in range(1, n):
        if K[i - 1] == 0 or K[i] == 0:
            K_face[i] = 0.0
        else:
            K_face[i] = 2.0 * K[i - 1] * K[i] / (K[i - 1] + K[i])

    # Distance between cell centers (denominator of the finite-difference flux)
    # Cell i has thickness dz[i] and spans z_face[i] .. z_face[i+1].
    dz_c = np.empty(n + 1)
    dz_c[0] = 0.5 * dz[0]
    dz_c[-1] = 0.5 * dz[-1]
    for i in range(1, n):
        dz_c[i] = 0.5 * (dz[i - 1] + dz[i])

    # Volumetric heat capacity per cell
    cap = rho_cp * dz  # [J m^-2 K^-1]

    a = np.zeros(n)
    b = np.zeros(n)
    c = np.zeros(n)

    for i in range(n):
        flux_left = K_face[i] / dz_c[i] if i > 0 else 0.0
        flux_right = K_face[i + 1] / dz_c[i + 1] if i < n - 1 else 0.0
        a[i] = -theta * dt * flux_left / cap[i]
        c[i] = -theta * dt * flux_right / cap[i]
        b[i] = 1.0 - (a[i] + c[i])

    return a, b, c


def solve_pixel(inputs: PixelInputs) -> PixelOutputs:  # pragma: no cover
    """Drive the 1D thermal solver for one pixel over ``inputs.t``.

    Not yet fully implemented. The remaining work is:

    1. Spin-up loop (>= 10 lunations) with a convergence check
       ``max |T^{k+1} - T^k| < 0.01 K`` between successive lunations.
    2. Non-linear surface BC via Newton iteration at each time step
       (uses :func:`surface_energy_balance_residual`).
    3. Property-update call to :mod:`lunar.properties` between steps
       (T-dependent K via the radiative term, and optional ice coupling).
    4. Numba ``@njit`` fast path for the tridiagonal sweep.

    Raises
    ------
    NotImplementedError
        Until the integration and Newton iteration are wired up and
        validated against the SKILL.md benchmarks.
    """
    raise NotImplementedError(
        "solve_pixel: tridiagonal assembly is in place but the non-linear "
        "surface BC and spin-up loop still need to be wired. See the "
        "physics agent in .claude/skills/agents/physics.md for the "
        "audit checklist."
    )
