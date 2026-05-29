"""
Process Stats NZ ITM553701 raw CSVs (direction x NZ region x citizenship) into long-format interim data.

Input:  4 files in data/raw/:
        ITM553701_total_{date}.csv    -- TOTAL ALL CITIZENSHIPS
        ITM553701_nz_{date}.csv       -- New Zealand
        ITM553701_au_{date}.csv       -- Australia
        ITM553701_non_nz_{date}.csv   -- Non-New Zealand

Output: data/interim/df_direction_region_{YYYYMMDD}.pkl / .csv

Schema:
    Month       datetime64[ns]
    Count       float64         (".." suppressed values become NaN)
    Direction   object          (Arrivals, Departures, Net)
    Citizenship object          (TOTAL ALL CITIZENSHIPS, New Zealand, Australia, Non-New Zealand)
    Region      object          (108 NZ areas including regional councils, TAs, and TOTAL ALL AREAS)
"""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Tuple

import pandas as pd


INTERIM_DIR = Path(__file__).parent.parent.parent / "data" / "interim"
RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

_HEADER_ROWS = 6
_SLUGS = ["total", "nz", "au", "non_nz"]


# ── Parsing ──

def _read_raw(file_path: str) -> Tuple[pd.DataFrame, str]:
    """Parse the 6-row header and return (wide_df, citizenship_label).

    Header layout:
        row 0: dataset title        (skip)
        row 1: 'Monthly'            (period label -- skip)
        row 2: direction names      -- Arrivals / Departures / Net, repeated once per 108-area group
        row 3: citizenship label    -- e.g. 'TOTAL ALL CITIZENSHIPS', 'New Zealand', etc.
        row 4: NZ area names        -- 108 values, repeating for each direction group
        row 5: 'Estimate' labels    (skip)
        row 6+: data
    """
    header_df = pd.read_csv(file_path, nrows=_HEADER_ROWS, header=None)

    citizenship = header_df.iloc[3, 1].strip()
    direction_row = header_df.iloc[2].ffill().astype(str)
    area_row = header_df.iloc[4].astype(str)

    column_names: list[str] = ["Month"]
    for i in range(1, len(direction_row)):
        direction = direction_row.iloc[i].strip()
        area = area_row.iloc[i].strip()
        if direction and area and area not in ("nan", ""):
            column_names.append(f"{direction}|{area}")

    data_df = pd.read_csv(
        file_path,
        skiprows=_HEADER_ROWS,
        header=None,
        na_values=[".."],   # ".." = suppressed / not available
    )

    n_cols = min(len(column_names), len(data_df.columns))
    data_df = data_df.iloc[:, :n_cols]
    data_df.columns = column_names[:n_cols]

    print(f"  Wide shape: {data_df.shape}  ({n_cols - 1} data columns)  citizenship={citizenship!r}")
    return data_df, citizenship


def _to_long(wide_df: pd.DataFrame, citizenship: str) -> pd.DataFrame:
    """Convert wide format to long format, parse Month, and add Citizenship column."""
    month_mask = wide_df["Month"].astype(str).str.match(r"^\d{4}M\d{2}$", na=False)
    df = wide_df[month_mask].copy()
    df["Month"] = pd.to_datetime(df["Month"], format="%YM%m")

    value_cols = [c for c in df.columns if c != "Month"]
    df_long = df.melt(
        id_vars=["Month"],
        value_vars=value_cols,
        var_name="Direction_Region",
        value_name="Count",
    )

    split = df_long["Direction_Region"].str.split("|", n=1, expand=True)
    df_long["Direction"] = split[0].str.strip()
    df_long["Region"] = split[1].str.strip()
    df_long = df_long.drop(columns=["Direction_Region"])
    df_long["Count"] = pd.to_numeric(df_long["Count"], errors="coerce")
    df_long["Citizenship"] = citizenship

    return df_long[["Month", "Count", "Direction", "Citizenship", "Region"]]


def _validate(df: pd.DataFrame) -> bool:
    """Validate schema and basic sanity checks."""
    expected = ["Month", "Count", "Direction", "Citizenship", "Region"]
    if list(df.columns) != expected:
        print(f"  FAIL Column mismatch: {list(df.columns)}")
        return False
    if not pd.api.types.is_datetime64_any_dtype(df["Month"]):
        print("  FAIL Month not datetime")
        return False
    if not pd.api.types.is_numeric_dtype(df["Count"]):
        print("  FAIL Count not numeric")
        return False
    print("  OK Validation passed")
    return True


# ── Entry point ──

def main() -> None:
    """Process all 4 ITM553701 citizenship files and combine into a single interim file."""
    print("=== Direction x Region x Citizenship Data Processing ===")

    frames = []
    date_suffix = None

    for slug in _SLUGS:
        matches = sorted(glob.glob(str(RAW_DIR / f"ITM553701_{slug}_*.csv")))
        if not matches:
            print(f"  WARNING: no file found for slug={slug}, skipping")
            continue
        f = matches[-1]
        if slug == "total":
            date_suffix = os.path.basename(f).split("_")[-1].split(".")[0]
        print(f"Input [{slug}]: {os.path.basename(f)}")
        wide_df, citizenship = _read_raw(f)
        df_long = _to_long(wide_df, citizenship)
        frames.append(df_long)

    if not frames:
        raise FileNotFoundError("No ITM553701_<slug>_*.csv files found in data/raw/")

    if date_suffix is None:
        # Fallback: extract date from first processed file's basename
        date_suffix = os.path.basename(sorted(glob.glob(str(RAW_DIR / "ITM553701_*.csv")))[-1]).split("_")[-1].split(".")[0]

    df_combined = pd.concat(frames, ignore_index=True)

    if not _validate(df_combined):
        raise ValueError("Validation failed -- aborting")

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_pkl = INTERIM_DIR / f"df_direction_region_{date_suffix}.pkl"
    out_csv = INTERIM_DIR / f"df_direction_region_{date_suffix}.csv"

    df_combined.to_pickle(out_pkl)
    df_combined.to_csv(out_csv, index=False)

    print(f"Saved:  {out_pkl.name}")
    print(f"Saved:  {out_csv.name}")
    print(f"Records: {len(df_combined):,}")
    print(f"Date range: {df_combined['Month'].min().date()} to {df_combined['Month'].max().date()}")
    print(f"Directions: {sorted(df_combined['Direction'].unique())}")
    print(f"Citizenships: {sorted(df_combined['Citizenship'].unique())}")
    print(f"Regions: {df_combined['Region'].nunique()} unique")
    suppressed = df_combined["Count"].isna().sum()
    print(f"Suppressed values (..): {suppressed:,}")


if __name__ == "__main__":
    main()
