
import pandas as pd

# DSHS county map, page 2, October 2023 through September 2024.
# Source: https://www.dshs.wa.gov/media/4293/download?inline=
# Blank counts mark counties in the source's 1–50 band with an asterisk.
APPLICANTS_FILE = 'applicants_vs_worksource.csv'
WORKSOURCE_FILE = 'worksource_locs.csv'
OUTPUT_FILE = 'MERGED_worksource_applicants.csv'


def load_data():
    """Read the applicant counts and the WorkSource office list."""
    applicants = pd.read_csv(APPLICANTS_FILE)[['County', 'Applicants']]
    worksource = pd.read_csv(WORKSOURCE_FILE)
    return applicants, worksource


def merge_data(applicants, worksource):
    """Count offices per county and merge them onto the applicant table."""
    offices = worksource.groupby(
        'County').size().rename('Offices').reset_index()
    df = applicants.merge(offices, on='County', how='left', validate='1:1')
    df['Offices'] = df['Offices'].fillna(
        0).astype(int)   # counties with no office
    return df


def applicant_bin(n):
    if pd.isna(n):
        return '1 - 50 (count unreported)'
    if n == 0:
        return 'No applicants'
    if n <= 9:
        return '1 - 9'
    if n <= 50:
        return '10 - 50'
    if n <= 100:
        return '51 - 100'
    if n <= 200:
        return '101 - 200'
    if n <= 500:
        return '201 - 500'
    if n <= 2000:
        return '501 - 2,000'
    return 'Over 2,000'


def strain_bin(row):
    n, o = row['Applicants'], row['Offices']
    if n == 0:
        return 'No applicants'
    if o == 0:
        return 'Applicants, no office'
    if pd.isna(n):
        return 'Applicant count unreported'
    ratio = n / o                           # applicants per office
    if ratio < 25:
        return 'Low (under 25 per office)'
    if ratio <= 100:
        return 'Moderate (25 - 100)'
    if ratio <= 300:
        return 'High (101 - 300)'
    return 'Very high (over 300)'


def add_bins(df):
    """Add the applicant bin and the strain bin columns."""
    df = df.copy()
    df['Bin'] = df['Applicants'].map(applicant_bin)
    df['Strain_Bin'] = df.apply(strain_bin, axis=1)
    return df


def save_output(df):
    df[['County', 'Bin', 'Strain_Bin']].to_csv(OUTPUT_FILE, index=False)


def main():
    applicants, worksource = load_data()
    merged = merge_data(applicants, worksource)
    binned = add_bins(merged)
    save_output(binned)
    print(f'Saved {OUTPUT_FILE} ({len(binned)} counties)')


if __name__ == '__main__':
    main()
