import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import StringIO

import glob
import os

current_dir = os.path.dirname(__file__)
interim_dir = os.path.join(current_dir, "../../data/interim")

# Main title for the dashboard
st.title("New Zealand Migration Trends")

st.markdown(
    "A dashboard for visualizing monthly permanent and long-term migration data from Statistics NZ. <br><br>For a detailed insight into the data from this dashboard, refer to the article in [Autonomous Econ](https://autonomousecon.substack.com/p/new-zealands-millennial-migration). <br><br>Note: you can highlight a selected area of the plot to zoom in. You can also make the plot full screen by clicking on the expand icon in the top right hand corner of the plot. <br><br>Data last updated: 28 Sep 2025",
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
REGION_COLORS = {
    "Northland Region": "#e6194b",
    "Auckland Region": "#3cb44b",
    "Waikato Region": "#ffe119",
    "Bay of Plenty Region": "#4363d8",
    "Gisborne Region": "#f58231",
    "Hawke's Bay Region": "#911eb4",
    "Taranaki Region": "#42d4f4",
    "Manawatu-Wanganui Region": "#f032e6",
    "Wellington Region": "#bfef45",
    "Tasman Region": "#fabed4",
    "Nelson Region": "#469990",
    "Marlborough Region": "#dcbeff",
    "West Coast Region": "#9a6324",
    "Canterbury Region": "#fffac8",
    "Otago Region": "#800000",
    "Southland Region": "#aaffc3",
}

REGIONAL_COUNCILS = list(REGION_COLORS.keys())

TERRITORIAL_AUTHORITIES_BY_REGION = {
    "Northland Region": ["Far North District", "Whangarei District", "Kaipara District"],
    "Auckland Region": ["Auckland"],
    "Waikato Region": [
        "Thames-Coromandel District", "Hauraki District", "Waikato District",
        "Matamata-Piako District", "Hamilton City", "Waipa District",
        "Otorohanga District", "South Waikato District", "Waitomo District", "Taupo District",
    ],
    "Bay of Plenty Region": [
        "Western Bay of Plenty District", "Tauranga City", "Rotorua District",
        "Whakatane District", "Kawerau District", "Opotiki District",
    ],
    "Gisborne Region": ["Gisborne District"],
    "Hawke's Bay Region": ["Wairoa District", "Hastings District", "Napier City", "Central Hawke's Bay District"],
    "Taranaki Region": ["New Plymouth District", "Stratford District", "South Taranaki District"],
    "Manawatu-Wanganui Region": [
        "Ruapehu District", "Whanganui District", "Rangitikei District",
        "Manawatu District", "Palmerston North City", "Tararua District", "Horowhenua District",
    ],
    "Wellington Region": [
        "Kapiti Coast District", "Porirua City", "Upper Hutt City", "Lower Hutt City",
        "Wellington City", "Masterton District", "Carterton District", "South Wairarapa District",
    ],
    "Tasman Region": ["Tasman District"],
    "Nelson Region": ["Nelson City"],
    "Marlborough Region": ["Marlborough District", "Kaikoura District"],
    "West Coast Region": ["Buller District", "Grey District", "Westland District"],
    "Canterbury Region": [
        "Hurunui District", "Waimakariri District", "Christchurch City", "Selwyn District",
        "Ashburton District", "Timaru District", "Mackenzie District", "Waimate District",
        "Chatham Islands Territory",
    ],
    "Otago Region": [
        "Waitaki District", "Central Otago District", "Queenstown-Lakes District",
        "Dunedin City", "Clutha District",
    ],
    "Southland Region": ["Southland District", "Gore District", "Invercargill City"],
}

AUCKLAND_LOCAL_BOARDS = [
    "Albert-Eden local board area", "Devonport-Takapuna local board area",
    "Franklin local board area", "Great Barrier local board area",
    "Henderson-Massey local board area", "Hibiscus and Bays local board area",
    "Howick local board area", "Kaipatiki local board area",
    "Mangere-Otahuhu local board area", "Manurewa local board area",
    "Maungakiekie-Tamaki local board area", "Orakei local board area",
    "Otara-Papatoetoe local board area", "Papakura local board area",
    "Puketapapa local board area", "Rodney local board area",
    "Upper Harbour local board area", "Waiheke local board area",
    "Waitakere Ranges local board area", "Waitemata local board area",
    "Whau local board area",
]

ALL_TERRITORIAL_AUTHORITIES = [ta for tas in TERRITORIAL_AUTHORITIES_BY_REGION.values() for ta in tas]
TA_TO_REGION = {ta: region for region, tas in TERRITORIAL_AUTHORITIES_BY_REGION.items() for ta in tas}

AUCKLAND_LOCAL_BOARD_COLORS = {
    "Albert-Eden local board area": "#1f77b4",
    "Devonport-Takapuna local board area": "#ff7f0e",
    "Franklin local board area": "#2ca02c",
    "Great Barrier local board area": "#d62728",
    "Henderson-Massey local board area": "#9467bd",
    "Hibiscus and Bays local board area": "#8c564b",
    "Howick local board area": "#e377c2",
    "Kaipatiki local board area": "#7f7f7f",
    "Mangere-Otahuhu local board area": "#bcbd22",
    "Manurewa local board area": "#17becf",
    "Maungakiekie-Tamaki local board area": "#aec7e8",
    "Orakei local board area": "#ffbb78",
    "Otara-Papatoetoe local board area": "#98df8a",
    "Papakura local board area": "#ff9896",
    "Puketapapa local board area": "#c5b0d5",
    "Rodney local board area": "#c49c94",
    "Upper Harbour local board area": "#f7b6d2",
    "Waiheke local board area": "#c7c7c7",
    "Waitakere Ranges local board area": "#dbdb8d",
    "Waitemata local board area": "#9edae5",
    "Whau local board area": "#393b79",
}


def create_label(row):
    if breakdown_type == "Direction, Citizenship":
        return f"{row['Direction']}, {row['Citizenship']}"
    elif breakdown_type == "Direction, Age, Sex":
        return f"{row['Direction']}, {row['Sex']}, {row['Age Group']}"
    elif breakdown_type == "Direction, Visa":
        return f"{row['Direction']}, {row['Visa']}"
    elif breakdown_type == "Citizenship, Visa":
        return f"{row['Visa']}, {row['Citizenship']}"
    elif breakdown_type == "Direction, Region":
        return f"{row['Direction']}, {row['Region']}"


def _latest_pkl(pattern):
    """Return the path of the most recent .pkl file matching pattern."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No interim data files found matching: {pattern}")
    return files[-1]


def _apply_transform(df, transform, base_year=None):
    """Apply a time series transform to the filtered dataframe.

    Operates per-series (grouped by Label column). Returns the transformed
    dataframe and a y-axis label string.
    """
    df = df.sort_values(["Label", "Month"]).copy()
    if transform == "None":
        return df, "Count"
    elif transform == "Cumulative from base year":
        df = df[df["Month"].dt.year >= int(base_year)]
        df["Count"] = df.groupby("Label")["Count"].cumsum()
        return df, f"Cumulative count (from {int(base_year)})"
    elif transform == "3-month moving average":
        df["Count"] = df.groupby("Label")["Count"].transform(
            lambda s: s.rolling(3, min_periods=1).mean()
        )
        return df, "3-month moving average"
    elif transform == "12-month moving average":
        df["Count"] = df.groupby("Label")["Count"].transform(
            lambda s: s.rolling(12, min_periods=1).mean()
        )
        return df, "12-month moving average"
    elif transform == "3-month moving sum":
        df["Count"] = df.groupby("Label")["Count"].transform(
            lambda s: s.rolling(3, min_periods=1).sum()
        )
        return df, "3-month moving sum"
    elif transform == "12-month moving sum":
        df["Count"] = df.groupby("Label")["Count"].transform(
            lambda s: s.rolling(12, min_periods=1).sum()
        )
        return df, "12-month moving sum"


# Function to load datasets
@st.cache_data  # Use Streamlit's cache to load the data only once
def load_data(data_path):
    df = pd.read_pickle(data_path)
    df["Month"] = pd.to_datetime(df["Month"])
    return df


# Select breakdown type
breakdown_type = st.selectbox(
    "Select the breakdown to explore:",
    ["Direction, Citizenship", "Direction, Age, Sex", "Direction, Visa", "Citizenship, Visa", "Direction, Region"],
)

# Resolve the latest interim file for the selected breakdown
_patterns = {
    "Direction, Citizenship": os.path.join(interim_dir, "df_citizenship_direction_*.pkl"),
    "Direction, Age, Sex":    os.path.join(interim_dir, "df_direction_age_sex_*.pkl"),
    "Direction, Visa":        os.path.join(interim_dir, "df_direction_visa_*.pkl"),
    "Citizenship, Visa":      os.path.join(interim_dir, "df_citizenship_visa_*.pkl"),
    "Direction, Region":      os.path.join(interim_dir, "df_direction_region_*.pkl"),
}
data_path = _latest_pkl(_patterns[breakdown_type])

# Load the selected dataset
df = load_data(data_path)

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
    elif breakdown_type == "Citizenship, Visa":
        citizenship = st.multiselect(
            "Select Citizenship:",
            sorted(df["Citizenship"].unique()),
            default=sorted(df["Citizenship"].unique())[:3],
        )
        visa = st.multiselect(
            "Select visa type:",
            [v for v in df["Visa"].unique() if v != "TOTAL"],
            default=[v for v in df["Visa"].unique() if v not in ("TOTAL", "New Zealand and Australian citizens")][:3],
        )
        filtered_df = df[
            df["Citizenship"].isin(citizenship)
            & df["Visa"].isin(visa)
        ]
        plot_title = "Migrant arrivals by citizenship and visa type"
    elif breakdown_type == "Direction, Region":
        directions = st.multiselect(
            "Select directions:",
            df["Direction"].unique(),
            default=["Arrivals"],
        )
        level_t1 = st.radio(
            "Area level:",
            ["Regional Councils", "Territorial Authorities", "Auckland Local Boards"],
            key="level_t1_region",
        )
        if level_t1 == "Regional Councils":
            region_options_t1 = REGIONAL_COUNCILS
            default_t1 = REGIONAL_COUNCILS
        elif level_t1 == "Territorial Authorities":
            filter_regions_t1 = st.multiselect(
                "Filter by region:",
                REGIONAL_COUNCILS,
                default=REGIONAL_COUNCILS,
                key="filter_regions_t1",
            )
            region_options_t1 = [
                ta for r in filter_regions_t1
                for ta in TERRITORIAL_AUTHORITIES_BY_REGION.get(r, [])
            ]
            default_t1 = region_options_t1[:5]
        else:
            region_options_t1 = AUCKLAND_LOCAL_BOARDS
            default_t1 = AUCKLAND_LOCAL_BOARDS
        region = st.multiselect(
            "Select area:",
            region_options_t1,
            default=default_t1,
            key="region_t1",
        )
        filtered_df = df[df["Direction"].isin(directions) & df["Region"].isin(region)]
        plot_title = "Migration by direction and NZ area"

    # Apply the function to create a new column 'Label' for plotting
    filtered_df["Label"] = filtered_df.apply(create_label, axis=1)

    # ── Transform controls ──
    st.markdown("---")
    transform = st.selectbox(
        "Transform",
        [
            "None",
            "Cumulative from base year",
            "3-month moving average",
            "12-month moving average",
            "3-month moving sum",
            "12-month moving sum",
        ],
        key="transform_select",
    )
    base_year = None
    if transform == "Cumulative from base year":
        base_year = st.number_input(
            "Base year", min_value=2001, max_value=2025, value=2022, step=1
        )
    filtered_df, y_label = _apply_transform(filtered_df, transform, base_year)

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
    fig.update_layout(hovermode="closest", yaxis_title=y_label)
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
    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)
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


# Stacked Area Plots Tab
with tab2:
    if breakdown_type not in ("Citizenship, Visa",):
        direction = st.selectbox(
            "Select Direction:",
            df["Direction"].unique(),
            key="direction_select",
        )
    else:
        direction = "Arrivals"

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
    elif breakdown_type == "Citizenship, Visa":
        citizenships_area = st.multiselect(
            "Select Citizenship:",
            sorted(df["Citizenship"].unique()),
            default=sorted(df["Citizenship"].unique())[:5],
            key="citizenships_area",
        )
        visas_area = st.multiselect(
            "Select Visa Type:",
            [v for v in df["Visa"].unique() if v != "TOTAL"],
            default=[v for v in df["Visa"].unique() if v != "TOTAL"],
            key="visas_area",
        )
        filtered_df = df[
            df["Citizenship"].isin(citizenships_area)
            & df["Visa"].isin(visas_area)
        ]
        pivot_columns = "Visa"
        plot_title = "Stacked Area: Arrivals by visa type"
    elif breakdown_type == "Direction, Region":
        level_t2 = st.radio(
            "Area level:",
            ["Regional Councils", "Territorial Authorities", "Auckland Local Boards"],
            key="level_t2_region",
        )
        if level_t2 == "Regional Councils":
            region_options_t2 = REGIONAL_COUNCILS
            default_t2 = REGIONAL_COUNCILS
        elif level_t2 == "Territorial Authorities":
            filter_regions_t2 = st.multiselect(
                "Filter by region:",
                REGIONAL_COUNCILS,
                default=["Auckland Region", "Canterbury Region", "Wellington Region"],
                key="filter_regions_t2",
            )
            region_options_t2 = [
                ta for r in filter_regions_t2
                for ta in TERRITORIAL_AUTHORITIES_BY_REGION.get(r, [])
            ]
            default_t2 = region_options_t2[:5]
        else:
            region_options_t2 = AUCKLAND_LOCAL_BOARDS
            default_t2 = AUCKLAND_LOCAL_BOARDS
        regions_area = st.multiselect(
            "Select areas:",
            region_options_t2,
            default=default_t2,
            key="regions_area",
        )
        filtered_df = df[
            (df["Direction"] == direction)
            & df["Region"].isin(regions_area)
        ]
        pivot_columns = "Region"
        plot_title = f"Stacked Area: {direction} by NZ area"

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
        "Citizenship, Visa": "Visa",
        "Direction, Region": "Region",
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

    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)

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

    elif breakdown_type == "Citizenship, Visa":
        visa_color_map = {
            "Residence": "#E63946",
            "Student": "#F1C40F",
            "Visitor": "#2ECC71",
            "Work": "#3498DB",
            "New Zealand and Australian citizens": "#9B59B6",
            "Other": "#E67E22",
        }
        direction_treemap = st.selectbox(
            "Select Direction:", ["Arrivals"], key="direction_treemap_cv"
        )
        start_month = st.date_input(
            "Start month",
            value=datetime(2022, 1, 1),
            key="start_month_cv",
            min_value=min_date,
            max_value=max_date,
        )
        end_month = st.date_input(
            "End month",
            value=datetime(2023, 12, 31),
            key="end_month_cv",
            min_value=min_date,
            max_value=max_date,
        )
        filtered_df = df[
            (df["Month"] >= pd.to_datetime(start_month))
            & (df["Month"] <= pd.to_datetime(end_month))
            & (df["Visa"] != "TOTAL")
            & (df["Citizenship"] != "Total All Countries of Last Permanent Residence")
        ]
        grouped_df = filtered_df.groupby(["Visa", "Citizenship"], as_index=False)["Count"].sum()

        # Two-level treemap: Visa (parent) → Citizenship (leaf)
        visa_agg = grouped_df.groupby("Visa", as_index=False)["Count"].sum()
        visa_agg["Percentage"] = (visa_agg["Count"] / visa_agg["Count"].sum() * 100).round(1)

        leaf_pct_denom = grouped_df.groupby("Visa")["Count"].transform("sum")
        grouped_df["Percentage"] = (grouped_df["Count"] / leaf_pct_denom * 100).round(1)

        ids = list(visa_agg["Visa"]) + [
            f"{r['Visa']}|{r['Citizenship']}" for _, r in grouped_df.iterrows()
        ]
        labels = list(visa_agg["Visa"]) + list(grouped_df["Citizenship"])
        parents = [""] * len(visa_agg) + list(grouped_df["Visa"])
        values = list(visa_agg["Count"]) + list(grouped_df["Count"])
        customdata = list(visa_agg["Percentage"]) + list(grouped_df["Percentage"])
        colors = [visa_color_map.get(v, "#aaaaaa") for v in visa_agg["Visa"]] + [
            visa_color_map.get(r["Visa"], "#aaaaaa") for _, r in grouped_df.iterrows()
        ]

        fig = go.Figure(
            go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                customdata=customdata,
                marker_colors=colors,
                texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                branchvalues="total",
            )
        )

    elif breakdown_type == "Direction, Region":
        direction = st.selectbox(
            "Select Direction:", df["Direction"].unique(), key="direction_treemap_region"
        )
        level_t3 = st.radio(
            "Area level:",
            ["Regional Councils", "Territorial Authorities", "Auckland Local Boards"],
            key="level_t3_region",
        )
        start_month = st.date_input(
            "Start month",
            value=datetime(2022, 1, 1),
            key="start_month_region",
            min_value=min_date,
            max_value=max_date,
        )
        end_month = st.date_input(
            "End month",
            value=datetime(2023, 12, 31),
            key="end_month_region",
            min_value=min_date,
            max_value=max_date,
        )
        if level_t3 == "Regional Councils":
            filtered_df = df[
                (df["Direction"] == direction)
                & (df["Month"] >= pd.to_datetime(start_month))
                & (df["Month"] <= pd.to_datetime(end_month))
                & (df["Region"].isin(REGIONAL_COUNCILS))
            ]
            grouped_df = filtered_df.groupby(["Direction", "Region"], as_index=False)["Count"].sum()
            total_by_dir = grouped_df.groupby("Direction")["Count"].transform("sum")
            grouped_df["Percentage"] = (grouped_df["Count"] / total_by_dir * 100).round(1)
            grouped_df["Color"] = grouped_df["Region"].map(REGION_COLORS)
            fig = go.Figure(
                go.Treemap(
                    labels=grouped_df["Region"],
                    parents=grouped_df["Direction"],
                    values=grouped_df["Count"],
                    customdata=grouped_df["Percentage"],
                    marker_colors=grouped_df["Color"],
                    texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                    branchvalues="total",
                )
            )
        elif level_t3 == "Territorial Authorities":
            filtered_df = df[
                (df["Direction"] == direction)
                & (df["Month"] >= pd.to_datetime(start_month))
                & (df["Month"] <= pd.to_datetime(end_month))
                & (df["Region"].isin(ALL_TERRITORIAL_AUTHORITIES))
            ]
            leaf_df = filtered_df.groupby("Region", as_index=False)["Count"].sum()
            leaf_df["ParentRegion"] = leaf_df["Region"].map(TA_TO_REGION)
            leaf_df = leaf_df[leaf_df["ParentRegion"].notna()].copy()
            region_agg = leaf_df.groupby("ParentRegion", as_index=False)["Count"].sum()
            region_agg.rename(columns={"ParentRegion": "Region"}, inplace=True)
            leaf_df["Percentage"] = (
                leaf_df["Count"]
                / leaf_df.groupby("ParentRegion")["Count"].transform("sum")
                * 100
            ).round(1)
            region_agg["Percentage"] = (region_agg["Count"] / region_agg["Count"].sum() * 100).round(1)
            ids = list(region_agg["Region"]) + [
                f"{r['ParentRegion']}|{r['Region']}" for _, r in leaf_df.iterrows()
            ]
            labels = list(region_agg["Region"]) + list(leaf_df["Region"])
            parents = [""] * len(region_agg) + list(leaf_df["ParentRegion"])
            values = list(region_agg["Count"]) + list(leaf_df["Count"])
            customdata = list(region_agg["Percentage"]) + list(leaf_df["Percentage"])
            colors = [REGION_COLORS.get(r, "#aaaaaa") for r in region_agg["Region"]] + [
                REGION_COLORS.get(r, "#aaaaaa") for r in leaf_df["ParentRegion"]
            ]
            grouped_df = leaf_df.rename(columns={"Region": "TA", "ParentRegion": "Region"})
            fig = go.Figure(
                go.Treemap(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values,
                    customdata=customdata,
                    marker_colors=colors,
                    texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                    branchvalues="total",
                )
            )
        else:  # Auckland Local Boards
            filtered_df = df[
                (df["Direction"] == direction)
                & (df["Month"] >= pd.to_datetime(start_month))
                & (df["Month"] <= pd.to_datetime(end_month))
                & (df["Region"].isin(AUCKLAND_LOCAL_BOARDS))
            ]
            grouped_df = filtered_df.groupby("Region", as_index=False)["Count"].sum()
            total = grouped_df["Count"].sum()
            grouped_df["Percentage"] = (grouped_df["Count"] / total * 100).round(1)
            ids = ["Auckland Region"] + list(grouped_df["Region"])
            labels = ["Auckland Region"] + list(grouped_df["Region"])
            parents = [""] + ["Auckland Region"] * len(grouped_df)
            values = [total] + list(grouped_df["Count"])
            customdata = [100.0] + list(grouped_df["Percentage"])
            colors = [REGION_COLORS.get("Auckland Region", "#3cb44b")] + [
                AUCKLAND_LOCAL_BOARD_COLORS.get(r, "#aaaaaa") for r in grouped_df["Region"]
            ]
            fig = go.Figure(
                go.Treemap(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values,
                    customdata=customdata,
                    marker_colors=colors,
                    texttemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{customdata}%<extra></extra>",
                    branchvalues="total",
                )
            )

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    # Using st.markdown to create a flex container with two text elements, with adjusted font size
    st.markdown(footer_text, unsafe_allow_html=True)
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
