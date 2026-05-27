# Streamlit App Rules

## Running locally

```bash
streamlit run src/visualization/streamlit_app_plotly.py
```

## Key files

| File | Purpose |
|---|---|
| `src/visualization/streamlit_app_plotly.py` | Main interactive dashboard — 5 breakdown types, Plotly charts |
| `src/visualization/visualize.py` | `ExploratoryDataAnalysis` class for programmatic/static plotting |
| `src/utility/` | Shared plot settings and utilities |

## Supported breakdown types

1. Direction × Citizenship (`df_citizenship_direction`)
2. Direction × Age/Sex (`df_direction_age_sex`)
3. Direction × Visa type (`df_direction_visa`)
4. Citizenship × Visa type (`df_citizenship_visa`)
5. Direction × Region (`df_direction_region`)

## Caching

All data-loading functions use `@st.cache_data`. Do not remove — the pkl files are read on every interaction without it.

## Color maps

Predefined per breakdown type at module level. Consistent across all chart types (time series, stacked area, treemap). Do not redefine inline.

## Railway deployment

Config: `railway.json` at repo root.

**Start command:**
```
streamlit run src/visualization/streamlit_app_plotly.py \
  --server.address 0.0.0.0 \
  --server.port $PORT \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false \
  --client.showErrorDetails false \
  --client.toolbarMode minimal \
  --server.enableStaticServing false \
  --server.enableCORS false \
  --server.enableXsrfProtection true
```

**Deploy process:**
1. Push to the connected branch (check Railway dashboard for which branch is linked)
2. Railway auto-detects `railway.json` and runs the start command
3. `$PORT` is injected by Railway — do not hardcode a port

**Key flags:**
- `--server.fileWatcherType none` — disables inotify (not available on Railway's filesystem)
- `--server.enableCORS false` — required for Railway's proxy layer
- `--client.toolbarMode minimal` — hides the Streamlit hamburger menu in production
