"""
Process Auckland local board area boundaries from Stats NZ shapefile.

Input:  data/raw/statsnz-territorial-authority-local-board-2025-clipped-SHP.zip
Output: dashboard/assets/auckland_albs.geojson

Properties in output:
    alb_code        — TALB2025_V code (e.g. '07604')
    alb_name        — display name with macrons, suffix stripped
                      (e.g. 'Kaipātiki')
    alb_name_ascii  — ASCII name, suffix stripped, used as featureidkey
                      in Plotly choropleth (e.g. 'Kaipatiki')
"""

import json
import re
import unicodedata
from pathlib import Path

import geopandas as gpd

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_SHP_ZIP = _REPO_ROOT / "data" / "raw" / "statsnz-territorial-authority-local-board-2025-clipped-SHP.zip"
_SHP_NAME = "territorial-authority-local-board-2025-clipped.shp"
_OUT_PATH = _REPO_ROOT / "dashboard" / "assets" / "auckland_albs.geojson"

_ALB_CODE_PREFIX = "076"
_SUFFIX_RE = re.compile(r"\s+local board area$", re.IGNORECASE)

# Simplification tolerance in degrees (~20 m at NZ latitudes).
_SIMPLIFY_TOLERANCE = 0.001


# ── Helpers ────────────────────────────────────────────────────────────────────


def _strip_suffix(name: str) -> str:
    return _SUFFIX_RE.sub("", name).strip()


def _to_ascii(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    if not _SHP_ZIP.exists():
        raise FileNotFoundError(f"Shapefile zip not found: {_SHP_ZIP}")

    print("Reading shapefile...")
    gdf = gpd.read_file(f"zip://{_SHP_ZIP}!{_SHP_NAME}")

    print(f"  Total features: {len(gdf)}")

    alb = gdf[gdf["TALB2025_V"].str.startswith(_ALB_CODE_PREFIX)].copy()
    print(f"  Auckland local boards: {len(alb)}")

    print("Reprojecting to WGS84...")
    alb = alb.to_crs(epsg=4326)

    print(f"Simplifying geometry (tolerance={_SIMPLIFY_TOLERANCE})...")
    alb["geometry"] = alb["geometry"].simplify(_SIMPLIFY_TOLERANCE, preserve_topology=True)

    alb["alb_code"] = alb["TALB2025_V"]
    alb["alb_name"] = alb["TALB2025_1"].apply(_strip_suffix)
    alb["alb_name_ascii"] = alb["TALB2025_2"].apply(_strip_suffix).apply(_to_ascii)

    out_gdf = alb[["alb_code", "alb_name", "alb_name_ascii", "geometry"]].reset_index(drop=True)

    print("Sample name mapping:")
    for _, row in out_gdf.iterrows():
        print(f"  {row['alb_code']}  {row['alb_name']!r:35s} -> {row['alb_name_ascii']!r}")

    print(f"\nSaving to {_OUT_PATH} ...")
    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_gdf.to_file(_OUT_PATH, driver="GeoJSON")

    size_kb = _OUT_PATH.stat().st_size / 1024
    print(f"Done. File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
