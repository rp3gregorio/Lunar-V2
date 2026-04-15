"""DEM processing, horizon tracing, and secondary illumination.

Primary reference: Mazarico et al. (2011), Icarus 211, 1066-1081.
Primary DEM product: ``LDEM_80S_20MPP_ADJ.TIF`` (20 m / pixel, 80-90 S),
Barker et al. (2023), https://pgda.gsfc.nasa.gov/products/90 .

This module is intentionally a scaffold: each function has the signature
the pipeline will call, but raises :class:`NotImplementedError` until the
horizon tracer and view-factor computation are written. See the
illumination agent in ``.claude/skills/agents/illumination.md`` for the
algorithmic details (nested grid, SPICE ephemeris, reciprocity check).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class DEM:
    """Projected digital elevation model subset."""

    elevation: np.ndarray  # [m], shape (H, W)
    x: np.ndarray  # easting [m], shape (W,)
    y: np.ndarray  # northing [m], shape (H,)
    crs: str  # e.g., 'EPSG:...' polar stereographic


def load_lola_dem(path: str | Path) -> DEM:  # pragma: no cover
    """Load a LOLA DEM GeoTIFF (rasterio / rioxarray).

    Not implemented — awaiting data-ingestion layer.
    """
    raise NotImplementedError(
        "load_lola_dem: implement via rasterio / rioxarray once the "
        "DEM location is fixed in the pipeline config."
    )


def compute_horizon(
    dem: DEM,
    n_azimuth: int = 720,
    nested_dems: list[DEM] | None = None,
) -> np.ndarray:  # pragma: no cover
    """Compute horizon elevation angles per pixel and azimuth.

    Returns an array of shape ``(dem.elevation.shape..., n_azimuth)``
    giving the maximum elevation angle of the horizon in each azimuth
    direction, in radians. Uses the Mazarico et al. (2011) ray-marching
    algorithm with a nested-grid hand-off for far-field shadows.

    Per the illumination agent's audit checklist: n_azimuth must be
    >= 360 (720 recommended), and nested_dems must be supplied at the
    south pole so that distant crater rims >100 km away are captured.
    """
    raise NotImplementedError(
        "compute_horizon: Mazarico (2011) horizon tracer not yet written."
    )


def is_illuminated(
    solar_elev: float,
    solar_azimuth: float,
    horizon_profile: np.ndarray,
    az_angles: np.ndarray,
) -> bool:
    """Binary direct-illumination check for a single pixel and time step.

    Parameters
    ----------
    solar_elev, solar_azimuth : float
        Solar elevation and azimuth [rad].
    horizon_profile : np.ndarray
        Per-azimuth maximum elevation [rad], shape ``(n_azimuth,)``.
    az_angles : np.ndarray
        Azimuth bin centers [rad], shape ``(n_azimuth,)``.
    """
    if solar_elev <= 0.0:
        return False
    idx = int(np.searchsorted(az_angles, solar_azimuth)) % az_angles.size
    return solar_elev > horizon_profile[idx]


def compute_view_factors(dem: DEM) -> np.ndarray:  # pragma: no cover
    """Sparse PSR-to-sunlit view-factor matrix.

    Implementation plan (see illumination agent, audit checklist):
      * Phase 1 — sparse: only pixels inside a PSR as receivers.
      * Phase 2 — distance cutoff at ~2-3 km (1/r^2 falloff).
      * Phase 3 — optional HODLR compression (Potter et al. 2023).

    Output must satisfy reciprocity ``A_i * F_ij == A_j * F_ji`` and
    the energy-conservation bound ``sum_j F_ij <= 1``; these are checked
    in the tests once implemented.
    """
    raise NotImplementedError(
        "compute_view_factors: see Schorghofer Planetary-Code-Collection "
        "Topo3D/fieldofview.f90 for a reference implementation."
    )
