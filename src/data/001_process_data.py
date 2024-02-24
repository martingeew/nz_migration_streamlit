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
    "../../data/raw/direction_citizenship_202401.csv",
)

# --------------------------------------------------------------
# 3. Process data
# --------------------------------------------------------------

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

# Display the modified DataFrame
print(df_melted.head())

df_melted.dtypes



# --------------------------------------------------------------
# Export
# --------------------------------------------------------------

df_melted.to_pickle("../../data/interim/df_citizenship_direction.pkl")
