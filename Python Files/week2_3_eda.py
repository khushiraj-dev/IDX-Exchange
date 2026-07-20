'''
Week 2-3 – Dataset Structuring, Validation and EDA
Purpose: Inspect and validate the combined CRMLS datasets, perform missing value analysis,
generate numeric distribution summaries, visualizations, and answer key EDA questions.
'''

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
RAW_DIR = Path(r"C:\Users\khush\idx files")
REPORTS_DIR = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports")
VIZ_DIR = REPORTS_DIR / "Visualizations"
os.makedirs(VIZ_DIR, exist_ok=True)

# Load data
sold = pd.read_csv(RAW_DIR / "sold_combined.csv", low_memory=False)
listings = pd.read_csv(RAW_DIR / "listings_combined.csv", low_memory=False)

print("Sold shape:", sold.shape)
print("Listings shape:", listings.shape)

# -----------------------------
# Field Classification
# -----------------------------
CORE_FIELDS = {
    'ClosePrice', 'ListPrice', 'OriginalListPrice',
    'LivingArea', 'LotSizeAcres', 'BedroomsTotal', 'BathroomsTotalInteger',
    'DaysOnMarket', 'YearBuilt', 'PropertyType', 'PropertySubType',
    'CountyOrParish', 'City', 'PostalCode', 'Latitude', 'Longitude',
    'CloseDate', 'ListingContractDate', 'PurchaseContractDate',
    'ContractStatusChangeDate', 'ListingKey', 'ListingId'
}

METADATA_FIELDS = {
    'ListAgentFirstName', 'ListAgentLastName', 'ListAgentFullName', 'ListAgentEmail',
    'CoListAgentFirstName', 'CoListAgentLastName',
    'BuyerAgentFirstName', 'BuyerAgentLastName', 'BuyerAgentMlsId',
    'CoBuyerAgentFirstName', 'ListOfficeName', 'BuyerOfficeName',
    'CoListOfficeName', 'BuyerOfficeAOR', 'BuyerAgentAOR', 'ListAgentAOR',
    'OriginatingSystemName', 'OriginatingSystemSubName',
    'ListingKeyNumeric', 'MlsStatus', 'StreetNumberNumeric'
}

def classify_fields(columns):
    rows = []
    for col in columns:
        if col in METADATA_FIELDS:
            category = 'metadata'
        elif col in CORE_FIELDS:
            category = 'core'
        else:
            category = 'market_analysis_other'
        rows.append({'column': col, 'category': category})
    return pd.DataFrame(rows)

field_classification = classify_fields(sold.columns)
field_classification.to_csv(REPORTS_DIR / "field_classification.csv", index=False)
print("Field classification saved!")

# -----------------------------
# Data Types Review
# -----------------------------
print("\nSold data types summary:")
print(sold.dtypes.value_counts())
print("\nListings data types summary:")
print(listings.dtypes.value_counts())
# Note: date columns stored as strings — will be converted in Weeks 4-5

# -----------------------------
# Missing Value Analysis - Sold
# -----------------------------
missing_sold = sold.isnull().sum()
missing_pct_sold = (missing_sold / len(sold)) * 100
missing_summary_sold = pd.DataFrame({
    'missing_count': missing_sold,
    'missing_pct': missing_pct_sold
}).sort_values('missing_pct', ascending=False)

high_missing_sold = missing_summary_sold[missing_summary_sold['missing_pct'] > 90]
print("\nColumns with >90% missing (Sold):")
print(high_missing_sold)

# Columns to drop vs retain:
# Drop: 100% empty fields (TaxAnnualAmount, AboveGradeFinishedArea, TaxYear, etc.)
# Keep: WaterfrontYN, BasementYN, BelowGradeFinishedArea, BuilderName (useful features)
# Keep: school fields for Week 6 feature engineering

missing_summary_sold.to_csv(REPORTS_DIR / "missing_value_report_sold.csv", index=False)

# -----------------------------
# Missing Value Analysis - Listings
# -----------------------------
missing_listings = listings.isnull().sum()
missing_pct_listings = (missing_listings / len(listings)) * 100
missing_summary_listings = pd.DataFrame({
    'missing_count': missing_listings,
    'missing_pct': missing_pct_listings
}).sort_values('missing_pct', ascending=False)

high_missing_listings = missing_summary_listings[missing_summary_listings['missing_pct'] > 90]
print("\nColumns with >90% missing (Listings):")
print(high_missing_listings)

missing_summary_listings.to_csv(REPORTS_DIR / "missing_value_report_listings.csv", index=False)
print("Missing value reports saved!")

# -----------------------------
# Numeric Distribution Summary
# -----------------------------
numeric_cols = ['ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea',
                'LotSizeAcres', 'BedroomsTotal', 'BathroomsTotalInteger',
                'DaysOnMarket', 'YearBuilt']

distribution_summary = sold[numeric_cols].describe(percentiles=[.05, .25, .5, .75, .95])
print("\nNumeric distribution summary:")
print(distribution_summary)
distribution_summary.to_csv(REPORTS_DIR / "numeric_distribution_summary.csv", index=False)

# -----------------------------
# Visualizations (outliers removed for readability)
# -----------------------------
for col in numeric_cols:
    series = sold[col].dropna()

    # Filter outliers using IQR
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    filtered = series[(series >= q1 - 1.5*iqr) & (series <= q3 + 1.5*iqr)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    filtered.hist(bins=50, ax=ax1)
    ax1.set_title(f'Histogram - {col}')
    ax1.set_xlabel(col)
    ax1.set_ylabel('Count')
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if 'Price' in col else f'{x:,.0f}'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    filtered.to_frame().boxplot(ax=ax2)
    ax2.set_title(f'Boxplot - {col}')

    plt.suptitle(f'{col} (outliers removed for readability)')
    plt.tight_layout()
    plt.savefig(VIZ_DIR / f"{col}_hist_box.png")
    plt.close()

print("Visualizations saved to Reports/Visualizations!")

# -----------------------------
# EDA Questions
# -----------------------------

# 1. Residential vs. other property type share
# Dataset was filtered to Residential only in Week 1.
# After filtering: 448,253 Residential sold records (100% of combined dataset)
# Before filter: 666,037 total sold rows -> 448,253 Residential (67%)

# 2. Median and average close prices
print("\nMedian close price:", sold['ClosePrice'].median())
print("Average close price:", sold['ClosePrice'].mean())
# Median is lower than average due to right skew from extreme high-value outliers

# 3. Days on Market distribution
print("\nDays on Market summary:")
print(sold['DaysOnMarket'].describe())
# Right-skewed: most homes sell fast, but outliers drag mean up
# Min is -288 (impossible) and max is 12,430 (34 years) — to be cleaned in Weeks 4-5

# 4. Percentage sold above vs. below list price
sold['priceDiff'] = sold['ClosePrice'] - sold['ListPrice']
above = (sold['priceDiff'] > 0).sum()
below = (sold['priceDiff'] < 0).sum()
equal = (sold['priceDiff'] == 0).sum()
total = len(sold)

print(f"\nSold above list price: {above/total*100:.1f}%")
print(f"Sold below list price: {below/total*100:.1f}%")
print(f"Sold at list price: {equal/total*100:.1f}%")

# 5. Date consistency issues
print("\nSample date values:")
print(sold[['ListingContractDate', 'PurchaseContractDate', 'CloseDate']].head(10))
print("\nMissing dates (Sold):")
print(sold[['ListingContractDate', 'PurchaseContractDate', 'CloseDate']].isnull().sum())
# Date format consistent (YYYY-MM-DD) but stored as strings
# Some CloseDate precedes PurchaseContractDate — flags to be created in Weeks 4-5
# Missing: ListingContractDate=1, PurchaseContractDate=197, CloseDate=0

# 6. Counties with highest median prices
county_median = sold.groupby('CountyOrParish')['ClosePrice'].median().sort_values(ascending=False)
print("\nTop 10 counties by median close price:")
print(county_median.head(10))
# Note: Del Norte has only 1 sale so its median is not representative
# Future analysis should filter to counties with >= 50 sales

print("\nWeek 2-3 EDA complete. All reports saved to:", REPORTS_DIR)