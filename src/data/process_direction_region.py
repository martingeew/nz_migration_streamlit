"""
Process Stats NZ ITM553701 raw CSV (direction x NZ region) into long-format interim data.

Input:  data/raw/ITM553701_*.csv  (6-row header, 324 data columns: 3 directions x 108 NZ areas)
Output: data/interim/df_direction_region_{YYYYMMDD}.pkl / .csv

Schema:
    Month      datetime64[ns]
    Count      float64         (".." suppressed values become NaN)
    Direction  object          (Arrivals, Departures, Net)
    Region     object          (108 NZ areas including regional councils, TAs, and TOTAL ALL AREAS)
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import pandas as pd


INTERIM_DIR = Path(__file__).parent.parent.parent / "data" / "interim"
RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

_HEADER_ROWS = 6


# ── Parsing ──

def _read_raw(file_path: str) -> pd.DataFrame:
    """Parse the 6-row header and return a wide-format DataFrame.

    Header layout:
        row 0: dataset title        (skip)
        row 1: 'Monthly'            (period label — skip)
        row 2: direction names      — Arrivals / Departures / Net, repeated once per 108-area group
        row 3: 'TOTAL ALL CITIZENSHIPS' (citizenship filter label — skip)
        row 4: NZ area names        — 108 values, repeating for each direction group
        row 5: 'Estimate' labels    (skip)
        row 6+: data
    """
    header_df = pd.read_csv(file_path, nrows=_HEADER_ROWS, header=None)

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

    print(f"  Wide shape: {data_df.shape}  ({n_cols - 1} data columns)")
    return data_df


def _to_long(wide_df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide format to long format and parse Month."""
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

    return df_long[["Month", "Count", "Direction", "Region"]]


def _validate(df: pd.DataFrame) -> bool:
    """Validate schema and basic sanity checks."""
    expected = ["Month", "Count", "Direction", "Region"]
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
    """Auto-detect latest ITM553701 raw file and process it."""
    print("=== Direction x Region Data Processing ===")

    files = sorted(glob.glob(str(RAW_DIR / "ITM553701_*.csv")))
    if not files:
        raise FileNotFoundError("No ITM553701_*.csv files found in data/raw/")

    input_file = files[-1]
    date_suffix = os.path.basename(input_file).split("_")[1]
    print(f"Input:  {os.path.basename(input_file)}")

    wide_df = _read_raw(input_file)
    df_long = _to_long(wide_df)

    if not _validate(df_long):
        raise ValueError("Validation failed — aborting")

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_pkl = INTERIM_DIR / f"df_direction_region_{date_suffix}.pkl"
    out_csv = INTERIM_DIR / f"df_direction_region_{date_suffix}.csv"

    df_long.to_pickle(out_pkl)
    df_long.to_csv(out_csv, index=False)

    print(f"Saved:  {out_pkl.name}")
    print(f"Saved:  {out_csv.name}")
    print(f"Records: {len(df_long):,}")
    print(f"Date range: {df_long['Month'].min().date()} to {df_long['Month'].max().date()}")
    print(f"Directions: {sorted(df_long['Direction'].unique())}")
    print(f"Regions: {df_long['Region'].nunique()} unique")
    suppressed = df_long["Count"].isna().sum()
    print(f"Suppressed values (..): {suppressed:,}")


if __name__ == "__main__":
    main()
