"""Bootstrap-download the Diviner GCP validation subset for Phase 2.

Pulls the six 10° latitude bands needed to replicate Martinez & Siegler
(2021) figures: 0°, 30°, 45°, 60°, 80° (north-hemisphere bands, used for
T7 mid-latitude diurnal curves) plus 87.91°S Shoemaker (south-hemisphere
band, used for channel 9 polar comparison).

Each band is ~156 MB; total subset ~940 MB. Files cache in
``data/diviner/gcp/`` (gitignored). Re-running is a no-op once cached.

Usage::

    python scripts/download_diviner_gcp.py [--force] [--cache DIR]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow ``python scripts/...`` from the repo root without installing.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lunar.diviner import download_gcp_band, gcp_band_for_latitude


# Validation subset chosen to track LPSC 2022 abstract figures 2-5 plus
# extra mid-latitudes for the wider replication. The Shoemaker target
# latitude 87.91°S falls inside the 80-90°S band.
_TARGET_LATITUDES: tuple[float, ...] = (
    5.0,    # 0-10°N (low-latitude / equatorial)
    35.0,   # 30-40°N (mid-lat, mare)
    45.0,   # 40-50°N (LPSC Fig 2 highlands site)
    65.0,   # 60-70°N (mid-high lat, mare)
    85.0,   # 80-90°N (high lat, highlands)
    -85.0,  # 80-90°S (Shoemaker / PSR validation)
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files exist on disk.",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="Cache directory (default: data/diviner/gcp/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the download plan but do not fetch.",
    )
    args = parser.parse_args(argv)

    bands = sorted({gcp_band_for_latitude(lat) for lat in _TARGET_LATITUDES})
    print(f"Validation subset: {len(bands)} latitude bands × ~156 MB each")
    for lat_min, lat_max in bands:
        print(f"  {lat_min:+4d}° to {lat_max:+4d}°")
    if args.dry_run:
        return 0

    total_bytes = 0
    start = time.time()
    for i, (lat_min, lat_max) in enumerate(bands, 1):
        print(f"[{i}/{len(bands)}] band {lat_min:+d}..{lat_max:+d}°", flush=True)
        files = download_gcp_band(
            lat_min,
            lat_max,
            cache_dir=args.cache,
            force=args.force,
        )
        sz = files["tab"].stat().st_size
        total_bytes += sz
        print(f"           {files['tab'].name}: {sz / 1e6:.1f} MB", flush=True)

    elapsed = time.time() - start
    print(
        f"Done. {total_bytes / 1e6:.1f} MB across {len(bands)} bands "
        f"in {elapsed:.0f} s."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
