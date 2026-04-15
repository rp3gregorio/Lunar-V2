"""Ice stability depth and sublimation rates.

The ice-stability depth ``z_star`` is the shallowest depth at which the
annual-mean sublimation rate of water ice into a vacuum falls below a
loss threshold (conventionally 1 mm Gyr^-1 — Schorghofer & Taylor 2007,
JGR 112, E02010).

This module is intentionally a scaffold. The sublimation flux depends on
the annual-mean temperature profile coming out of :mod:`lunar.solver`,
so it cannot be wired in until the solver produces validated output.
"""

from __future__ import annotations

import numpy as np


def saturation_vapor_pressure(T: np.ndarray) -> np.ndarray:  # pragma: no cover
    """Saturation vapor pressure of H2O ice [Pa].

    Source candidates:
      * Murphy & Koop (2005), Q.J.R. Meteorol. Soc. 131, 1539-1565.
      * Feistel & Wagner (2007), J. Phys. Chem. Ref. Data 36, 433-458.

    Pick ONE and cite it. Not implemented until we commit to the choice.
    """
    raise NotImplementedError(
        "saturation_vapor_pressure: choose Murphy & Koop (2005) or "
        "Feistel & Wagner (2007) and cite it before implementing."
    )


def sublimation_rate(T: np.ndarray) -> np.ndarray:  # pragma: no cover
    """Free-molecular sublimation mass flux [kg m^-2 s^-1] into vacuum.

    Hertz-Knudsen form

    .. math::

        E = P_{\\mathrm{sat}}(T) \\sqrt{\\frac{m}{2 \\pi k_B T}}

    where ``m = 2.991e-26`` kg is the H2O molecular mass.
    """
    raise NotImplementedError(
        "sublimation_rate: implement after saturation_vapor_pressure is fixed."
    )


def ice_stability_depth(
    z: np.ndarray,
    T_mean: np.ndarray,
    loss_threshold_mm_per_Gyr: float = 1.0,
) -> float:  # pragma: no cover
    """Return ``z_star`` [m] — shallowest stable depth for water ice.

    Parameters
    ----------
    z : np.ndarray
        Depth grid [m] (monotonic, starting from surface).
    T_mean : np.ndarray
        Annual-mean temperature profile [K], same shape as ``z``.
    loss_threshold_mm_per_Gyr : float
        Acceptable long-term loss rate. Schorghofer & Taylor (2007) use
        1 mm per Gyr.
    """
    raise NotImplementedError(
        "ice_stability_depth: implement after sublimation_rate is in place."
    )
