"""
Shared data export for the scrollytelling prototypes.

Builds one JSON file that all three prototypes (Closeread, Observable Framework,
Svelte) read, so the numbers are identical and only the rendering differs.

Inputs:
    data/interim/df_citizenship_direction_*.pkl  (via src.dashboard.DataLoader)

Outputs:
    prototypes/data/net_migration_citizenship.json

The story: annual net migration (12-month rolling sum) from 2001 to the latest
month, split into New Zealand and non-New Zealand citizens. Annotation points
(record peak, NZ-citizen trough, latest reading) are computed here rather than
hardcoded in each prototype's JavaScript.

Run from the repo root:
    .venv/Scripts/python prototypes/export_prototype_data.py
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.dashboard.base import PALETTE  # noqa: E402
from src.dashboard.data_loader import DataLoader  # noqa: E402

# ── Constants ──────────────────────────────────────────────────────────────────

OUTPUT_PATH = REPO_ROOT / "prototypes" / "data" / "net_migration_citizenship.json"

ROLLING_WINDOW = 12  # months — annual running total, the standard presentation

# Citizenship labels as they appear in the Stats NZ data
CIT_TOTAL = "TOTAL ALL CITIZENSHIPS"
CIT_NZ = "New Zealand"
CIT_NON_NZ = "Non-New Zealand"

SERIES_COLORS = {
    "total": PALETTE[6],   # #045275 darkest teal
    "nz": PALETTE[4],      # #089099
    "non_nz": PALETTE[2],  # #7CCBA2
}

SOURCE = "Statistics NZ ITM552301 - migrant arrivals and departures by citizenship"


# ── Data transforms ────────────────────────────────────────────────────────────

def _build_series(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot to one row per month with total / nz / non_nz annual net migration.

    Args:
        df: Long-format frame with Month, Count, Direction, Citizenship.

    Returns:
        Frame indexed by Month with columns total, nz, non_nz — each a
        12-month rolling sum of monthly net migration.
    """
    net = df[df["Direction"] == "Net"]

    wide = (
        net[net["Citizenship"].isin([CIT_TOTAL, CIT_NZ, CIT_NON_NZ])]
        .pivot_table(index="Month", columns="Citizenship", values="Count")
        .rename(columns={CIT_TOTAL: "total", CIT_NZ: "nz", CIT_NON_NZ: "non_nz"})
        .sort_index()
    )

    missing = {"total", "nz", "non_nz"} - set(wide.columns)
    if missing:
        raise ValueError(f"Missing expected citizenship series: {sorted(missing)}")

    rolling = wide[["total", "nz", "non_nz"]].rolling(ROLLING_WINDOW).sum()
    return rolling.dropna()


def _annotations(series: pd.DataFrame) -> Dict[str, Any]:
    """Compute the three annotation points the story steps refer to."""
    peak_month = series["total"].idxmax()
    trough_month = series["nz"].idxmin()
    latest_month = series.index[-1]

    def _point(month: pd.Timestamp, column: str) -> Dict[str, Any]:
        return {
            "month": month.strftime("%Y-%m"),
            "label": month.strftime("%b %Y"),
            "value": round(float(series.loc[month, column])),
            "series": column,
        }

    return {
        "peak": _point(peak_month, "total"),
        "nz_trough": _point(trough_month, "nz"),
        "latest": _point(latest_month, "total"),
    }


def _records(series: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert the wide frame to a compact list of JSON records."""
    return [
        {
            "month": month.strftime("%Y-%m"),
            "total": round(float(row["total"])),
            "nz": round(float(row["nz"])),
            "non_nz": round(float(row["non_nz"])),
        }
        for month, row in series.iterrows()
    ]


# ── Story definition ───────────────────────────────────────────────────────────

def _steps(annotations: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The five scroll steps, shared across all three prototypes.

    `visible` drives which series each prototype draws; `focus` names the
    annotation to surface. Prose lives here so the three versions say the
    same thing.
    """
    peak = annotations["peak"]
    trough = annotations["nz_trough"]
    latest = annotations["latest"]

    return [
        {
            "id": "total",
            "visible": ["total"],
            "focus": None,
            "title": "Net migration, 2001 to today",
            "body": (
                "Each point is the net gain of migrants over the previous 12 months. "
                "The line spent two decades between 10,000 and 70,000."
            ),
        },
        {
            "id": "peak",
            "visible": ["total"],
            "focus": "peak",
            "title": "Then came the post-border surge",
            "body": (
                f"Net migration peaked at {peak['value']:,} in the year to "
                f"{peak['label']}, far above anything in the previous two decades."
            ),
        },
        {
            "id": "split",
            "visible": ["nz", "non_nz"],
            "focus": None,
            "title": "One line, two very different stories",
            "body": (
                "Splitting by citizenship shows the total hides an offset. "
                "Non-New Zealand citizens drove the surge while New Zealand "
                "citizens left in growing numbers."
            ),
        },
        {
            "id": "trough",
            "visible": ["nz", "non_nz"],
            "focus": "nz_trough",
            "title": "New Zealanders left at a record rate",
            "body": (
                f"Net migration of New Zealand citizens bottomed at "
                f"{trough['value']:,} in the year to {trough['label']}."
            ),
        },
        {
            "id": "latest",
            "visible": ["total"],
            "focus": "latest",
            "title": "Where it sits now",
            "body": (
                f"The total has fallen back to {latest['value']:,} in the year to "
                f"{latest['label']}."
            ),
        },
    ]


# ── Main ───────────────────────────────────────────────────────────────────────

def build_payload(quiet: bool = False) -> Dict[str, Any]:
    """Build the full JSON payload from the latest interim pkl.

    Exposed as a function so Observable Framework's Python data loader can
    reuse the exact same code path and emit to stdout at build time.

    Args:
        quiet: Suppress DataLoader's stdout chatter. Required when the caller
            is writing JSON to stdout, as Framework data loaders do.
    """
    loader = DataLoader(base_path=REPO_ROOT)

    if quiet:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            df = loader.load_citizenship_direction()
    else:
        df = loader.load_citizenship_direction()

    series = _build_series(df)
    annotations = _annotations(series)

    return {
        "meta": {
            "source": SOURCE,
            "generated": date.today().isoformat(),
            "unit": f"{ROLLING_WINDOW}-month rolling sum of net migration",
            "months": len(series),
            "start": series.index[0].strftime("%Y-%m"),
            "end": series.index[-1].strftime("%Y-%m"),
        },
        "colors": SERIES_COLORS,
        "labels": {
            "total": "All citizenships",
            "nz": "New Zealand citizens",
            "non_nz": "Non-New Zealand citizens",
        },
        "annotations": annotations,
        "steps": _steps(annotations),
        "series": _records(series),
    }


def main() -> None:
    print("Building scrollytelling prototype data")
    print("-" * 60)

    payload = build_payload()
    annotations = payload["annotations"]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"  Months:      {payload['meta']['months']:,} "
          f"({payload['meta']['start']} to {payload['meta']['end']})")
    print(f"  Peak:        {annotations['peak']['value']:,} "
          f"({annotations['peak']['label']})")
    print(f"  NZ trough:   {annotations['nz_trough']['value']:,} "
          f"({annotations['nz_trough']['label']})")
    print(f"  Latest:      {annotations['latest']['value']:,} "
          f"({annotations['latest']['label']})")
    print("-" * 60)
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
