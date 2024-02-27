import pandas as pd

# --------------------------------------------------------------
# 1. Define objective
# --------------------------------------------------------------

""" 
The objective of this script is to transform migration data for NZ into a format for data vizualisation

"""

# --------------------------------------------------------------
# 2. Read raw data
# --------------------------------------------------------------


df_raw = pd.read_csv(
    "../../data/raw/direction_citizenship_202312.csv",
)

# Load the new dataset
df_raw_age_sex = pd.read_csv("../../data/raw/direction_age_sex_202312.csv", header=[0, 1, 2])

# --------------------------------------------------------------
# 3. Process data
# --------------------------------------------------------------
# Process the direction_citizenship data file

# Step 3: Correctly set column names using the first row (country names)
country_names = df_raw.iloc[0][1:]  # Skipping the first entry ('Month')
new_column_names = ['Month'] + [f"{direction}_{country}" for direction, country in zip(df_raw.columns[1:], country_names)]
df_raw.columns = new_column_names

# Step 4: Drop the first row as it's now redundant
df_raw = df_raw.drop(index=0)

# Step 5: Convert 'Month' to a proper datetime format
df_raw['Month'] = pd.to_datetime(df_raw['Month'], format='%YM%m', errors='coerce')

# Step 6: Melt the dataframe to long format
df_melted = df_raw.melt(id_vars=['Month'], var_name='Direction_Citizenship', value_name='Value')

# Correct Step 7: Split the 'Direction_Citizenship' column into separate 'Direction' and 'Citizenship' columns
df_melted[['Direction', 'Citizenship']] = df_melted['Direction_Citizenship'].str.split('_', n=1, expand=True)


# Step 8: Drop the original 'Direction_Citizenship' column as it's no longer needed
df_melted.drop(columns=['Direction_Citizenship'], inplace=True)

# Step 9: Reorder columns for clarity
df_melted = df_melted[['Month', 'Direction', 'Citizenship', 'Value']]


# Define the function to generalize the direction
def generalize_direction(value):
    if 'Arrival' in value:  # Checks if the substring 'Arrival' is in the string
        return 'Arrivals'
    elif 'Departure' in value:
        return 'Departures'
    elif 'Net' in value:
        return 'Net'
    else:
        return value

# Apply the generalize_direction function to a specific column
df_melted['Direction'] = df_melted['Direction'].apply(generalize_direction)

# Convert the value column to int type
df_melted['Value'] = df_melted['Value'].astype(int)

# Display the modified DataFrame
print(df_melted.head())

# Print dtypes
print(df_melted.dtypes)

# --------------------------------------------------------------
# Process the direction_age_sex data file

# Convert the first column (Month) to datetime format directly during the read operation
df_raw_age_sex.iloc[:, 0] = pd.to_datetime(df_raw_age_sex.iloc[:, 0], format='%YM%m')

# Fixing the column assignment to ensure 'Month' is recognized and handled correctly
# Extracting the first column as 'Month' before redefining column names
month_column = df_raw_age_sex.iloc[:, 0]
df_raw_age_sex.drop(df_raw_age_sex.columns[0], axis=1, inplace=True)

# Flatten the MultiIndex for column names by joining the levels with underscores
df_raw_age_sex.columns = ['_'.join(col).strip() for col in df_raw_age_sex.columns.values]
df_raw_age_sex.insert(0, 'Month', month_column)

# Now, transform the DataFrame to long format
df_long_raw_age = pd.melt(df_raw_age_sex, id_vars=['Month'], var_name='Attributes', value_name='Count')

# Split 'Attributes' into 'Direction', 'Age_Group', and 'Sex'
df_long_raw_age[['Direction', 'Age Group', 'Sex']] = df_long_raw_age['Attributes'].str.split('_', expand=True)

# Drop the 'Attributes' column as it's no longer needed
df_long_raw_age.drop('Attributes', axis=1, inplace=True)

# Display the first few rows of the long-form DataFrame to verify the transformation
print(df_long_raw_age.head())

# Print dtypes
print(df_long_raw_age.dtypes)


# --------------------------------------------------------------
# Export
# --------------------------------------------------------------

df_melted.to_pickle("../../data/interim/df_citizenship_direction_202312.pkl")
df_melted.to_csv("../../data/interim/df_citizenship_direction_202312.csv", index=False)

df_long_raw_age.to_pickle("../../data/interim/df_direction_age_sex_202312.pkl")
df_long_raw_age.to_csv("../../data/interim/df_direction_age_sex_202312.csv", index=False)


