# Data Workflow Rules

## Processing scripts

Run from repo root. Each script auto-detects the latest matching raw file in `data/raw/`.

| Script | Input | Output |
|---|---|---|
| `src/data/process_direction_citizenship.py` | ITM552301 | `df_citizenship_direction_{date}.pkl/csv` |
| `src/data/process_direction_age_sex.py` | ITM552101 | `df_direction_age_sex_{date}.pkl/csv` |
| `src/data/process_arrivals_visatype.py` | ITM552201 | `df_direction_visa_{date}.pkl/csv` |
| `src/data/process_clpr_india_visa.py` | ITM553001 | `df_clpr_india_visa_{date}.pkl/csv` |
| `src/data/process_direction_region.py` | ITM553701 (4 files: total/nz/au/non_nz) | `df_direction_region_{date}.pkl/csv` |

Download latest raw files first: `python src/data/download_stats_nz.py`

## Data schema

| Dataset | Columns |
|---|---|
| df_citizenship_direction | Month, Count, Direction, Citizenship |
| df_direction_age_sex | Month, Count, Direction, Age Group, Sex |
| df_direction_visa | Month, Count, Direction, Visa |
| df_clpr_india_visa | Month, Count, Direction, CLPR, Visa, Citizenship |
| df_direction_region | Month, Count, Direction, Citizenship, Region |

All `Month` columns are `pd.Timestamp`. `Count` is `float64` in new files, `int64` in legacy 202312 reference files — both are fine.

## Raw CSV header structure

Stats NZ Infoshare files have multi-row headers before data rows (first data row = `2001M01`):

| Dataset | Header rows | Row breakdown |
|---|---|---|
| ITM552301 | 4 | title / direction / citizenship / estimate |
| ITM552101 | 5 | title / direction / age group / sex / estimate |
| ITM552201 | 4 | title / direction / visa type / estimate |
| ITM553001 | 6 | title / direction / citizenship / visa type / CLPR country / estimate |
| ITM553701 | 6 | title / period / direction / citizenship / NZ area / estimate — row 3 (citizenship) is now extracted per file, not skipped |

## ITM553001 (CLPR dataset) — specifics

Dataset: "Estimated migrant arrivals by citizenship, visa type and CLPR, 12/16-month rule (Monthly)"

**6-row header structure (rows 0–5):**
- Row 0: Dataset title — **SKIP** when building column names (corrupts dimension mapping if included)
- Row 1: Direction (`"Arrivals"`)
- Row 2: Citizenship (`"Non-New Zealand"` aggregate — one value, constant across all columns)
- Row 3: Visa type (Residence | Student | Visitor | Work | NZ and Australian citizens | Other | TOTAL — each spanning 25 cols)
- Row 4: CLPR country (UAE, Australia, Canada, China, ... India, ..., Total All Countries — 25 values, repeating per visa type)
- Row 5: Estimate type (`"Estimate"`) — skip

**Processing:**
- Build column names by iterating rows 1–5 (skip row 0)
- After melting: `combo_parts[0]`=Direction, `[1]`=Citizenship, `[2]`=Visa, `[3]`=CLPR
- Filter `CLPR == "India"` before saving — all 7 visa types are retained
- File detected by: `glob("ITM553001_*.csv")` in `data/raw/`

## File naming

Interim files: `df_{slug}_{YYYYMMDD}.pkl` and `.csv` where date comes from the raw filename.
`DataLoader` picks the lexicographically latest file matching each pattern.

## Windows print() encoding

Use **ASCII-only characters** in all `print()` statements in data scripts. Unicode box-drawing (`──`), arrows (`→`), and emoji (`✅`) crash with `UnicodeEncodeError` on Windows cp1252 terminal. Use dashes (`---`), `"to"`, and plain text instead.
