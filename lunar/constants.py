"""Physical constants and default regolith parameters.

All values are SI. Every constant has a source citation in its docstring.
Do not add numbers here without a citation — the project scientific-integrity
rule is that unsourced values are forbidden.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Universal physical constants
# ---------------------------------------------------------------------------

#: Stefan-Boltzmann constant [W m^-2 K^-4] — CODATA 2018.
SIGMA_SB: float = 5.670374419e-8

#: Solar constant at 1 AU [W m^-2] — Kopp & Lean (2011), GRL 38, L01706.
SOLAR_CONSTANT: float = 1361.0

#: Mean lunar distance from Sun [AU] (treated as 1 AU for the thermal problem).
LUNAR_DISTANCE_AU: float = 1.0

#: Sidereal lunar day / synodic lunation [s] — 29.530589 days.
LUNATION_SECONDS: float = 29.530589 * 86400.0

#: Ice density (crystalline Ih, 100 K) [kg m^-3] — Feistel & Wagner (2006).
RHO_ICE: float = 917.0


# ---------------------------------------------------------------------------
# Regolith thermal parameters (Hayne et al. 2017)
# ---------------------------------------------------------------------------
# Hayne, P. O. et al. (2017). "Global regolith thermophysical properties of
# the Moon from the Diviner Lunar Radiometer Experiment." JGR: Planets 122,
# 2371-2400. doi:10.1002/2017JE005387

#: Surface bulk density [kg m^-3] — Hayne et al. (2017) Table 2.
RHO_SURFACE: float = 1100.0

#: Deep bulk density [kg m^-3] — Hayne et al. (2017) Table 2.
RHO_DEEP: float = 1800.0

#: H-parameter (density/conductivity scale height) [m] — Hayne et al. (2017).
H_PARAMETER: float = 0.06

#: Surface contact conductivity [W m^-1 K^-1] — Hayne et al. (2017) Table 2.
K_SURFACE: float = 7.4e-4

#: Deep contact conductivity [W m^-1 K^-1] — Hayne et al. (2017) Table 2.
#: NOTE: earlier versions of heat1d had an incorrect value here. The correct
#: published value is 3.4e-3.
K_DEEP: float = 3.4e-3

#: Radiative conductivity coefficient chi [dimensionless] — Hayne et al. (2017).
CHI_RADIATIVE: float = 2.7

#: Reference temperature for the radiative term [K] — Hayne et al. (2017).
T_REFERENCE: float = 350.0


# ---------------------------------------------------------------------------
# Boundary conditions
# ---------------------------------------------------------------------------

#: Default Bond albedo (may be tuned per pixel from Diviner).
ALBEDO_DEFAULT: float = 0.12

#: Default thermal emissivity.
EMISSIVITY_DEFAULT: float = 0.95

#: Equatorial geothermal heat flux [W m^-2] — Apollo 15/17 HFE average,
#: Langseth et al. (1976), Nagihara et al. (2018).
Q_B_EQUATORIAL: float = 0.018

#: South-polar geothermal heat flux [W m^-2] — Chang'E-2 MRM inversions,
#: Feng et al. (2020); actual range 0.005-0.012.
Q_B_SOUTH_POLAR: float = 0.012


# ---------------------------------------------------------------------------
# Grid defaults (geometric)
# ---------------------------------------------------------------------------

#: Default maximum depth for the subsurface grid [m].
Z_MAX_DEFAULT: float = 3.0

#: Default thickness of the top layer [m] (2 mm).
DZ0_DEFAULT: float = 0.002

#: Default geometric-growth factor (new_dz = old_dz * (1 + GROWTH)).
GROWTH_DEFAULT: float = 0.15
