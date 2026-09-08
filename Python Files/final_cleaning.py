'''
Final Cleaning – Data Quality Resolution
Purpose: Resolve all flagged data quality issues in sold_features.csv including:
- Delete confirmed non-California and foreign country records
- Fix zip code typos for CA properties
- Repair positive longitudes (dropped minus signs) where recoverable
- Set invalid numeric values to null
- Fix extreme sale-to-list ratios caused by bad OriginalListPrice entries
- Fix LivingArea = 1 sqft records
- Flag year built anomalies
- Recalculate engineered metrics after fixes
'''

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
INPUT  = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports\sold_features.csv")
OUTPUT = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports\sold_final_cleaned.csv")

print("Loading data...")
df = pd.read_csv(INPUT, low_memory=False)
print(f"Starting shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

# ── Step 1 – Delete confirmed non-CA and foreign records ───────────────────
print("\n--- Step 1: Removing non-CA and foreign records ---")

# Out of state records (StateOrProvince != CA)
non_ca_mask = df['out_of_state_flag'] == True

# Foreign country records
foreign_mask = df['CountyOrParish'].astype(str).str.contains('Foreign', na=False)

# Records with coordinates clearly outside CA AND city says "Outside"
outside_city_mask = df['City'].astype(str).str.contains('Outside Area', na=False)

# Combine all deletion masks
delete_mask = non_ca_mask | foreign_mask

rows_before = len(df)
df = df[~delete_mask].copy()
print(f"Deleted {rows_before - len(df):,} non-CA/foreign records -> {len(df):,} rows remaining")

# ── Step 2 – Fix zip code typos ────────────────────────────────────────────
print("\n--- Step 2: Fixing zip code typos ---")

ZIP_FIXES = {
    '22677':  '92677',   # Laguna Niguel
    '98245':  '92845',   # Garden Grove
    '97381':  '91381',   # Valencia
    '82553':  '92553',   # Moreno Valley
    '05073':  '95073',   # Chico
    '01010':  '91010',   # Duarte
    '19351':  '91351',   # Canyon Country
    '980803': '90803',   # Long Beach (extra digit)
    '02336':  '92336',   # Fontana
    '82630':  '92630',   # Lake Forest
    '80802':  '90802',   # Long Beach
    '88888':  '92880',   # Corona (placeholder)
    '00000':  None,      # Invalid — set to null
    '02637':  '92637',   # Laguna Woods
    '20448':  '92377',   # Rialto
    '20205':  '92377',   # Rialto
    '20536':  '91761',   # Ontario
}

df['PostalCode'] = df['PostalCode'].astype(str).str.strip()
fixed_count = 0
for bad_zip, good_zip in ZIP_FIXES.items():
    mask = df['PostalCode'] == bad_zip
    count = mask.sum()
    if count > 0:
        if good_zip is None:
            df.loc[mask, 'PostalCode'] = np.nan
        else:
            df.loc[mask, 'PostalCode'] = good_zip
        print(f"  {bad_zip} -> {good_zip if good_zip else 'null'}: {count} records")
        fixed_count += count

print(f"Total zip codes fixed: {fixed_count}")

# ── Step 3 – Fix positive longitudes (dropped minus signs) ─────────────────
print("\n--- Step 3: Fixing positive longitudes ---")

pos_lon_mask = df['Longitude'] > 0
flipped = -df.loc[pos_lon_mask, 'Longitude']
recoverable = (
    df.loc[pos_lon_mask, 'Latitude'].between(32.529508, 42.009503) &
    flipped.between(-124.482003, -114.131211)
)

# Flip recoverable ones
df.loc[pos_lon_mask & recoverable, 'Longitude'] = -df.loc[pos_lon_mask & recoverable, 'Longitude']
print(f"Flipped {recoverable.sum()} positive longitudes to negative")

# Set unrecoverable ones to null
unrecoverable = pos_lon_mask & ~recoverable
df.loc[unrecoverable, ['Latitude', 'Longitude']] = np.nan
print(f"Set {unrecoverable.sum()} unrecoverable coordinates to null")

# ── Step 4 – Fix zero coordinates ─────────────────────────────────────────
print("\n--- Step 4: Fixing zero coordinates ---")
zero_coord_mask = (df['Latitude'] == 0) | (df['Longitude'] == 0)
df.loc[zero_coord_mask, ['Latitude', 'Longitude']] = np.nan
print(f"Set {zero_coord_mask.sum()} zero coordinates to null")

# ── Step 5 – Fix invalid numeric values ────────────────────────────────────
print("\n--- Step 5: Fixing invalid numeric values ---")

# ClosePrice = null (1 record)
close_price_null = df['ClosePrice'].isna()
print(f"ClosePrice null: {close_price_null.sum()} records (kept as null)")

# LivingArea = 0 or 1 (placeholder values)
bad_area = df['LivingArea'].isin([0, 1]) | (df['LivingArea'].isna())
df.loc[df['LivingArea'].isin([0, 1]), 'LivingArea'] = np.nan
print(f"Set {(df['LivingArea'].isin([0, 1])).sum()} LivingArea=0/1 to null")

# DaysOnMarket < 0 (already flagged, set to null)
neg_dom = df['DaysOnMarket'] < 0
df.loc[neg_dom, 'DaysOnMarket'] = np.nan
print(f"Set {neg_dom.sum()} negative DaysOnMarket to null")

# ── Step 6 – Fix extreme sale-to-list ratios ───────────────────────────────
print("\n--- Step 6: Fixing extreme sale-to-list ratios ---")

# Ratio > 2 or < 0.3 suggests bad OriginalListPrice
extreme_ratio = (df['sale_to_list_ratio'] > 2) | (df['sale_to_list_ratio'] < 0.3)
df.loc[extreme_ratio, 'OriginalListPrice'] = np.nan
print(f"Set OriginalListPrice to null for {extreme_ratio.sum()} extreme ratio records")

# ── Step 7 – Flag year built anomalies ────────────────────────────────────
print("\n--- Step 7: Flagging year built anomalies ---")

df['yearbuilt_anomaly_flag'] = (df['YearBuilt'] < 1900) | (df['YearBuilt'] > 2026)
# Set after 2026 to null (impossible)
future_built = df['YearBuilt'] > 2026
df.loc[future_built, 'YearBuilt'] = np.nan
print(f"Flagged {df['yearbuilt_anomaly_flag'].sum()} year built anomalies")
print(f"Set {future_built.sum()} future year built values to null")

# ── Step 8 – Recalculate engineered metrics ────────────────────────────────
print("\n--- Step 8: Recalculating engineered metrics ---")

df['price_per_sqft'] = df['ClosePrice'] / df['LivingArea']
df['sale_to_list_ratio'] = df['ClosePrice'] / df['ListPrice']
df['close_to_original_list_ratio'] = df['ClosePrice'] / df['OriginalListPrice']

print("Recalculated: price_per_sqft, sale_to_list_ratio, close_to_original_list_ratio")

# ── Step 9 – Update geographic flags ──────────────────────────────────────
print("\n--- Step 9: Updating geographic flags ---")

df['missing_coordinate_flag'] = df['Latitude'].isna() | df['Longitude'].isna()
df['zero_coordinate_flag'] = (df['Latitude'] == 0) | (df['Longitude'] == 0)
df['positive_longitude_flag'] = df['Longitude'] > 0
df['out_of_state_flag'] = df['StateOrProvince'] != 'CA'
df['out_of_bounds_flag'] = (
    ~df['Latitude'].between(32.529508, 42.009503) |
    ~df['Longitude'].between(-124.482003, -114.131211)
).fillna(False)

print("Geographic flags updated")

# ── Final Summary ──────────────────────────────────────────────────────────
print("\n=== FINAL SUMMARY ===")
print(f"Final shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"\nFlag summary:")
flag_cols = [c for c in df.columns if 'flag' in c]
for col in flag_cols:
    print(f"  {col}: {df[col].sum():,} ({df[col].mean()*100:.2f}%)")

print(f"\nKey metrics after cleaning:")
print(f"  Median ClosePrice: ${df['ClosePrice'].median():,.0f}")
print(f"  Median LivingArea: {df['LivingArea'].median():,.0f} sqft")
print(f"  Median DaysOnMarket: {df['DaysOnMarket'].median():.0f} days")
print(f"  Median price_per_sqft: ${df['price_per_sqft'].median():,.0f}")
print(f"  Median sale_to_list_ratio: {df['sale_to_list_ratio'].median():.3f}")

# ── Save ───────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT, index=False)
print(f"\nSaved to: {OUTPUT}")