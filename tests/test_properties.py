"""Regolith property model tests.

We check limiting behavior and known-published numbers rather than
fitting to any particular temperature — the goal is to catch regressions
against SKILL.md benchmarks and the Hayne (2017) model definition.
"""

import numpy as np
import pytest

from lunar import properties
from lunar.constants import (
    CHI_RADIATIVE,
    H_PARAMETER,
    K_DEEP,
    K_SURFACE,
    RHO_DEEP,
    RHO_SURFACE,
    T_REFERENCE,
)


# ---------- density_hayne ----------------------------------------------------


def test_density_surface_limit():
    assert properties.density_hayne(np.array([0.0])) == pytest.approx(RHO_SURFACE)


def test_density_deep_limit():
    # Several H scale heights down — should be essentially rho_d.
    deep = properties.density_hayne(np.array([10.0 * H_PARAMETER]))
    assert deep == pytest.approx(RHO_DEEP, rel=1e-3)


def test_density_is_monotonic():
    z = np.linspace(0.0, 3.0, 100)
    rho = properties.density_hayne(z)
    assert np.all(np.diff(rho) >= 0)


# ---------- conductivity_hayne -----------------------------------------------


def test_conductivity_surface_cold_limit():
    # At T=0 K the radiative term vanishes, leaving only K_s at the surface.
    K = properties.conductivity_hayne(np.array([0.0]), np.array([0.0]))
    assert K == pytest.approx(K_SURFACE)


def test_conductivity_deep_cold_limit():
    # Deep and cold -> K_d.
    K = properties.conductivity_hayne(
        np.array([0.0]), np.array([10.0 * H_PARAMETER])
    )
    assert K == pytest.approx(K_DEEP, rel=1e-3)


def test_conductivity_radiative_term_at_reference_T():
    # At T = T_REFERENCE the radiative factor is (1 + chi).
    K = properties.conductivity_hayne(
        np.array([T_REFERENCE]), np.array([0.0])
    )
    assert K == pytest.approx(K_SURFACE * (1.0 + CHI_RADIATIVE))


# ---------- ice-coupled (novel) ----------------------------------------------


def test_ice_coupled_reduces_to_dry_when_phi_zero():
    T = np.full(5, 100.0)
    z = np.linspace(0.0, 0.1, 5)
    phi = np.zeros(5)
    K_ice = properties.conductivity_icy(T, z, phi)
    K_dry = properties.conductivity_martinez(T, z)
    np.testing.assert_allclose(K_ice, K_dry)


def test_ice_coupled_increases_K_for_full_ice():
    T = np.full(5, 100.0)
    z = np.linspace(0.0, 0.1, 5)
    phi = np.ones(5)
    K_ice = properties.conductivity_icy(T, z, phi)
    # Klinger (1980): K_ice(100 K) = 5.67 W/m/K.
    assert np.all(K_ice > 5.0)


def test_density_icy_adds_ice_mass():
    z = np.array([0.0])
    phi = np.array([0.3])
    rho = properties.density_icy(z, phi)
    # Adds 0.3 * 917 kg/m^3 to dry regolith.
    assert rho[0] > RHO_SURFACE


# ---------- specific heat (intentionally stubbed) ----------------------------


def test_specific_heat_refuses_to_fabricate():
    # Per the project scientific-integrity rule, this must raise until a
    # verified polynomial from heat1d is wired in.
    with pytest.raises(NotImplementedError):
        properties.specific_heat(np.array([200.0]))


# ---------- model registry ---------------------------------------------------


def test_get_conductivity_model_valid_names():
    for name in ("hayne", "martinez", "ice_coupled"):
        assert callable(properties.get_conductivity_model(name))


def test_get_conductivity_model_rejects_unknown():
    with pytest.raises(ValueError):
        properties.get_conductivity_model("bogus_model")
