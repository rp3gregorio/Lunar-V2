"""DEM processing, horizon tracing, and secondary illumination.

Primary reference: Mazarico et al. (2011), Icarus 211, 1066-1081.
Primary DEM product: ``LDEM_80S_20MPP_ADJ.TIF`` (20 m / pixel, 80-90 S),
Barker et al. (2023), https://pgda.gsfc.nasa.gov/products/90 .

This module implements the horizon tracer used by the illumination
pipeline. The view-factor computation is still a scaffold pending the
Phase 1 (sparse) implementation — see
``.claude/skills/agents/illumination.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    from numba import njit, prange
    _HAVE_NUMBA = True
except ImportError:  # pragma: no cover
    _HAVE_NUMBA = False

    def njit(*args, **kwargs):  # type: ignore[no-redef]
        if len(args) == 1 and callable(args[0]):
            return args[0]

        def wrap(fn):
            return fn

        return wrap

    def prange(*args, **kwargs):  # type: ignore[no-redef]
        return range(*args, **kwargs)


@dataclass
class DEM:
    """Projected digital elevation model subset.

    Attributes
    ----------
    elevation : np.ndarray
        Elevation values [m], shape ``(H, W)`` where rows index
        northing (``y``) and columns index easting (``x``).
    x, y : np.ndarray
        1-D coordinate arrays [m]. Must be uniformly spaced. ``y`` is
        ordered *north-to-south* in the raster, i.e. ``y[0] > y[-1]``.
    crs : str
        Coordinate reference system identifier, e.g.
        ``'EPSG:32761'`` (south polar stereographic).
    """

    elevation: np.ndarray
    x: np.ndarray
    y: np.ndarray
    crs: str

    @property
    def dx(self) -> float:
        return float(abs(self.x[1] - self.x[0]))

    @property
    def dy(self) -> float:
        return float(abs(self.y[1] - self.y[0]))


def load_lola_dem(
    path: str | Path,
    window: tuple[int, int, int, int] | None = None,
    subsample: int = 1,
) -> DEM:
    """Load a LOLA polar-stereographic DEM GeoTIFF via rasterio.

    Parameters
    ----------
    path : str or Path
        GeoTIFF to load. Designed for the PGDA product 90 files
        (``LDEM_80S_{20,40,80}MPP_ADJ.TIF``) but works for any
        rasterio-readable single-band DEM.
    window : (row_start, row_stop, col_start, col_stop), optional
        Pixel window to read. If None, the full raster is read.
        Rows/cols are 0-indexed and exclusive on the stop side.
    subsample : int, default 1
        Integer decimation factor along both axes. ``subsample=4``
        reads every fourth pixel; useful for quicklooks of the 20 MPP
        product (~43 Mpix) on memory-constrained hosts.

    Returns
    -------
    DEM
        Elevation [m] with x/y 1-D coordinate vectors in the DEM's
        native projected CRS (polar stereographic for the PGDA files).

    Notes
    -----
    The PGDA polar DEMs use EPSG-less custom "Moon (2015) - Sphere /
    Ocentric / South Polar" CRS with ``latitude_of_origin = -90``,
    ``central_meridian = 0``, sphere radius 1 737 400 m, and axes in
    metres. ``nodata`` is NaN.
    """
    try:
        import rasterio  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "load_lola_dem requires rasterio. "
            "Install with `pip install 'lunar-clean[geo]'` or "
            "`pip install rasterio`."
        ) from exc

    path = Path(path)
    with rasterio.open(path) as src:
        if window is not None:
            r0, r1, c0, c1 = window
            rio_window = rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0)
            elev = src.read(1, window=rio_window)
            win_transform = src.window_transform(rio_window)
        else:
            elev = src.read(1)
            win_transform = src.transform

        if subsample > 1:
            elev = elev[::subsample, ::subsample]
            # Scale the affine so world coords still match the pixels.
            win_transform = win_transform * win_transform.scale(subsample, subsample)

        crs_str = src.crs.to_wkt() if src.crs is not None else ""

    # Build 1-D coordinate arrays. rasterio affine uses
    # (a, b, c, d, e, f): x = a*col + b*row + c, y = d*col + e*row + f.
    # For a north-up raster b = 0, d = 0.
    a, b, c, _d, e, f = (
        win_transform.a,
        win_transform.b,
        win_transform.c,
        win_transform.d,
        win_transform.e,
        win_transform.f,
    )
    H, W = elev.shape
    cols = np.arange(W, dtype=np.float64) + 0.5  # pixel centers
    rows = np.arange(H, dtype=np.float64) + 0.5
    x = a * cols + c
    y = e * rows + f

    # Cast to float64 for downstream math; rasterio gives float32.
    elev64 = elev.astype(np.float64, copy=False)
    return DEM(elevation=elev64, x=x, y=y, crs=crs_str)


# ---------------------------------------------------------------------------
# Horizon tracing (Mazarico et al. 2011)
# ---------------------------------------------------------------------------


@njit(cache=True)
def _bilinear_sample(elev: np.ndarray, fx: float, fy: float) -> float:
    """Bilinear sample of a 2-D elevation array at fractional (row, col)
    indices. Returns NaN outside the grid.
    """
    H, W = elev.shape
    if fy < 0.0 or fy > H - 1.0 or fx < 0.0 or fx > W - 1.0:
        return np.nan
    i0 = int(np.floor(fy))
    j0 = int(np.floor(fx))
    i1 = min(i0 + 1, H - 1)
    j1 = min(j0 + 1, W - 1)
    wy = fy - i0
    wx = fx - j0
    return (
        (1.0 - wy) * (1.0 - wx) * elev[i0, j0]
        + (1.0 - wy) * wx * elev[i0, j1]
        + wy * (1.0 - wx) * elev[i1, j0]
        + wy * wx * elev[i1, j1]
    )


@njit(cache=True, parallel=True)
def _horizon_grid(
    elev: np.ndarray,
    dx: float,
    dy: float,
    n_az: int,
    max_range_m: float,
    step_m: float,
) -> np.ndarray:
    """Trace the horizon at every DEM pixel.

    Parameters
    ----------
    elev : np.ndarray, shape (H, W)
        Elevation [m]. Row index = northing index (north-to-south).
    dx, dy : float
        Pixel spacing [m] in the x (easting) and y (northing) directions.
    n_az : int
        Number of azimuth bins (equally spaced in [0, 2*pi)).
    max_range_m : float
        How far out to march the ray [m]. Mazarico (2011) recommends
        at least the horizontal range to the tallest off-grid feature;
        for polar crater work ~100 km is typical.
    step_m : float
        Ray-march step size [m]. Should be smaller than ``min(dx, dy)``
        to avoid aliasing across narrow rim features.

    Returns
    -------
    horizon : np.ndarray, shape (H, W, n_az)
        Maximum elevation angle of the horizon in each azimuth
        direction, in radians. 0 means a flat horizon; pi/2 means an
        obstruction is directly overhead.
    """
    H, W = elev.shape
    horizon = np.zeros((H, W, n_az), dtype=np.float64)
    n_steps = int(max_range_m / step_m)

    # Precompute per-azimuth unit vectors in world coordinates. Azimuth
    # is measured clockwise from north, matching planetary convention.
    sin_az = np.empty(n_az, dtype=np.float64)
    cos_az = np.empty(n_az, dtype=np.float64)
    for k in range(n_az):
        az = 2.0 * np.pi * k / n_az
        sin_az[k] = np.sin(az)  # east component
        cos_az[k] = np.cos(az)  # north component

    for i in prange(H):
        for j in range(W):
            z0 = elev[i, j]
            for k in range(n_az):
                # World-coordinate unit vector along this azimuth.
                vx = sin_az[k]
                vy = cos_az[k]
                max_ang = 0.0
                for s in range(1, n_steps + 1):
                    r = s * step_m
                    # Target world offset from pixel center.
                    wx = r * vx
                    wy = r * vy
                    # Convert to fractional grid indices. Row index
                    # decreases with +y (north-up raster).
                    fj = j + wx / dx
                    fi = i - wy / dy
                    z = _bilinear_sample(elev, fj, fi)
                    if np.isnan(z):
                        break
                    ang = np.arctan2(z - z0, r)
                    if ang > max_ang:
                        max_ang = ang
                horizon[i, j, k] = max_ang
    return horizon


def compute_horizon(
    dem: DEM,
    n_azimuth: int = 720,
    max_range_m: float | None = None,
    step_m: float | None = None,
    nested_dems: list[DEM] | None = None,
) -> np.ndarray:
    """Compute the horizon elevation angles per pixel and azimuth.

    Ray-marches from each pixel center outward in ``n_azimuth`` uniformly
    spaced directions, returning the maximum elevation angle in each
    direction. This is the core Mazarico et al. (2011) algorithm; the
    nested-grid extension for far-field shadows is left as a follow-up
    (``nested_dems`` is accepted for API stability but not yet used).

    Parameters
    ----------
    dem : DEM
        Input DEM. ``dem.x`` and ``dem.y`` must be uniformly spaced.
    n_azimuth : int, default 720
        Number of azimuth bins. >=360 is recommended per the illumination
        agent's audit checklist.
    max_range_m : float, optional
        Maximum ray-march range [m]. Defaults to the DEM diagonal.
    step_m : float, optional
        Ray-march step size [m]. Defaults to ``0.5 * min(dx, dy)``.
    nested_dems : list[DEM], optional
        Coarser-resolution DEMs covering a wider footprint, for the
        far-field hand-off. Not yet implemented; accepted as a no-op
        for API compatibility.

    Returns
    -------
    horizon : np.ndarray, shape ``(H, W, n_azimuth)``
        Horizon elevation angles [rad].
    """
    if nested_dems is not None:  # pragma: no cover
        # Explicit no-op for now so callers can start wiring the API.
        pass

    dx = dem.dx
    dy = dem.dy
    if step_m is None:
        step_m = 0.5 * min(dx, dy)
    if max_range_m is None:
        H, W = dem.elevation.shape
        max_range_m = float(np.hypot(W * dx, H * dy))

    return _horizon_grid(
        np.ascontiguousarray(dem.elevation, dtype=np.float64),
        float(dx),
        float(dy),
        int(n_azimuth),
        float(max_range_m),
        float(step_m),
    )


def azimuth_bin_centers(n_azimuth: int) -> np.ndarray:
    """Azimuth-bin centers [rad], measured clockwise from north."""
    return 2.0 * np.pi * np.arange(n_azimuth) / n_azimuth


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
        Solar elevation and azimuth [rad]. Azimuth is clockwise from
        north to match :func:`compute_horizon`.
    horizon_profile : np.ndarray
        Per-azimuth maximum elevation [rad], shape ``(n_azimuth,)``.
    az_angles : np.ndarray
        Azimuth bin centers [rad], shape ``(n_azimuth,)``. Must be
        monotonically increasing and span ``[0, 2*pi)``.
    """
    if solar_elev <= 0.0:
        return False
    # Wrap the solar azimuth into [0, 2*pi) then find the nearest bin.
    sa = float(solar_azimuth) % (2.0 * np.pi)
    idx = int(np.argmin(np.abs(az_angles - sa)))
    return bool(solar_elev > horizon_profile[idx])


# ---------------------------------------------------------------------------
# Synthetic test fixtures
# ---------------------------------------------------------------------------


def synthetic_crater_dem(
    n: int = 101,
    pixel_m: float = 20.0,
    rim_radius_m: float = 400.0,
    rim_height_m: float = 200.0,
    rim_width_m: float = 60.0,
) -> DEM:
    """Build a circular crater DEM for horizon-tracer unit tests.

    Produces an ``n x n`` square grid with a Gaussian rim at
    ``rim_radius_m`` from the center. The interior is flat at z=0.
    A ray from the center in any azimuth therefore hits the rim at
    ``r = rim_radius_m`` with apparent elevation angle
    ``arctan(rim_height_m / rim_radius_m)`` — a closed-form answer the
    tracer must reproduce.
    """
    half = (n - 1) / 2
    x = (np.arange(n) - half) * pixel_m
    y = (np.arange(n) - half)[::-1] * pixel_m  # north-up
    xx, yy = np.meshgrid(x, y, indexing="xy")
    r = np.hypot(xx, yy)
    elev = rim_height_m * np.exp(-((r - rim_radius_m) ** 2) / (2.0 * rim_width_m**2))
    return DEM(elevation=elev, x=x, y=y, crs="synthetic")


# ---------------------------------------------------------------------------
# View factors — still a scaffold
# ---------------------------------------------------------------------------


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
