import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import combinations
import seaborn as sns
import numpy as np


class ExploratoryDataAnalysis:
    def __init__(self, df):
        self.df = df

    def plot_time_series_individual(self):
        """
        Plot each column of the DataFrame as a separate interactive time series using Plotly.

        Parameters:
        df (pandas.DataFrame): DataFrame with 'Month' as index and time series data in columns.
        """
        if self.df.index.name != "Month":
            print(
                "The index of the DataFrame is not 'Month'. Please set the 'Month' column as the index."
            )
            return

        for column in self.df.columns:
            fig = go.Figure(
                [
                    go.Scatter(
                        x=self.df.index, y=self.df[column], mode="lines", name=column
                    )
                ]
            )
            fig.update_layout(
                title=f"Time Series Plot of {column}",
                xaxis_title="Month",
                yaxis_title="Value",
                template="plotly_dark",
            )
            fig.show()

    def plot_dual_axis_time_series(self, column1, column2, shift_periods=0):
        """
        Plot two columns of a DataFrame as a time series with two different y-axes using Plotly.
        The second column can be shifted by a specified number of periods.

        Parameters:
        df (pandas.DataFrame): DataFrame with 'Month' as index.
        column1 (str): The name of the first column to plot.
        column2 (str): The name of the second column to plot.
        shift_periods (int): The number of periods to shift the second column. Positive for lag, negative for lead.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=self.df.index, y=self.df[column1], name=column1),
            secondary_y=False,
        )

        shifted_column2 = self.df[column2].shift(shift_periods)

        fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=shifted_column2,
                name=f"{column2} (shifted by {shift_periods})",
            ),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="Time Series with Dual Y-Axis",
            xaxis_title="Month",
            yaxis_title=column1,
            yaxis2_title=f"{column2} (shifted)",
            template="plotly_dark",
        )

        fig.show()

    def check_missing_values(self):
        """
        Check and report missing values in each column of the DataFrame.

        Parameters:
        df (pandas.DataFrame): The DataFrame to check for missing values.

        Returns:
        pandas.DataFrame: A DataFrame summarizing the count and percentage of missing values in each column.
        """
        missing_count = self.df.isnull().sum()
        missing_percentage = (missing_count / len(self.df)) * 100
        missing_df = pd.DataFrame(
            {"Missing Values": missing_count, "Percentage (%)": missing_percentage}
        )
        return missing_df[missing_df["Missing Values"] > 0].sort_values(
            by="Missing Values", ascending=False
        )

    def plot_histograms(self):
        """
        Plot histograms for each column in the DataFrame using Plotly.

        Parameters:
        df (pandas.DataFrame): The DataFrame containing the data to plot.
        """
        for column in self.df.columns:
            fig = go.Figure(data=[go.Histogram(x=self.df[column])])
            fig.update_layout(
                title_text=f"Histogram of {column}",
                xaxis_title_text=column,
                yaxis_title_text="Count",
                bargap=0.2,
                template="plotly_dark",
            )
            fig.show()

    def plot_boxplots(self):
        """
        Plot boxplots for each column in the DataFrame using Plotly.

        Parameters:
        df (pandas.DataFrame): The DataFrame containing the data to plot.
        """
        for column in self.df.columns:
            fig = go.Figure(data=[go.Box(y=self.df[column], name=column)])
            fig.update_layout(
                title_text=f"Boxplot of {column}",
                yaxis_title_text="Value",
                template="plotly_dark",
            )
            fig.show()

    def plot_all_scatter_combinations(self, col1=None, col2=None):
        """
        Plot 2D scatter plot combinations of columns in the DataFrame using Plotly.
        Plots all combinations by default, or specific columns if specified.

        Parameters:
        df (pandas.DataFrame): The DataFrame containing the data to plot.
        col1 (str, optional): The name of the first column to plot. Default is None.
        col2 (str, optional): The name of the second column to plot. Default is None.
        """
        if col1 is not None and col2 is not None:
            if col1 not in self.df.columns or col2 not in self.df.columns:
                raise ValueError("Specified columns are not in the DataFrame")
            column_pairs = [(col1, col2)]
        else:
            column_pairs = combinations(self.df.columns, 2)

        for col1, col2 in column_pairs:
            fig = go.Figure(
                data=go.Scatter(
                    x=self.df[col1],
                    y=self.df[col2],
                    mode="markers",
                    name=f"{col1} vs {col2}",
                )
            )
            fig.update_layout(
                title_text=f"Scatter Plot of {col1} vs {col2}",
                xaxis_title_text=col1,
                yaxis_title_text=col2,
                template="plotly_dark",
            )
            fig.show()

    def find_lead_lag_relationship(self, col1, col2, max_lag=12):
        """
        Find the lead and lag relationship between two columns using cross-correlation and plot with Plotly.

        Parameters:
        df (pandas.DataFrame): DataFrame containing the time series data.
        col1, col2 (str): Column names to compare.
        max_lag (int): Maximum number of lags/leads to consider.

        Returns:
        A Plotly figure showing cross-correlations for different lags.
        """
        if col1 not in self.df.columns or col2 not in self.df.columns:
            raise ValueError("Specified columns are not in the DataFrame")

        correlations = []
        for lag in range(-max_lag, max_lag + 1):
            shifted = self.df[col2].shift(lag)
            correlation = self.df[col1].corr(shifted)
            correlations.append(correlation)

        lags = np.arange(-max_lag, max_lag + 1)
        fig = go.Figure(data=go.Scatter(x=lags, y=correlations, mode="lines+markers"))
        fig.update_layout(
            title=f"Cross-Correlation between {col1} and {col2}",
            xaxis_title="Lag",
            yaxis_title="Correlation",
            template="plotly_dark",
        )
        fig.show()

    def create_pairgrid_plot_all_columns(self):
        """
        Create a PairGrid plot comparing all columns in a DataFrame using Seaborn.

        Parameters:
        df (pandas.DataFrame): The DataFrame containing the data.
        """
        g = sns.PairGrid(self.df)
        g.map(sns.scatterplot)
        g.fig.suptitle("PairGrid Plot for All Columns", fontsize=12, y=1.05)
