import pandas as pd
from data_processing import transform_dataframe_to_long_format

# --------------------------------------------------------------
# 1. Define objective
# --------------------------------------------------------------

""" 
The objective of this script is to transform migration data for NZ into a format for data vizualisation

"""

# --------------------------------------------------------------
# 2. Read raw data
# --------------------------------------------------------------

df_raw_direction_citizen = pd.read_csv(
    "../../data/raw/direction_citizenship_202312.csv", header=[0, 1]
)

# Load the new dataset
df_raw_direction_age_sex = pd.read_csv(
    "../../data/raw/direction_age_sex_202312.csv", header=[0, 1, 2]
)

# --------------------------------------------------------------
# 3. Process data
# --------------------------------------------------------------

# Process the direction_citizenship data file into long format
df_direction_citizen = transform_dataframe_to_long_format(
    df_raw_direction_citizen, attributes=["Direction", "Citizenship"]
)

# Display the first few rows of the long-form DataFrame to verify the transformation
print(df_direction_citizen.head())

# Print dtypes
print(df_direction_citizen.dtypes)

# Process the direction_age_sex data file into long format
df_direction_age_sex = transform_dataframe_to_long_format(
    df_raw_direction_age_sex, attributes=["Direction", "Age Group", "Sex"]
)

# Display the first few rows of the long-form DataFrame to verify the transformation
print(df_direction_age_sex.head())

# Print dtypes
print(df_direction_age_sex.dtypes)

# --------------------------------------------------------------
# Export
# --------------------------------------------------------------

df_raw_direction_citizen.to_pickle(
    "../../data/interim/df_citizenship_direction_202312.pkl"
)
df_raw_direction_citizen.to_csv(
    "../../data/interim/df_citizenship_direction_202312.csv", index=False
)

df_direction_age_sex.to_pickle("../../data/interim/df_direction_age_sex_202312.pkl")
df_direction_age_sex.to_csv(
    "../../data/interim/df_direction_age_sex_202312.csv", index=False
)
