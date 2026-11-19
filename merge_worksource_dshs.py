import pandas as pd

w = pd.read_csv('worksource_locs.csv')
d = pd.read_csv('wa_applicants_dshs_oct2023_sep2024.csv')

# one row per WorkSource office, with its county's bin attached
merged = w.merge(d, on='County', how='left', validate='m:1')
merged.to_csv('worksource_with_bins.csv', index=False)

# one row per county, with a count of WorkSource offices
offices = w.groupby('County').size().rename('WorkSource_Offices').reset_index()
summary = d.merge(offices, on='County', how='left')
summary['WorkSource_Offices'] = summary['WorkSource_Offices'].fillna(0).astype(int)
summary.to_csv('county_bins_with_worksource_counts.csv', index=False)
