import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# Load the dataset
@st.cache_data  # Use Streamlit's cache to load the data only once
def load_data():
    df = pd.read_pickle("../../data/interim/df_citizenship_direction_202312.pkl")
    df["Month"] = pd.to_datetime(
        df["Month"]
    )  # Ensure the Month column is datetime type
    return df


df = load_data()

# Create tabs
tab1, tab2 = st.tabs(["Time Series Plot", "Stacked Area Plots"])

# Time Series Plot Tab
with tab1:
    directions = st.multiselect(
        "Select Directions:",
        df["Direction"].unique(),
        default=df["Direction"].unique()[0],
    )
    citizenship = st.selectbox("Select Citizenship:", df["Citizenship"].unique())

    # Filter the dataframe based on the selections
    filtered_df = df[
        df["Direction"].isin(directions) & (df["Citizenship"] == citizenship)
    ]

    # Plotting
    fig, ax = plt.subplots()
    for direction in directions:
        df_plot = filtered_df[filtered_df["Direction"] == direction]
        ax.plot(
            df_plot["Month"],
            df_plot["Count"],
            marker="o",
            linestyle="-",
            label=direction,
        )
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.set_title(f"Time Series for {citizenship}")
    ax.legend()

    # Display the plot in the Streamlit app
    st.pyplot(fig)

# Stacked Area Plots Tab
with tab2:
    direction = st.selectbox(
        "Select Direction for Stacked Area Plot:",
        df["Direction"].unique(),
        key="direction2",
    )
    citizenships = st.multiselect(
        "Select Citizenships:",
        df["Citizenship"].unique(),
        default=df["Citizenship"].unique()[:2],
        key="citizenships",
    )

    # Preparing data for the stacked area plot
    filtered_df = df[
        (df["Direction"] == direction) & (df["Citizenship"].isin(citizenships))
    ]
    pivot_df = filtered_df.pivot_table(
        index="Month", columns="Citizenship", values="Count", aggfunc="sum"
    ).fillna(0)

    # Plotting
    fig, ax = plt.subplots()
    ax.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns)
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.set_title(f"Stacked Area Plot for {direction}")
    ax.legend(loc="upper left")

    # Display the plot in the Streamlit app
    st.pyplot(fig)


# Add large title
# add source
# add logo and blog link
# add readme with blog link and a image of the dashboard

# Time series
# Need a note saying how countries and regions total up
# Add tool tip
# allow smoothing - 3 month or raw
# make markers smaller

# Stacked area
# add tool tip
# Use cool colour pallette
# have some very light grid lines
# allow smoothing - 3 month or raw
