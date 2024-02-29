import streamlit as st
import pandas as pd
import plotly.express as px


# Function to load datasets
@st.cache_data  # Use Streamlit's cache to load the data only once
def load_data(breakdown):
    if breakdown == "Direction, Citizenship":
        df = pd.read_pickle("../../data/interim/df_citizenship_direction_202312.pkl")
    elif breakdown == "Direction, Age, Sex":
        df = pd.read_pickle("../../data/interim/df_direction_age_sex_202312.pkl")
    df["Month"] = pd.to_datetime(
        df["Month"]
    )  # Ensure the Month column is datetime type
    return df


# Select breakdown type
breakdown_type = st.selectbox(
    "Select breakdown", ["Direction, Citizenship", "Direction, Age, Sex"]
)

# Load the selected dataset
df = load_data(breakdown_type)

# Create tabs
tab1, tab2 = st.tabs(["Time Series Plot", "Stacked Area Plots"])

# Time Series Plot Tab
with tab1:
    # Define a function to create a label for each unique combination
    def create_label(row):
        if breakdown_type == "Direction, Citizenship":
            return f"{row['Direction']}, {row['Citizenship']}"
        else:  # Direction, Age, Sex
            return f"{row['Direction']}, {row['Sex']}, {row['Age Group']}"

    if breakdown_type == "Direction, Citizenship":
        directions = st.multiselect(
            "Select Directions:",
            df["Direction"].unique(),
            default=df["Direction"].unique()[0],
        )
        citizenship = st.multiselect("Select Citizenship:", df["Citizenship"].unique())
        filtered_df = df[
            (df["Direction"].isin(directions)) & (df["Citizenship"].isin(citizenship))
        ]
    else:  # Direction, Age, Sex
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

    # Apply the function to create a new column 'Label' for plotting
    filtered_df["Label"] = filtered_df.apply(create_label, axis=1)

    # Plotting with Plotly
    fig = px.line(
        filtered_df,
        x="Month",
        y="Count",
        color="Label",
        title="Time Series with Multiple Selections",
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
    if breakdown_type == "Direction, Citizenship":
        direction = st.selectbox("Select Direction:", df["Direction"].unique())
        citizenships = st.multiselect(
            "Select Citizenships:",
            df["Citizenship"].unique(),
            default=df["Citizenship"].unique()[:2],
        )
        filtered_df = df[
            (df["Direction"] == direction) & (df["Citizenship"].isin(citizenships))
        ]
        # Preparing data for the plot
        pivot_df = filtered_df.pivot_table(
            index="Month", columns="Citizenship", values="Count", aggfunc="sum"
        ).fillna(0)

    else:  # Direction, Age, Sex
        direction = st.selectbox("Select Direction:", df["Direction"].unique())
        sex = st.selectbox("Select Sex:", df["Sex"].unique())
        age_groups = st.multiselect(
            "Select Age Groups:",
            df["Age Group"].unique(),
            default=df["Age Group"].unique()[:2],
        )
        filtered_df = df[
            (df["Direction"] == direction)
            & (df["Sex"] == sex)
            & (df["Age Group"].isin(age_groups))
        ]
        # Preparing data for the plot
        pivot_df = filtered_df.pivot_table(
            index="Month", columns="Age Group", values="Count", aggfunc="sum"
        ).fillna(0)

    # Plotting with Plotly
    fig = px.area(pivot_df, facet_col_wrap=2)

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Count",
        title=(
            "Stacked Area Plot"
            if breakdown_type == "Direction, Citizenship"
            else "Stacked Area Plot for Direction, Age, Sex"
        ),
        legend_title_text=(
            "Age Group" if breakdown_type == "Direction, Age, Sex" else "Citizenship"
        ),
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
