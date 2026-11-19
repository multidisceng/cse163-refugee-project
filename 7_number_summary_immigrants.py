import pandas as pd

MERGED_FILE = "worksource_immigrant_merged.csv"


def load_data(path: str) -> pd.DataFrame:
    """Load the merged CSV and clean up the column names."""
    data = pd.read_csv(path)
    data.columns = data.columns.str.strip()
    return data


def convert_percent_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Turn text columns like '24.5%' into numbers (24.5) so they can be summarized."""
    data = data.copy()
    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            continue
        values = data[column].dropna().astype(str).str.strip()
        if len(values) > 0 and values.str.endswith("%").all():
            data[column] = pd.to_numeric(
                data[column].astype(str).str.rstrip("%").str.strip(), errors="coerce"
            )
    return data


def get_numeric_columns(data: pd.DataFrame) -> list[str]:
    """Return the names of all numeric variables in the dataframe."""
    return data.select_dtypes(include="number").columns.tolist()


def seven_number_summary(series: pd.Series) -> pd.Series:
    """Return mean, standard deviation, minimum, Q1, median, Q3 and maximum.

    Missing values (NaN) are skipped by pandas, so counties with no
    WorkSource location are left out of 'Immigrants per Location'.
    """
    return pd.Series({
        "Mean": series.mean(),
        "Standard deviation": series.std(),  # sample std (ddof=1), pandas default
        "Minimum": series.min(),
        "First quartile (Q1)": series.quantile(0.25),
        "Median": series.median(),
        "Third quartile (Q3)": series.quantile(0.75),
        "Maximum": series.max(),
    })


def summarize_all(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Build one table with a seven-number summary column for each variable."""
    return pd.DataFrame({column: seven_number_summary(data[column]) for column in columns})


def main() -> None:
    data = convert_percent_columns(load_data(MERGED_FILE))
    columns = get_numeric_columns(data)

    print(f"Variables summarized ({len(columns)}): {columns}")
    print(f"Counties (rows): {len(data)}\n")

    summary = summarize_all(data, columns)
    print(summary.round(1).to_string())

    print("\nCounties used (n) per variable:")
    print(data[columns].count().to_string())


if __name__ == "__main__":
    main()
