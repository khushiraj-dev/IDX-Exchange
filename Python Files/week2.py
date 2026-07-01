import pandas as pd

folder = r"C:\Users\khush\idx files"
reports_folder = r"C:\Users\khush\Desktop\IDX-Exchange\Reports"
reports_folder_hist_box = r"C:\Users\khush\Desktop\IDX-Exchange\Reports\Histograms_Boxplots_Wk2_3"


sold = pd.read_csv(folder + r"\sold_combined.csv", low_memory=False)
listings = pd.read_csv(folder + r"\listings_combined.csv", low_memory=False)

#number of rows + columns
print("Sold:", sold.shape) #430716 rows , 82 columns
print("Listings:", listings.shape) # 583650 rows, 84 columns

#review column data types
print(sold.dtypes.value_counts())
print(listings.dtypes.value_counts())
#some date values are stored as string instead of int/date, which may make it hard to sort by date or group
#7 object columns - mb mixed types 

#identifying high-missing columns + Calculate missing counts and percentages per column - sold
missing_sold = sold.isnull().sum()
missing_pct_sold = (missing_sold / len(sold)) * 100
missing_summary_sold = pd.DataFrame({
    'missing_count': missing_sold,
    'missing_pct': missing_pct_sold
}).sort_values('missing_pct', ascending = False)

print(missing_summary_sold)

# flag columns with ?90% missing values - sold

high_missing_sold = missing_summary_sold[missing_summary_sold['missing_pct'] > 90]
print(high_missing_sold)

# Missing value analysis - Listings
missing_listings = listings.isnull().sum()
missing_pct_listings = (missing_listings / len(listings)) * 100
missing_summary_listings = pd.DataFrame({
    'missing_count': missing_listings,
    'missing_pct': missing_pct_listings
}).sort_values('missing_pct', ascending=False)

print(missing_summary_listings)

# Flag columns with >90% missing (Listings)
high_missing_listings = missing_summary_listings[missing_summary_listings['missing_pct'] > 90]
print("Columns with >90% missing (Listings):")
print(high_missing_listings)

# Save both missing value reports
missing_summary_sold.to_csv(reports_folder + r"\missing_value_report_sold.csv")
missing_summary_listings.to_csv(reports_folder + r"\missing_value_report_listings.csv")
print("Missing value reports saved!")

# Decide which columns to drop vs. retain (keep core fields even if partially missing)

#will drop 100% empty fields since it's useless like TaxAnnualAmmount
#will keep key features like WaterfrontYN, BasementYN, BelowGradeFinishedArea, BuilderName
#LotSizeDimensions not critical, BuildingAreaTotal similar to LivingArea, so redundant, ad CoBuyerAgentFirstName can be dropped

##Numeric Distribution Review
import matplotlib.pyplot as plt

# Numeric distribution summary
numeric_cols = ['ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea',
                'LotSizeAcres', 'BedroomsTotal', 'BathroomsTotalInteger', 
                'DaysOnMarket', 'YearBuilt']

distribution_summary = sold[numeric_cols].describe(percentiles=[.05, .25, .5, .75, .95])
print("\nNumeric distribution summary:")
print(distribution_summary)

# Histograms for each numeric field
for col in numeric_cols:
    plt.figure(figsize=(8, 4))
    sold[col].dropna().hist(bins=50)
    plt.title(f'Histogram - {col}')
    plt.xlabel(col)
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(reports_folder_hist_box + rf"\histogram_{col}.png")
    plt.close()

# Boxplots for each numeric field
for col in numeric_cols:
    plt.figure(figsize=(8, 4))
    sold[[col]].boxplot()
    plt.title(f'Boxplot - {col}')
    plt.tight_layout()
    plt.savefig(reports_folder_hist_box + rf"\boxplot_{col}.png")
    plt.close()

# Save summary
distribution_summary.to_csv(reports_folder + r"\numeric_distribution_summary.csv")

###EDA Questions
## 1. Residential vs. other property type share
# Dataset was filtered to Residential only in Week 1.
# After filtering: 430,716 Residential sold records (100% of combined dataset)
# Non-residential records were removed during Week 1 aggregation.
# Before filter: 640,526 total sold rows -> 430,716 Residential (67%)


#What are the median and average close prices?
print("Median close price:", sold['ClosePrice'].median()) #825,000
print("Average close price:", sold['ClosePrice'].mean()) #1,180,000


#What does the Days on Market distribution look like?
print(sold['DaysOnMarket'].describe())
#The days on market distribution looks heavily right-skewed, so most homes sell fast but some drag the mean up to 37 days
#Max could be data error and min is -288 days, so we need to clean this out


#What percentage of homes sold above vs. below list price?
sold['priceDiff'] = sold['ClosePrice'] - sold['ListPrice']
above = (sold['priceDiff'] > 0).sum()
below = (sold['priceDiff'] < 0).sum()
equal = (sold['priceDiff'] == 0).sum()
total = len(sold)

print("Sold above:")
print(above/total * 100)
print("sold below")
print(below/total*100)
print("sold at")
print(equal/total*100) 


#Which counties have the highest median prices?
country_median = sold.groupby('CountyOrParish')['ClosePrice'].median().sort_values(ascending=False)
print(country_median.head(10))

print(sold[sold['CountyOrParish'] == 'Del Norte']['ClosePrice'].count())

# Note: Del Norte county only has 1 sale, so its median is not representative
# In future analysis, filter to counties with sufficient sample size (e.g. >= 50 sales)

#Are there any date consistency issues (e.g., close date before listing date)?
# 5. Date consistency checks
print("\nSample date values:")
print(sold[['ListingContractDate', 'PurchaseContractDate', 'CloseDate']].head(10))

# Check for null dates
print("\nMissing dates (Sold):")
print(sold[['ListingContractDate', 'PurchaseContractDate', 'CloseDate']].isnull().sum())
# Date format appears consistent (YYYY-MM-DD) but dates are still strings
# Visible issues: some CloseDate precedes PurchaseContractDate (e.g. rows 5, 9)
# Full date consistency flags (listing_after_close_flag, purchase_after_close_flag, 
# negative_timeline_flag) will be created in Weeks 4-5 after converting to datetime
# Missing: ListingContractDate=1, PurchaseContractDate=196, CloseDate=0

