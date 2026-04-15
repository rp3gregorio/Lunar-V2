"""TSUKIMI radiative-transfer-model coupling.

The pipeline hands per-pixel thermal profiles to TSUKIMI's terahertz RTM
as the dictionary schema documented in the data agent
(``.claude/skills/agents/data.md``). This module owns the schema and
its serialization to NetCDF4 / HDF5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

ModelName = Literal["hayne", "martinez", "ice_coupled"]


@dataclass
class TsukimiPixelRecord:
    """One pixel's thermal profile in TSUKIMI RTM schema.

    Fields mirror the dictionary described in the data agent. The names
    and dtypes are part of the contract with the RTM — change them only
    in lock-step with the RTM team.
    """

    lat: float  # degrees
    lon: float  # degrees
    z: np.ndarray  # depth nodes [m], shape (N_z,)
    dz: np.ndarray  # layer thicknesses [m], shape (N_z,)
    rho: np.ndarray  # density [kg m^-3], shape (N_z,)
    T: np.ndarray  # temperature [K], shape (N_z, N_t)
    t: np.ndarray  # time [s], shape (N_t,)
    local_time: np.ndarray  # local solar time [hr], shape (N_t,)
    H: float  # H-parameter [m]
    albedo: float
    emissivity: float
    Q_b: float  # bottom heat flux [W m^-2]
    model: ModelName
    phi_ice: np.ndarray | None = None  # shape (N_z,) if ice-coupled
    z_star: float | None = None  # ice stability depth [m] if computed
    diagnostics: dict = field(default_factory=dict)


def write_netcdf(records: list[TsukimiPixelRecord], path: str) -> None:  # pragma: no cover
    """Serialize a list of per-pixel records to NetCDF4.

    Not yet implemented — waiting on the schema lock-in with the TSUKIMI
    team at NICT/Tohoku. The schema is documented in the data agent and
    will be CF-compliant.
    """
    raise NotImplementedError(
        "write_netcdf: agree on CF-compliant dimension names with the "
        "TSUKIMI team before writing the serializer."
    )
