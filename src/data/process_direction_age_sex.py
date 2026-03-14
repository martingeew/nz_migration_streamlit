import glob
import os

import pandas as pd

# --------------------------------------------------------------
# 1. Define objective
# --------------------------------------------------------------

"""
Direct processing script for migration data with Direction, Age Group and Sex breakdowns.
Handles the 5-row header structure of ITM552101 raw CSVs and converts to long format.

Designed to be reusable for future data releases.
"""

# --------------------------------------------------------------
# 2. Direct processing functions
# --------------------------------------------------------------

def read_complex_header_file(file_path):
    """
    Read a CSV file with complex multi-row headers and construct proper column names.

    Expected structure:
    - Row 1: Title (skip)
    - Row 2: Direction categories (Arrivals, Departures, Net)
    - Row 3: Age group names
    - Row 4: Sex (Female, Male, TOTAL)
    - Row 5: "Estimate" labels (skip)
    - Row 6+: Data

    Parameters:
    - file_path (str): Path to the CSV file

    Returns:
    - pd.DataFrame: DataFrame with proper column names and data
    """

    print(f"Reading file: {file_path}")

    header_df = pd.read_csv(file_path, nrows=5, header=None)

    print("Analyzing header structure...")

    direction_row = header_df.iloc[1].fillna('').astype(str)
    age_row = header_df.iloc[2].fillna('').astype(str)
    sex_row = header_df.iloc[3].fillna('').astype(str)

    column_names = []
    current_direction = ""
    current_age = ""

    for i in range(len(direction_row)):
        if i == 0:
            column_names.append("Month")
        else:
            if direction_row.iloc[i].strip():
                current_direction = direction_row.iloc[i].strip()
            if age_row.iloc[i].strip():
                current_age = age_row.iloc[i].strip()
            sex = sex_row.iloc[i].strip()
            if sex:
                column_names.append(f"{current_direction}_{current_age}_{sex}")

    print(f"Constructed {len(column_names)} column names")
    print(f"First few columns: {column_names[:5]}")

    data_df = pd.read_csv(file_path, skiprows=5, header=None)

    if len(column_names) > len(data_df.columns):
        print(f"Warning: More column names ({len(column_names)}) than data columns ({len(data_df.columns)})")
        column_names = column_names[:len(data_df.columns)]
    elif len(column_names) < len(data_df.columns):
        print(f"Warning: Fewer column names ({len(column_names)}) than data columns ({len(data_df.columns)})")
        for i in range(len(column_names), len(data_df.columns)):
            column_names.append(f"Column_{i}")

    data_df.columns = column_names

    print(f"Data shape: {data_df.shape}")

    return data_df


def convert_to_long_format(df):
    """
    Convert the wide format DataFrame to long format directly.

    Parameters:
    - df (pd.DataFrame): Wide format DataFrame with Month and Direction_AgeGroup_Sex columns

    Returns:
    - pd.DataFrame: Long format DataFrame with Month, Count, Direction, Age Group, Sex columns
    """

    print("Converting to long format...")

    month_pattern = r'^\d{4}M\d{2}$'
    valid_rows = df['Month'].astype(str).str.match(month_pattern, na=False)

    original_rows = len(df)
    df = df[valid_rows].copy()
    filtered_rows = len(df)

    print(f"Filtered dataset: {original_rows} -> {filtered_rows} rows ({original_rows - filtered_rows} footer rows removed)")

    print("Converting Month column to datetime...")
    df['Month'] = pd.to_datetime(df['Month'], format='%YM%m')

    value_columns = [col for col in df.columns if col != 'Month']

    print(f"Found {len(value_columns)} value columns")

    df_long = pd.melt(
        df,
        id_vars=['Month'],
        value_vars=value_columns,
        var_name='Direction_AgeGroup_Sex',
        value_name='Count'
    )

    print(f"Melted DataFrame shape: {df_long.shape}")

    print("Splitting Direction_AgeGroup_Sex column...")

    split_data = df_long['Direction_AgeGroup_Sex'].str.split('_', n=2, expand=True)

    if split_data.shape[1] != 3:
        raise ValueError("Could not properly split Direction_AgeGroup_Sex column into 3 parts")

    df_long['Direction'] = split_data[0]
    df_long['Age Group'] = split_data[1]
    df_long['Sex'] = split_data[2]

    df_long = df_long.drop('Direction_AgeGroup_Sex', axis=1)

    df_long = df_long[['Month', 'Count', 'Direction', 'Age Group', 'Sex']]

    df_long['Count'] = pd.to_numeric(df_long['Count'], errors='coerce')

    print(f"Final DataFrame shape: {df_long.shape}")
    print(f"Unique Directions: {df_long['Direction'].unique()}")
    print(f"Unique Age Groups: {df_long['Age Group'].nunique()}")
    print(f"Unique Sex values: {df_long['Sex'].unique()}")

    return df_long


def validate_output(df):
    """
    Validate that the output DataFrame has the expected structure.

    Parameters:
    - df (pd.DataFrame): Processed DataFrame to validate

    Returns:
    - bool: True if validation passes
    """

    print("Validating output...")

    expected_columns = ['Month', 'Count', 'Direction', 'Age Group', 'Sex']
    if list(df.columns) != expected_columns:
        print(f"FAIL Column mismatch. Expected: {expected_columns}, Got: {list(df.columns)}")
        return False

    if not pd.api.types.is_datetime64_any_dtype(df['Month']):
        print("FAIL Month column is not datetime type")
        return False

    if not pd.api.types.is_numeric_dtype(df['Count']):
        print("FAIL Count column is not numeric type")
        return False

    for col in ['Direction', 'Age Group', 'Sex']:
        if df[col].isna().any():
            print(f"FAIL Found missing values in {col} column")
            return False

    expected_directions = {'Arrivals', 'Departures', 'Net'}
    actual_directions = set(df['Direction'].unique())
    if not actual_directions.issubset(expected_directions):
        print(f"FAIL Unexpected Direction values: {actual_directions - expected_directions}")
        return False

    print("OK Output validation passed")
    return True


# --------------------------------------------------------------
# 3. Main processing function
# --------------------------------------------------------------

def process_migration_file(input_file, output_date_suffix):
    """
    Process a migration CSV file and convert it to the standard long format.

    Parameters:
    - input_file (str): Path to input CSV file
    - output_date_suffix (str): Date suffix for output files (e.g., "20260314")

    Returns:
    - pd.DataFrame: Processed DataFrame
    """

    try:
        df_raw = read_complex_header_file(input_file)

        df_processed = convert_to_long_format(df_raw)

        if not validate_output(df_processed):
            raise ValueError("Output validation failed")

        output_pickle = f"../../data/interim/df_direction_age_sex_{output_date_suffix}.pkl"
        output_csv = f"../../data/interim/df_direction_age_sex_{output_date_suffix}.csv"

        print(f"Saving processed data...")
        df_processed.to_pickle(output_pickle)
        df_processed.to_csv(output_csv, index=False)

        print(f"OK Successfully processed and saved:")
        print(f"   - {output_pickle}")
        print(f"   - {output_csv}")

        print(f"\nSummary:")
        print(f"   - Total records: {len(df_processed):,}")
        print(f"   - Date range: {df_processed['Month'].min()} to {df_processed['Month'].max()}")
        print(f"   - Directions: {', '.join(df_processed['Direction'].unique())}")
        print(f"   - Unique age groups: {df_processed['Age Group'].nunique()}")
        print(f"   - Sex values: {', '.join(df_processed['Sex'].unique())}")

        return df_processed

    except Exception as e:
        print(f"Error during processing: {str(e)}")
        raise


# --------------------------------------------------------------
# 4. Script execution
# --------------------------------------------------------------

def main():
    """Main execution function — auto-detects the latest ITM552101 raw file"""

    print("=== Direction/Age Group/Sex Data Processing ===")

    files = sorted(glob.glob("../../data/raw/ITM552101_*.csv"))
    if not files:
        raise FileNotFoundError("No ITM552101_*.csv files found in data/raw/")

    input_file = files[-1]
    output_suffix = os.path.basename(input_file).split('_')[1]

    print(f"Processing {os.path.basename(input_file)} ...")

    df_result = process_migration_file(input_file, output_suffix)

    print("\n=== Processing Complete ===")
    print(f"Processed {len(df_result):,} records successfully")


if __name__ == "__main__":
    main()
