"""
Process Stats NZ ITM553001 raw CSV (citizenship x visa type) into long-format interim data.

Input:  data/raw/ITM553001_*.csv  (6-row header, 175 data columns: 7 visa types x 25 citizenships)
Output: data/interim/df_citizenship_visa_{YYYYMMDD}.pkl / .csv

Schema:
    Month         datetime64[ns]
    Count         float64
    Visa          object  (Residence, Student, Visitor, Work, NZ and AU citizens, Other, TOTAL)
    Citizenship   object  (24 countries + Total All Countries...)
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
        row 0: dataset title  (skip)
        row 1: 'Arrivals'     (single direction — skip)
        row 2: 'Non-New Zealand' CLPR label  (skip)
        row 3: visa type names — one per 25-column group, blank elsewhere
        row 4: citizenship names — repeating 25 values per visa group
        row 5: 'Estimate' labels  (skip)
        row 6+: data
    """
    header_df = pd.read_csv(file_path, nrows=_HEADER_ROWS, header=None)

    visa_row = header_df.iloc[3].ffill().astype(str)
    citizenship_row = header_df.iloc[4].astype(str)

    column_names: list[str] = ["Month"]
    for i in range(1, len(visa_row)):
        visa = visa_row.iloc[i].strip()
        citizenship = citizenship_row.iloc[i].strip()
        if visa and citizenship and citizenship not in ("nan", ""):
            column_names.append(f"{visa}|{citizenship}")

    data_df = pd.read_csv(file_path, skiprows=_HEADER_ROWS, header=None)

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
        var_name="Visa_Citizenship",
        value_name="Count",
    )

    split = df_long["Visa_Citizenship"].str.split("|", n=1, expand=True)
    df_long["Visa"] = split[0].str.strip()
    df_long["Citizenship"] = split[1].str.strip()
    df_long = df_long.drop(columns=["Visa_Citizenship"])
    df_long["Count"] = pd.to_numeric(df_long["Count"], errors="coerce")

    return df_long[["Month", "Count", "Visa", "Citizenship"]]


def _validate(df: pd.DataFrame) -> bool:
    """Validate schema and basic sanity checks."""
    expected = ["Month", "Count", "Visa", "Citizenship"]
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
    """Auto-detect latest ITM553001 raw file and process it."""
    print("=== Citizenship x Visa Data Processing ===")

    files = sorted(glob.glob(str(RAW_DIR / "ITM553001_*.csv")))
    if not files:
        raise FileNotFoundError("No ITM553001_*.csv files found in data/raw/")

    input_file = files[-1]
    date_suffix = os.path.basename(input_file).split("_")[1]
    print(f"Input:  {os.path.basename(input_file)}")

    wide_df = _read_raw(input_file)
    df_long = _to_long(wide_df)

    if not _validate(df_long):
        raise ValueError("Validation failed — aborting")

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_pkl = INTERIM_DIR / f"df_citizenship_visa_{date_suffix}.pkl"
    out_csv = INTERIM_DIR / f"df_citizenship_visa_{date_suffix}.csv"

    df_long.to_pickle(out_pkl)
    df_long.to_csv(out_csv, index=False)

    print(f"Saved:  {out_pkl.name}")
    print(f"Saved:  {out_csv.name}")
    print(f"Records: {len(df_long):,}")
    print(f"Date range: {df_long['Month'].min().date()} to {df_long['Month'].max().date()}")
    print(f"Visa types ({df_long['Visa'].nunique()}): {sorted(df_long['Visa'].unique())}")
    print(f"Citizenships ({df_long['Citizenship'].nunique()} unique)")


if __name__ == "__main__":
    main()
