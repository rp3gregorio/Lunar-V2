"""Ice stability depth and sublimation rates.

The ice-stability depth ``z_star`` is the shallowest depth at which the
annual-mean sublimation rate of water ice into a vacuum falls below a
loss threshold (conventionally 1 mm Gyr⁻¹ — Schorghofer & Taylor 2007,
JGR 112, E02010).

The sublimation physics follows the Hertz-Knudsen free-molecular flux:

.. math::

    E = P_{\\text{sat}}(T) \\sqrt{\\frac{m}{2\\pi k_B T}}

where ``P_sat`` is the saturation vapor pressure of ice Ih (Murphy & Koop
2005) and ``m = 2.99151e-26 kg`` is the mass of one H₂O molecule.

References
----------
* Murphy, D. M. & Koop, T. (2005), Q.J.R. Meteorol. Soc. 131, 1539-1565.
  doi:10.1256/qj.04.94 — Eq. 10 (ice Ih saturation).
* Schorghofer, N. & Taylor, G. J. (2007), JGR 112, E02010.
  doi:10.1029/2006JE002779 — loss threshold 1 mm/Gyr.
* Schorghofer, N. (2010), Icarus 208, 598-607.
  doi:10.1016/j.icarus.2010.03.022 — thermal-diffusion correction.
* Hayne, P. O. et al. (2021), Nat. Astron. 5, 169-175.
  doi:10.1038/s41550-020-01270-3 — micro cold traps & stability maps.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Physical constants for sublimation physics
# ---------------------------------------------------------------------------

#: Boltzmann constant [J K^-1] — CODATA 2018.
K_BOLTZMANN: float = 1.380649e-23

#: Mass of one H2O molecule [kg] — NIST (18.01528 g/mol / 6.02214076e23).
M_H2O: float = 2.99151e-26

#: Density of crystalline ice Ih [kg m^-3] — Feistel & Wagner (2006).
RHO_ICE: float = 917.0


# ---------------------------------------------------------------------------
# Saturation vapor pressure — Murphy & Koop (2005)
# ---------------------------------------------------------------------------


def saturation_vapor_pressure(T: np.ndarray) -> np.ndarray:
    """Saturation vapor pressure of H₂O ice Ih [Pa].

    Murphy & Koop (2005) Eq. 10, valid for 110 K < T < 273.15 K.
    Extrapolated below 110 K (pressure drops to effectively zero).

    Parameters
    ----------
    T : np.ndarray
        Temperature [K].

    Returns
    -------
    np.ndarray
        Saturation vapor pressure [Pa].

    References
    ----------
    Murphy, D. M. & Koop, T. (2005), "Review of the vapour pressures of
    ice and supercooled water for atmospheric applications", Q.J.R.
    Meteorol. Soc. 131, 1539-1565.  Equation 10.
    """
    T = np.asarray(T, dtype=np.float64)
    # Murphy & Koop (2005) Eq. 10:
    # ln(P_ice) = 9.550426 − 5723.265/T + 3.53068·ln(T) − 0.00728332·T
    ln_p = 9.550426 - 5723.265 / T + 3.53068 * np.log(T) - 0.00728332 * T
    return np.exp(ln_p)


# ---------------------------------------------------------------------------
# Hertz-Knudsen free-molecular sublimation flux
# ---------------------------------------------------------------------------


def sublimation_rate(T: np.ndarray) -> np.ndarray:
    """Free-molecular sublimation mass flux [kg m⁻² s⁻¹] into vacuum.

    Hertz-Knudsen form for evaporation from an ice surface into a
    vacuum (no back-pressure), with sticking coefficient = 1:

    .. math::

        E = P_{\\text{sat}}(T) \\sqrt{\\frac{m}{2\\pi k_B T}}

    Parameters
    ----------
    T : np.ndarray
        Temperature [K].

    Returns
    -------
    np.ndarray
        Mass flux [kg m⁻² s⁻¹]. Always >= 0.
    """
    T = np.asarray(T, dtype=np.float64)
    P_sat = saturation_vapor_pressure(T)
    return P_sat * np.sqrt(M_H2O / (2.0 * np.pi * K_BOLTZMANN * T))


def sublimation_rate_mm_per_Gyr(T: np.ndarray) -> np.ndarray:
    """Sublimation loss rate in mm per Gyr (for threshold comparison).

    Converts the mass flux [kg m⁻² s⁻¹] to a linear retreat rate
    [mm Gyr⁻¹] using ice density 917 kg m⁻³.

    Parameters
    ----------
    T : np.ndarray
        Temperature [K].

    Returns
    -------
    np.ndarray
        Loss rate [mm Gyr⁻¹].
    """
    E = sublimation_rate(T)  # kg m^-2 s^-1
    # Convert to m/s → m/Gyr → mm/Gyr
    SECONDS_PER_GYR = 1e9 * 365.25 * 86400.0
    rate_m_per_s = E / RHO_ICE
    return rate_m_per_s * SECONDS_PER_GYR * 1e3  # mm/Gyr


# ---------------------------------------------------------------------------
# Ice stability depth
# ---------------------------------------------------------------------------


def ice_stability_depth(
    z: np.ndarray,
    T_mean: np.ndarray,
    loss_threshold_mm_per_Gyr: float = 1.0,
) -> float:
    """Return ``z_star`` [m] — shallowest stable depth for water ice.

    Finds the depth where the annual-mean sublimation rate drops below
    the loss threshold.  If ice is stable even at the surface (z=0),
    returns 0.0.  If ice is unstable at all depths in the profile,
    returns ``np.inf``.

    Parameters
    ----------
    z : np.ndarray
        Depth grid [m], monotonically increasing from the surface.
    T_mean : np.ndarray
        Annual-mean temperature profile [K], same shape as ``z``.
        This should come from a spin-up run of :func:`lunar.solver.solve_pixel`
        (average ``T`` over the final lunation).
    loss_threshold_mm_per_Gyr : float
        Acceptable long-term loss rate.  Schorghofer & Taylor (2007)
        use 1 mm per Gyr.

    Returns
    -------
    float
        ``z_star`` [m]. 0.0 if surface-stable, np.inf if unstable
        everywhere in the profile.

    References
    ----------
    Schorghofer, N. & Taylor, G. J. (2007), JGR 112, E02010.
    """
    z = np.asarray(z, dtype=np.float64)
    T_mean = np.asarray(T_mean, dtype=np.float64)

    if z.shape != T_mean.shape:
        raise ValueError(
            f"z and T_mean must have the same shape: {z.shape} vs {T_mean.shape}"
        )

    rates = sublimation_rate_mm_per_Gyr(T_mean)

    # Find the shallowest depth where rate <= threshold
    stable = rates <= loss_threshold_mm_per_Gyr

    if stable[0]:
        return 0.0

    if not np.any(stable):
        return float("inf")

    # Linear interpolation to find the crossing depth
    idx = int(np.argmax(stable))  # first True
    # Interpolate between idx-1 (unstable) and idx (stable)
    if idx == 0:
        return float(z[0])

    r0 = rates[idx - 1]
    r1 = rates[idx]
    z0 = z[idx - 1]
    z1 = z[idx]

    # log-linear interpolation (sublimation rate varies exponentially with T)
    if r0 > 0 and r1 > 0:
        log_r0 = np.log(r0)
        log_r1 = np.log(r1)
        log_thresh = np.log(loss_threshold_mm_per_Gyr)
        frac = (log_thresh - log_r0) / (log_r1 - log_r0)
    else:
        frac = (loss_threshold_mm_per_Gyr - r0) / (r1 - r0)

    frac = np.clip(frac, 0.0, 1.0)
    return float(z0 + frac * (z1 - z0))


def ice_stability_map(
    z: np.ndarray,
    T_mean_grid: np.ndarray,
    loss_threshold_mm_per_Gyr: float = 1.0,
) -> np.ndarray:
    """Compute ice stability depth for a 2-D grid of temperature profiles.

    Parameters
    ----------
    z : np.ndarray
        Depth grid [m], shape ``(N_z,)``.
    T_mean_grid : np.ndarray
        Annual-mean temperature profiles, shape ``(N_y, N_x, N_z)``
        or ``(N_pixels, N_z)``.
    loss_threshold_mm_per_Gyr : float
        Acceptable long-term loss rate [mm Gyr⁻¹].

    Returns
    -------
    np.ndarray
        Ice stability depth ``z_star`` [m] at each pixel. Shape
        ``(N_y, N_x)`` or ``(N_pixels,)``.  ``np.inf`` = unstable
        everywhere; ``0.0`` = surface-stable.
    """
    orig_shape = T_mean_grid.shape[:-1]
    profiles = T_mean_grid.reshape(-1, z.size)
    z_star = np.empty(profiles.shape[0])

    for i in range(profiles.shape[0]):
        z_star[i] = ice_stability_depth(z, profiles[i], loss_threshold_mm_per_Gyr)

    return z_star.reshape(orig_shape)
