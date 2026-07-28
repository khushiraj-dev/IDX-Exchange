# %% [markdown]
# ## Outlier Detection and Data Quality
# 
# Extreme values in price, price per square footage, close to list ratio, or days on market can distort market
# averages and trends. You will implement a statistical method to identify and remove these records.

# %%
import pandas as pd
from pathlib import Path

REPORTS_DIR = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports")

sold = pd.read_csv(REPORTS_DIR / "sold_with_districts.csv", low_memory=False)

print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")

# %%
# Baseline distribution before outlier flagging
numeric_cols = ['ClosePrice', 'LivingArea', 'DaysOnMarket']

print("=== Baseline Distribution (Before Outlier Flagging) ===")
print(sold[numeric_cols].describe(percentiles=[.05, .25, .5, .75, .95]))

# %% [markdown]
# Key numbers to remember for comparison later:
# 
# Median ClosePrice: $825,000
# 
# Median LivingArea: 1,646 sqft
# 
# Median DaysOnMarket: 18 days

# %%
# IQR Outlier Detection
def add_iqr_flag(df, column, multiplier=1.5):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    flag_col = f"{column.lower()}_outlier_flag"
    df[flag_col] = (df[column] < lower) | (df[column] > upper)
    print(f"{column}: lower={lower:,.0f}, upper={upper:,.0f}, flagged={df[flag_col].sum():,} ({df[flag_col].mean()*100:.1f}%)")
    return df

sold = add_iqr_flag(sold, 'ClosePrice')
sold = add_iqr_flag(sold, 'LivingArea')
sold = add_iqr_flag(sold, 'DaysOnMarket')

# %%
# Compare with 3.0x multiplier
print("=== Comparison: 1.5x vs 3.0x IQR multiplier ===\n")

for col in ['ClosePrice', 'LivingArea', 'DaysOnMarket']:
    Q1 = sold[col].quantile(0.25)
    Q3 = sold[col].quantile(0.75)
    IQR = Q3 - Q1
    
    for multiplier in [1.5, 3.0]:
        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR
        flagged = ((sold[col] < lower) | (sold[col] > upper)).sum()
        pct = flagged / len(sold) * 100
        print(f"{col} ({multiplier}x): upper={upper:,.0f}, flagged={flagged:,} ({pct:.1f}%)")
    print()

# %% [markdown]
# ging w/ 3.0 x multiplier since it is less agressive to cutting out luxury homes

# %%
# Redo IQR flags with 3.0x multiplier
sold = add_iqr_flag(sold, 'ClosePrice', multiplier=3.0)
sold = add_iqr_flag(sold, 'LivingArea', multiplier=3.0)
sold = add_iqr_flag(sold, 'DaysOnMarket', multiplier=3.0)

# Combined flag — True if ANY field is flagged
sold['iqr_outlier_any_flag'] = (
    sold['closeprice_outlier_flag'] |
    sold['livingarea_outlier_flag'] |
    sold['daysonmarket_outlier_flag']
)

print(f"Records flagged by at least one IQR flag: {sold['iqr_outlier_any_flag'].sum():,} ({sold['iqr_outlier_any_flag'].mean()*100:.1f}%)")

# %%
# Save full flagged dataset (all records with flag columns)
sold.to_csv(REPORTS_DIR / "sold_flagged.csv", index=False)
print(f"Full flagged dataset saved: {sold.shape[0]:,} rows x {sold.shape[1]} columns")

# Save clean filtered dataset (only non-flagged records)
sold_filtered = sold[~sold['iqr_outlier_any_flag']]
sold_filtered.to_csv(REPORTS_DIR / "sold_filtered.csv", index=False)
print(f"Clean filtered dataset saved: {sold_filtered.shape[0]:,} rows x {sold_filtered.shape[1]} columns")

# Written comparison
print("\n=== Before vs After Filtering ===")
print(f"{'Metric':<25} {'Before':>15} {'After':>15} {'Change':>10}")
print("-" * 65)
print(f"{'Row count':<25} {len(sold):>15,} {len(sold_filtered):>15,} {len(sold_filtered)-len(sold):>10,}")
print(f"{'Median ClosePrice':<25} ${sold['ClosePrice'].median():>14,.0f} ${sold_filtered['ClosePrice'].median():>14,.0f} ${sold_filtered['ClosePrice'].median()-sold['ClosePrice'].median():>9,.0f}")
print(f"{'Median LivingArea':<25} {sold['LivingArea'].median():>14,.0f} {sold_filtered['LivingArea'].median():>14,.0f} {sold_filtered['LivingArea'].median()-sold['LivingArea'].median():>10,.0f}")
print(f"{'Median DaysOnMarket':<25} {sold['DaysOnMarket'].median():>14,.0f} {sold_filtered['DaysOnMarket'].median():>14,.0f} {sold_filtered['DaysOnMarket'].median()-sold['DaysOnMarket'].median():>10,.0f}")
print(f"{'Mean ClosePrice':<25} ${sold['ClosePrice'].mean():>14,.0f} ${sold_filtered['ClosePrice'].mean():>14,.0f} ${sold_filtered['ClosePrice'].mean()-sold['ClosePrice'].mean():>9,.0f}")

# %% [markdown]
# ### Week 7 – Outlier Detection Summary
# 
# **Method:** Interquartile Range (IQR) with 3.0x multiplier
# A 3.0x multiplier was chosen over the textbook 1.5x because California real estate 
# is heavily right-skewed. The 1.5x multiplier flagged 7.5% of ClosePrice records with 
# an upper bound of $2.4M — too low for legitimate luxury markets like San Mateo ($1.7M median) 
# and Santa Clara ($1.6M median). The 3.0x multiplier sets a more appropriate $3.475M upper 
# bound and flags only 3.2% of records.
# 
# **IQR Bounds (3.0x multiplier):**
# - ClosePrice: upper = $3,475,000 — flagged 14,451 records (3.2%)
# - LivingArea: upper = 5,152 sqft — flagged 4,931 records (1.1%)
# - DaysOnMarket: upper = 168 days — flagged 11,941 records (2.7%)
# - Combined (any flag): 26,695 records flagged (6.0%)
# 
# **Before vs After Filtering:**
# 
# | Metric | Before | After | Change |
# |---|---|---|---|
# | Row count | 448,253 | 421,558 | -26,695 |
# | Median ClosePrice | $825,000 | $808,000 | -$17,000 |
# | Median LivingArea | 1,646 sqft | 1,614 sqft | -32 sqft |
# | Median DaysOnMarket | 18 days | 17 days | -1 day |
# | Mean ClosePrice | $1,183,711 | $984,326 | -$199,385 |
# 
# **Key Takeaway:**
# Removing the 6% flagged records moved the **median close price by only 2%** ($17k) 
# but the **mean by 17%** ($199k). This confirms that medians resist outliers and 
# justifies their use throughout this project's market analysis. The filtered dataset 
# (421,558 rows) will be used for Tableau dashboards where typical market behavior 
# is the focus, while the full flagged dataset (448,253 rows) is preserved for 
# complete market analysis.


