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
    """Find the most recently downloaded CLPR raw CSV (ITM553001).

    The CLPR dataset (citizenship × visa type × CLPR) is published under
    ITM553001 on Stats NZ Infoshare.
    """
    candidates = sorted(
        RAW_DIR.glob("ITM553001_*.csv"), key=lambda p: p.stat().st_mtime
    )
    if candidates:
        return candidates[-1]
    raise FileNotFoundError(
        f"No CLPR raw CSV (ITM553001) found in {RAW_DIR}. "
        "Run: python src/data/download_stats_nz.py --dataset itm_citizenship_visa"
    )


def _parse_month(s: str) -> pd.Timestamp | None:
    """Parse YYYYM## format → Timestamp, return None for non-data rows."""
    if re.match(r"^\d{4}M\d{2}$", str(s)):
        return pd.to_datetime(s, format="%YM%m")
    return None


# ── Main processing ────────────────────────────────────────────────────────────

def process(raw_path: Path) -> pd.DataFrame:
    """Parse the raw CLPR CSV (ITM553001) into long-format DataFrame.

    The raw file header structure (6 rows):
        Row 0: Dataset title — skip when building column names
        Row 1: Direction       ("Arrivals")
        Row 2: Citizenship     ("Non-New Zealand" aggregate)
        Row 3: Visa type       (Residence | Student | Visitor | Work | NZ/AU | Other | TOTAL)
        Row 4: CLPR country    (UAE | Australia | ... | India | ... | Total)
        Row 5: Estimate type   ("Estimate") — skipped

    Args:
        raw_path: Path to the raw ITM553001 CSV file.

    Returns:
        Long-format DataFrame (all CLPR countries) with columns:
        Month, Count, Direction, CLPR, Visa, Citizenship
    """
    print(f"Processing: {raw_path.name}")

    # Read raw CSV without header
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

    # Forward-fill each header row across columns so sparse labels propagate
    header_rows = raw.iloc[:n_header_rows, :].ffill(axis=1)

    # Build column names by joining non-empty unique parts.
    # Start from row 1 to skip the dataset title in row 0.
    # Also skip "estimate" rows (not useful as a dimension label).
    col_parts = []
    for col_idx in range(1, raw.shape[1]):  # skip Month column (col 0)
        parts = []
        seen: set[str] = set()
        for row_idx in range(1, n_header_rows):  # row 0 = title, skip it
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

    # Parse combo into dimensions.
    # With row 0 skipped, each combo has 3–4 parts:
    #   Direction | Citizenship | Visa | CLPR country   (4 parts — expected)
    #   Direction | Visa | CLPR country                 (3 parts — fallback)
    combo_parts = long["combo"].str.split("|", expand=True)
    n_parts = combo_parts.shape[1]
    print(f"  Column parts per combo: {n_parts}  (sample: {long['combo'].iloc[0]})")

    if n_parts >= 4:
        long["Direction"] = combo_parts[0]
        long["Citizenship"] = combo_parts[1]
        long["Visa"] = combo_parts[2]
        long["CLPR"] = combo_parts[3]
    elif n_parts == 3:
        long["Direction"] = combo_parts[0]
        long["Citizenship"] = "Non-New Zealand"
        long["Visa"] = combo_parts[1]
        long["CLPR"] = combo_parts[2]
    else:
        raise ValueError(f"Unexpected number of column parts: {n_parts}. Check header structure.")

    long["Count"] = pd.to_numeric(long["Count"], errors="coerce")
    long = long.dropna(subset=["Month"])

    long = long[["Month", "Count", "Direction", "CLPR", "Visa", "Citizenship"]]
    long = long.sort_values(["Month", "Direction", "Visa"]).reset_index(drop=True)

    return long


def _filter_clpr(long: pd.DataFrame, clpr: str) -> pd.DataFrame:
    """Filter long-format data to a single CLPR country."""
    filtered = long[long["CLPR"] == clpr].copy().reset_index(drop=True)
    print(f"  Rows (CLPR = {clpr}): {len(filtered):,}")
    if len(filtered):
        print(f"  Visas: {filtered['Visa'].unique()}")
        print(f"  Date range: {filtered['Month'].min()} to {filtered['Month'].max()}")
    else:
        print(f"  WARNING: no rows matched CLPR = {clpr!r}")
        print(f"  Available CLPR values: {sorted(long['CLPR'].unique())}")
    return filtered


def _save(df: pd.DataFrame, slug: str, date_suffix: str) -> None:
    out_name = f"df_clpr_{slug}_visa_{date_suffix}"
    pkl_path = INTERIM_DIR / f"{out_name}.pkl"
    csv_path = INTERIM_DIR / f"{out_name}.csv"
    df.to_pickle(pkl_path)
    df.to_csv(csv_path, index=False)
    print(f"  Saved: {pkl_path.name}")
    print(f"  Saved: {csv_path.name}")


def main() -> None:
    raw_path = _find_raw_file()

    # Derive date suffix from filename (e.g. ITM55xxxx_20260520_...)
    date_match = re.search(r"_(\d{8})_", raw_path.name)
    date_suffix = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")

    long = process(raw_path)

    print("\n--- India ---")
    _save(_filter_clpr(long, "India"), "india", date_suffix)

    print("\n--- China ---")
    _save(_filter_clpr(long, "China, People's Republic of"), "china", date_suffix)


if __name__ == "__main__":
    main()
