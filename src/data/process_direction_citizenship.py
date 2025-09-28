import pandas as pd
import numpy as np

# --------------------------------------------------------------
# 1. Define objective
# --------------------------------------------------------------

"""
Direct processing script for migration data with Direction and Citizenship breakdowns.
This script handles complex header structures and converts them directly to long format
without relying on external transformation functions.

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
    - Row 3: Citizenship names
    - Row 4: "Estimate" labels (skip)
    - Row 5+: Data

    Parameters:
    - file_path (str): Path to the CSV file

    Returns:
    - pd.DataFrame: DataFrame with proper column names and data
    """

    print(f"Reading file: {file_path}")

    # Read the header rows to analyze structure
    header_df = pd.read_csv(file_path, nrows=4, header=None)

    print("Analyzing header structure...")

    # Extract direction row (row 2, index 1)
    direction_row = header_df.iloc[1].fillna('').astype(str)

    # Extract citizenship row (row 3, index 2)
    citizenship_row = header_df.iloc[2].fillna('').astype(str)

    # Build column names by combining direction and citizenship
    column_names = []
    current_direction = ""

    for i, (direction, citizenship) in enumerate(zip(direction_row, citizenship_row)):
        if i == 0:  # First column is Month
            column_names.append("Month")
        else:
            # Update direction if not empty
            if direction.strip() and direction.strip() != '':
                current_direction = direction.strip()

            # Create combined column name
            if citizenship.strip() and citizenship.strip() != '':
                column_name = f"{current_direction}_{citizenship.strip()}"
                column_names.append(column_name)

    print(f"Constructed {len(column_names)} column names")
    print(f"First few columns: {column_names[:5]}")

    # Read the actual data starting from row 5 (index 4)
    data_df = pd.read_csv(file_path, skiprows=4, header=None)

    # Ensure we have the right number of columns
    if len(column_names) > len(data_df.columns):
        print(f"Warning: More column names ({len(column_names)}) than data columns ({len(data_df.columns)})")
        column_names = column_names[:len(data_df.columns)]
    elif len(column_names) < len(data_df.columns):
        print(f"Warning: Fewer column names ({len(column_names)}) than data columns ({len(data_df.columns)})")
        # Pad with generic names
        for i in range(len(column_names), len(data_df.columns)):
            column_names.append(f"Column_{i}")

    # Assign column names
    data_df.columns = column_names

    print(f"Data shape: {data_df.shape}")

    return data_df

def convert_to_long_format(df):
    """
    Convert the wide format DataFrame to long format directly.

    Parameters:
    - df (pd.DataFrame): Wide format DataFrame with Month and Direction_Citizenship columns

    Returns:
    - pd.DataFrame: Long format DataFrame with Month, Count, Direction, Citizenship columns
    """

    print("Converting to long format...")

    # Filter out footer information - look for rows where Month doesn't match expected pattern
    print("Filtering out footer information...")

    # Keep only rows where the first column looks like a month (starts with year)
    month_pattern = r'^\d{4}M\d{2}$'
    valid_rows = df['Month'].astype(str).str.match(month_pattern, na=False)

    original_rows = len(df)
    df = df[valid_rows].copy()
    filtered_rows = len(df)

    print(f"Filtered dataset: {original_rows} -> {filtered_rows} rows ({original_rows - filtered_rows} footer rows removed)")

    # Convert Month column to datetime
    print("Converting Month column to datetime...")
    df['Month'] = pd.to_datetime(df['Month'], format='%YM%m')

    # Get all columns except Month
    value_columns = [col for col in df.columns if col != 'Month']

    print(f"Found {len(value_columns)} value columns")

    # Melt the DataFrame to long format
    df_long = pd.melt(
        df,
        id_vars=['Month'],
        value_vars=value_columns,
        var_name='Direction_Citizenship',
        value_name='Count'
    )

    print(f"Melted DataFrame shape: {df_long.shape}")

    # Split the Direction_Citizenship column
    print("Splitting Direction_Citizenship column...")

    # Split on the first underscore to handle citizenship names with underscores
    split_data = df_long['Direction_Citizenship'].str.split('_', n=1, expand=True)

    if split_data.shape[1] != 2:
        raise ValueError("Could not properly split Direction_Citizenship column")

    df_long['Direction'] = split_data[0]
    df_long['Citizenship'] = split_data[1]

    # Drop the combined column
    df_long = df_long.drop('Direction_Citizenship', axis=1)

    # Reorder columns
    df_long = df_long[['Month', 'Count', 'Direction', 'Citizenship']]

    # Convert Count to numeric, handling any non-numeric values
    df_long['Count'] = pd.to_numeric(df_long['Count'], errors='coerce')

    print(f"Final DataFrame shape: {df_long.shape}")
    print(f"Unique Directions: {df_long['Direction'].unique()}")
    print(f"Number of unique Citizenships: {len(df_long['Citizenship'].unique())}")

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

    # Check columns
    expected_columns = ['Month', 'Count', 'Direction', 'Citizenship']
    if list(df.columns) != expected_columns:
        print(f"❌ Column mismatch. Expected: {expected_columns}, Got: {list(df.columns)}")
        return False

    # Check data types
    if not pd.api.types.is_datetime64_any_dtype(df['Month']):
        print("❌ Month column is not datetime type")
        return False

    if not pd.api.types.is_numeric_dtype(df['Count']):
        print("❌ Count column is not numeric type")
        return False

    # Check for missing values in key columns
    if df['Direction'].isna().any():
        print("❌ Found missing values in Direction column")
        return False

    if df['Citizenship'].isna().any():
        print("❌ Found missing values in Citizenship column")
        return False

    # Check expected Direction values
    expected_directions = ['Arrivals', 'Departures', 'Net']
    actual_directions = df['Direction'].unique()
    if not all(direction in expected_directions for direction in actual_directions):
        print(f"❌ Unexpected Direction values: {actual_directions}")
        return False

    print("✅ Output validation passed")
    return True

# --------------------------------------------------------------
# 3. Main processing function
# --------------------------------------------------------------

def process_migration_file(input_file, output_date_suffix):
    """
    Process a migration CSV file and convert it to the standard long format.

    Parameters:
    - input_file (str): Path to input CSV file
    - output_date_suffix (str): Date suffix for output files (e.g., "202509")

    Returns:
    - pd.DataFrame: Processed DataFrame
    """

    try:
        # Read the file with complex headers
        df_raw = read_complex_header_file(input_file)

        # Convert to long format
        df_processed = convert_to_long_format(df_raw)

        # Validate the output
        if not validate_output(df_processed):
            raise ValueError("Output validation failed")

        # Define output paths
        output_pickle = f"../../data/interim/df_citizenship_direction_{output_date_suffix}.pkl"
        output_csv = f"../../data/interim/df_citizenship_direction_{output_date_suffix}.csv"

        # Save the processed data
        print(f"Saving processed data...")
        df_processed.to_pickle(output_pickle)
        df_processed.to_csv(output_csv, index=False)

        print(f"✅ Successfully processed and saved:")
        print(f"   - {output_pickle}")
        print(f"   - {output_csv}")

        # Print summary statistics
        print(f"\nSummary:")
        print(f"   - Total records: {len(df_processed):,}")
        print(f"   - Date range: {df_processed['Month'].min()} to {df_processed['Month'].max()}")
        print(f"   - Directions: {', '.join(df_processed['Direction'].unique())}")
        print(f"   - Unique citizenships: {len(df_processed['Citizenship'].unique())}")

        return df_processed

    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        raise

# --------------------------------------------------------------
# 4. Script execution
# --------------------------------------------------------------

def main():
    """Main execution function for processing the 202509 data"""

    print("=== Direction/Citizenship Data Processing ===")
    print("Processing 202509 migration data...")

    input_file = "../../data/raw/direction_citizenship_202509.csv"
    output_suffix = "202509"

    df_result = process_migration_file(input_file, output_suffix)

    print("\n=== Processing Complete ===")
    print(f"Processed {len(df_result):,} records successfully")

if __name__ == "__main__":
    main()