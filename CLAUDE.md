# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based data visualization application for exploring New Zealand migration trends. The project processes raw migration data from Statistics NZ and provides interactive dashboards for analyzing permanent and long-term migration patterns by citizenship, age/sex demographics, and visa types.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (if not already done)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Run the main Streamlit dashboard (recommended)
streamlit run src/visualization/streamlit_app_plotly.py

# Alternative basic matplotlib version
streamlit run src/visualization/streamlit_app.py
```

### Data Processing
```bash
# Process raw data files into interim format (run each from src/data/)
cd src/data
python process_direction_citizenship.py  # ITM552301 → df_citizenship_direction_{date}.pkl/csv
python process_direction_age_sex.py      # ITM552101 → df_direction_age_sex_{date}.pkl/csv
python process_arrivals_visatype.py      # ITM552201 → df_direction_visa_{date}.pkl/csv
```
Each script auto-detects the latest matching `ITM55xxxx_*.csv` in `data/raw/` and derives the output date suffix from the filename.

### Data Download (automated)
```bash
# Download latest raw data from Stats NZ Infoshare
cd src/data
python download_stats_nz.py

# First-time setup
pip install playwright
playwright install chromium
```

## Project Architecture

### Directory Structure
- `src/data/` - Data processing scripts and utilities
- `src/visualization/` - Streamlit applications and plotting utilities
- `src/features/` - Business logic and feature engineering
- `src/models/` - Machine learning models (if any)
- `src/utility/` - Shared utilities like plot settings
- `data/raw/` - Raw CSV files from Statistics NZ
- `data/interim/` - Processed pickle and CSV files ready for visualization

### Key Components

**Data Processing Pipeline:**
- `src/data/process_direction_citizenship.py` - Processes ITM552301 raw CSV → `df_citizenship_direction_{date}.pkl/csv`
- `src/data/process_direction_age_sex.py` - Processes ITM552101 raw CSV → `df_direction_age_sex_{date}.pkl/csv`
- `src/data/process_arrivals_visatype.py` - Processes ITM552201 raw CSV → `df_direction_visa_{date}.pkl/csv`
- `src/data/data_processing.py` - Legacy `transform_dataframe_to_long_format()` utility (used by older scripts)

**Visualization Applications:**
- `src/visualization/streamlit_app_plotly.py` - Main interactive dashboard with time series plots, stacked area charts, and treemaps using Plotly
- `src/visualization/streamlit_app.py` - Basic version using matplotlib
- `src/visualization/visualize.py` - `ExploratoryDataAnalysis` class for programmatic plotting

### Data Flow
1. Raw CSV files are downloaded from Stats NZ Infoshare into `data/raw/` (filenames: `ITM55xxxx_YYYYMMDD_*.csv`)
2. Each `process_*.py` script parses the multi-row headers directly and converts to long format
3. Processed data is saved as both pickle and CSV in `data/interim/`
4. Streamlit apps load pickle files for interactive visualization

### Data Schema
Processed datasets follow this schema:
- `Month` (datetime) - Time period
- `Count` (numeric) - Migration count values
- Additional categorical columns depend on breakdown type:
  - Direction/Citizenship: `Direction`, `Citizenship`
  - Direction/Age/Sex: `Direction`, `Age Group`, `Sex`
  - Direction/Visa: `Direction`, `Visa`

### Key Dependencies
- **streamlit** - Web application framework
- **plotly** - Interactive plotting (main dashboard)
- **matplotlib/seaborn** - Static plotting (basic dashboard and EDA)
- **pandas** - Data manipulation and processing
- **numpy** - Numerical operations

## Important Notes

- Main data files use relative paths from script locations (`../../data/`)
- Streamlit cache is used extensively with `@st.cache_data` decorator for performance
- The application expects specific MultiIndex column structures in raw CSV files
- Color maps are predefined for consistent visualization across different breakdowns