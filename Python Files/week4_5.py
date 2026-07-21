'''
Weeks 4-5 – Data Cleaning and Preparation
Purpose: Clean and prepare the enriched CRMLS datasets for analysis.
Transformations include date conversions, dropping high-missing and redundant
columns, flagging invalid numeric values, date consistency checks, and
geographic quality flags. Records are flagged rather than deleted to preserve
raw data for future reference.
'''

import pandas as pd
from pathlib import Path

# Paths
REPORTS_DIR = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports")

# Load enriched datasets from Weeks 2-3
sold = pd.read_csv(REPORTS_DIR / "sold_with_rates.csv", low_memory=False)
listings = pd.read_csv(REPORTS_DIR / "listings_with_rates.csv", low_memory=False)

print("=== Starting shapes ===")
print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")
print(f"Listings: {listings.shape[0]:,} rows x {listings.shape[1]} columns")

# -----------------------------
# Step 1 – Convert Date Columns to Datetime
# Date columns are stored as strings by default. Converting them to datetime
# allows sorting, time difference calculations, and consistency checks.
# errors='coerce' sets badly formatted dates to null instead of crashing.
# -----------------------------
date_cols_sold = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']
date_cols_listings = ['ListingContractDate', 'ContractStatusChangeDate']

sold[date_cols_sold] = sold[date_cols_sold].apply(pd.to_datetime, errors='coerce')
listings[date_cols_listings] = listings[date_cols_listings].apply(pd.to_datetime, errors='coerce')

# Add Month and Year columns for easier Tableau grouping
sold['Month'] = pd.to_datetime(sold['year_month'], format='%Y-%m', errors='coerce').dt.month
sold['Year'] = pd.to_datetime(sold['year_month'], format='%Y-%m', errors='coerce').dt.year
listings['Month'] = pd.to_datetime(listings['year_month'], format='%Y-%m', errors='coerce').dt.month
listings['Year'] = pd.to_datetime(listings['year_month'], format='%Y-%m', errors='coerce').dt.year

print("\nDate columns converted to datetime successfully")

# -----------------------------
# Step 2 – Drop Columns with 100% Missing Values and >90% Missing
# 100% empty columns contain no data and add no analytical value.
# >90% missing columns are also dropped unless they are core fields.
# School fields (ElementarySchool, MiddleOrJuniorSchool, HighSchool) are
# retained for Week 6 school district feature engineering.
# -----------------------------
cols_to_drop = [
    # 100% empty
    'TaxAnnualAmount', 'AboveGradeFinishedArea', 'TaxYear',
    'ElementarySchoolDistrict', 'CoveredSpaces', 'BusinessType',
    'MiddleOrJuniorSchoolDistrict', 'FireplacesTotal',
    # >90% missing and not useful for analysis
    'WaterfrontYN', 'BelowGradeFinishedArea', 'BuilderName',
    'LotSizeDimensions', 'BuildingAreaTotal', 'CoBuyerAgentFirstName'
]

sold = sold.drop(columns=cols_to_drop, errors='ignore')
listings = listings.drop(columns=cols_to_drop, errors='ignore')

print(f"\nAfter dropping high-missing columns:")
print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")
print(f"Listings: {listings.shape[0]:,} rows x {listings.shape[1]} columns")

# -----------------------------
# Step 3 – Drop Redundant and Metadata Columns
# Removing columns that are duplicates, purely administrative,
# or not needed for market or competitive analysis.
# -----------------------------

# Drop .1 duplicate columns from listings first
dot1_cols = [col for col in listings.columns if col.endswith('.1')]
listings = listings.drop(columns=dot1_cols, errors='ignore')
print(f"\nDropped {len(dot1_cols)} duplicate .1 columns from listings")

redundant_cols = [
    'LotSizeArea', 'LotSizeSquareFeet',            # redundant with LotSizeAcres
    'ListingKeyNumeric', 'ListingId',               # redundant with ListingKey
    'BuyerAgencyCompensationType', 'BuyerAgencyCompensation',  # not needed
    'OriginatingSystemName', 'OriginatingSystemSubName',       # admin metadata
    'StreetNumberNumeric',                          # redundant with UnparsedAddress
    'MlsStatus',                                    # always Closed in sold data
    'PropertyType',                                 # always Residential
    'CoListAgentFirstName', 'CoListAgentLastName',  # co-agent metadata
    'BuyerAgentMlsId',                              # admin metadata
    'AssociationFeeFrequency',                      # less useful than AssociationFee
    'SubdivisionName',                              # not needed for market analysis
]

sold = sold.drop(columns=redundant_cols, errors='ignore')
listings = listings.drop(columns=redundant_cols, errors='ignore')

print(f"\nAfter dropping redundant columns:")
print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")
print(f"Listings: {listings.shape[0]:,} rows x {listings.shape[1]} columns")

# -----------------------------
# Step 4 – Flag Invalid Numeric Values
# Records are flagged rather than deleted to preserve raw data.
# ClosePrice <= 0, LivingArea <= 0, DaysOnMarket < 0 are impossible values.
# Negative bedrooms or bathrooms are also impossible.
# -----------------------------
sold['invalid_close_price'] = sold['ClosePrice'] <= 0
sold['invalid_living_area'] = sold['LivingArea'] <= 0
sold['invalid_days_on_market'] = sold['DaysOnMarket'] < 0
sold['invalid_bed_or_bath'] = (sold['BedroomsTotal'] < 0) | (sold['BathroomsTotalInteger'] < 0)

listings['invalid_living_area'] = listings['LivingArea'] <= 0
listings['invalid_days_on_market'] = listings['DaysOnMarket'] < 0
listings['invalid_bed_or_bath'] = (listings['BedroomsTotal'] < 0) | (listings['BathroomsTotalInteger'] < 0)

print("\n=== Invalid Numeric Flags (Sold) ===")
print(f"Invalid ClosePrice: {sold['invalid_close_price'].sum()}")
print(f"Invalid LivingArea: {sold['invalid_living_area'].sum()}")
print(f"Invalid DaysOnMarket: {sold['invalid_days_on_market'].sum()}")
print(f"Invalid Bed/Bath: {sold['invalid_bed_or_bath'].sum()}")

print("\n=== Invalid Numeric Flags (Listings) ===")
print(f"Invalid LivingArea: {listings['invalid_living_area'].sum()}")
print(f"Invalid DaysOnMarket: {listings['invalid_days_on_market'].sum()}")
print(f"Invalid Bed/Bath: {listings['invalid_bed_or_bath'].sum()}")

# -----------------------------
# Step 5 – Date Consistency Flags
# ListingContractDate should precede PurchaseContractDate,
# which should precede CloseDate. Flag any violations for later review.
# -----------------------------
sold['listing_after_close_flag'] = sold['ListingContractDate'] > sold['CloseDate']
sold['purchase_after_close_flag'] = sold['PurchaseContractDate'] > sold['CloseDate']
sold['negative_timeline_flag'] = sold['ListingContractDate'] > sold['PurchaseContractDate']

print("\n=== Date Consistency Flags (Sold) ===")
print(f"Listing after close: {sold['listing_after_close_flag'].sum()}")
print(f"Purchase after close: {sold['purchase_after_close_flag'].sum()}")
print(f"Negative timeline: {sold['negative_timeline_flag'].sum()}")

# -----------------------------
# Step 6 – Geographic Data Quality Flags
# California bounding box coordinates:
# Latitude: 32.529508 to 42.009503
# Longitude: -124.482003 to -114.131211
# -----------------------------
sold['missing_coordinates'] = sold['Latitude'].isnull() | sold['Longitude'].isnull()
sold['zero_coordinates'] = (sold['Latitude'] == 0) | (sold['Longitude'] == 0)
sold['invalid_longitude'] = sold['Longitude'] > 0
sold['out_of_state_flag'] = sold['StateOrProvince'] != 'CA'
sold['out_of_bounds_flag'] = (
    ~sold['Latitude'].between(32.529508, 42.009503) |
    ~sold['Longitude'].between(-124.482003, -114.131211)
).fillna(False)

listings['missing_coordinates'] = listings['Latitude'].isnull() | listings['Longitude'].isnull()
listings['zero_coordinates'] = (listings['Latitude'] == 0) | (listings['Longitude'] == 0)
listings['invalid_longitude'] = listings['Longitude'] > 0
listings['out_of_state_flag'] = listings['StateOrProvince'] != 'CA'
listings['out_of_bounds_flag'] = (
    ~listings['Latitude'].between(32.529508, 42.009503) |
    ~listings['Longitude'].between(-124.482003, -114.131211)
).fillna(False)

print("\n=== Geographic Flags (Sold) ===")
print(f"Missing coordinates: {sold['missing_coordinates'].sum()}")
print(f"Zero coordinates: {sold['zero_coordinates'].sum()}")
print(f"Invalid longitude: {sold['invalid_longitude'].sum()}")
print(f"Out of state: {sold['out_of_state_flag'].sum()}")
print(f"Out of bounds: {sold['out_of_bounds_flag'].sum()}")

print("\n=== Geographic Flags (Listings) ===")
print(f"Missing coordinates: {listings['missing_coordinates'].sum()}")
print(f"Zero coordinates: {listings['zero_coordinates'].sum()}")
print(f"Invalid longitude: {listings['invalid_longitude'].sum()}")
print(f"Out of state: {listings['out_of_state_flag'].sum()}")
print(f"Out of bounds: {listings['out_of_bounds_flag'].sum()}")

# -----------------------------
# Step 7 – Save Cleaned Datasets
# -----------------------------
sold.to_csv(REPORTS_DIR / "sold_cleaned.csv", index=False)
listings.to_csv(REPORTS_DIR / "listings_cleaned.csv", index=False)

print("\n=== Final Shapes ===")
print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")
print(f"Listings: {listings.shape[0]:,} rows x {listings.shape[1]} columns")
print(f"\nFiles saved to: {REPORTS_DIR}")