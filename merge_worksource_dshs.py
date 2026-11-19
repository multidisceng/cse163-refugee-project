import pandas as pd
 
# applicants_vs_worksource.csv: County + exact DSHS applicant counts
# (Applicants is blank where DSHS suppressed the value, meaning 1-9 applicants)
a = pd.read_csv('applicants_vs_worksource.csv')[['County', 'Applicants']]
w = pd.read_csv('worksource_locs.csv')
 
# count WorkSource offices per county, then merge onto the applicant table
offices = w.groupby('County').size().rename('Offices').reset_index()
df = a.merge(offices, on='County', how='left', validate='1:1')
df['Offices'] = df['Offices'].fillna(0).astype(int)   # counties with no office
 
 
def applicant_bin(n):
    if pd.isna(n):  return '1 - 9'          # suppressed by DSHS
    if n == 0:      return 'No applicants'
    if n <= 9:      return '1 - 9'
    if n <= 50:     return '10 - 50'
    if n <= 100:    return '51 - 100'
    if n <= 200:    return '101 - 200'
    if n <= 500:    return '201 - 500'
    if n <= 2000:   return '501 - 2,000'
    return 'Over 2,000'
 
 
def strain_bin(row):
    n, o = row['Applicants'], row['Offices']
    if n == 0:  return 'No applicants'
    if o == 0:  return 'Applicants, no office'
    upper = 9 if pd.isna(n) else n          # suppressed counties have at most 9
    ratio = upper / o                       # applicants per office
    if ratio < 25:    return 'Low (under 25 per office)'
    if ratio <= 100:  return 'Moderate (25 - 100)'
    if ratio <= 300:  return 'High (101 - 300)'
    return 'Very high (over 300)'
 
 
df['Bin'] = df['Applicants'].map(applicant_bin)
df['Strain_Bin'] = df.apply(strain_bin, axis=1)
 
df[['County', 'Bin', 'Strain_Bin']].to_csv('county_bins_strain.csv', index=False)
