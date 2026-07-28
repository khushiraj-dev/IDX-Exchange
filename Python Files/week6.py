# %% [markdown]
# ## Future Engineering and Market Metrics
# 
# With clean data in hand, you will engineer the key market indicators that power the Tableau dashboards.

# %%
import pandas as pd
from pathlib import Path

REPORTS_DIR = Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports")

sold = pd.read_csv(REPORTS_DIR / "sold_cleaned.csv", low_memory=False)

print(f"Sold: {sold.shape[0]:,} rows x {sold.shape[1]} columns")

# %%
date_cols = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate']
sold[date_cols] = sold[date_cols].apply(pd.to_datetime, errors='coerce')

print("Date dtypes after conversion:")
print(sold[date_cols].dtypes)

# %%
# -----------------------------
# Feature Engineering – Market Metrics
# -----------------------------

# Price Ratio: measures negotiation strength (how close to original list price)
sold['price_ratio'] = sold['ClosePrice'] / sold['OriginalListPrice']

# Price Per Square Foot: normalizes price across different home sizes
sold['price_per_sqft'] = sold['ClosePrice'] / sold['LivingArea']

# YrMo: year-month string derived from CloseDate for time-series analysis
sold['YrMo'] = sold['CloseDate'].dt.to_period('M').astype(str)

# Close to Original List Ratio: captures full price reduction history
sold['close_to_original_list_ratio'] = sold['ClosePrice'] / sold['OriginalListPrice']

# Listing to Contract Days: time from listing to accepted offer
sold['listing_to_contract_days'] = (sold['PurchaseContractDate'] - sold['ListingContractDate']).dt.days

# Contract to Close Days: escrow and closing period duration
sold['contract_to_close_days'] = (sold['CloseDate'] - sold['PurchaseContractDate']).dt.days

# Preview new columns
print(sold[['ClosePrice', 'OriginalListPrice', 'LivingArea', 
            'price_ratio', 'price_per_sqft', 'YrMo',
            'listing_to_contract_days', 'contract_to_close_days']].head())

print(f"\nNew shape: {sold.shape[0]:,} rows x {sold.shape[1]} columns")

# %% [markdown]
# ### Market Metrics – Key Observations
# 
# **Price Ratio / Close to Original List Ratio** (ClosePrice / OriginalListPrice)
# - A ratio above 1.0 means the home sold above original list price (competitive market)
# - A ratio below 1.0 means the seller had to reduce their price
# 
# 
# **Price Per Square Foot** (ClosePrice / LivingArea)
# - Normalizes price across homes of different sizes
# - Allows fair comparison between a 1,000 sqft condo and a 3,000 sqft house
# - Row 4 shows $928/sqft — likely a high-end property in a premium location
# 
# **YrMo**
# - Derived from CloseDate for time-series grouping in Tableau
# - Enables monthly trend analysis across the full Jan 2024 – Jun 2026 dataset
# 
# **Listing to Contract Days**
# - Median: 25 days — typical California home goes under contract in about 3.5 weeks
# - Max: 14,657 days (40 years) — extreme outliers exist, will be addressed in Week 7 IQR filtering
# - Rows 0-2 show unusually long values (777, 114, 255 days) — these are valid but unusual cases
# 
# **Contract to Close Days**
# - Median: 29 days — typical escrow period is about 30 days, which aligns perfectly
# - Max: 36,629 days — clearly bad data, will be flagged in Week 7
# - Most homes (75th percentile) close within 36 days of going under contract

# %%
print("listing_to_contract_days summary:")
print(sold['listing_to_contract_days'].describe(percentiles=[.05, .25, .5, .75, .95]))

print("\ncontract_to_close_days summary:")
print(sold['contract_to_close_days'].describe(percentiles=[.05, .25, .5, .75, .95]))

# %% [markdown]
# ### Listing to Contract Days & Contract to Close Days – Distribution Summary
# 
# **Listing to Contract Days**
# - Median: 25 days — most homes go under contract within 3.5 weeks
# - 75% of homes go under contract within 58 days
# - 95th percentile: 153 days — only 5% of homes take longer than 5 months
# - Max: 14,657 days — extreme outlier, likely a data error, will be handled in Week 7
# 
# **Contract to Close Days**
# - Median: 29 days — closely matches the standard 30-day escrow period
# - 75% of homes close within 36 days of going under contract
# - 95th percentile: 64 days — only 5% of escrow periods exceed 2 months
# - Max: 36,629 days (100 years) — clearly bad data, will be handled in Week 7
# 
# **Key Takeaway**
# The median values are reliable and align with industry expectations for California real estate. 
# The extreme maximums will be addressed in Week 7 outlier detection.
# Both metrics confirm that California homes move quickly. From listing to close typically takes 
# about 54 days (25 + 29) for the median property.

# %%
# Segment Analysis — grouped summary statistics
# By County
county_summary = sold.groupby('CountyOrParish').agg(
    median_close_price=('ClosePrice', 'median'),
    median_days_on_market=('DaysOnMarket', 'median'),
    median_price_per_sqft=('price_per_sqft', 'median'),
    median_price_ratio=('price_ratio', 'median'),
    total_sales=('ClosePrice', 'count')
).sort_values('median_close_price', ascending=False).reset_index()

print("Top 10 counties by median close price:")
print(county_summary.head(10))

# %% [markdown]
# ### Segment Analysis – County
# 
# **Top Counties by Median Close Price (Jan 2024 – Jun 2026)**
# - San Mateo ($1.7M) and Santa Clara ($1.6M) lead — Bay Area tech corridor commands significant premium
# - San Francisco ($1.2M) ranks 4th despite being the most famous CA market — condo-heavy mix lowers median
# - Orange County ($1.18M) is the most active luxury market with 50,393 sales — largest sample size at the top
# 
# **Market Competitiveness (Price Ratio)**
# - Santa Clara (1.022) and Alameda (1.020) are the most competitive — homes selling above list price
# - Marin (0.976) and Santa Cruz (0.983) see more negotiation — buyers have more leverage
# - A ratio above 1.0 signals a seller's market; below 1.0 signals a buyer's market
# 
# **Speed of Sale (Median Days on Market)**
# - Santa Clara (10 days) and San Mateo (12 days) are the fastest moving markets
# - Del Norte (320 days) and Alpine (231 days) are extremely slow — but both have only 1 sale so not representative
# - Future analysis should filter to counties with at least 50 sales for reliable comparisons
# 
# **Price Per Square Foot**
# - San Mateo ($1,051/sqft) and Santa Clara ($965/sqft) are by far the most expensive per sqft
# - San Francisco ($897/sqft) ranks 3rd — dense urban market with smaller units
# - Orange County ($674/sqft) offers more space for the price compared to Bay Area

# %%
# By PropertySubType
subtype_summary = sold.groupby('PropertySubType').agg(
    median_close_price=('ClosePrice', 'median'),
    median_days_on_market=('DaysOnMarket', 'median'),
    median_price_per_sqft=('price_per_sqft', 'median'),
    total_sales=('ClosePrice', 'count')
).sort_values('total_sales', ascending=False).reset_index()

print("Sales by PropertySubType:")
print(subtype_summary)

# By ListOfficeName (top 20 offices by volume)
office_summary = sold.groupby('ListOfficeName').agg(
    total_sales=('ClosePrice', 'count'),
    total_volume=('ClosePrice', 'sum'),
    median_close_price=('ClosePrice', 'median')
).sort_values('total_sales', ascending=False).reset_index()

print("\nTop 20 listing offices by sales volume:")
print(office_summary.head(20))

# %% [markdown]
# ### Segment Analysis – Property Subtype and Listing Office
# 
# **Sales by Property Subtype**
# - SingleFamilyResidence dominates with 335,766 sales — 75% of all residential transactions
# - Condominiums are the second most common at a significantly lower median price ($626,500 vs $895,000)
# - Townhouses sit between the two at $800,000 median — popular middle ground for buyers
# - Multi-unit properties (Duplex $910k, Triplex $1.135M, Quadruplex $1.275M) command higher prices 
#   as investors factor in rental income potential
# - MobileHome has the longest median DOM at 76 days — hardest property type to sell
# - Cabin (46.5 days) and Timeshare (58 days) also take significantly longer than average
# 
# **Speed of Sale by Subtype**
# - SingleFamilyResidence and Townhouse both sell in 17 days median — fastest moving types
# - DeededParking sells fastest at 12 days median — niche but high demand in dense urban areas
# - MobileHome (76 days) and Timeshare (58 days) are the slowest moving property types
# 
# **Top Listing Offices by Volume**
# - High volume offices represent the most active brokerages in the California market
# - Total volume figures show which offices handle the highest dollar value of transactions
# - This data powers the competitive intelligence dashboards in Weeks 8-10
# - Offices with high volume but lower median prices likely focus on entry-level or mid-market homes
# - Offices with lower volume but higher median prices likely specialize in luxury properties

# %% [markdown]
# **Adding in the school district boundaries using GeoPandas**

# %%
import geopandas as gpd
from pathlib import Path

# Load California School District boundaries
geojson_path = Path(r"C:\Users\khush\Desktop\IDX-Exchange\data\DistrictAreas2526_-284845464123469011.geojson")
school_districts = gpd.read_file(geojson_path)

print("School districts shape:", school_districts.shape)
print("\nColumns:", school_districts.columns.tolist())
print("\nSample:")
print(school_districts.head(3))

# %%
#filter to Unified districts only:
unified = school_districts[school_districts['DistrictType'] == 'Unified']
print(f"Total districts: {len(school_districts)}")
print(f"Unified districts only: {len(unified)}")
print(unified['DistrictType'].value_counts())

# %%
# Check current coordinate system of school districts
print("School districts CRS:", unified.crs)

# %% [markdown]
# EPSG:3857 is a projected coordinate system (meters, used for web maps like Google Maps). Our property lat/lon coordinates are in EPSG:4326 (standard latitude/longitude). We need to reproject the school districts to match.

# %%
#Reproject school districts to EPSG:4326
unified_4326 = unified.to_crs("EPSG:4326")
print("Reprojected CRS:", unified_4326.crs)
print(unified_4326.geometry.head(2))

# %%
# Convert sold properties to GeoDataFrame using Latitude and Longitude
sold_geo = gpd.GeoDataFrame(
    sold,
    geometry=gpd.points_from_xy(sold['Longitude'], sold['Latitude']),
    crs="EPSG:4326"
)

print(f"Sold GeoDataFrame shape: {sold_geo.shape}")
print(sold_geo.geometry.head(3))

# %%
# Perform spatial join to find which school district each property falls in
sold_with_districts = gpd.sjoin(
    sold_geo,
    unified_4326[['DistrictName', 'geometry']],
    how='left',
    predicate='within'
)

print(f"Shape after spatial join: {sold_with_districts.shape}")
print(f"Properties matched to a district: {sold_with_districts['DistrictName'].notna().sum():,}")
print(f"Properties not matched: {sold_with_districts['DistrictName'].isna().sum():,}")

# %%
# Drop the extra columns added by the spatial join
sold_with_districts = sold_with_districts.drop(columns=['geometry', 'index_right'])

# Convert back to regular DataFrame
sold_with_districts = pd.DataFrame(sold_with_districts)

print(f"Final shape: {sold_with_districts.shape}")
print(f"\nSample of DistrictName column:")
print(sold_with_districts[['CountyOrParish', 'City', 'DistrictName']].dropna().head(10))

# %%
sold_with_districts.to_csv(
    Path(r"C:\Users\khush\Desktop\IDX-Exchange\Reports") / "sold_with_districts.csv",
    index=False
)

print("Saved sold_with_districts.csv!")
print(f"Final shape: {sold_with_districts.shape[0]:,} rows x {sold_with_districts.shape[1]} columns")
print(f"\nDistrict coverage: {sold_with_districts['DistrictName'].notna().sum():,} / {len(sold_with_districts):,} properties ({sold_with_districts['DistrictName'].notna().mean()*100:.1f}%)")

# %% [markdown]
# ### School District Mapping
# 
# - Downloaded California Unified School District boundaries (2025-26) from data.ca.gov
# - Filtered from 936 total districts to 345 Unified districts only
# - Reprojected from EPSG:3857 to EPSG:4326 to match property lat/lon coordinates
# - Performed spatial join (gpd.sjoin) to match each property's coordinates to a district polygon
# - Added DistrictName column to the sold dataset
# 
# **Coverage:** 335,602 / 448,253 properties matched (74.9%)
# 
# **Unmatched properties (25.1%) are likely due to:**
# - Missing or invalid coordinates (flagged in Weeks 4-5)
# - Properties in areas not covered by a Unified district
# - Properties on district boundaries
# 
# The DistrictName column will be used in Tableau dashboards to filter and group market analysis by school district.

# %%
# By MLSAreaMajor
mls_area_summary = sold_with_districts.groupby('MLSAreaMajor').agg(
    median_close_price=('ClosePrice', 'median'),
    median_days_on_market=('DaysOnMarket', 'median'),
    median_price_per_sqft=('price_per_sqft', 'median'),
    median_price_ratio=('price_ratio', 'median'),
    total_sales=('ClosePrice', 'count')
).sort_values('total_sales', ascending=False).reset_index()

print("Top 20 MLS Areas by total sales:")
print(mls_area_summary.head(20))

# %%
# By BuyerOfficeName (competitive intelligence)
buyer_office_summary = sold_with_districts.groupby('BuyerOfficeName').agg(
    total_purchases=('ClosePrice', 'count'),
    total_volume=('ClosePrice', 'sum'),
    median_close_price=('ClosePrice', 'median')
).sort_values('total_purchases', ascending=False).reset_index()

print("Top 20 buyer offices by purchases:")
print(buyer_office_summary.head(20))

# %% [markdown]
# ### Segment Analysis – MLSAreaMajor and BuyerOfficeName
# 
# **MLS Area Analysis**
# - "699 - Not Defined" is the largest area with 46,384 sales — these are properties without a specific MLS area assigned
# - Southwest Riverside County is the most active defined area with 21,893 sales
# - Inland Empire dominates the top 20 by volume — Riverside, Corona, San Bernardino, Moreno Valley, Fontana, Ontario
# - La Quinta South of HWY 111 (50 days) and Rancho Mirage (48.5 days) have the longest DOM — resort/luxury markets move slower
# - Fullerton (12 days) and Whittier (14 days) are the fastest moving areas in the top 20
# - Price ratios are very close to 1.0 across most areas — suggesting balanced market conditions
# 
# **Buyer Office Competitive Intelligence**
# - **Compass dominates** with 29,646 purchases and $53.5B total volume — by far the most active buyer brokerage
# - **Coldwell Banker Realty** is second with 16,226 purchases
# - **Compass has the highest median close price** at $1.337M — serving the luxury market
# - **The Agency** has only 2,756 purchases but $1.55M median price — pure luxury specialist
# - **Sotheby's International Realty** ($1.395M median) and **Intero** ($1.335M) also focus on high-end properties
# - **NONMEMBER MRML** (9,766 purchases) represents transactions where the buyer's agent is not an MLS member
# - **eXp Realty** appears twice under slightly different names — data quality issue worth noting
# - **Redfin** also appears twice — same issue, combined they would rank higher


