"""High-level pipeline driver.

Wire order (see SKILL.md "What this pipeline does"):
    1. Load LOLA DEM subset (:mod:`lunar.illumination`)
    2. Compute horizon profiles per pixel
    3. For each time step, compute direct + secondary illumination
    4. Run :func:`lunar.solver.solve_pixel` per pixel (parallel)
    5. Compute ice stability via :mod:`lunar.ice_stability`
    6. If ice-coupled model: iterate steps 4-5 until z_star converges
    7. Emit TSUKIMI records via :mod:`lunar.rtm_coupling`

This module defines the orchestration surface. The internal stages are
stubbed until their underlying modules are implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .rtm_coupling import TsukimiPixelRecord


@dataclass
class PipelineConfig:
    """Top-level pipeline configuration."""

    dem_path: str
    conductivity_model: Literal["hayne", "martinez", "ice_coupled"] = "hayne"
    n_lunations_spinup: int = 10
    ice_feedback_max_iter: int = 5
    ice_feedback_tol_z: float = 1e-3  # [m]
    output_path: str = "outputs/tsukimi_records.nc"


def run_pipeline(config: PipelineConfig) -> list[TsukimiPixelRecord]:  # pragma: no cover
    """Run the full pipeline for the area defined in ``config.dem_path``.

    Not yet implemented — this is the top-level orchestrator and will be
    written last, once each downstream module is individually validated
    against the SKILL.md benchmarks.
    """
    raise NotImplementedError(
        "run_pipeline: stub. Implement bottom-up: grid -> properties -> "
        "solver -> illumination -> ice_stability -> rtm_coupling."
    )
