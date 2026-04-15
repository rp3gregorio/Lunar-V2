"""Illumination tests — horizon tracer on a synthetic crater DEM.

The primary check is that the ray-march horizon tracer reproduces the
closed-form answer for a circular-rim crater: from the center, the rim
subtends the same apparent elevation angle in every azimuth direction.
"""

from __future__ import annotations

import numpy as np

from lunar.illumination import (
    azimuth_bin_centers,
    compute_horizon,
    is_illuminated,
    synthetic_crater_dem,
)


def test_horizon_on_flat_dem_is_zero():
    n = 41
    pixel = 20.0
    x = np.arange(n) * pixel
    y = np.arange(n)[::-1] * pixel
    from lunar.illumination import DEM

    flat = DEM(
        elevation=np.zeros((n, n), dtype=np.float64),
        x=x,
        y=y,
        crs="synthetic",
    )
    horizon = compute_horizon(flat, n_azimuth=36, max_range_m=400.0, step_m=20.0)
    assert horizon.shape == (n, n, 36)
    # All elevation angles must be <= 0 (we clamp at 0 inside the tracer).
    assert float(horizon.max()) == 0.0


def test_horizon_on_synthetic_crater_center():
    """From the center of a circular-rim crater, the horizon elevation
    angle in every azimuth must equal arctan(rim_height / rim_radius)."""
    rim_radius = 400.0
    rim_height = 200.0
    dem = synthetic_crater_dem(
        n=81,
        pixel_m=20.0,
        rim_radius_m=rim_radius,
        rim_height_m=rim_height,
        rim_width_m=30.0,
    )
    # Step finer than the rim width so the tracer actually samples the peak.
    horizon = compute_horizon(
        dem, n_azimuth=72, max_range_m=700.0, step_m=5.0
    )
    ci = dem.elevation.shape[0] // 2
    cj = dem.elevation.shape[1] // 2
    expected = np.arctan2(rim_height, rim_radius)
    center_profile = horizon[ci, cj]
    # All azimuths should see the rim at the same apparent elevation.
    assert np.allclose(center_profile, expected, atol=0.02), (
        f"max dev = {np.max(np.abs(center_profile - expected)):.4f} rad, "
        f"expected {expected:.4f} rad"
    )


def test_is_illuminated_flat_horizon_sun_above():
    az_centers = azimuth_bin_centers(36)
    horizon_profile = np.zeros(36)
    # Sun 10 deg above flat horizon — illuminated.
    assert is_illuminated(
        solar_elev=np.deg2rad(10.0),
        solar_azimuth=np.deg2rad(180.0),
        horizon_profile=horizon_profile,
        az_angles=az_centers,
    )
    # Sun below local horizon — not illuminated.
    assert not is_illuminated(
        solar_elev=np.deg2rad(-1.0),
        solar_azimuth=np.deg2rad(180.0),
        horizon_profile=horizon_profile,
        az_angles=az_centers,
    )


def test_is_illuminated_respects_horizon():
    az_centers = azimuth_bin_centers(36)
    horizon_profile = np.zeros(36)
    # Tall obstruction to the south (azimuth ~180 deg).
    south_idx = int(np.argmin(np.abs(az_centers - np.pi)))
    horizon_profile[south_idx] = np.deg2rad(30.0)
    # Sun 10 deg up, due south — blocked.
    assert not is_illuminated(
        solar_elev=np.deg2rad(10.0),
        solar_azimuth=np.pi,
        horizon_profile=horizon_profile,
        az_angles=az_centers,
    )
    # Sun 40 deg up, due south — above the obstruction.
    assert is_illuminated(
        solar_elev=np.deg2rad(40.0),
        solar_azimuth=np.pi,
        horizon_profile=horizon_profile,
        az_angles=az_centers,
    )
