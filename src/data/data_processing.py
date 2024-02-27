import pandas as pd


def transform_dataframe_to_long_format(df, attributes):
    """
    Transforms a DataFrame with a MultiIndex column structure into a long format,
    converting the first column to 'Month' and datetime format, and specifying attributes
    for splitting the 'Attributes' column.

    Parameters:
    - df (pd.DataFrame): The DataFrame to be transformed.
    - attributes (list of str): List of attribute names to be used for splitting the 'Attributes' column.

    Returns:
    - pd.DataFrame: Transformed DataFrame in long format with specified attributes split into separate columns.

    Raises:
    - ValueError: If 'attributes' is not specified.
    """
    if not attributes or not isinstance(attributes, list):
        raise ValueError("Attributes must be specified as a list of strings.")

    # Convert the first column to datetime format
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%YM%m")

    # Extract the 'Month' column before redefining column names
    month_column = df.iloc[:, 0]
    df.drop(df.columns[0], axis=1, inplace=True)

    # Flatten the MultiIndex for column names by joining the levels with underscores
    df.columns = ["_".join(col).strip() for col in df.columns.values]
    df.insert(0, "Month", month_column)

    # Transform the DataFrame to long format
    df_long = pd.melt(df, id_vars=["Month"], var_name="Attributes", value_name="Count")

    # Split 'Attributes' into specified attributes
    split_columns = df_long["Attributes"].str.split("_", expand=True)
    split_columns.columns = attributes

    # Merge the split columns back into the main DataFrame
    df_long = pd.concat([df_long, split_columns], axis=1)

    # Drop the 'Attributes' column as it's no longer needed
    df_long.drop("Attributes", axis=1, inplace=True)

    return df_long
