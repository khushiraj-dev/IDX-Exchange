'''
Week 2-3 – Mortgage Rate Enrichment
Purpose: Fetch the 30-year fixed mortgage rate from FRED, resample from weekly 
to monthly frequency, and merge onto both sold and listings datasets using a 
year_month key. Save both enriched datasets as CSVs.
'''

import pandas as pd
from pathlib import Path

# Paths
RAW_DIR = Path(r"C:\Users\khush\idx files")
REPORTS_DIR = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports")

# Load combined datasets from Week 1
sold = pd.read_csv(RAW_DIR / "sold_combined.csv", low_memory=False)
listings = pd.read_csv(RAW_DIR / "listings_combined.csv", low_memory=False)

print("Sold shape:", sold.shape)
print("Listings shape:", listings.shape)

# -----------------------------
# Step 1 – Fetch mortgage rate data from FRED
# No API key required — data is publicly available
# -----------------------------
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=['observation_date'])
mortgage.columns = ['date', 'rate_30yr_fixed']

print(f"\nMortgage data fetched: {len(mortgage)} weekly records")
print(mortgage.tail())

# -----------------------------
# Step 2 – Resample weekly rates to monthly averages
# FRED publishes weekly (every Thursday) so we average all weeks in each month
# -----------------------------
mortgage['year_month'] = mortgage['date'].dt.to_period('M')
mortgage_monthly = (
    mortgage.groupby('year_month')['rate_30yr_fixed']
    .mean()
    .reset_index()
)

print(f"\nMortgage data resampled to {len(mortgage_monthly)} monthly records")
print(mortgage_monthly.tail())

# -----------------------------
# Step 3 – Create year_month key on MLS datasets
# Sold: key off CloseDate (when transaction completed)
# Listings: key off ListingContractDate (when listing went live)
# -----------------------------
sold['year_month'] = pd.to_datetime(sold['CloseDate']).dt.to_period('M')
listings['year_month'] = pd.to_datetime(listings['ListingContractDate']).dt.to_period('M')

# -----------------------------
# Step 4 – Merge mortgage rates onto both datasets
# Using left merge to keep all MLS records even if no rate match
# -----------------------------
sold_with_rates = sold.merge(mortgage_monthly, on='year_month', how='left')
listings_with_rates = listings.merge(mortgage_monthly, on='year_month', how='left')

print("\nPreview of merged sold dataset:")
print(sold_with_rates[['CloseDate', 'year_month', 'ClosePrice', 'rate_30yr_fixed']].head())

# -----------------------------
# Step 5 – Validate merge
# rate_30yr_fixed should be null for 0 rows if all months matched
# -----------------------------
sold_null_rates = sold_with_rates['rate_30yr_fixed'].isnull().sum()
listings_null_rates = listings_with_rates['rate_30yr_fixed'].isnull().sum()

print(f"\nNull rate values after merge (Sold): {sold_null_rates}")
print(f"Null rate values after merge (Listings): {listings_null_rates}")

if sold_null_rates == 0 and listings_null_rates == 0:
    print("Validation passed — no null rate values!")
else:
    print("Warning — some rows did not match a mortgage rate!")

# -----------------------------
# Save enriched datasets
# -----------------------------
sold_with_rates.to_csv(REPORTS_DIR / "sold_with_rates.csv", index=False)
listings_with_rates.to_csv(REPORTS_DIR / "listings_with_rates.csv", index=False)
