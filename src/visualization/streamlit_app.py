import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


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

    # Define a function to create a label for each unique combination
    def create_label(row):
        if breakdown_type == "Direction, Citizenship":
            return f"{row['Direction']}, {row['Citizenship']}"
        else:  # Direction, Age, Sex
            return f"{row['Direction']}, {row['Sex']}, {row['Age Group']}"

    # Apply the function to create a new column 'Label' for plotting
    filtered_df["Label"] = filtered_df.apply(create_label, axis=1)

    # Plotting - Adjusted to handle multiple series with legend outside
    fig, ax = plt.subplots()
    unique_labels = filtered_df["Label"].unique()
    for label in unique_labels:
        df_plot = filtered_df[filtered_df["Label"] == label]
        ax.plot(
            df_plot["Month"], df_plot["Count"], marker="o", linestyle="-", label=label
        )

    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.set_title("Time Series with Multiple Selections")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))  # Adjust legend position

    # Display the plot in the Streamlit app, adjusting for the new layout
    st.pyplot(fig, bbox_inches="tight")


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
        index="Month",
        columns=(
            "Age Group" if breakdown_type == "Direction, Age, Sex" else "Citizenship"
        ),
        values="Count",
        aggfunc="sum",
    ).fillna(0)

    # Plotting
    fig, ax = plt.subplots()
    ax.stackplot(pivot_df.index, pivot_df.T, labels=pivot_df.columns)
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    title = (
        "Stacked Area Plot"
        if breakdown_type == "Direction, Citizenship"
        else "Stacked Area Plot for Direction, Age, Sex"
    )
    ax.set_title(title)
    ax.legend(loc="upper left")
    st.pyplot(fig)


# Add large title
# add source
# add logo and blog link
# add readme with blog link and a image of the dashboard
# add new column prime age
# allow smoothing - 3 month or raw

# Time series
# Need a note saying how countries and regions total up
# Add tool tip
# make markers smaller
# put the leged box to the right outside the plot area

# Stacked area
# add tool tip
# Use cool colour pallette
# have some very light grid lines
# allow smoothing - 3 month or raw
# put the leged box to the right outside the plot area
