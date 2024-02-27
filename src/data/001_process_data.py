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


df_raw_direction_citizen = pd.read_csv("../../data/raw/direction_citizenship_202312.csv", 
header=[0, 1])

# Load the new dataset
df_raw_age_sex = pd.read_csv("../../data/raw/direction_age_sex_202312.csv", header=[0, 1, 2])

# --------------------------------------------------------------
# 3. Process data
# --------------------------------------------------------------

# Process the direction_citizenship data file

# Convert the first column (Month) to datetime format directly during the read operation
df_raw_direction_citizen.iloc[:, 0] = pd.to_datetime(df_raw_direction_citizen.iloc[:, 0], format='%YM%m')

# Fixing the column assignment to ensure 'Month' is recognized and handled correctly
# Extracting the first column as 'Month' before redefining column names
month_column = df_raw_direction_citizen.iloc[:, 0]
df_raw_direction_citizen.drop(df_raw_direction_citizen.columns[0], axis=1, inplace=True)

# Flatten the MultiIndex for column names by joining the levels with underscores
df_raw_direction_citizen.columns = ['_'.join(col).strip() for col in df_raw_direction_citizen.columns.values]
df_raw_direction_citizen.insert(0, 'Month', month_column)

# Now, transform the DataFrame to long format
df_raw_direction_citizen = pd.melt(df_raw_direction_citizen, id_vars=['Month'], var_name='Attributes', value_name='Count')

# Split 'Attributes' into 'Direction', 'Age_Group', and 'Sex'
df_raw_direction_citizen[['Direction', 'Citizenship']] = df_raw_direction_citizen['Attributes'].str.split('_', expand=True)

# Drop the 'Attributes' column as it's no longer needed
df_raw_direction_citizen.drop('Attributes', axis=1, inplace=True)

# Display the first few rows of the long-form DataFrame to verify the transformation
print(df_raw_direction_citizen.head())

# Print dtypes
print(df_raw_direction_citizen.dtypes)

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

df_raw_direction_citizen.to_pickle("../../data/interim/df_citizenship_direction_202312.pkl")
df_raw_direction_citizen.to_csv("../../data/interim/df_citizenship_direction_202312.csv", index=False)

df_long_raw_age.to_pickle("../../data/interim/df_direction_age_sex_202312.pkl")
df_long_raw_age.to_csv("../../data/interim/df_direction_age_sex_202312.csv", index=False)


