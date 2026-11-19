from merge_worksource_immigrants import (
    LOCATIONS_FILE,
    COUNTIES_FILE,
    load_data,
    count_locations_by_county,
    merge_datasets
)


def main():
    locations, counties = load_data(LOCATIONS_FILE, COUNTIES_FILE)
    office_counts = count_locations_by_county(locations)
    merged = merge_datasets(counties, office_counts)

    # tests for County-WorkSource Locations
    assert merged["County"].nunique() == 39
    assert merged["WorkSource Locations"].sum() == 127

    # tests for Adam County: appears only once, with zero listed locations
    north = merged["County"] == "Adams"
    items = merged.loc[north, "WorkSource Locations"]
    assert items.tolist() == [0]


if __name__ == "__main__":
    main()
