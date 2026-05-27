# NZ Migration — Project Guide

## Overview

Two products live in this repo:
- **Streamlit app** — interactive explorer for NZ migration trends, deployed on Railway
- **Quarto dashboard** — single-page public site (GitHub Pages) that fact-checks political migration claims against Stats NZ data

## Quick-start

```bash
# Environment
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install -r requirements-dashboard.txt

# Streamlit app
streamlit run src/visualization/streamlit_app_plotly.py

# Dashboard build + preview
python src/build_dashboard.py   # regenerates dashboard/data/*.html
quarto render dashboard/        # outputs to docs/
quarto preview dashboard/       # opens browser preview
```

## Directory structure

```
nz_migration_streamlit/
├── data/
│   ├── raw/              # Raw CSVs from Stats NZ Infoshare (ITM55xxxx_YYYYMMDD_*.csv)
│   └── interim/          # Processed pkl + csv files (df_{slug}_{date}.pkl/csv)
├── dashboard/            # Quarto site source
│   ├── _quarto.yml       # output-dir: ../docs
│   ├── index.qmd         # Single scrollable page
│   └── data/             # Pre-generated chart HTML (gitignored — rebuilt each run)
├── docs/                 # Quarto render output — COMMITTED for GitHub Pages
├── output/               # Internal reports (fact_check_report.md etc.)
├── src/
│   ├── dashboard/        # Dashboard Python package (base, data_loader, stories)
│   ├── data/             # Data processing + download scripts
│   └── visualization/    # Streamlit app
├── railway.json          # Railway deployment config
└── requirements*.txt
```

## Workflow rules

@.claude/rules/data.md
@.claude/rules/quarto.md
@.claude/rules/streamlit.md
