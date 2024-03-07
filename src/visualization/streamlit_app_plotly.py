import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import StringIO

import os

current_dir = os.path.dirname(__file__)

# Main title for the dashboard
st.title("New Zealand Migration Trends")

st.markdown(
    "A dashboard for visualizing monthly permanent and long-term migration data from Statistics NZ. <br><br>Refer to the article in [Autonomous Econ](https://autonomousecon.substack.com/publish/home). <br><br>Note: you can highlight a selected area of the plot to zoom in. You can also make the plot full screen by clicking on the expand icon in the top right hand corner of the plot. <br><br>Data last updated: 15 Feb 2024",
    unsafe_allow_html=True,
)


# Define the footer text
footer_text = """
<div style="text-align: right; font-size: 12px;">  <!-- Apply text alignment and font size here -->
    <div>Source: Stats NZ</div>
    <div>autonomousecon.substack.com</div>  <!-- Each <div> will be on its own line -->
</div>
"""


# Function to create a label for each unique combination
def create_label(row):
    if breakdown_type == "Direction, Citizenship":
        return f"{row['Direction']}, {row['Citizenship']}"
    elif breakdown_type == "Direction, Age, Sex":
        return f"{row['Direction']}, {row['Sex']}, {row['Age Group']}"
    elif breakdown_type == "Direction, Visa":  # New condition for Direction, Visa
        return f"{row['Direction']}, {row['Visa']}"


# Function to load datasets
@st.cache_data  # Use Streamlit's cache to load the data only once
def load_data(breakdown):
    # Get the current directory where the script is running
    current_dir = os.path.dirname(__file__)

    # Construct the path to the data file based on the breakdown
    if breakdown == "Direction, Citizenship":
        data_path = os.path.join(
            current_dir, "../../data/interim/df_citizenship_direction_202312.pkl"
        )
    elif breakdown == "Direction, Age, Sex":
        data_path = os.path.join(
            current_dir, "../../data/interim/df_direction_age_sex_202312.pkl"
        )
    elif breakdown == "Direction, Visa":
        data_path = os.path.join(
            current_dir, "../../data/interim/df_direction_visa_202312.pkl"
        )

    # Load the data from the constructed path
    df = pd.read_pickle(data_path)

    # Ensure the Month column is datetime type
    df["Month"] = pd.to_datetime(df["Month"])

    return df


# Select breakdown type
breakdown_type = st.selectbox(
    "Select the breakdown to explore:",
    ["Direction, Citizenship", "Direction, Age, Sex", "Direction, Visa"],
)

# Load the selected dataset
df = load_data(breakdown_type)

# Create tabs
tab1, tab2, tab3 = st.tabs(["Time Series Plot", "Stacked Area Plots", "Tree Maps"])

# Time Series Plot Tab
with tab1:
    if breakdown_type == "Direction, Citizenship":
        directions = st.multiselect(
            "Select directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        citizenship = st.multiselect(
            "Select Citizenship:",
            df["Citizenship"].unique(),
            default=df["Citizenship"].unique()[0],
        )
        filtered_df = df[
            (df["Direction"].isin(directions)) & (df["Citizenship"].isin(citizenship))
        ]
        plot_title = "Permanent and long term migration by Citizenship"
    elif breakdown_type == "Direction, Age, Sex":
        directions = st.multiselect(
            "Select directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        sex = st.multiselect(
            "Select Sex:", df["Sex"].unique(), default=df["Sex"].unique()[0]
        )
        age_group = st.multiselect(
            "Select age group:",
            df["Age Group"].unique(),
            default=df["Age Group"].unique()[:2],
        )
        filtered_df = df[
            df["Direction"].isin(directions)
            & df["Sex"].isin(sex)
            & df["Age Group"].isin(age_group)
        ]
        plot_title = f"Permanent and long term migration by age group"
    elif breakdown_type == "Direction, Visa":
        directions = st.multiselect(
            "Select directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        visa = st.multiselect(
            "Select visa type:",
            df["Visa"].unique(),
            default=df["Visa"].unique()[:2],
        )
        filtered_df = df[df["Direction"].isin(directions) & df["Visa"].isin(visa)]
        plot_title = f"Permanent and long term arrivals by visa type"

    # Apply the function to create a new column 'Label' for plotting
    filtered_df["Label"] = filtered_df.apply(create_label, axis=1)

    # Plotting with Plotly
    fig = px.line(
        filtered_df,
        x="Month",
        y="Count",
        color="Label",
        title=plot_title,
        markers=True,
    )  # Adding a horizontal line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="grey")
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(hovermode="closest")
    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="bottom",
            y=-0.5,  # Adjust this value to move the legend up or down relative to the bottom
            xanchor="center",
            x=0.5,  # Centers the legend horizontally
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    # Convert DataFrame to CSV string
    csv = filtered_df.to_csv(index=False)
    csv_file = StringIO(csv)
    csv_filename = "migration_data.csv"

    # Add a download button and specify the method to download the data
    st.download_button(
        label="Download Data as CSV",
        data=csv_file.getvalue(),
        file_name=csv_filename,
        mime="text/csv",
        key="download_timeseries",
    )
    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)


# Stacked Area Plots Tab
with tab2:
    direction = st.selectbox(
        "Select Direction:",
        df["Direction"].unique(),
        key="direction_select",  # Use a consistent key for the direction selectbox across conditions
    )

    if breakdown_type == "Direction, Citizenship":
        citizenships = st.multiselect(
            "Select Citizenships:",
            df["Citizenship"].unique(),
            default=df["Citizenship"].unique()[:2],
            key="citizenships",
        )
        filtered_df = df[
            (df["Direction"] == direction) & (df["Citizenship"].isin(citizenships))
        ]
        pivot_columns = "Citizenship"
        plot_title = f"Stacked Area Plot of {direction} by Citizenship"

    elif breakdown_type == "Direction, Age, Sex":
        sex = st.selectbox("Select Sex:", df["Sex"].unique(), key="sex_age_sex")
        age_groups = st.multiselect(
            "Select Age Groups:",
            df["Age Group"].unique(),
            default=df["Age Group"].unique()[:2],
            key="age_groups_age_sex",
        )
        filtered_df = df[
            (df["Direction"] == direction)
            & (df["Sex"] == sex)
            & (df["Age Group"].isin(age_groups))
        ]
        pivot_columns = "Age Group"
        plot_title = f"Stacked Area Plot of {direction} by age group ({sex}) "

    elif breakdown_type == "Direction, Visa":
        visas = st.multiselect(
            "Select Visa Type:",
            df["Visa"].unique(),
            default=df["Visa"].unique()[:2],
            key="visas_visa",
        )
        filtered_df = df[(df["Direction"] == direction) & (df["Visa"].isin(visas))]
        pivot_columns = "Visa"
        plot_title = f"Stacked Area Plot of {direction} by Visa type"

    # Preparing data for the plot
    pivot_df = filtered_df.pivot_table(
        index="Month", columns=pivot_columns, values="Count", aggfunc="sum"
    ).fillna(0)

    # Plotting with Plotly
    fig = px.area(pivot_df, facet_col_wrap=2)

    # Define a dictionary mapping breakdown types to legend title texts
    legend_title_map = {
        "Direction, Citizenship": "Citizenship",
        "Direction, Age, Sex": "Age Group",
        "Direction, Visa": "Visa",
    }

    # Use the breakdown_type to get the corresponding legend title text from the dictionary
    legend_title_text = legend_title_map.get(
        breakdown_type, "Category"
    )  # Default to "Category" if breakdown_type is not in the map

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Count",
        title=plot_title,
        legend_title_text=legend_title_text,
        hovermode="x unified",
    )

    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="bottom",
            y=-0.5,  # Adjust this value to move the legend up or down relative to the bottom
            xanchor="center",
            x=0.5,  # Centers the legend horizontally
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Convert DataFrame to CSV string
    csv = filtered_df.to_csv(index=False)
    csv_file = StringIO(csv)
    csv_filename = "migration_data.csv"

    # Add a download button and specify the method to download the data
    st.download_button(
        label="Download Data as CSV",
        data=csv_file.getvalue(),
        file_name=csv_filename,
        mime="text/csv",
        key="download_stackarea",
    )

    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)

# Treemap Tab
with tab3:
    # Setting up the minimum and maximum dates the user can select
    min_date = datetime(2001, 1, 1)
    max_date = datetime(2026, 12, 31)
    if breakdown_type == "Direction, Citizenship":
        # User input widgets
        direction = st.selectbox(
            "Select Direction:", df["Direction"].unique(), key="direction_treemap"
        )

        start_month = st.date_input(
            "Start month",
            value=datetime(2022, 1, 1),
            key="start_month",
            min_value=min_date,
            max_value=max_date,
        )

        end_month = st.date_input(
            "End month",
            value=datetime(2023, 12, 1),
            key="end_month",
            min_value=min_date,
            max_value=max_date,
        )
        color_map = {
            "New Zealand": "#2ca02c",  # Forest green
            "Australia": "#e7ba52",  # Gold
            "Fiji": "#8ca252",  # Sage
            "Tonga": "#ffbb78",  # Peach
            "Samoa": "#1f77b4",  # Vivid blue
            "China, People's Republic of": "#d62728",  # Brick red
            "Hong Kong (Special Administrative Region)": "#e377c2",  # Pink
            "Indonesia": "#ff9896",  # Salmon pink
            "India": "#9467bd",  # Medium purple
            "Japan": "#c5b0d5",  # Lavender
            "Korea, Republic of": "#8c564b",  # Brownish pink
            "Sri Lanka": "#c49c94",  # Rosy brown
            "Malaysia": "#98df8a",  # Soft lime
            "Nepal": "#f7b6d2",  # Pale pink
            "Philippines": "#7f7f7f",  # Grey
            "Pakistan": "#c7c7c7",  # Silver
            "Thailand": "#6b6ecf",  # Soft indigo
            "Taiwan": "#dbdb8d",  # Pale olive
            "Viet Nam": "#17becf",  # Cyan
            "Czechia": "#9edae5",  # Pale cyan
            "Germany": "#bcbd22",  # Olive green
            "France": "#5254a3",  # Indigo
            "United Kingdom": "#393b79",  # Dark blue
            "Ireland": "#9c9ede",  # Periwinkle
            "Italy": "#637939",  # Moss green
            "Netherlands": "#ff7f0e",  # Bright orange
            "Argentina": "#b5cf6b",  # Light olive
            "Brazil": "#cedb9c",  # Pale lime
            "Canada": "#8c6d31",  # Mustard
            "Chile": "#bd9e39",  # Bronze
            "United States of America": "#aec7e8",  # Light blue
            "South Africa": "#e7cb94",  # Khaki
        }

        exclude_nz = st.checkbox("Exclude New Zealand", value=True, key="exclude_nz")

        # Adjust the non_countries list based on checkbox
        non_countries = [
            "Oceania and Antarctica",
            "North-East Asia",
            "Southern and Central Asia",
            "South-East Asia",
            "Asia",
            "North-West Europe",
            "Southern and Eastern Europe",
            "Europe",
            "The Americas",
            "North Africa and the Middle East",
            "Sub-Saharan Africa",
            "Africa and the Middle East",
            "Non-New Zealand",
            "TOTAL ALL CITIZENSHIPS",
        ]

        if exclude_nz:
            non_countries.append("New Zealand")

        # Filtering DataFrame
        filtered_df = df[
            (df["Direction"] == direction)
            & (df["Month"] >= pd.to_datetime(start_month))
            & (df["Month"] <= pd.to_datetime(end_month))
            & (~df["Citizenship"].isin(non_countries))
        ]

        # Grouping and calculating percentage
        grouped_df = filtered_df.groupby(["Direction", "Citizenship"], as_index=False)[
            "Count"
        ].sum()
        total_counts_by_direction = grouped_df.groupby("Direction")["Count"].transform(
            "sum"
        )
        grouped_df["Percentage"] = (
            grouped_df["Count"] / total_counts_by_direction * 100
        ).round(1)

        grouped_df["Color"] = grouped_df["Citizenship"].map(color_map)

        # Creating the Treemap
        fig = go.Figure(
            go.Treemap(
                labels=grouped_df["Citizenship"],
                parents=grouped_df["Direction"],
                values=grouped_df["Count"],
                customdata=grouped_df["Percentage"],
                marker_colors=grouped_df["Color"],
                texttemplate="<b>%{label}</b><br>Count: %{value}</b><br>Share: %{customdata}%",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                branchvalues="total",
            )
        )

    elif breakdown_type == "Direction, Age, Sex":
        # User input widgets for Direction, Start month, and End month
        direction = st.selectbox(
            "Select Direction:", df["Direction"].unique(), key="direction_treemap_age"
        )
        sex = st.selectbox(
            "Select Sex:", df["Sex"].unique(), key="direction_treemap_sex"
        )
        start_month = st.date_input(
            "Start month",
            value=datetime(2022, 1, 1),
            key="start_month",
            min_value=min_date,
            max_value=max_date,
        )

        end_month = st.date_input(
            "End month",
            value=datetime(2023, 12, 1),
            key="end_month",
            min_value=min_date,
            max_value=max_date,
        )
        color_map = {
            "15-19 Years": "#e41a1c",  # Red
            "20-24 Years": "#377eb8",  # Blue
            "25-29 Years": "#4daf4a",  # Green
            "30-34 Years": "#984ea3",  # Purple
            "35-39 Years": "#ff7f00",  # Orange
            "40-44 Years": "#ffff33",  # Yellow
            "45-49 Years": "#a65628",  # Brown
            "50-54 Years": "#f781bf",  # Pink
            "55-59 Years": "#999999",  # Grey
            "60-64 Years": "#a6cee3",  # Light blue
            "Under 15 Years": "#b2df8a",  # Light green
            "65 Years and Over": "#fb9a99",  # Light red
        }

        # Filtering DataFrame for the selected direction and month range, excluding 'Total All Ages'
        filtered_df = df[
            (df["Direction"] == direction)
            & (df["Sex"] == sex)
            & (df["Month"] >= pd.to_datetime(start_month))
            & (df["Month"] <= pd.to_datetime(end_month))
            & (df["Age Group"] != "Total All Ages")  # Exclude 'Total All Ages'
        ]

        # Grouping by 'Direction' and 'Age', then calculating the count and percentage
        grouped_df = filtered_df.groupby(["Direction", "Age Group"], as_index=False)[
            "Count"
        ].sum()
        total_counts_by_direction = grouped_df.groupby("Direction")["Count"].transform(
            "sum"
        )
        grouped_df["Percentage"] = (
            grouped_df["Count"] / total_counts_by_direction * 100
        ).round(1)
        grouped_df["Color"] = grouped_df["Age Group"].map(color_map)

        # Creating the Treemap visualization for Age
        fig = go.Figure(
            go.Treemap(
                labels=grouped_df["Age Group"],
                parents=grouped_df["Direction"],
                values=grouped_df["Count"],
                customdata=grouped_df["Percentage"],
                marker_colors=grouped_df["Color"],
                texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                branchvalues="total",
            )
        )

    elif breakdown_type == "Direction, Visa":
        # User input widgets for Direction, Start month, and End month
        direction = st.selectbox(
            "Select Direction:", df["Direction"].unique(), key="direction_treemap_visa"
        )
        start_month = st.date_input(
            "Start month",
            value=datetime(2022, 1, 1),
            key="start_month",
            min_value=min_date,
            max_value=max_date,
        )

        end_month = st.date_input(
            "End month",
            value=datetime(2023, 12, 1),
            key="end_month",
            min_value=min_date,
            max_value=max_date,
        )
        color_map = {
            "Residence": "#E63946",  # Bright red
            "Student": "#F1C40F",  # Vivid yellow
            "Visitor": "#2ECC71",  # Emerald green
            "Work": "#3498DB",  # Bright blue
            "New Zealand and Australian citizens": "#9B59B6",  # Amethyst purple
            "Other": "#E67E22",  # Pumpkin orange
        }

        # Filtering DataFrame for the selected direction and month range, excluding 'Total All Ages'
        filtered_df = df[
            (df["Direction"] == direction)
            & (df["Month"] >= pd.to_datetime(start_month))
            & (df["Month"] <= pd.to_datetime(end_month))
            & (df["Visa"] != "TOTAL")  # Exclude 'Total'
        ]

        # Grouping by 'Direction' and 'Visa', then calculating the count and percentage
        grouped_df = filtered_df.groupby(["Direction", "Visa"], as_index=False)[
            "Count"
        ].sum()
        total_counts_by_direction = grouped_df.groupby("Direction")["Count"].transform(
            "sum"
        )
        grouped_df["Percentage"] = (
            grouped_df["Count"] / total_counts_by_direction * 100
        ).round(1)
        grouped_df["Color"] = grouped_df["Visa"].map(color_map)

        # Creating the Treemap visualization for Visa
        fig = go.Figure(
            go.Treemap(
                labels=grouped_df["Visa"],
                parents=grouped_df["Direction"],
                values=grouped_df["Count"],
                customdata=grouped_df["Percentage"],
                marker_colors=grouped_df["Color"],
                texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                branchvalues="total",
            )
        )

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    # Convert DataFrame to CSV string
    csv = grouped_df.to_csv(index=False)
    csv_file = StringIO(csv)
    csv_filename = "migration_data.csv"

    # Add a download button and specify the method to download the data
    st.download_button(
        label="Download Data as CSV",
        data=csv_file.getvalue(),
        file_name=csv_filename,
        mime="text/csv",
        key="download_treemap",
    )

    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)
