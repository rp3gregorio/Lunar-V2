"""Tests for ice stability depth and sublimation physics.

Validates the Murphy & Koop (2005) saturation vapor pressure,
the Hertz-Knudsen sublimation rate, and the z_star finder.
"""

from __future__ import annotations

import numpy as np
import pytest

from lunar.ice_stability import (
    ice_stability_depth,
    saturation_vapor_pressure,
    sublimation_rate,
    sublimation_rate_mm_per_Gyr,
)


class TestSaturationVaporPressure:
    def test_at_273K_matches_triple_point(self):
        """At 273.15 K, P_sat should be ~611 Pa (triple point of water)."""
        P = saturation_vapor_pressure(np.array([273.15]))
        assert 600.0 < float(P[0]) < 620.0

    def test_monotonically_increasing(self):
        """P_sat must increase with temperature."""
        T = np.linspace(110.0, 270.0, 100)
        P = saturation_vapor_pressure(T)
        assert np.all(np.diff(P) > 0)

    def test_extremely_cold_is_negligible(self):
        """At 50 K, sublimation pressure is effectively zero."""
        P = saturation_vapor_pressure(np.array([50.0]))
        assert float(P[0]) < 1e-30


class TestSublimationRate:
    def test_positive(self):
        """Sublimation rate must be non-negative for all T > 0."""
        T = np.linspace(50.0, 300.0, 100)
        E = sublimation_rate(T)
        assert np.all(E >= 0)

    def test_increases_with_temperature(self):
        """Hotter surface = faster sublimation."""
        T = np.linspace(100.0, 200.0, 50)
        E = sublimation_rate(T)
        assert np.all(np.diff(E) > 0)

    def test_mm_per_Gyr_at_110K(self):
        """At ~110 K, loss rate should be on the order of mm/Gyr
        (the regime where the Schorghofer threshold lives)."""
        rate = sublimation_rate_mm_per_Gyr(np.array([110.0]))
        # At 110 K the rate is significant but finite
        assert float(rate[0]) > 1e-3
        assert float(rate[0]) < 1e12

    def test_at_50K_effectively_zero(self):
        """At 50 K, ice loss is negligible over Gyr timescales."""
        rate = sublimation_rate_mm_per_Gyr(np.array([50.0]))
        assert float(rate[0]) < 1e-10  # way below 1 mm/Gyr


class TestIceStabilityDepth:
    def test_cold_profile_surface_stable(self):
        """A uniformly cold profile (50 K) has ice stable at the surface."""
        z = np.linspace(0, 3.0, 100)
        T_mean = np.full_like(z, 50.0)
        z_star = ice_stability_depth(z, T_mean)
        assert z_star == 0.0

    def test_hot_profile_unstable_everywhere(self):
        """A uniformly hot profile (300 K) has no stable ice."""
        z = np.linspace(0, 3.0, 100)
        T_mean = np.full_like(z, 300.0)
        z_star = ice_stability_depth(z, T_mean)
        assert z_star == float("inf")

    def test_transition_profile_finds_crossing(self):
        """A profile that transitions from hot surface to cold deep
        interior should find z_star between the extremes."""
        z = np.linspace(0, 2.0, 200)
        # Surface at 200 K (unstable), exponential decay to 50 K at depth
        T_mean = 50.0 + 150.0 * np.exp(-z / 0.3)
        z_star = ice_stability_depth(z, T_mean)
        assert 0.0 < z_star < 2.0
        # At z_star, T should be in the regime where loss rate ~ 1 mm/Gyr
        T_at_zstar = np.interp(z_star, z, T_mean)
        assert 80.0 < T_at_zstar < 130.0  # physically reasonable

    def test_shape_mismatch_raises(self):
        """z and T_mean must have the same shape."""
        with pytest.raises(ValueError, match="same shape"):
            ice_stability_depth(
                np.linspace(0, 1, 10),
                np.full(20, 100.0),
            )

    def test_threshold_sensitivity(self):
        """Stricter threshold (lower loss rate) should push z_star deeper."""
        z = np.linspace(0, 2.0, 200)
        T_mean = 50.0 + 150.0 * np.exp(-z / 0.3)
        z_star_1 = ice_stability_depth(z, T_mean, loss_threshold_mm_per_Gyr=1.0)
        z_star_01 = ice_stability_depth(z, T_mean, loss_threshold_mm_per_Gyr=0.1)
        # Stricter threshold → deeper stability depth
        assert z_star_01 > z_star_1
