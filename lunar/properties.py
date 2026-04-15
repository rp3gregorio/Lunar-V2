"""Regolith thermal property models.

Three models are provided, all sharing the same public signature so they
can be swapped through :func:`get_property_model`:

A. ``hayne``    — baseline, Hayne et al. (2017).
B. ``martinez`` — low-T contact-conductivity correction,
   Martinez & Siegler (2021) JGR:Planets 126, e2021JE006829.
C. ``ice_coupled`` — novel ice-coupled properties
   (Gregorio 2026, in prep). The ice volume fraction ``phi_ice``
   modifies K, rho, and c_p; this is the project's novel contribution.

Scientific-integrity rules (see .claude/skills/SKILL.md):
  * Never fabricate numerical values.
  * Always cite the source in the docstring.
  * Specific-heat polynomial coefficients MUST come from the heat1d
    source (github.com/phayne/heat1d) — they are intentionally not
    hardcoded here until that verification step is done.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from .constants import (
    CHI_RADIATIVE,
    H_PARAMETER,
    K_DEEP,
    K_SURFACE,
    RHO_DEEP,
    RHO_ICE,
    RHO_SURFACE,
    T_REFERENCE,
)

# ---------------------------------------------------------------------------
# Density
# ---------------------------------------------------------------------------


def density_hayne(
    z: np.ndarray,
    rho_s: float = RHO_SURFACE,
    rho_d: float = RHO_DEEP,
    H: float = H_PARAMETER,
) -> np.ndarray:
    """Bulk density [kg m^-3] vs depth.

    Hayne et al. (2017), Eq. 5::

        rho(z) = rho_d - (rho_d - rho_s) * exp(-z / H)

    Parameters
    ----------
    z : np.ndarray
        Depth [m], any shape.
    rho_s, rho_d : float
        Surface and deep bulk density [kg m^-3].
    H : float
        Density/conductivity scale height [m].
    """
    z = np.asarray(z, dtype=np.float64)
    return rho_d - (rho_d - rho_s) * np.exp(-z / H)


def density_icy(
    z: np.ndarray,
    phi_ice: np.ndarray,
    rho_s: float = RHO_SURFACE,
    rho_d: float = RHO_DEEP,
    H: float = H_PARAMETER,
    rho_ice: float = RHO_ICE,
) -> np.ndarray:
    """Bulk density [kg m^-3] with ice filling a fraction of pore space.

    Novel (Gregorio 2026, in prep). Assumes ice adds mass without
    changing the matrix porosity — i.e., ice occupies void space that
    would otherwise be vacuum.

    Parameters
    ----------
    z : np.ndarray
        Depth [m].
    phi_ice : np.ndarray
        Ice volume fraction in [0, 1] at each depth, same shape as ``z``.
    """
    rho_dry = density_hayne(z, rho_s, rho_d, H)
    return rho_dry + np.asarray(phi_ice, dtype=np.float64) * rho_ice


# ---------------------------------------------------------------------------
# Thermal conductivity
# ---------------------------------------------------------------------------


def conductivity_hayne(
    T: np.ndarray,
    z: np.ndarray,
    Ks: float = K_SURFACE,
    Kd: float = K_DEEP,
    H: float = H_PARAMETER,
    chi: float = CHI_RADIATIVE,
) -> np.ndarray:
    """Thermal conductivity K(T, z) [W m^-1 K^-1] — Hayne baseline.

    Hayne et al. (2017), Eq. 4::

        K_c(z) = K_d - (K_d - K_s) * exp(-z / H)
        K(T, z) = K_c(z) * (1 + chi * (T / 350 K)^3)

    The radiative term ``chi * (T/350)^3`` MUST be present; omitting it
    is one of the known bugs listed in SKILL.md.
    """
    T = np.asarray(T, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    Kc = Kd - (Kd - Ks) * np.exp(-z / H)
    return Kc * (1.0 + chi * (T / T_REFERENCE) ** 3)


def conductivity_martinez(
    T: np.ndarray,
    z: np.ndarray,
    Ks: float = K_SURFACE,
    Kd: float = K_DEEP,
    H: float = H_PARAMETER,
    chi: float = CHI_RADIATIVE,
) -> np.ndarray:
    """Thermal conductivity with Martinez & Siegler (2021) low-T correction.

    Martinez, B. & Siegler, M. A. (2021). JGR:Planets 126, e2021JE006829.
    Code: https://zenodo.org/records/12586656

    .. warning::
       The exact functional form below (``f_T = (T/150)^1.5`` for T<150 K)
       is a placeholder approximation. Before using this model for any
       published result, replace it with the fit from Eqs. 7-9 of the
       Martinez & Siegler paper — the placeholder is flagged here rather
       than hidden so that the physics auditor (skill agent) will catch it.
    """
    T = np.asarray(T, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    Kc = Kd - (Kd - Ks) * np.exp(-z / H)
    # TODO(physics-audit): replace with Martinez & Siegler (2021) Eqs. 7-9.
    f_T = np.where(T < 150.0, (T / 150.0) ** 1.5, 1.0)
    return Kc * f_T * (1.0 + chi * (T / T_REFERENCE) ** 3)


def conductivity_icy(
    T: np.ndarray,
    z: np.ndarray,
    phi_ice: np.ndarray,
    Ks: float = K_SURFACE,
    Kd: float = K_DEEP,
    H: float = H_PARAMETER,
    chi: float = CHI_RADIATIVE,
) -> np.ndarray:
    """Ice-coupled thermal conductivity [W m^-1 K^-1] — NOVEL.

    Gregorio (2026, in prep). The novel contribution of Lunar-Clean v2.

    When ice fills pore space, effective K increases by several orders
    of magnitude relative to dry regolith. Crystalline ice Ih follows
    ``K_ice(T) ~ 567 / T`` [W m^-1 K^-1] (Klinger 1980, Science 209,
    271-272). At 100 K this gives ~5.67 W m^-1 K^-1 vs ~10^-3 for dry
    regolith — a factor of ~10^3.

    Mixing rule
    -----------
    We use a volumetric arithmetic mean as the default::

        K_eff = (1 - phi_ice) * K_dry + phi_ice * K_ice

    The Hashin-Shtrikman lower bound is also a defensible choice; the
    sensitivity of the ice-stability depth to this choice is a planned
    study (Chapter 6 of the thesis).

    Parameters
    ----------
    phi_ice : np.ndarray
        Ice volume fraction in [0, 1] at each depth.
    """
    T = np.asarray(T, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    phi = np.asarray(phi_ice, dtype=np.float64)
    K_dry = conductivity_martinez(T, z, Ks, Kd, H, chi)
    # Klinger (1980); guard against T = 0 K (unphysical in this project).
    K_ice = 567.0 / np.maximum(T, 1.0)
    return (1.0 - phi) * K_dry + phi * K_ice


# ---------------------------------------------------------------------------
# Specific heat
# ---------------------------------------------------------------------------


def specific_heat(T: np.ndarray) -> np.ndarray:
    """Regolith specific heat capacity [J kg^-1 K^-1].

    Hayne et al. (2017) use a polynomial fit to Hemingway et al. (1981)
    lunar sample calorimetry. Multiple coefficient sets exist in the
    literature; the authoritative source is the ``heat1d`` code at
    https://github.com/phayne/heat1d.

    This stub raises :class:`NotImplementedError` on purpose: per the
    project scientific-integrity rule, we refuse to hardcode coefficients
    from memory. Populate this function with the verified polynomial
    from heat1d before running any thermal simulation.
    """
    raise NotImplementedError(
        "specific_heat(T) must be populated with the verified polynomial "
        "from github.com/phayne/heat1d. Do not copy coefficients from memory."
    )


def specific_heat_icy(T: np.ndarray, phi_ice: np.ndarray) -> np.ndarray:
    """Effective specific heat with ice-filled pore space.

    Regolith contribution from :func:`specific_heat`; ice contribution
    from NIST / Giauque & Stout (1936). The linear approximation
    ``c_p,ice(T) ~ 7.49 * T + 90`` [J kg^-1 K^-1] is valid over
    40-270 K but should be verified against NIST before publication.
    """
    cp_reg = specific_heat(T)
    phi = np.asarray(phi_ice, dtype=np.float64)
    cp_ice = 7.49 * np.asarray(T, dtype=np.float64) + 90.0  # TODO: NIST check
    return (1.0 - phi) * cp_reg + phi * cp_ice


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

PropertyModel = Callable[..., np.ndarray]

_CONDUCTIVITY_MODELS: dict[str, PropertyModel] = {
    "hayne": conductivity_hayne,
    "martinez": conductivity_martinez,
    "ice_coupled": conductivity_icy,
}


def get_conductivity_model(name: str) -> PropertyModel:
    """Look up a conductivity model by name.

    Valid names are ``'hayne'``, ``'martinez'``, and ``'ice_coupled'``.
    """
    try:
        return _CONDUCTIVITY_MODELS[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown conductivity model {name!r}. "
            f"Valid options: {sorted(_CONDUCTIVITY_MODELS)}"
        ) from exc
