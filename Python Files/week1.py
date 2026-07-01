import pandas as pd
import os
import re


folder = r"C:\Users\khush\idx files"

# Getting all the monthly files
listing_files = sorted([f for f in os.listdir(folder) if f.startswith('CRMLSListing') and f.endswith('.csv')])
sold_files = sorted([f for f in os.listdir(folder) if f.startswith('CRMLSSold') and f.endswith('.csv')])

# For sold files, we're keeping _filled version if it exists for a month, otherwise keep regular
sold_months = {}
for f in sold_files:
    match = re.search(r'CRMLSSold(\d{6})', f)
    if match:
        month = match.group(1)
        if month not in sold_months:
            sold_months[month] = f
        elif '_filled' in f:
            sold_months[month] = f  # prefer filled version

sold_files_deduped = sorted(sold_months.values())

# Loading and concatenating all sold files
sold_dfs = []
for f in sold_files_deduped:
    df = pd.read_csv(os.path.join(folder, f), low_memory=False)
    # Dropping extra columns from _filled files
    df = df.drop(columns=['latfilled', 'lonfilled'], errors='ignore')
    sold_dfs.append(df)

sold = pd.concat(sold_dfs, ignore_index=True)
print(f"Total sold rows before filter: {len(sold)}")

# Loading and concatenating all listing files
listing_dfs = []
for f in listing_files:
    df = pd.read_csv(os.path.join(folder, f), low_memory=False)
    # Dropping extra columns from _filled files if present
    df = df.drop(columns=['latfilled', 'lonfilled'], errors='ignore')
    listing_dfs.append(df)

listings = pd.concat(listing_dfs, ignore_index=True)
print(f"Total listing rows before filter: {len(listings)}")

# Filtering to Residential only
sold_residential = sold[sold['PropertyType'] == 'Residential']
listings_residential = listings[listings['PropertyType'] == 'Residential']

print(f"Total sold rows after Residential filter: {len(sold_residential)}")
print(f"Total listing rows after Residential filter: {len(listings_residential)}")

# Row counts confirmed:
# Total sold rows before Residential filter: 640526
# Total listing rows before Residential filter: 917740
# Total sold rows after Residential filter: 430716
# Total listing rows after Residential filter: 583650

# Saving to CSV
sold_residential.to_csv(os.path.join(folder, 'sold_combined.csv'), index=False)
listings_residential.to_csv(os.path.join(folder, 'listings_combined.csv'), index=False)
