import pandas as pd

LOCATIONS_FILE = "worksource_locs.csv"
COUNTIES_FILE = "county_pop.csv"
OUTPUT_FILE = "worksource_immigrant_merged.csv"


def load_data(locations_path: str, counties_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the WorkSource locations and county immigrant 
    population CSVs.
    """
    locations = pd.read_csv(locations_path)
    counties = pd.read_csv(counties_path)
    return locations, counties


def count_locations_by_county(locations: pd.DataFrame) -> pd.DataFrame:
    """
    Return the number of WorkSource locations in each 
    county.
    """
    return (
        locations.groupby("County")
        .size()
        .reset_index(name="WorkSource Locations")
    )


def merge_datasets(counties: pd.DataFrame, office_counts: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join location counts onto the county table, 
    keeping counties with 0 locations.
    """
    merged = counties.merge(office_counts, on="County", how="left")
    merged["WorkSource Locations"] = merged["WorkSource Locations"].fillna(0).astype(int)
    return merged


def add_immigrants_per_location(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Add immigrants per WorkSource location (blank where 
    a county has none).
    """
    merged = merged.copy()
    merged["Immigrants per Location"] = (
        (merged["Immigrant (Foreign-Born) Population"] / merged["WorkSource Locations"])
        .where(merged["WorkSource Locations"] > 0)
        .round(0)
    )
    return merged


def validate(merged: pd.DataFrame, locations: pd.DataFrame) -> None:
    """
    Confirm every location was matched to a county.
    """
    matched = merged["WorkSource Locations"].sum()
    assert matched == len(locations), (
        f"Only {matched} of {len(locations)} locations matched a county"
    )


def save_results(merged: pd.DataFrame, output_path: str) -> None:
    """
    Write the merged dataframe to CSV.
    """
    merged.to_csv(output_path, index=False)


def print_summary(merged: pd.DataFrame, locations: pd.DataFrame) -> None:
    """
    Print the merged table and a short summary.
    """
    print(merged.to_string(index=False))
    print("\nTotal locations matched:", merged["WorkSource Locations"].sum(), "of", len(locations))
    no_location = merged.loc[merged["WorkSource Locations"] == 0, "County"].tolist()
    print("Counties with no location:", no_location)


def main() -> None:
    locations, counties = load_data(LOCATIONS_FILE, COUNTIES_FILE)
    office_counts = count_locations_by_county(locations)
    merged = merge_datasets(counties, office_counts)
    merged = add_immigrants_per_location(merged)
    validate(merged, locations)
    save_results(merged, OUTPUT_FILE)
    print_summary(merged, locations)


if __name__ == "__main__":
    main()
