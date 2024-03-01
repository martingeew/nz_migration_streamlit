import streamlit as st
import pandas as pd
import plotly.express as px


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
    if breakdown == "Direction, Citizenship":
        df = pd.read_pickle("../../data/interim/df_citizenship_direction_202312.pkl")
    elif breakdown == "Direction, Age, Sex":
        df = pd.read_pickle("../../data/interim/df_direction_age_sex_202312.pkl")
    elif breakdown == "Direction, Visa":
        df = pd.read_pickle("../../data/interim/df_direction_visa_202312.pkl")
    df["Month"] = pd.to_datetime(
        df["Month"]
    )  # Ensure the Month column is datetime type
    return df


# Select breakdown type
breakdown_type = st.selectbox(
    "Select breakdown",
    ["Direction, Citizenship", "Direction, Age, Sex", "Direction, Visa"],
)

# Load the selected dataset
df = load_data(breakdown_type)

# Create tabs
tab1, tab2 = st.tabs(["Time Series Plot", "Stacked Area Plots"])

# Time Series Plot Tab
with tab1:
    if breakdown_type == "Direction, Citizenship":
        directions = st.multiselect(
            "Select Directions:",
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
            "Select Directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        sex = st.multiselect(
            "Select Sex:", df["Sex"].unique(), default=df["Sex"].unique()[0]
        )
        age_group = st.multiselect(
            "Select Age Group:",
            df["Age Group"].unique(),
            default=df["Age Group"].unique()[:2],
        )
        filtered_df = df[
            df["Direction"].isin(directions)
            & df["Sex"].isin(sex)
            & df["Age Group"].isin(age_group)
        ]
        plot_title = f"Permanent and long term migration by age group"
    elif breakdown_type == "Direction, Visa":  # New inclusion for Direction, Visa
        directions = st.multiselect(
            "Select Directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        visa = st.multiselect(
            "Select Visa Type:",
            df["Visa"].unique(),
            default=df["Visa"].unique()[:2],
        )
        filtered_df = df[df["Direction"].isin(directions) & df["Visa"].isin(visa)]
        plot_title = f"Permanent and long term arrivals by Visa type"

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
    )
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
