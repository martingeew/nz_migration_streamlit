"""
Process CLPR × Visa × Citizenship raw CSV into long-format pkl/csv.

Source: Stats NZ Infoshare — "Estimated migrant arrivals by citizenship,
visa type and CLPR, 12/16-month rule (Monthly)". Downloaded with:
    python src/data/download_stats_nz.py --dataset itm_citizenship_visa

The raw file has a multi-row header structure:
    Row 0: Direction
    Row 1: CLPR (country of last permanent residence)
    Row 2: Visa type
    Row 3: Citizenship
    Row 4+: Data rows (Month, counts...)

Output: data/interim/df_clpr_india_visa_{date}.pkl and .csv
    Columns: Month, Count, Direction, CLPR, Visa, Citizenship

Usage:
    python src/data/process_clpr_india_visa.py
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
INTERIM_DIR = Path(__file__).parent.parent.parent / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

# Filename pattern for the raw CLPR download
# (Stats NZ names it with a random-ish suffix)
RAW_PATTERN = "ITM55*_*.csv"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _find_raw_file() -> Path:
    """Find the most recently downloaded CLPR raw CSV."""
    # The itm_citizenship_visa download produces a file that contains
    # multiple CLPR/Visa/Citizenship combinations. We need to find it.
    # Look for any ITM55 file that we haven't previously processed.
    already_known = {
        "ITM552101",  # direction × age × sex
        "ITM552201",  # direction × visa
        "ITM552301",  # direction × citizenship
        "ITM553001",  # citizenship × visa
        "ITM553701",  # direction × region
    }
    candidates = []
    for f in sorted(RAW_DIR.glob(RAW_PATTERN)):
        prefix = f.name[:9]  # e.g. "ITM552101"
        if prefix not in already_known:
            candidates.append(f)

    if not candidates:
        # Fallback: look for any ITM55 file newer than the itm553701 file
        all_files = sorted(RAW_DIR.glob("ITM55*.csv"), key=lambda p: p.stat().st_mtime)
        if all_files:
            candidates = [all_files[-1]]

    if not candidates:
        raise FileNotFoundError(
            f"No CLPR raw CSV found in {RAW_DIR}. "
            "Run: python src/data/download_stats_nz.py --dataset itm_citizenship_visa"
        )
    # Use the most recently modified file
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _parse_month(s: str) -> pd.Timestamp | None:
    """Parse YYYYM## format → Timestamp, return None for non-data rows."""
    if re.match(r"^\d{4}M\d{2}$", str(s)):
        return pd.to_datetime(s, format="%YM%m")
    return None


# ── Main processing ────────────────────────────────────────────────────────────

def process(raw_path: Path) -> pd.DataFrame:
    """Parse the raw CLPR CSV into long-format DataFrame.

    The raw file has a complex multi-row header. We read it without a header
    and reconstruct the column index from the first several rows.

    Args:
        raw_path: Path to the raw CSV file.

    Returns:
        Long-format DataFrame with columns:
        Month, Count, Direction, CLPR, Visa, Citizenship
    """
    print(f"Processing: {raw_path.name}")

    # Read raw CSV (no header) to inspect structure
    raw = pd.read_csv(raw_path, header=None, dtype=str)

    # Find the first data row (matches YYYYM## format in col 0)
    data_start = 0
    for i, val in enumerate(raw.iloc[:, 0]):
        if _parse_month(val) is not None:
            data_start = i
            break

    if data_start == 0:
        raise ValueError(f"Could not find data rows in {raw_path.name}")

    n_header_rows = data_start
    print(f"  Header rows: {n_header_rows}, data starts at row {data_start}")

    # Extract header rows
    header_rows = raw.iloc[:n_header_rows, :].fillna(method="ffill", axis=1)

    # The column labels are built from stacking all header rows
    # Typical structure (4-6 header rows depending on dataset version):
    #   Row 0: Direction (e.g. "Arrivals")
    #   Row 1: CLPR (e.g. "India")
    #   Row 2: Visa type (e.g. "Work")
    #   Row 3: Citizenship (e.g. "India")
    #   Row 4: Estimate type (e.g. "Estimate") — may be absent
    #   Row 5+: More levels

    # Build column names by joining non-empty unique parts
    col_parts = []
    for col_idx in range(1, raw.shape[1]):  # skip Month column (col 0)
        parts = []
        seen = set()
        for row_idx in range(n_header_rows):
            val = str(header_rows.iloc[row_idx, col_idx]).strip()
            if val and val not in seen and val.lower() not in ("nan", "estimate"):
                parts.append(val)
                seen.add(val)
        col_parts.append("|".join(parts))

    # Data section
    data_raw = raw.iloc[data_start:, :].copy()
    data_raw = data_raw[data_raw.iloc[:, 0].apply(lambda x: _parse_month(x) is not None)]

    months = data_raw.iloc[:, 0].apply(_parse_month)
    counts = data_raw.iloc[:, 1:].copy()
    counts.columns = col_parts

    # Melt to long format
    counts["Month"] = months.values
    long = counts.melt(id_vars=["Month"], var_name="combo", value_name="Count")

    # Parse the combo column (Direction|CLPR|Visa|Citizenship)
    combo_parts = long["combo"].str.split("|", expand=True)
    n_parts = combo_parts.shape[1]

    # Assign based on expected number of header rows
    # Minimum: Direction, Visa, Citizenship (3 parts)
    # With CLPR: Direction, CLPR, Visa, Citizenship (4 parts)
    if n_parts >= 4:
        long["Direction"] = combo_parts[0]
        long["CLPR"] = combo_parts[1]
        long["Visa"] = combo_parts[2]
        long["Citizenship"] = combo_parts[3]
    elif n_parts == 3:
        long["Direction"] = combo_parts[0]
        long["CLPR"] = "India"  # inferred from download config (India only)
        long["Visa"] = combo_parts[1]
        long["Citizenship"] = combo_parts[2]
    else:
        raise ValueError(f"Unexpected number of column parts: {n_parts}. Check header structure.")

    long["Count"] = pd.to_numeric(long["Count"], errors="coerce")
    long = long.dropna(subset=["Month"])
    long = long[["Month", "Count", "Direction", "CLPR", "Visa", "Citizenship"]]
    long = long.sort_values(["Month", "Direction", "CLPR", "Visa", "Citizenship"]).reset_index(drop=True)

    print(f"  Rows: {len(long):,}")
    print(f"  Directions: {long['Direction'].unique()}")
    print(f"  CLPRs: {long['CLPR'].unique()}")
    print(f"  Visas: {long['Visa'].unique()}")
    print(f"  Citizenships (first 5): {long['Citizenship'].unique()[:5]}")

    return long


def main() -> None:
    raw_path = _find_raw_file()

    # Derive date suffix from filename (e.g. ITM55xxxx_20260520_...)
    date_match = re.search(r"_(\d{8})_", raw_path.name)
    date_suffix = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")

    df = process(raw_path)

    out_name = f"df_clpr_india_visa_{date_suffix}"
    pkl_path = INTERIM_DIR / f"{out_name}.pkl"
    csv_path = INTERIM_DIR / f"{out_name}.csv"

    df.to_pickle(pkl_path)
    df.to_csv(csv_path, index=False)

    print(f"\nSaved: {pkl_path.name}")
    print(f"Saved: {csv_path.name}")


if __name__ == "__main__":
    main()
