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
# Process raw data files into interim format
cd src/data
python 001_process_data.py
```

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
- `src/data/data_processing.py` - Core transformation function `transform_dataframe_to_long_format()` that converts MultiIndex column structures to long format suitable for visualization
- `src/data/001_process_data.py` - Main processing script that transforms raw CSV files with complex headers into standardized long-format datasets

**Visualization Applications:**
- `src/visualization/streamlit_app_plotly.py` - Main interactive dashboard with time series plots, stacked area charts, and treemaps using Plotly
- `src/visualization/streamlit_app.py` - Basic version using matplotlib
- `src/visualization/visualize.py` - `ExploratoryDataAnalysis` class for programmatic plotting

### Data Flow
1. Raw CSV files with MultiIndex headers are loaded from `data/raw/`
2. `transform_dataframe_to_long_format()` processes them into long format with separate columns for attributes
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