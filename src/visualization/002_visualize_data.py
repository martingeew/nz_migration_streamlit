import pandas as pd
from visualize import ExploratoryDataAnalysis

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------

data = pd.read_pickle("../../data/interim/merged_india_nz_arrivals_data.pkl")

# --------------------------------------------------------------
# Create plots
# --------------------------------------------------------------

# Example usage
# data = pd.read_csv('your_data.csv') or data = pd.read_pickle('your_data.pkl')
# eda = ExploratoryDataAnalysis(df)
# eda.plot_time_series_individual()
# eda.plot_dual_axis_time_series('column1', 'column2')
# ... and so on for other methods

eda = ExploratoryDataAnalysis(data)

# Vizualise the data
eda.plot_time_series_individual()
eda.plot_dual_axis_time_series('india_arrivals_esimate', 'India_visa_search')

# Check missing values
eda.check_missing_values()

# Check distribution
eda.plot_histograms()
eda.plot_boxplots()

# Check correlations
eda.create_pairgrid_plot_all_columns()
eda.plot_all_scatter_combinations()  # Plots all combinations as individual plots
eda.plot_all_scatter_combinations('india_arrivals_esimate', 'India_visa_search')  # Plots only col1 vs col2
eda.find_lead_lag_relationship('india_arrivals_esimate', 'India_visa_search', max_lag=36)
eda.plot_dual_axis_time_series('india_arrivals_esimate', 'India_visa_search', shift_periods=12)

