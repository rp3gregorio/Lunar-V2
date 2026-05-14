"""Download a LOLA south-polar DEM tile for Phase 2 / global-model work.

Source
------
PGDA Product 90 (Barker et al. 2023):
    https://pgda.gsfc.nasa.gov/products/90

Three grid resolutions are available; pick based on your disk + RAM:

    Tile                          Pixels        Approx size
    LDEM_80S_80MPP_ADJ.TIF        7500x7500     ~225 MB    (recommended for demo)
    LDEM_80S_40MPP_ADJ.TIF        15000x15000   ~900 MB
    LDEM_80S_20MPP_ADJ.TIF        30000x30000   ~3.6 GB

All cover the south-polar cap from latitude -80 deg to -90 deg in a
polar-stereographic projection (Moon 2015 sphere, R=1737.4 km).

Usage
-----
    python3 scripts/phase2/global/download_lola_dem.py            # 80MPP (recommended)
    python3 scripts/phase2/global/download_lola_dem.py --mpp 40   # 40m/pixel
    python3 scripts/phase2/global/download_lola_dem.py --mpp 20   # 20m/pixel (LARGE)

The file lands at ``data/lola/LDEM_80S_<MPP>MPP_ADJ.TIF``.

Requirements
------------
``requests`` (pip install requests). The DEMs are publicly hosted and
require no authentication.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

# Real PGDA base for the south-polar 80S LDEM tiles. Verified 2026-05-11
# against `curl -sIL ...80S_80MPP_ADJ.TIF` (200, image/tiff, ~189 MB).
# Earlier path (`LOLA_5mpp/POLE_LDEM`) returns an HTML error page silently.
PGDA_BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp"

URLS = {
    80: f"{PGDA_BASE}/LDEM_80S_80MPP_ADJ.TIF",
    40: f"{PGDA_BASE}/LDEM_80S_40MPP_ADJ.TIF",
    20: f"{PGDA_BASE}/LDEM_80S_20MPP_ADJ.TIF",
}


def download(url: str, dest: Path, chunk_size: int = 1 << 20) -> None:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "requests is required: pip install requests"
        ) from exc

    print(f"GET {url}")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        dest.parent.mkdir(parents=True, exist_ok=True)
        n_done = 0
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size):
                f.write(chunk)
                n_done += len(chunk)
                if total > 0:
                    pct = 100 * n_done / total
                    sys.stdout.write(
                        f"\r  {n_done/1e6:7.1f} / {total/1e6:7.1f} MB "
                        f"({pct:5.1f}%)"
                    )
                    sys.stdout.flush()
        print()
    print(f"Saved {dest}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--mpp", type=int, choices=(80, 40, 20), default=80,
        help="meters per pixel (80 = smallest = recommended for demo)",
    )
    args = p.parse_args()

    url = URLS[args.mpp]
    dest = _REPO_ROOT / "data" / "lola" / f"LDEM_80S_{args.mpp}MPP_ADJ.TIF"
    if dest.exists():
        print(f"Already have {dest} ({dest.stat().st_size/1e6:.1f} MB).")
        print("Delete it first if you want to re-download.")
        return 0

    download(url, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
