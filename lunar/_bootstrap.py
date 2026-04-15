"""Notebook bootstrap helpers.

Lets a user open any notebook in this repo and click "Run All" without
needing to know anything about venvs, pip, git, or data downloads. The
bootstrap cell at the top of each notebook imports this module and calls
`ensure_lunar()` (and optionally `ensure_data(...)`). Everything else is
handled automatically.

Design goals
------------
* Self-healing: works regardless of which Python/kernel the notebook was
  launched with, as long as that kernel can `pip install`.
* No venv required: if the `lunar` package isn't importable, we put the
  repo root on ``sys.path`` directly, bypassing ``pip install -e .``.
* Offline-tolerant: if data downloads fail, the calling notebook should
  degrade gracefully (each notebook guards its data-dependent cells).
* Zero third-party deps at import time — only stdlib.
"""

from __future__ import annotations

import importlib
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Iterable


# ---------------------------------------------------------------------------
# Path + package bootstrap
# ---------------------------------------------------------------------------


def find_repo_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """Walk upward from ``start`` until we find the Lunar-V2 repo root.

    The repo root is identified by the presence of both ``pyproject.toml``
    and a ``lunar/`` package directory.
    """
    here = (start or pathlib.Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "lunar" / "__init__.py"
        ).is_file():
            return candidate
    raise RuntimeError(
        f"Could not locate Lunar-V2 repo root starting from {here}. "
        "Run this notebook from inside a cloned Lunar-V2 checkout."
    )


def _pip_install(*pkgs: str, quiet: bool = True) -> None:
    """Install packages into *this* kernel's Python via ``sys.executable``.

    Using ``sys.executable`` guarantees the install lands in the same
    environment the notebook is running under, no matter which kernel the
    user picked.
    """
    cmd = [sys.executable, "-m", "pip", "install"]
    if quiet:
        cmd.append("-q")
    cmd.extend(pkgs)
    subprocess.check_call(cmd)


def ensure_packages(packages: Iterable[tuple[str, str]]) -> list[str]:
    """Make sure each ``(pip_name, import_name)`` pair is importable.

    Installs any that are missing. Returns the list of packages that were
    actually installed (useful for logging).
    """
    installed: list[str] = []
    for pip_name, import_name in packages:
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"  installing {pip_name} ...")
            _pip_install(pip_name)
            installed.append(pip_name)
    return installed


def ensure_lunar(extra: Iterable[str] = ()) -> pathlib.Path:
    """One-stop bootstrap for notebook 00/01/02/03.

    1. Locate the repo root and put it on ``sys.path`` so
       ``import lunar`` works without ``pip install -e .``.
    2. Install the core third-party deps (numpy, scipy, numba, matplotlib)
       plus anything in ``extra`` (e.g. ``"rasterio"``, ``"spiceypy"``).
    3. Print the Python executable and the lunar package location so the
       user can confirm the kernel is correctly wired.

    Parameters
    ----------
    extra : iterable of str, optional
        Pip names of additional packages to ensure. Each entry may be a
        ``(pip_name, import_name)`` tuple if the two names differ; a bare
        string is treated as both.

    Returns
    -------
    pathlib.Path
        The repo root (also added to ``sys.path``).
    """
    repo = find_repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    core = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("numba", "numba"),
        ("matplotlib", "matplotlib"),
    ]
    extras: list[tuple[str, str]] = []
    for item in extra:
        if isinstance(item, tuple):
            extras.append(item)
        else:
            extras.append((item, item))

    print("Lunar-V2 notebook bootstrap")
    print("  python :", sys.executable)
    print("  repo   :", repo)
    installed = ensure_packages(core + extras)
    if not installed:
        print("  deps   : all present")

    import lunar  # noqa: F401

    print("  lunar  :", lunar.__file__)
    return repo


# ---------------------------------------------------------------------------
# Data downloads
# ---------------------------------------------------------------------------


def _download(url: str, dest: pathlib.Path, min_bytes: int = 1024) -> bool:
    """Download ``url`` to ``dest`` unless the file already looks complete.

    Returns True if the file exists and is at least ``min_bytes`` after the
    call. Prints a short progress line.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size >= min_bytes:
        return True
    print(f"  fetching {dest.name}")
    try:
        urllib.request.urlretrieve(url, dest)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"    FAILED: {exc}")
        return False
    return dest.is_file() and dest.stat().st_size >= min_bytes


def ensure_spice_kernels(repo_root: pathlib.Path | None = None) -> bool:
    """Download the 6 SPICE kernels needed by ``lunar.ephem`` if missing.

    Total size ~46 MB. Returns True iff all 6 are present after the call.
    """
    repo = repo_root or find_repo_root()
    spice_dir = repo / "data" / "spice"
    base = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels"
    kernels = [
        (f"{base}/lsk/naif0012.tls", "naif0012.tls"),
        (f"{base}/pck/pck00011.tpc", "pck00011.tpc"),
        (f"{base}/pck/moon_pa_de440_200625.bpc", "moon_pa_de440_200625.bpc"),
        (f"{base}/fk/satellites/moon_de440_250416.tf", "moon_de440_250416.tf"),
        (f"{base}/fk/satellites/moon_assoc_me.tf", "moon_assoc_me.tf"),
        (f"{base}/spk/planets/de440s.bsp", "de440s.bsp"),
    ]
    print("Ensuring SPICE kernels ...")
    ok = True
    for url, name in kernels:
        ok &= _download(url, spice_dir / name)
    return ok


def ensure_apollo_hfe(
    repo_root: pathlib.Path | None = None,
    probes: Iterable[str] = ("p1f1", "p1f2", "p1f3", "p1f4"),
    mission: str = "a15",
) -> bool:
    """Download a minimal Apollo HFE file set (default: Apollo 15 Probe 1).

    Only the sensor timeseries + depth table for the requested mission /
    probes are fetched. Total size < 10 MB for the default set.
    """
    repo = repo_root or find_repo_root()
    base = (
        "https://pds-geosciences.wustl.edu/lunar/"
        "urn-nasa-pds-a15_17_hfe_concatenated/data"
    )
    data_dir = repo / "data" / "apollo" / mission
    depth_dir = repo / "data" / "apollo" / "depth"
    print(f"Ensuring Apollo HFE ({mission}) ...")
    ok = True
    for probe in probes:
        url = f"{base}/clean/{mission}/{mission}{probe}.tab"
        ok &= _download(url, data_dir / f"{mission}{probe}.tab")
    # Depth tables (p1 / p2)
    for depth_name in ("p1", "p2"):
        url = f"{base}/depth/{mission}{depth_name}_depth.tab"
        ok &= _download(url, depth_dir / f"{mission}{depth_name}_depth.tab")
    return ok


def ensure_lola_dem_80mpp(repo_root: pathlib.Path | None = None) -> bool:
    """Download the 80 m/pixel south polar LOLA DEM (~180 MB).

    This is the smallest of the three PGDA polar DEMs and is enough for
    the illumination notebook quicklooks.
    """
    repo = repo_root or find_repo_root()
    url = (
        "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
        "LDEM_80S_80MPP_ADJ.TIF"
    )
    dest = repo / "data" / "dem" / "LDEM_80S_80MPP_ADJ.TIF"
    print("Ensuring LOLA 80 MPP DEM ...")
    return _download(url, dest, min_bytes=10_000_000)
